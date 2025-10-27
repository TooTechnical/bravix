"""
Braivix – File Upload and Financial Parsing Route (Enhanced Accuracy)
---------------------------------------------------------------------
Uses a 2-step AI pipeline:
1️⃣ Extract numeric metrics from any-language financial reports.
2️⃣ Provide both structured values + summarized context for analysis.
"""

import io
import re
import os
import json
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from docx import Document
from pdfminer.high_level import extract_text
from openai import OpenAI

router = APIRouter()


# -------------------------------------------------------------------
#  GPT client
# -------------------------------------------------------------------
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY environment variable")
    return OpenAI(api_key=api_key)


# -------------------------------------------------------------------
#  Step 1 – Smart AI-based financial extraction
# -------------------------------------------------------------------
def extract_financial_data_with_ai(raw_text: str):
    """
    Use GPT to semantically extract key financial metrics (multi-language + table-aware).
    Automatically detects European number formatting and numeric columns from PDF text.
    """
    client = get_gpt_client()

    # 🧹 Step 1: Pre-clean
    cleaned = (
        raw_text
        .replace("(", "-")  # treat brackets as negative
        .replace(")", "")
        .replace(",", "")
        .replace("  ", " ")
        .replace(" ", " ")  # non-breaking space
    )

    # Insert a space between letters and digits (REVENUE4.1 -> REVENUE 4.1)
    import re
    cleaned = re.sub(r"([A-Za-z])(\d)", r"\1 \2", cleaned)
    cleaned = re.sub(r"(\d)([A-Za-z])", r"\1 \2", cleaned)

    # 🧠 Step 2: Prompt GPT-5/4o-mini with strong numeric extraction logic
    prompt = f"""
You are a multilingual financial data extraction engine.

The following text contains a company's financial report. Identify numeric values
for these indicators, in **millions** where applicable:

- assets
- liabilities
- equity
- revenue (or total revenue / sales / income)
- profit (or net income / result)
- ebitda (or operating income)

The text may use European notation (commas for decimals, spaces for thousands),
and the words may appear in all caps or mixed case. Example formats include:
"REVENUE 24963.9" or "ASSETS 77109.3" or "EBITDA 4865.3".

If values appear multiple times (for 2023 and 2024), pick the **most recent period**.
If a value is missing, set it to null.

Return **only valid JSON**:
{{
  "company_name": "...",
  "fiscal_year": "...",
  "assets": ...,
  "liabilities": ...,
  "equity": ...,
  "revenue": ...,
  "profit": ...,
  "ebitda": ...
}}
Text:
{cleaned[:8500]}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a financial data parser specialized in numeric table extraction."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=700,
        )

        import json
        text = response.choices[0].message.content.strip()
        print("🧠 AI extraction raw output:", text)
        return json.loads(text)

    except Exception as e:
        print("❌ AI extraction failed:", str(e))
        return {
            "company_name": None,
            "fiscal_year": None,
            "assets": None,
            "liabilities": None,
            "equity": None,
            "revenue": None,
            "profit": None,
            "ebitda": None,
        }


# -------------------------------------------------------------------
#  Step 2 – Regex backup (for fallback)
# -------------------------------------------------------------------
def extract_indicators_from_text(text: str):
    """Fallback pattern extractor (if GPT parsing fails)."""
    indicators = {}
    clean = re.sub(r"\s+", " ", text.upper())

    def find_number(keyword):
        pattern = rf"{keyword}[:\s]+([\d]+[\d\s\.\,]*)"
        match = re.search(pattern, clean)
        if match:
            num_str = match.group(1).replace(",", "").replace(" ", "")
            try:
                return float(num_str)
            except ValueError:
                return None
        return None

    return {
        "revenue": find_number("REVENUE") or find_number("TOTAL REVENUE"),
        "profit": find_number("PROFIT") or find_number("NET INCOME"),
        "assets": find_number("ASSETS"),
        "equity": find_number("EQUITY"),
        "liabilities": find_number("LIABILITIES"),
        "ebitda": find_number("EBITDA"),
    }


# -------------------------------------------------------------------
#  Upload endpoint
# -------------------------------------------------------------------
@router.post("/upload")
async def upload_file(file: UploadFile = File(...), x_api_key: str = Header(None)):
    """Handles uploads for Braivix AI – extracts text, structured metrics, and summary."""
    try:
        filename = file.filename.lower()
        contents = await file.read()

        # --- Extract text by file type ---
        if filename.endswith(".pdf"):
            raw_text = extract_text(io.BytesIO(contents)) or ""
        elif filename.endswith(".docx"):
            doc = Document(io.BytesIO(contents))
            raw_text = "\n".join(p.text for p in doc.paragraphs)
        elif filename.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(contents))
            raw_text = df.to_string(index=False)
        elif filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
            raw_text = df.to_string(index=False)
        else:
            raw_text = contents.decode("utf-8", errors="ignore")

        # --- Limit text for Vercel ---
        if len(raw_text) > 9000:
            raw_text = raw_text[:9000] + "\n\n[Text truncated for size limit]"

        if not raw_text.strip():
            raise ValueError("No readable content extracted from file.")

        # --- Step 1: AI-based extraction ---
        ai_data = extract_financial_data_with_ai(raw_text)
        financials = ai_data.get("financials", {})
        summary = ai_data.get("summary", "")

        # --- Step 2: Regex fallback if missing ---
        if not any(financials.values()):
            financials = extract_indicators_from_text(raw_text)
            print("🔁 Fallback extraction used:", financials)

        print("✅ Final extracted financials:", financials)

        return {
            "status": "success",
            "message": "File parsed successfully",
            "data": {
                "raw_text": raw_text,
                "summary": summary,
                "indicators": financials,
            },
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid or unsupported file format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File parsing failed: {str(e)}")

"""
Braivix – File Upload and Financial Parsing Route
-------------------------------------------------
Handles uploads of financial documents (PDF, Excel, CSV, DOCX)
and extracts both raw text and initial financial indicators
for AI analysis using hybrid (AI + regex) parsing.
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
def get_gpt_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY environment variable")
    return OpenAI(api_key=api_key)


# -------------------------------------------------------------------
#  AI-based financial extractor (multilingual)
# -------------------------------------------------------------------
def extract_financial_data_with_ai(raw_text: str):
    """Use GPT to semantically extract key financial metrics (multi-language support)."""
    client = get_gpt_client()

    prompt = f"""
    You are a multilingual financial document parser.
    Extract the following figures as **numeric values** only (in millions if mentioned),
    using any language present in the text. If currency symbols are used (€, $, £),
    convert to millions and remove commas.

    Return strictly JSON:
    {{
      "assets": ...,
      "liabilities": ...,
      "equity": ...,
      "revenue": ...,
      "profit": ...,
      "ebitda": ...
    }}

    If any value is missing, set it to null.

    Text excerpt:
    {raw_text[:8000]}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a precise financial data extractor."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=400,
        )

        text = response.choices[0].message.content.strip()
        print("🧠 AI extraction raw output:", text)
        return json.loads(text)

    except Exception as e:
        print("❌ AI extraction failed:", str(e))
        return {
            "assets": None,
            "liabilities": None,
            "equity": None,
            "revenue": None,
            "profit": None,
            "ebitda": None,
        }


# -------------------------------------------------------------------
#  Regex backup extractor
# -------------------------------------------------------------------
def extract_indicators_from_text(text: str):
    """Fallback pattern extractor for financial indicators."""
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

    revenue = (
        find_number("REVENUE")
        or find_number("TOTAL REVENUE")
        or find_number("INCOME")
        or find_number("NET SALES")
    )
    profit = (
        find_number("PROFIT")
        or find_number("NET INCOME")
        or find_number("RESULT OF THE PERIOD")
        or find_number("NET RESULT")
    )
    assets = find_number("TOTAL ASSETS") or find_number("ASSETS")
    equity = find_number("TOTAL EQUITY") or find_number("EQUITY ATTRIBUTABLE TO OWNERS")
    liabilities = find_number("TOTAL LIABILITIES") or find_number("LIABILITIES")
    ebitda = find_number("EBITDA") or find_number("OPERATING INCOME") or find_number("EBIT")

    indicators.update({
        "revenue": revenue,
        "profit": profit,
        "assets": assets,
        "equity": equity,
        "liabilities": liabilities,
        "ebitda": ebitda,
    })
    return indicators


# -------------------------------------------------------------------
#  Upload endpoint
# -------------------------------------------------------------------
@router.post("/upload")
async def upload_file(file: UploadFile = File(...), x_api_key: str = Header(None)):
    """
    Handles file uploads for the Braivix AI Financial Analyzer.
    Extracts text and calculates indicators via AI + regex fallback.
    """
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
        if len(raw_text) > 8000:
            raw_text = raw_text[:8000] + "\n\n[Text truncated for size limit]"

        if not raw_text.strip():
            raise ValueError("No readable content extracted from file.")

        # --- Primary: GPT AI extraction ---
        ai_data = extract_financial_data_with_ai(raw_text)
        print("✅ AI parsed financials:", ai_data)

        # --- Fallback: Regex extraction if AI failed ---
        if not any(ai_data.values()):
            ai_data = extract_indicators_from_text(raw_text)
            print("🔁 Fallback extraction used:", ai_data)

        return {
            "status": "success",
            "message": "File parsed successfully",
            "data": {
                "raw_text": raw_text,
                "indicators": ai_data,
            },
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid or unsupported file format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File parsing failed: {str(e)}")

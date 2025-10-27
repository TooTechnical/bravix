"""
Braivix – File Upload and Financial Parsing Route
-------------------------------------------------
Handles uploads of financial documents (PDF, Excel, CSV, DOCX)
and extracts both raw text and initial financial indicators
for AI analysis.
"""
import io, re, json, pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from docx import Document
from pdfminer.high_level import extract_text
from openai import OpenAI
import os

router = APIRouter()

# ----------------------------------------------------------------------
#  OpenAI client
# ----------------------------------------------------------------------
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY environment variable")
    return OpenAI(api_key=api_key)

# ----------------------------------------------------------------------
#  GPT-based extraction
# ----------------------------------------------------------------------
def extract_financial_data_with_ai(raw_text: str):
    """Use GPT to semantically extract key financial metrics (table-aware, multilingual)."""
    client = get_openai_client()

    # --- clean numbers ---
    txt = raw_text.replace("(", "-").replace(")", "")
    txt = re.sub(r"([A-Za-z])(\d)", r"\1 \2", txt)
    txt = re.sub(r"(\d)([A-Za-z])", r"\1 \2", txt)
    txt = re.sub(r"\s{2,}", " ", txt)

    prompt = f"""
You are a multilingual financial data parser.
From the text below, extract approximate numeric values (in millions where relevant)
for these keys: assets, liabilities, equity, revenue, profit, ebitda.
If a figure appears for multiple years, take the most recent.
Return only strict JSON like:
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
{txt[:8000]}
    """

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You extract numeric financial data precisely."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=600,
        )
        out = resp.choices[0].message.content.strip()
        print("🧠 GPT raw:", out)
        return json.loads(out)
    except Exception as e:
        print("❌ AI extraction failed:", e)
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

# ----------------------------------------------------------------------
#  Main upload route
# ----------------------------------------------------------------------
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Parse file and run AI extraction."""
    try:
        name = file.filename.lower()
        content = await file.read()

        if name.endswith(".pdf"):
            text = extract_text(io.BytesIO(content)) or ""
        elif name.endswith(".docx"):
            doc = Document(io.BytesIO(content))
            text = "\n".join(p.text for p in doc.paragraphs)
        elif name.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(content))
            text = df.to_string(index=False)
        elif name.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
            text = df.to_string(index=False)
        else:
            text = content.decode("utf-8", errors="ignore")

        if not text.strip():
            raise ValueError("No readable content found.")

        if len(text) > 8000:
            text = text[:8000] + "\n[Text truncated for size limit]"

        indicators = extract_financial_data_with_ai(text)

        return {
            "status": "success",
            "message": "File parsed successfully",
            "data": {
                "raw_text": text,
                "indicators": indicators,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File parsing failed: {e}")

"""
Braivix – Smart File Upload + Financial Extraction
--------------------------------------------------
Extracts key metrics from financial documents (PDF, DOCX, XLSX, CSV).
"""
import io, os, re, json, pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from docx import Document
from pdfminer.high_level import extract_text
from openai import OpenAI

router = APIRouter()

def get_openai_client():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("Missing OPENAI_API_KEY")
    return OpenAI(api_key=key)

def extract_financial_data_with_ai(raw_text: str):
    client = get_openai_client()

    cleaned = re.sub(r"\s+", " ", raw_text)
    cleaned = cleaned.replace("(", "-").replace(")", "")

    prompt = f"""
    You are a multilingual financial parser.
    Identify numeric values (millions if stated) for:
    assets, liabilities, equity, revenue, profit (net income), EBITDA/operating income.

    Output ONLY valid JSON:
    {{
      "company_name": "CMA CGM",
      "fiscal_year": "2024",
      "assets": 77109.3,
      "liabilities": 27371.4,
      "equity": 49738.0,
      "revenue": 25011.1,
      "profit": 1445.8,
      "ebitda": 4865.3
    }}

    If you cannot find a number, use null.
    Text:
    {cleaned[:8000]}
    """

    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=600,
        )
        content = resp.choices[0].message.content.strip()
        data = json.loads(content)
        return data
    except Exception as e:
        print("❌ Extraction failed:", e)
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

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        name = file.filename.lower()
        raw = await file.read()

        if name.endswith(".pdf"):
            text = extract_text(io.BytesIO(raw)) or ""
        elif name.endswith(".docx"):
            doc = Document(io.BytesIO(raw))
            text = "\n".join(p.text for p in doc.paragraphs)
        elif name.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(raw)); text = df.to_string(index=False)
        elif name.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(raw)); text = df.to_string(index=False)
        else:
            text = raw.decode("utf-8", errors="ignore")

        if len(text) > 10000:
            text = text[:10000]

        ai_data = extract_financial_data_with_ai(text)

        print("✅ Extracted:", ai_data)

        return {
            "status": "success",
            "message": "File parsed successfully",
            "data": {
                "raw_text": text,
                "indicators": ai_data,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

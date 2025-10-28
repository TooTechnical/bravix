"""
Braivix – Smart File Upload + Financial Extraction (Hybrid Parser)
-----------------------------------------------------------------
Extracts key metrics from financial documents (PDF, DOCX, XLSX, CSV)
using regex heuristics first, then GPT-4o fallback if necessary.
"""

import io, os, re, json, pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from docx import Document
from pdfminer.high_level import extract_text
from openai import OpenAI

router = APIRouter()

# -------------------------------------------------------------
#  Helpers
# -------------------------------------------------------------
def get_openai_client():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("Missing OPENAI_API_KEY")
    return OpenAI(api_key=key)


def safe_float(val):
    """Convert possible strings or None to float safely."""
    try:
        if val in [None, "null", "", "NaN"]:
            return None
        cleaned = re.sub(r"[^\d\.\-]", "", str(val))
        return float(cleaned) if cleaned else None
    except Exception:
        return None


# -------------------------------------------------------------
#  Regex-based quick extraction
# -------------------------------------------------------------
def extract_financial_data_regex(text: str):
    """Try to identify key metrics directly from raw text before using GPT."""
    data = {}
    clean_text = text.replace(",", "").replace("(", "-").replace(")", "")
    clean_text = re.sub(r"\s+", " ", clean_text)

    patterns = {
        "revenue": r"(?:total\s+)?revenue[:\s]+([\d\.\-]+)",
        "profit": r"(?:net\s+)?profit(?:\s*/\s*\(loss\))?[:\s]+([\d\.\-]+)",
        "ebitda": r"(?:EBITDA|operating\s+income)[:\s]+([\d\.\-]+)",
        "assets": r"total\s+assets[:\s]+([\d\.\-]+)",
        "liabilities": r"total\s+liabilities[:\s]+([\d\.\-]+)",
        "equity": r"(?:total\s+equity|shareholders'?[\s]+equity)[:\s]+([\d\.\-]+)",
        "fiscal_year": r"(?:for\s+the\s+year\s+ended|fiscal\s+year)[:\s]*(\d{4})",
        "company_name": r"^\s*([A-Z][A-Za-z0-9&,\.\s\-]{2,50})\s*(?:Ltd|Inc|PLC|Group|Company|Corporation|S\.A\.|N\.V\.)?"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match:
            data[key] = match.group(1)

    # Normalize numbers
    for k in ["assets", "liabilities", "equity", "revenue", "profit", "ebitda"]:
        data[k] = safe_float(data.get(k))

    # Heuristic fallback: if revenue/profit appear multiple times, pick the largest
    for key in ["revenue", "profit", "assets", "liabilities", "equity"]:
        if not data.get(key):
            matches = re.findall(rf"{key}[^0-9\-]*([\d\.\-]+)", clean_text, re.IGNORECASE)
            if matches:
                numbers = [safe_float(m) for m in matches if safe_float(m) is not None]
                if numbers:
                    data[key] = max(numbers)

    return data


# -------------------------------------------------------------
#  GPT Fallback Extraction
# -------------------------------------------------------------
def extract_financial_data_with_ai(raw_text: str):
    """Use GPT-4o only if regex did not find enough data."""
    client = get_openai_client()

    cleaned = re.sub(r"\s+", " ", raw_text)
    cleaned = cleaned.replace("(", "-").replace(")", "")

    prompt = f"""
    You are a multilingual financial parser.
    Identify numeric values (in millions if stated) for:
    assets, liabilities, equity, revenue, profit (net income), and EBITDA/operating income.

    Return ONLY valid compact JSON:
    {{
      "company_name": "...",
      "fiscal_year": "2024",
      "assets": 0.0,
      "liabilities": 0.0,
      "equity": 0.0,
      "revenue": 0.0,
      "profit": 0.0,
      "ebitda": 0.0
    }}

    If uncertain, use null.

    Text:
    {cleaned[:8000]}
    """

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=400,
        )
        content = resp.choices[0].message.content.strip()
        # Fix occasional stray text around JSON
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            raise ValueError("No JSON found in AI response")
        data = json.loads(match.group(0))
        return data
    except Exception as e:
        print("❌ GPT extraction failed:", e)
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


# -------------------------------------------------------------
#  Upload Route
# -------------------------------------------------------------
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Accepts file uploads, extracts text, then parses financial indicators."""
    try:
        name = file.filename.lower()
        raw = await file.read()

        # Extract text from supported formats
        if name.endswith(".pdf"):
            text = extract_text(io.BytesIO(raw)) or ""
        elif name.endswith(".docx"):
            doc = Document(io.BytesIO(raw))
            text = "\n".join(p.text for p in doc.paragraphs)
        elif name.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(raw))
            text = df.to_string(index=False)
        elif name.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(raw))
            text = df.to_string(index=False)
        else:
            text = raw.decode("utf-8", errors="ignore")

        if len(text) > 15000:
            text = text[:15000]

        # --- Step 1: Regex parse ---
        extracted = extract_financial_data_regex(text)
        print("🔍 Regex result:", extracted)

        # --- Step 2: AI fallback if missing core fields ---
        core_fields = ["assets", "liabilities", "equity", "revenue", "profit", "ebitda"]
        missing = sum(1 for k in core_fields if not extracted.get(k))
        ai_data = None

        if missing >= 3:
            print("⚠️ Insufficient regex data, using GPT fallback...")
            ai_data = extract_financial_data_with_ai(text)
            # merge
            for k, v in ai_data.items():
                if not extracted.get(k):
                    extracted[k] = v

        # Final cleanup: ensure all required keys exist
        for key in ["company_name", "fiscal_year", "assets", "liabilities", "equity", "revenue", "profit", "ebitda"]:
            extracted.setdefault(key, None)

        print("✅ Final extracted indicators:", extracted)

        return {
            "status": "success",
            "message": "File parsed successfully",
            "data": {
                "raw_text": text,
                "indicators": extracted,
            },
        }

    except Exception as e:
        print("❌ Upload error:", e)
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

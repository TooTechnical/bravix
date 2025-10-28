"""
Braivix – Smart File Upload + Financial Extraction
--------------------------------------------------
Hybrid AI + heuristic extraction that reliably pulls
core financial metrics from PDF/CSV/Excel/DOCX in any language.
"""
import io, os, re, json, pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from docx import Document
from pdfminer.high_level import extract_text
from openai import OpenAI

router = APIRouter()

# ----------------------------------------------------------------------
#  GPT client
# ----------------------------------------------------------------------
def get_openai_client():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("Missing OPENAI_API_KEY")
    return OpenAI(api_key=key)

# ----------------------------------------------------------------------
#  AI extraction
# ----------------------------------------------------------------------
def extract_financial_data_with_ai(raw_text: str):
    """Use GPT-4o to semantically extract key financial values."""
    client = get_openai_client()

    # Clean text for better tokenisation
    text = re.sub(r"[ \s]+", " ", raw_text.replace("(", "-").replace(")", ""))
    text = re.sub(r"([A-Za-z])(\d)", r"\1 \2", text)
    text = re.sub(r"(\d)([A-Za-z])", r"\1 \2", text)

    prompt = f"""
You are a multilingual financial-statement parser.
From the text below, identify the **most recent period's** approximate values
for these metrics (in millions if stated): assets, liabilities, equity,
revenue, profit (net income), and EBITDA/operating income.

Return ONLY valid JSON, like:
{{
  "company_name": "Example Corp",
  "fiscal_year": "2024",
  "assets": 1234.5,
  "liabilities": 678.9,
  "equity": 555.6,
  "revenue": 890.1,
  "profit": 123.4,
  "ebitda": 222.2
}}

If any value is missing, set it to null.
Text:
{text[:8000]}
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You extract numeric financial data accurately."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=700,
        )
        reply = resp.choices[0].message.content.strip()
        print("🧠 GPT raw response:", reply)
        data = json.loads(reply)
        return data
    except Exception as e:
        print("❌ AI extraction failed:", e)
        return {
            "company_name": None, "fiscal_year": None,
            "assets": None, "liabilities": None, "equity": None,
            "revenue": None, "profit": None, "ebitda": None
        }

# ----------------------------------------------------------------------
#  Heuristic backup if GPT fails
# ----------------------------------------------------------------------
def regex_backup(text: str):
    """Fallback numeric grabber."""
    t = text.upper().replace(",", "")
    def find(pats):
        for p in pats:
            m = re.search(rf"{p}[^0-9\-]+([\-]?\d+\.?\d*)", t)
            if m: return float(m.group(1))
        return None
    return {
        "revenue": find(["REVENUE","SALES","INCOME"]),
        "profit": find(["PROFIT","NET INCOME","RESULT OF THE PERIOD"]),
        "assets": find(["TOTAL ASSETS"]),
        "liabilities": find(["TOTAL LIABILITIES"]),
        "equity": find(["TOTAL EQUITY"]),
        "ebitda": find(["EBITDA","OPERATING INCOME","EBIT"])
    }

# ----------------------------------------------------------------------
#  Main upload route
# ----------------------------------------------------------------------
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Parse uploaded file and run hybrid extraction."""
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

        if len(text) > 9000:
            text = text[:9000] + "\n[Truncated for size limit]"

        ai_data = extract_financial_data_with_ai(text)

        # Fallback if all None
        if all(v in [None, 0] for v in ai_data.values()):
            print("⚙️ Using regex fallback...")
            ai_data.update(regex_backup(text))

        print("✅ Final extracted data:", ai_data)

        return {
            "status": "success",
            "message": "File parsed successfully",
            "data": {
                "raw_text": text,
                "indicators": ai_data,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File parsing failed: {e}")

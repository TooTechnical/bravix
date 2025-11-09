"""
Bravix – Bulletproof Financial Extraction (v2.1 Smart Regex Edition)
--------------------------------------------------------------------
Improved pattern matching for CMA CGM & IFRS reports.
Handles dotted lines, colons, and spaced numeric formats automatically.
"""

import io, os, re, json, pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from pdfminer.high_level import extract_text
from docx import Document
from openai import OpenAI

try:
    import camelot
except ImportError:
    camelot = None

router = APIRouter()


# ---------- Helper Utilities ----------

def get_openai_client():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("Missing OPENAI_API_KEY")
    return OpenAI(api_key=key)


def safe_float(val):
    try:
        if val in [None, "", "NaN", "null"]:
            return None
        cleaned = re.sub(r"[^\d\.\-]", "", str(val))
        return float(cleaned) if cleaned else None
    except Exception:
        return None


def detect_unit_multiplier(text: str) -> int:
    text_lower = text.lower()
    if "in millions" in text_lower or "in € million" in text_lower:
        return 1_000_000
    elif "in thousands" in text_lower or "in € thousand" in text_lower:
        return 1_000
    else:
        return 1


def normalize_label(label: str):
    label = label.lower().strip()
    replacements = {
        "assets": ["total assets", "assets"],
        "liabilities": ["total liabilities", "liabilities"],
        "equity": ["total equity", "shareholders’ equity", "shareholders' equity"],
        "revenue": ["revenue", "income", "turnover", "sales"],
        "profit": ["profit", "net income", "net result"],
        "ebitda": ["ebitda", "operating profit", "operating income"],
        "ebit": ["ebit", "earnings before interest"],
        "inventory": ["inventory", "inventories", "stock"],
        "cash": ["cash", "cash and cash equivalents"],
        "receivables": ["trade receivables", "accounts receivable", "customers"],
        "cost_of_sales": ["cost of sales", "operating expenses"],
    }
    for key, terms in replacements.items():
        for term in terms:
            if term in label:
                return key
    return None


# ---------- Regex Extraction ----------

def extract_from_text(text: str):
    """Extract values directly using regex from raw text (now handles dotted patterns)."""
    data = {}
    # Accept spaces, dots, dashes, or colons between label and number
    gap = r"[\s\.\:\-–—…]*"

    patterns = {
        "assets": rf"total assets{gap}([\d,\.]+)",
        "liabilities": rf"total liabilities{gap}([\d,\.]+)",
        "equity": rf"total equity{gap}([\d,\.]+)",
        "revenue": rf"(?:revenue|turnover|income from operations){gap}([\d,\.]+)",
        "profit": rf"(?:net profit|profit for the year|net income){gap}([\d,\.]+)",
        "ebit": rf"\bebit{gap}([\d,\.]+)",
        "ebitda": rf"\bebitda{gap}([\d,\.]+)",
        "inventory": rf"(?:inventory|inventories){gap}([\d,\.]+)",
        "cash": rf"(?:cash and cash equivalents|cash){gap}([\d,\.]+)",
        "receivables": rf"(?:trade receivables|accounts receivable){gap}([\d,\.]+)",
        "cost_of_sales": rf"(?:cost of sales|operating expenses){gap}([\d,\.]+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = safe_float(match.group(1))
            if val:
                data[key] = val

    return data


# ---------- AI Fallback ----------

def extract_with_gpt(text: str):
    client = get_openai_client()
    prompt = f"""
    You are a financial data extractor.
    Extract key values (use millions if noted) for:
    assets, liabilities, equity, revenue, profit, ebit, ebitda, cash, inventory, receivables.

    Return valid JSON only, e.g.:
    {{
      "assets": ...,
      "liabilities": ...,
      "equity": ...,
      "revenue": ...,
      "profit": ...,
      "ebit": ...,
      "ebitda": ...,
      "cash": ...,
      "inventory": ...,
      "receivables": ...
    }}
    """
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt + "\n\n" + text[:7000]}],
            temperature=0,
            max_tokens=700,
        )
        match = re.search(r"\{.*\}", res.choices[0].message.content, re.DOTALL)
        return json.loads(match.group(0)) if match else {}
    except Exception as e:
        print("❌ GPT extraction failed:", e)
        return {}


# ---------- Upload Endpoint ----------

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Accepts file, extracts core financial data via regex + fallback."""
    try:
        name = file.filename.lower()
        raw = await file.read()

        # 1️⃣ Extract text
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

        multiplier = detect_unit_multiplier(text)

        # 2️⃣ Extract with improved regex
        structured = extract_from_text(text)
        for k in structured:
            structured[k] = structured[k] * multiplier

        # 3️⃣ Try structured tables (camelot)
        if not structured and name.endswith(".pdf") and camelot:
            try:
                tables = camelot.read_pdf(io.BytesIO(raw), pages="1-end")
                for table in tables:
                    df = table.df
                    for _, row in df.iterrows():
                        joined = " ".join(str(x) for x in row.tolist())
                        key = normalize_label(joined)
                        if key:
                            nums = re.findall(r"[-+]?\d*\.\d+|\d+", joined)
                            if nums:
                                structured[key] = safe_float(nums[-1]) * multiplier
            except Exception as e:
                print("⚠️ Camelot failed:", e)

        # 4️⃣ AI Fallback if still missing
        needed = ["assets", "liabilities", "equity", "revenue", "profit"]
        if any(k not in structured for k in needed):
            gpt_data = extract_with_gpt(text)
            for k, v in gpt_data.items():
                structured.setdefault(k, v)

        # 5️⃣ Derive missing equity if possible
        if "assets" in structured and "liabilities" in structured and "equity" not in structured:
            structured["equity"] = round(structured["assets"] - structured["liabilities"], 2)

        # 6️⃣ Validation
        if structured.get("assets") and structured.get("liabilities") and structured.get("equity"):
            diff = abs((structured["liabilities"] + structured["equity"]) - structured["assets"])
            if diff > 0.05 * structured["assets"]:
                print(f"⚠️ Balance sheet mismatch ({diff})")

        print("🧾 Extracted fields for analysis:", json.dumps(structured, indent=2))

        return {
            "status": "success",
            "message": "AI financial analysis completed successfully.",
            "data": {
                "raw_text": text,
                "indicators": structured
            }
        }

    except Exception as e:
        print("❌ Upload error:", e)
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

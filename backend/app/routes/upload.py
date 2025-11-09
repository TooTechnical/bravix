"""
Bravix – Bulletproof Financial Extraction (v3 OCR-Enhanced Edition)
-------------------------------------------------------------------
✅ New:
- OCR fallback for scanned or image-based PDFs (CMA CGM, Deloitte, IFRS)
- Smarter regex with dotted-line + spaced-number detection
- Auto unit multiplier detection (millions / thousands)
"""

import io, os, re, json, pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from pdfminer.high_level import extract_text
from docx import Document
from openai import OpenAI

# OCR imports
from pdf2image import convert_from_bytes
import pytesseract

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
    """Convert messy strings to float safely."""
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

# ---------- OCR + Text Extraction ----------

def extract_text_robust(pdf_bytes: bytes) -> str:
    """Try pdfminer first; if digits are missing, use OCR fallback."""
    text = extract_text(io.BytesIO(pdf_bytes)) or ""
    if len(re.findall(r"\d", text)) < 20:  # very few numbers => try OCR
        print("🔍 OCR fallback engaged (low numeric density detected)")
        try:
            pages = convert_from_bytes(pdf_bytes, dpi=200)
            ocr_text = ""
            for page in pages:
                ocr_text += pytesseract.image_to_string(page)
            text = ocr_text
        except Exception as e:
            print("⚠️ OCR fallback failed:", e)
    return text

# ---------- Regex Extraction ----------

def extract_from_text(text: str):
    """Extract values from messy PDF text (handles line breaks, dots, NBSP, etc.)."""
    data = {}

    clean_text = (
        text.replace("\u202f", " ")
        .replace("\xa0", " ")
        .replace("·", ".")
        .replace("•", ".")
        .replace("‧", ".")
    )
    clean_text = re.sub(r"\s{2,}", " ", clean_text)
    gap = r"(?:[\s\.\:\-–—…]*|\n|\r)*"

    patterns = {
        "assets": rf"total assets{gap}([\d][\d,\.\s]+)",
        "liabilities": rf"total liabilities{gap}([\d][\d,\.\s]+)",
        "equity": rf"total equity{gap}([\d][\d,\.\s]+)",
        "revenue": rf"(?:revenue|turnover|income from operations){gap}([\d][\d,\.\s]+)",
        "profit": rf"(?:net profit|profit for the year|net income){gap}([\d][\d,\.\s]+)",
        "ebit": rf"\bebit{gap}([\d][\d,\.\s]+)",
        "ebitda": rf"\bebitda{gap}([\d][\d,\.\s]+)",
        "inventory": rf"(?:inventory|inventories){gap}([\d][\d,\.\s]+)",
        "cash": rf"(?:cash and cash equivalents|cash){gap}([\d][\d,\.\s]+)",
        "receivables": rf"(?:trade receivables|accounts receivable){gap}([\d][\d,\.\s]+)",
        "cost_of_sales": rf"(?:cost of sales|operating expenses){gap}([\d][\d,\.\s]+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match:
            val = safe_float(match.group(1))
            if val is not None:
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
    """Accepts file, extracts core financial data via OCR + regex + fallback."""
    try:
        name = file.filename.lower()
        raw = await file.read()

        # Step 1 – Text extraction
        if name.endswith(".pdf"):
            text = extract_text_robust(raw)
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

        # Step 2 – Regex extraction
        structured = extract_from_text(text)
        for k in structured:
            structured[k] = structured[k] * multiplier

        # Step 3 – Try table extraction
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

        # Step 4 – GPT fallback if still missing
        needed = ["assets", "liabilities", "equity", "revenue", "profit"]
        if any(k not in structured for k in needed):
            gpt_data = extract_with_gpt(text)
            for k, v in gpt_data.items():
                structured.setdefault(k, v)

        # Step 5 – Derive equity if missing
        if "assets" in structured and "liabilities" in structured and "equity" not in structured:
            structured["equity"] = round(structured["assets"] - structured["liabilities"], 2)

        # Step 6 – Validation
        if structured.get("assets") and structured.get("liabilities") and structured.get("equity"):
            diff = abs((structured["liabilities"] + structured["equity"]) - structured["assets"])
            if diff > 0.05 * structured["assets"]:
                print(f"⚠️ Balance mismatch detected: {diff}")

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

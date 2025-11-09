"""
Bravix – Dual-Layer Financial Extraction (v5.1 Ultra OCR + Liquidity Edition)
----------------------------------------------------------------------------
✅ 300 DPI OCR with layout preservation
✅ Combines pdfminer text + Tesseract OCR
✅ Detects current assets & liabilities for accurate liquidity ratios
✅ Handles image-only and hybrid PDFs automatically
✅ Dumps OCR text to /tmp for inspection
"""

import io, os, re, json, pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from pdfminer.high_level import extract_text
from docx import Document
from openai import OpenAI
from pdf2image import convert_from_bytes
import pytesseract

try:
    import camelot
except ImportError:
    camelot = None

router = APIRouter()

# --------------------------------------------------------------------
# 🔧 Helper Utilities
# --------------------------------------------------------------------
def get_openai_client():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("Missing OPENAI_API_KEY")
    return OpenAI(api_key=key)


def safe_float(val):
    """Convert messy numeric strings to float."""
    try:
        if val in [None, "", "NaN", "null"]:
            return None
        cleaned = re.sub(r"[^\d\.\-]", "", str(val))
        return float(cleaned) if cleaned else None
    except Exception:
        return None


def detect_unit_multiplier(text: str) -> int:
    """Detect whether values are expressed in millions or thousands."""
    text_lower = text.lower()
    if "in millions" in text_lower or "in € million" in text_lower:
        return 1_000_000
    elif "in thousands" in text_lower or "in € thousand" in text_lower:
        return 1_000
    return 1


def normalize_label(label: str):
    """Normalize label text for table extraction fallback."""
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
        "current_assets": ["current assets"],
        "current_liabilities": ["current liabilities"],
    }
    for key, terms in replacements.items():
        if any(term in label for term in terms):
            return key
    return None


# --------------------------------------------------------------------
# 🧠 OCR & Text Extraction
# --------------------------------------------------------------------
def run_ocr_high_accuracy(pdf_bytes: bytes) -> str:
    """High-accuracy OCR with layout preservation for numeric-heavy PDFs."""
    try:
        pages = convert_from_bytes(pdf_bytes, dpi=300)
    except Exception as e:
        print("❌ PDF to image conversion failed:", e)
        return ""

    ocr_text = ""
    for i, page in enumerate(pages):
        page_text = pytesseract.image_to_string(
            page,
            lang="eng",
            config="--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz,.:- "
        )
        print(f"🧾 OCR page {i+1}: {len(page_text)} chars")
        ocr_text += f"\n\n--- PAGE {i+1} ---\n\n" + page_text

    try:
        with open("/tmp/ocr_dump.txt", "w") as f:
            f.write(ocr_text)
        print("✅ OCR dump saved to /tmp/ocr_dump.txt")
    except Exception:
        pass

    return ocr_text


def extract_text_hybrid(pdf_bytes: bytes) -> str:
    """Combine pdfminer text and OCR output into one text blob."""
    text_pdfminer = extract_text(io.BytesIO(pdf_bytes)) or ""
    print(f"🧠 PDFMiner text length: {len(text_pdfminer)}")
    ocr_text = ""

    # If PDFMiner fails to extract enough digits → run OCR fallback
    if len(re.findall(r"\d", text_pdfminer)) < 20 or len(text_pdfminer) < 500:
        print("🔍 Low text density detected → running OCR fallback")
        ocr_text = run_ocr_high_accuracy(pdf_bytes)

    merged = text_pdfminer + "\n" + ocr_text
    print(f"📄 Combined text length: {len(merged)}")
    return merged


# --------------------------------------------------------------------
# 🔍 Regex Extraction
# --------------------------------------------------------------------
def extract_from_text(text: str):
    """Extract structured financial values using flexible regex patterns."""
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
        # 🧾 Balance Sheet
        "assets": rf"total\s*assets{gap}([\d][\d\s,\.]+)",
        "current_assets": rf"current\s*assets{gap}([\d][\d\s,\.]+)",
        "liabilities": rf"total\s*liabilities{gap}([\d][\d\s,\.]+)",
        "current_liabilities": rf"current\s*liabilities{gap}([\d][\d\s,\.]+)",
        "equity": rf"(?:total\s*equity|shareholders[’']?\s*funds){gap}([\d][\d\s,\.]+)",

        # 📈 Income Statement
        "revenue": rf"(?:revenue|turnover|income\s*from\s*operations){gap}([\d][\d\s,\.]+)",
        "profit": rf"(?:net\s*profit|profit\s*for\s*the\s*year|net\s*income){gap}([\d][\d\s,\.]+)",
        "ebit": rf"\bebit{gap}([\d][\d\s,\.]+)",
        "ebitda": rf"\bebitda{gap}([\d][\d\s,\.]+)",
        "cost_of_sales": rf"(?:cost\s*of\s*sales|operating\s*expenses){gap}([\d][\d\s,\.]+)",

        # 💰 Liquidity
        "cash": rf"(?:cash\s*(?:and)?\s*cash\s*equivalents|cash){gap}([\d][\d\s,\.]+)",
        "inventory": rf"(?:inventory|inventories){gap}([\d][\d\s,\.]+)",
        "receivables": rf"(?:trade\s*receivables|accounts\s*receivable){gap}([\d][\d\s,\.]+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match:
            val = safe_float(match.group(1))
            if val is not None:
                data[key] = val
    return data


# --------------------------------------------------------------------
# 🧩 GPT Fallback
# --------------------------------------------------------------------
def extract_with_gpt(text: str):
    """Ask GPT to extract missing values in valid JSON format."""
    client = get_openai_client()
    prompt = f"""
    You are a senior financial analyst. Extract numeric values (in millions if specified) for:
    assets, liabilities, equity, current assets, current liabilities, revenue, profit,
    ebit, ebitda, cash, inventory, receivables, cost of sales.

    Return valid JSON, e.g.:
    {{
      "assets": ...,
      "liabilities": ...,
      "current_assets": ...,
      "current_liabilities": ...,
      "equity": ...,
      "revenue": ...,
      "profit": ...,
      "ebit": ...,
      "ebitda": ...,
      "cash": ...,
      "inventory": ...,
      "receivables": ...,
      "cost_of_sales": ...
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


# --------------------------------------------------------------------
# 🚀 Upload Endpoint
# --------------------------------------------------------------------
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Hybrid extraction pipeline: PDFMiner + OCR + GPT fallback."""
    try:
        name = file.filename.lower()
        raw = await file.read()

        # 1️⃣ Text extraction (hybrid)
        if name.endswith(".pdf"):
            text = extract_text_hybrid(raw)
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

        # 2️⃣ Regex extraction
        structured = extract_from_text(text)
        for k in structured:
            structured[k] *= multiplier

        # 3️⃣ GPT fallback for missing values
        needed = ["assets", "liabilities", "equity", "revenue", "profit", "current_assets", "current_liabilities"]
        if any(k not in structured for k in needed):
            gpt_data = extract_with_gpt(text)
            for k, v in gpt_data.items():
                structured.setdefault(k, v)

        # 4️⃣ Derive equity if possible
        if "assets" in structured and "liabilities" in structured and "equity" not in structured:
            structured["equity"] = round(structured["assets"] - structured["liabilities"], 2)

        # 5️⃣ Validation
        if structured.get("assets") and structured.get("liabilities") and structured.get("equity"):
            diff = abs((structured["liabilities"] + structured["equity"]) - structured["assets"])
            if diff > 0.05 * structured["assets"]:
                print(f"⚠️ Balance mismatch detected: {diff}")

        print("🧾 Extracted financial data:", json.dumps(structured, indent=2))
        if not structured:
            print("⚠️ No numeric data detected. Check /tmp/ocr_dump.txt")

        return {
            "status": "success",
            "message": "Ultra OCR financial extraction completed.",
            "data": {"raw_text": text, "indicators": structured},
        }

    except Exception as e:
        print("❌ Upload error:", e)
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

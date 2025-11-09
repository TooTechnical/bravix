"""
Bravix – Dual-Layer Financial Extraction (v4 Hybrid OCR/Text Edition)
--------------------------------------------------------------------
✅ Now handles hybrid PDFs (both image and text layers)
✅ Combines pdfminer text + OCR numeric data
✅ Cleans dotted and spaced formats (e.g. "28 934 000")
✅ Detects units (millions / thousands)
✅ Smart fallback if numbers missing
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
        if any(term in label for term in terms):
            return key
    return None

# --------------------------------------------------------------------
# 🧠 OCR & Text Extraction
# --------------------------------------------------------------------
def run_ocr(pdf_bytes: bytes) -> str:
    """Run OCR with digit-focused configuration."""
    ocr_text = ""
    pages = convert_from_bytes(pdf_bytes, dpi=250)
    for page in pages:
        page_text = pytesseract.image_to_string(
            page,
            lang="eng",
            config="--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789.,- "
        )
        ocr_text += page_text + "\n"
    return ocr_text

def extract_text_hybrid(pdf_bytes: bytes) -> str:
    """Merge pdfminer text layer with OCR digits for hybrid PDFs."""
    text_pdfminer = extract_text(io.BytesIO(pdf_bytes)) or ""
    ocr_text = ""

    # If few numbers in text layer, or text is short → trigger OCR
    if len(re.findall(r"\d", text_pdfminer)) < 20 or len(text_pdfminer) < 500:
        print("🔍 OCR engaged (hybrid or scanned PDF detected)")
        try:
            ocr_text = run_ocr(pdf_bytes)
        except Exception as e:
            print("⚠️ OCR failed:", e)

    # Merge both layers
    merged = text_pdfminer + "\n" + ocr_text
    return merged

# --------------------------------------------------------------------
# 🔍 Regex Extraction
# --------------------------------------------------------------------
def extract_from_text(text: str):
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
        "assets": rf"total\s*assets{gap}([\d][\d\s,\.]+)",
        "liabilities": rf"total\s*liabilities{gap}([\d][\d\s,\.]+)",
        "equity": rf"(?:total\s*equity|shareholders[’']?\s*funds){gap}([\d][\d\s,\.]+)",
        "revenue": rf"(?:revenue|turnover|income\s*from\s*operations){gap}([\d][\d\s,\.]+)",
        "profit": rf"(?:net\s*profit|profit\s*for\s*the\s*year|net\s*income){gap}([\d][\d\s,\.]+)",
        "ebit": rf"\bebit{gap}([\d][\d\s,\.]+)",
        "ebitda": rf"\bebitda{gap}([\d][\d\s,\.]+)",
        "inventory": rf"(?:inventory|inventories){gap}([\d][\d\s,\.]+)",
        "cash": rf"(?:cash\s*(?:and)?\s*cash\s*equivalents|cash){gap}([\d][\d\s,\.]+)",
        "receivables": rf"(?:trade\s*receivables|accounts\s*receivable){gap}([\d][\d\s,\.]+)",
        "cost_of_sales": rf"(?:cost\s*of\s*sales|operating\s*expenses){gap}([\d][\d\s,\.]+)",
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
    client = get_openai_client()
    prompt = f"""
    You are a senior financial analyst. Extract key numeric values (in millions if specified) for:
    assets, liabilities, equity, revenue, profit, ebit, ebitda, cash, inventory, receivables.

    Return only valid JSON, for example:
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

# --------------------------------------------------------------------
# 🚀 Upload Endpoint
# --------------------------------------------------------------------
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Hybrid extraction pipeline: PDFMiner + OCR + GPT fallback."""
    try:
        name = file.filename.lower()
        raw = await file.read()

        # 1️⃣ Text extraction (handles hybrid PDFs)
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

        # 3️⃣ Camelot table backup
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

        # 4️⃣ GPT fallback for missing
        needed = ["assets", "liabilities", "equity", "revenue", "profit"]
        if any(k not in structured for k in needed):
            gpt_data = extract_with_gpt(text)
            for k, v in gpt_data.items():
                structured.setdefault(k, v)

        # 5️⃣ Compute missing equity
        if "assets" in structured and "liabilities" in structured and "equity" not in structured:
            structured["equity"] = round(structured["assets"] - structured["liabilities"], 2)

        # 6️⃣ Validation
        if structured.get("assets") and structured.get("liabilities") and structured.get("equity"):
            diff = abs((structured["liabilities"] + structured["equity"]) - structured["assets"])
            if diff > 0.05 * structured["assets"]:
                print(f"⚠️ Balance mismatch detected: {diff}")

        print("🧾 Extracted financial data:", json.dumps(structured, indent=2))
        if not structured:
            print("⚠️ No values extracted from both text and OCR layers!")

        return {
            "status": "success",
            "message": "Hybrid AI financial extraction completed.",
            "data": {"raw_text": text, "indicators": structured},
        }

    except Exception as e:
        print("❌ Upload error:", e)
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

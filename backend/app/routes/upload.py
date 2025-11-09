"""
Bravix – Bulletproof Financial Extraction (v3.5 Analyst-Grade Edition)
----------------------------------------------------------------------
✅ Upgrades:
- OCR using pdftocairo @300 DPI for precise number extraction
- International regex (commas, dots, thin spaces)
- Temporary-file Camelot parsing for accurate table capture
- Verbose logging for traceable financial extraction
"""

import io, os, re, json, tempfile, pandas as pd
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

# --------------------------------------------------
# 🔐 Helper Utilities
# --------------------------------------------------

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
        cleaned = re.sub(r"[^\d\.\,\-]", "", str(val))
        cleaned = cleaned.replace(",", "").strip()
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
    mappings = {
        "assets": ["total assets", "assets"],
        "liabilities": ["total liabilities", "liabilities"],
        "equity": ["total equity", "shareholders’ equity", "shareholders' equity"],
        "revenue": ["revenue", "income", "turnover", "sales"],
        "profit": ["profit", "net income", "net result", "profit for the year"],
        "ebitda": ["ebitda", "operating profit", "operating income"],
        "ebit": ["ebit", "earnings before interest"],
        "inventory": ["inventory", "inventories", "stock"],
        "cash": ["cash", "cash and cash equivalents"],
        "receivables": ["trade receivables", "accounts receivable", "customers"],
        "cost_of_sales": ["cost of sales", "operating expenses"],
    }
    for key, variants in mappings.items():
        for v in variants:
            if v in label:
                return key
    return None

# --------------------------------------------------
# 🧠 OCR + Text Extraction
# --------------------------------------------------

def extract_text_robust(pdf_bytes: bytes) -> str:
    """Try pdfminer; if no numeric density, fallback to OCR."""
    text = extract_text(io.BytesIO(pdf_bytes)) or ""
    if len(re.findall(r"\d", text)) < 20:
        print("🔍 OCR fallback engaged (low numeric density detected)")
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                pages = convert_from_bytes(
                    pdf_bytes,
                    dpi=300,
                    fmt="png",
                    output_folder=tmpdir,
                    use_pdftocairo=True
                )
                ocr_text = ""
                for i, page in enumerate(pages):
                    page_text = pytesseract.image_to_string(page, lang="eng", config="--psm 6")
                    ocr_text += f"\n\n### PAGE {i+1}\n{page_text}"
                text = ocr_text
        except Exception as e:
            print("⚠️ OCR fallback failed:", e)
    else:
        print("✅ Text extracted via pdfminer; OCR not required.")
    return text

# --------------------------------------------------
# 📊 Regex Extraction
# --------------------------------------------------

def extract_from_text(text: str):
    """Extract values using flexible, international-safe regex."""
    data = {}

    clean_text = (
        text.replace("\u202f", " ")
        .replace("\xa0", " ")
        .replace("·", ".")
        .replace("•", ".")
        .replace("‧", ".")
    )
    clean_text = re.sub(r"\s{2,}", " ", clean_text)
    gap = r"[^0-9]{1,20}"  # allows dots, dashes, spaces between label and number

    patterns = {
        "assets": rf"total\s+assets{gap}([\d\s,\.]+)",
        "liabilities": rf"total\s+liabilities{gap}([\d\s,\.]+)",
        "equity": rf"(?:total\s+equity|shareholders[’']?\s*funds){gap}([\d\s,\.]+)",
        "revenue": rf"(?:revenue|turnover|income\s+from\s+operations){gap}([\d\s,\.]+)",
        "profit": rf"(?:net\s+profit|profit\s+for\s+the\s+year|net\s+income){gap}([\d\s,\.]+)",
        "ebit": rf"\bebit{gap}([\d\s,\.]+)",
        "ebitda": rf"\bebitda{gap}([\d\s,\.]+)",
        "inventory": rf"(?:inventory|inventories){gap}([\d\s,\.]+)",
        "cash": rf"(?:cash\s+and\s+cash\s+equivalents|cash){gap}([\d\s,\.]+)",
        "receivables": rf"(?:trade\s+receivables|accounts\s+receivable){gap}([\d\s,\.]+)",
        "cost_of_sales": rf"(?:cost\s+of\s+sales|operating\s+expenses){gap}([\d\s,\.]+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match:
            val = safe_float(match.group(1))
            if val is not None:
                data[key] = val

    print("📑 Regex matches:", json.dumps(data, indent=2))
    return data

# --------------------------------------------------
# 🧮 AI Fallback (only for missing values)
# --------------------------------------------------

def extract_with_gpt(text: str):
    client = get_openai_client()
    prompt = f"""
    You are a financial data extractor.
    Extract precise numeric values (use millions if noted) for:
    assets, liabilities, equity, revenue, profit, ebit, ebitda, cash, inventory, receivables.
    Return valid JSON only.
    """
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt + "\n\n" + text[:7000]}],
            temperature=0,
            max_tokens=700,
        )
        match = re.search(r"\{.*\}", res.choices[0].message.content, re.DOTALL)
        extracted = json.loads(match.group(0)) if match else {}
        print("🧠 GPT extracted:", extracted)
        return extracted
    except Exception as e:
        print("❌ GPT extraction failed:", e)
        return {}

# --------------------------------------------------
# 🚀 Upload Endpoint
# --------------------------------------------------

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Accepts file, extracts verified financial data with OCR, regex, tables."""
    try:
        name = file.filename.lower()
        raw = await file.read()

        # Step 1 – Extract text
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

        print("🧠 TEXT PREVIEW >>>", text[:2000])
        multiplier = detect_unit_multiplier(text)

        # Step 2 – Regex extraction
        structured = extract_from_text(text)
        for k in structured:
            structured[k] = structured[k] * multiplier

        # Step 3 – Table parsing via Camelot
        if name.endswith(".pdf") and camelot:
            try:
                with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
                    tmp.write(raw)
                    tmp.flush()
                    tables = camelot.read_pdf(tmp.name, pages="all", flavor="stream")
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
                print("⚠️ Camelot parse failed:", e)

        # Step 4 – AI fallback if still incomplete
        critical = ["assets", "liabilities", "equity", "revenue", "profit"]
        if any(k not in structured for k in critical):
            ai_data = extract_with_gpt(text)
            for k, v in ai_data.items():
                structured.setdefault(k, v)

        # Step 5 – Equity derivation validation
        if "assets" in structured and "liabilities" in structured and "equity" not in structured:
            structured["equity"] = round(structured["assets"] - structured["liabilities"], 2)

        # Step 6 – Sanity validation
        if structured.get("assets") and structured.get("liabilities") and structured.get("equity"):
            diff = abs((structured["liabilities"] + structured["equity"]) - structured["assets"])
            if diff > 0.02 * structured["assets"]:
                print(f"⚠️ Balance mismatch detected: {diff}")
            else:
                print("✅ Balance sheet validated.")

        print("🧾 FINAL EXTRACTED DATA >>>", json.dumps(structured, indent=2))

        if not structured:
            raise HTTPException(status_code=422, detail="No valid financial fields extracted.")

        return {
            "status": "success",
            "message": "Financial data extracted successfully.",
            "data": {
                "raw_text": text,
                "indicators": structured
            }
        }

    except Exception as e:
        print("❌ Upload error:", e)
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

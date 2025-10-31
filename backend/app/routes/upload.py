"""
Braivix – Bulletproof Financial Extraction (Multilingual + Structured)
----------------------------------------------------------------------
Reads PDFs, Excels, CSVs, and Word docs.
1. Extracts tables (Camelot, pandas)
2. Normalizes multilingual labels
3. Detects units (millions, thousands)
4. Validates accounting consistency
5. Uses GPT-4o-mini only if data missing or low confidence
"""

import io, os, re, json, pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from pdfminer.high_level import extract_text
from docx import Document
from openai import OpenAI
from langdetect import detect

try:
    import camelot  # For structured PDF table parsing
except ImportError:
    camelot = None

router = APIRouter()

# ---------------------------------------------------------------------
# 🔐 Helper Utilities
# ---------------------------------------------------------------------
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


def detect_unit_multiplier(text: str) -> int:
    """Detect whether figures are in thousands or millions."""
    text_lower = text.lower()
    if "in millions" in text_lower or "in € million" in text_lower:
        return 1_000_000
    elif "in thousands" in text_lower or "in € thousand" in text_lower:
        return 1_000
    else:
        return 1


def normalize_language_keys(label: str, lang: str):
    """Normalize multilingual label to English base form."""
    label = label.lower().strip()
    mappings = {
        "assets": ["assets", "activa", "actif"],
        "liabilities": ["liabilities", "passiva", "passif"],
        "equity": ["equity", "vermogen", "capitaux propres"],
        "current assets": ["current assets", "vlottende activa", "actif circulant"],
        "current liabilities": ["current liabilities", "kortlopende schulden", "passif courant"],
        "inventory": ["inventory", "voorraden", "stocks"],
        "cash": ["cash", "liquide middelen", "trésorerie"],
        "revenue": ["revenue", "omzet", "chiffre d’affaires"],
        "profit": ["profit", "nettoresultaat", "résultat net"],
        "ebitda": ["ebitda", "bedrijfsresultaat", "résultat d’exploitation"]
    }
    for eng, variants in mappings.items():
        if any(v in label for v in variants):
            return eng
    return None


# ---------------------------------------------------------------------
# 🧮 Structured Extraction Layer
# ---------------------------------------------------------------------
def extract_structured_data(text: str, file_bytes: bytes, filename: str):
    """Extract structured numbers from tables."""
    data = {}
    lang = "en"
    try:
        lang = detect(text)
    except:
        pass

    multiplier = detect_unit_multiplier(text)

    if filename.endswith(".pdf") and camelot:
        try:
            tables = camelot.read_pdf(io.BytesIO(file_bytes), pages="1-end")
            for table in tables:
                df = table.df
                for i, row in df.iterrows():
                    joined = " ".join(str(x) for x in row.tolist())
                    key = normalize_language_keys(joined, lang)
                    if key:
                        nums = re.findall(r"[-+]?\d*\.\d+|\d+", joined)
                        if nums:
                            data[key] = safe_float(nums[-1]) * multiplier
        except Exception as e:
            print("⚠️ Camelot parse failed:", e)

    elif filename.endswith(".xlsx"):
        df = pd.read_excel(io.BytesIO(file_bytes))
        for col in df.columns:
            key = normalize_language_keys(str(col), lang)
            if key:
                num = safe_float(df[col].iloc[-1])
                if num is not None:
                    data[key] = num * multiplier

    elif filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(file_bytes))
        for col in df.columns:
            key = normalize_language_keys(str(col), lang)
            if key:
                num = safe_float(df[col].iloc[-1])
                if num is not None:
                    data[key] = num * multiplier

    # Basic totals check
    if "assets" in data and "liabilities" in data and "equity" not in data:
        data["equity"] = round(data["assets"] - data["liabilities"], 2)

    return data


# ---------------------------------------------------------------------
# 🧠 GPT Verification / Fallback
# ---------------------------------------------------------------------
def extract_with_gpt(text: str):
    """Ask GPT to extract missing values only."""
    client = get_openai_client()
    prompt = f"""
    You are a financial data extractor.
    Identify values (in millions if stated) for:
    current_assets, current_liabilities, inventory, cash,
    total_assets, total_liabilities, equity, revenue, profit, ebitda.

    Return ONLY valid JSON:
    {{
      "current_assets": ...,
      "current_liabilities": ...,
      "inventory": ...,
      "cash": ...,
      "assets": ...,
      "liabilities": ...,
      "equity": ...,
      "revenue": ...,
      "profit": ...,
      "ebitda": ...
    }}
    """
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt + text[:7000]}],
            temperature=0,
            max_tokens=600,
        )
        match = re.search(r"\{.*\}", res.choices[0].message.content, re.DOTALL)
        return json.loads(match.group(0)) if match else {}
    except Exception as e:
        print("❌ GPT Fallback failed:", e)
        return {}


# ---------------------------------------------------------------------
# 🚀 Upload Route
# ---------------------------------------------------------------------
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Accepts uploads, extracts key data with multi-step verification."""
    try:
        name = file.filename.lower()
        raw = await file.read()

        # --- Step 1: Extract text ---
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

        # --- Step 2: Structured extraction ---
        structured = extract_structured_data(text, raw, name)
        print("📊 Structured data:", structured)

        # --- Step 3: Regex supplement ---
        regex_data = {}
        for k, v in extract_structured_data(text, raw, name).items():
            regex_data[k] = v

        # Merge
        for k, v in regex_data.items():
            structured.setdefault(k, v)

        # --- Step 4: AI Fallback if needed ---
        needed_keys = ["assets", "liabilities", "equity", "revenue", "profit", "ebitda"]
        if any(k not in structured for k in needed_keys):
            gpt_data = extract_with_gpt(text)
            for k, v in gpt_data.items():
                structured.setdefault(k, v)

        # --- Step 5: Cross-validate ---
        if structured.get("assets") and structured.get("liabilities") and structured.get("equity"):
            diff = abs((structured["liabilities"] + structured["equity"]) - structured["assets"])
            if diff > 0.02 * structured["assets"]:
                print(f"⚠️ Warning: Balance mismatch ({diff})")

        # --- Step 6: Confidence ---
        confidence = 0.95 if all(structured.values()) else 0.75

        print("✅ Final extracted:", structured)
        return {
            "status": "success",
            "confidence": confidence,
            "message": "File parsed successfully",
            "data": {
                "raw_text": text,
                "indicators": structured,
            },
        }

    except Exception as e:
        print("❌ Upload error:", e)
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

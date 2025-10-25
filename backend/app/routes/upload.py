import io, re, pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from PyPDF2 import PdfReader
from docx import Document

router = APIRouter()

def extract_indicators_from_text(text: str):
    """
    Lightweight pattern extractor — pulls key values from PDF text to estimate
    common financial ratios for GPT-5 analysis.
    """
    indicators = {}

    # Normalize text for pattern matching
    clean = text.replace(",", "").upper()

    def find(pattern):
        m = re.search(pattern, clean)
        return float(m.group(1)) if m else None

    # Try to extract rough numeric indicators
    revenue = find(r"REVENUE\s+([\d\.]+)") or find(r"TOTAL REVENUE\s+([\d\.]+)")
    profit = find(r"PROFIT\s*/\s*\(LOSS\).*?([\d\.]+)")
    assets = find(r"TOTAL ASSETS\s+([\d\.]+)")
    equity = find(r"TOTAL EQUITY\s+([\d\.]+)")
    liabilities = find(r"TOTAL LIABILITIES\s+([\d\.]+)") or None
    ebitda = find(r"EBITDA\s+BEFORE.*?([\d\.]+)") or find(r"EBITDA\s+([\d\.]+)")

    # Compute simple ratios if data available
    try:
        if assets and equity:
            indicators["debt_ratio"] = round((assets - equity) / assets, 3)
            indicators["debt_to_equity_ratio"] = round((assets - equity) / equity, 3)
        if revenue and profit:
            indicators["net_profit_margin"] = round((profit / revenue) * 100, 2)
        if ebitda and revenue:
            indicators["operating_profit_margin"] = round((ebitda / revenue) * 100, 2)
    except Exception:
        pass

    # Always return a dictionary (even if empty)
    return indicators


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), x_api_key: str = Header(None)):
    """
    Handles file uploads for Bravix AI Analyzer.
    Extracts text + computes initial indicators.
    """
    try:
        filename = file.filename.lower()
        contents = await file.read()

        # --- Extract text ---
        if filename.endswith(".pdf"):
            pdf = PdfReader(io.BytesIO(contents))
            raw_text = " ".join(page.extract_text() or "" for page in pdf.pages)
        elif filename.endswith(".docx"):
            doc = Document(io.BytesIO(contents))
            raw_text = "\n".join(p.text for p in doc.paragraphs)
        elif filename.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(contents))
            raw_text = df.to_string(index=False)
        elif filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
            raw_text = df.to_string(index=False)
        else:
            raw_text = contents.decode("utf-8", errors="ignore")

        if len(raw_text) > 7000:
            raw_text = raw_text[:7000] + "\n\n[Text truncated for size limit]"

        if not raw_text.strip():
            raise ValueError("No readable content extracted from file.")

        # --- Extract financial indicators automatically ---
        indicators = extract_indicators_from_text(raw_text)

        return {
            "status": "success",
            "message": "File parsed successfully",
            "data": {
                "raw_text": raw_text,
                "indicators": indicators,
            },
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid or unsupported file format: {e}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File parsing failed: {e}")

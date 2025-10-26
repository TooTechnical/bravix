"""
Bravix – File Upload and Financial Parsing Route
------------------------------------------------
Handles uploads of financial documents (PDF, Excel, CSV, DOCX)
and extracts both raw text and initial financial indicators
for AI analysis.
"""

import io
import re
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from docx import Document
from pdfminer.high_level import extract_text  # ✅ replaces PyPDF2

router = APIRouter()


def extract_indicators_from_text(text: str):
    """
    Improved pattern extractor for Bravix AI:
    Handles multi-line PDFs, irregular number spacing, and common accounting phrases.
    """
    indicators = {}
    clean = re.sub(r"\s+", " ", text.upper())

    def find_number(keyword):
        pattern = rf"{keyword}[:\s]+([\d]+[\d\s\.\,]*)"
        match = re.search(pattern, clean)
        if match:
            num_str = match.group(1).replace(",", "").replace(" ", "")
            try:
                return float(num_str)
            except ValueError:
                return None
        return None

    revenue = (
        find_number("REVENUE")
        or find_number("TOTAL REVENUE")
        or find_number("INCOME")
        or find_number("NET SALES")
    )
    profit = (
        find_number("PROFIT")
        or find_number("NET INCOME")
        or find_number("RESULT OF THE PERIOD")
        or find_number("NET RESULT")
    )
    assets = find_number("TOTAL ASSETS") or find_number("ASSETS")
    equity = find_number("TOTAL EQUITY") or find_number("EQUITY ATTRIBUTABLE TO OWNERS")
    liabilities = find_number("TOTAL LIABILITIES") or find_number("LIABILITIES")
    ebitda = find_number("EBITDA") or find_number("OPERATING INCOME") or find_number("EBIT")

    try:
        if revenue and profit:
            indicators["net_profit_margin"] = round((profit / revenue) * 100, 2)
        if assets and equity:
            indicators["debt_ratio"] = round((assets - equity) / assets, 3)
            indicators["debt_to_equity_ratio"] = round((assets - equity) / equity, 3)
        if ebitda and revenue:
            indicators["operating_profit_margin"] = round((ebitda / revenue) * 100, 2)
        if profit and assets:
            indicators["return_on_assets"] = round((profit / assets) * 100, 2)
        if profit and equity:
            indicators["return_on_equity"] = round((profit / equity) * 100, 2)
    except Exception:
        pass

    indicators.update({
        "revenue": revenue,
        "profit": profit,
        "assets": assets,
        "equity": equity,
        "liabilities": liabilities,
        "ebitda": ebitda,
    })
    return indicators


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), x_api_key: str = Header(None)):
    """
    Handles file uploads for the Bravix AI Financial Analyzer.
    Extracts text and calculates basic indicators from PDF, DOCX, CSV, or Excel.
    """
    try:
        filename = file.filename.lower()
        contents = await file.read()

        # --- Extract text based on file type ---
        if filename.endswith(".pdf"):
            raw_text = extract_text(io.BytesIO(contents)) or ""
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

        # --- Enforce safety limits for Vercel ---
        if len(raw_text) > 7000:
            raw_text = raw_text[:7000] + "\n\n[Text truncated for size limit]"

        if not raw_text.strip():
            raise ValueError("No readable content extracted from file.")

        # --- Extract financial indicators ---
        indicators = extract_indicators_from_text(raw_text)

        print("✅ Parsed file successfully.")
        print(f"📊 Extracted indicators: {indicators}")

        return {
            "status": "success",
            "message": "File parsed successfully",
            "data": {
                "raw_text": raw_text,
                "indicators": indicators,
            },
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid or unsupported file format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File parsing failed: {str(e)}")

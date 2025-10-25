import io
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from PyPDF2 import PdfReader
from docx import Document

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), x_api_key: str = Header(None)):
    """
    Handles file uploads for the Bravix AI Financial Analyzer.
    Extracts readable financial data text from PDF, DOCX, XLSX, or CSV files.
    """
    try:
        filename = file.filename.lower()
        contents = await file.read()

        # --- PDF Extraction ---
        if filename.endswith(".pdf"):
            try:
                pdf = PdfReader(io.BytesIO(contents))
                raw_text = " ".join(page.extract_text() or "" for page in pdf.pages)
            except Exception as e:
                raise ValueError(f"Failed to parse PDF: {e}")

        # --- Word Document Extraction ---
        elif filename.endswith(".docx"):
            try:
                doc = Document(io.BytesIO(contents))
                raw_text = "\n".join(p.text for p in doc.paragraphs)
            except Exception as e:
                raise ValueError(f"Failed to parse DOCX: {e}")

        # --- Excel Extraction ---
        elif filename.endswith(".xlsx"):
            try:
                df = pd.read_excel(io.BytesIO(contents))
                raw_text = df.to_string(index=False)
            except Exception as e:
                raise ValueError(f"Failed to parse XLSX: {e}")

        # --- CSV Extraction ---
        elif filename.endswith(".csv"):
            try:
                df = pd.read_csv(io.BytesIO(contents))
                raw_text = df.to_string(index=False)
            except Exception as e:
                raise ValueError(f"Failed to parse CSV: {e}")

        # --- Plain Text / Unknown ---
        else:
            raw_text = contents.decode("utf-8", errors="ignore")

        # --- Safety Trim for Vercel Upload Limits ---
        if len(raw_text) > 7000:
            raw_text = raw_text[:7000] + "\n\n[Text truncated for size limit]"

        # --- Return parsed data ---
        if not raw_text.strip():
            raise ValueError("No readable content extracted from file.")

        return {
            "status": "success",
            "message": "File parsed successfully",
            "data": {
                "raw_text": raw_text,
                "indicators": {},  # optional placeholder for now
            },
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid or unsupported file format: {str(e)}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File parsing failed: {str(e)}",
        )

import re
import pytesseract
from pdf2image import convert_from_bytes
from pdfminer.high_level import extract_text
import pandas as pd
from io import BytesIO
from docx import Document

def parse_file(file):
    """
    Parses uploaded financial documents (PDF, CSV, Excel, DOCX)
    Extracts core financial data and returns structured text.
    Automatically uses OCR for scanned PDFs.
    """

    filename = file.filename.lower()
    content = file.file.read()

    # --- PDF Handling ---
    if filename.endswith(".pdf"):
        text = extract_text(BytesIO(content))

        if not text or len(text.strip()) < 100:
            # 🧠 If the PDF has little or no text, switch to OCR mode
            print("🔍 No readable text detected — switching to OCR mode...")
            images = convert_from_bytes(content)
            ocr_text = []
            for i, img in enumerate(images):
                page_text = pytesseract.image_to_string(img, lang="eng")
                ocr_text.append(page_text)
            text = "\n".join(ocr_text)

        clean_text = (
            text.replace("€", "")
            .replace(",", "")
            .replace("(", "")
            .replace(")", "")
        )
        clean_text = re.sub(r"\s+", " ", clean_text)

        # --- Keyword patterns for number extraction ---
        patterns = {
            "revenue": [
                r"(?:total\s+)?revenue[^0-9\-]+([\d.,]+)",
                r"turnover[^0-9\-]+([\d.,]+)",
                r"operating income[^0-9\-]+([\d.,]+)",
                r"income from operations[^0-9\-]+([\d.,]+)",
                r"sales[^0-9\-]+([\d.,]+)"
            ],
            "profit": [
                r"net (?:result|income|profit)[^0-9\-]+([\d.,]+)",
                r"result for the year[^0-9\-]+([\d.,]+)"
            ],
            "assets": [
                r"total assets[^0-9\-]+([\d.,]+)",
                r"assets[^0-9\-]+([\d.,]+)"
            ],
            "equity": [
                r"(?:shareholders'? )?equity[^0-9\-]+([\d.,]+)"
            ],
            "debt": [
                r"liabilities[^0-9\-]+([\d.,]+)",
                r"borrowings[^0-9\-]+([\d.,]+)",
                r"loans[^0-9\-]+([\d.,]+)",
                r"financial debt[^0-9\-]+([\d.,]+)"
            ],
        }

        def parse_number(value):
            try:
                return float(value.replace(",", "").replace(" ", ""))
            except:
                return None

        def find_value(pattern_list):
            for pattern in pattern_list:
                match = re.search(pattern, clean_text, re.IGNORECASE)
                if match:
                    val = parse_number(match.group(1))
                    if val and val > 1000:  # ignore small or irrelevant values
                        return val
            return None

        data = {key: find_value(patterns[key]) for key in patterns}
        data["raw_text"] = clean_text[:10000]
        return {"parsed_data": data}

    # --- CSV Handling ---
    elif filename.endswith(".csv"):
        df = pd.read_csv(BytesIO(content))
        return {"parsed_data": df.to_dict(orient="records")[0]}

    # --- Excel Handling ---
    elif filename.endswith((".xls", ".xlsx")):
        df = pd.read_excel(BytesIO(content))
        return {"parsed_data": df.to_dict(orient="records")[0]}

    # --- Word Document Handling ---
    elif filename.endswith(".docx"):
        doc = Document(BytesIO(content))
        text = "\n".join([p.text for p in doc.paragraphs])
        return {"parsed_data": {"raw_text": text}}

    else:
        raise ValueError("Unsupported file format.")

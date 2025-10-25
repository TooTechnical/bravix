import re
import os
import pytesseract
from pdf2image import convert_from_bytes
from pdfminer.high_level import extract_text
import pandas as pd
from io import BytesIO
from docx import Document
from openai import OpenAI


# --- Initialize GPT client safely ---
def get_gpt_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY in environment")
    return OpenAI(api_key=api_key)


# --- Helper: Clean messy text from PDFs ---
def clean_text(raw_text: str) -> str:
    text = re.sub(r"[\t]+", " ", raw_text)
    text = re.sub(r"\s{2,}", " ", text)
    text = text.replace("€", "").replace(",", "")
    text = text.replace("(", "").replace(")", "")
    text = text.replace("USD million", "")
    return text.strip()


# --- Helper: Try to parse a numeric value ---
def parse_number(value):
    try:
        return float(value.replace(",", "").replace(" ", ""))
    except Exception:
        return None


# --- Helper: Search for any pattern in list ---
def find_value(pattern_list, text):
    for pattern in pattern_list:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = parse_number(match.group(1))
            if val and val > 0:  # ignore obviously bad values
                return val
    return None


# --- Main parser function ---
def parse_file(file):
    """
    Parses uploaded financial documents (PDF, CSV, Excel, DOCX).
    Extracts key financial figures (assets, debt, equity, profit, revenue).
    Uses OCR fallback for scanned PDFs and GPT fallback for complex layouts.
    """

    filename = file.filename.lower()
    content = file.file.read()

    # --- PDF Handling ---
    if filename.endswith(".pdf"):
        text = extract_text(BytesIO(content))

        if not text or len(text.strip()) < 100:
            # 🧠 OCR fallback for scanned PDFs
            print("🔍 No readable text detected — switching to OCR mode...")
            images = convert_from_bytes(content)
            ocr_text = []
            for i, img in enumerate(images):
                page_text = pytesseract.image_to_string(img, lang="eng")
                ocr_text.append(page_text)
            text = "\n".join(ocr_text)

        text = clean_text(text)

        # --- Keyword patterns (improved for inline table style) ---
        patterns = {
            "revenue": [
                r"REVENUE[^\d]{0,10}([\d]{3,}\.?\d*)",
                r"Revenue[^\d]{0,10}([\d]{3,}\.?\d*)",
                r"turnover[^\d]{0,10}([\d]{3,}\.?\d*)",
                r"sales[^\d]{0,10}([\d]{3,}\.?\d*)"
            ],
            "profit": [
                r"PROFIT\s*/\s*LOSS\s*OF\s*THE\s*PERIOD[^\d]{0,10}([\d]{3,}\.?\d*)",
                r"net\s*(?:result|income|profit)[^\d]{0,10}([\d]{3,}\.?\d*)",
                r"profit\s*/\s*loss[^\d]{0,10}([\d]{3,}\.?\d*)",
                r"result\s*for\s*the\s*year[^\d]{0,10}([\d]{3,}\.?\d*)"
            ],
            "assets": [
                r"TOTAL\s+ASSETS[^\d]{0,10}([\d]{3,}\.?\d*)",
                r"Total\s+Assets[^\d]{0,10}([\d]{3,}\.?\d*)",
                r"ASSETS[^\d]{0,10}([\d]{3,}\.?\d*)"
            ],
            "equity": [
                r"TOTAL\s+EQUITY[^\d]{0,10}([\d]{3,}\.?\d*)",
                r"Equity\s+Attributable[^\d]{0,10}([\d]{3,}\.?\d*)",
                r"(?:Shareholders'|Owners'|Parent\s+Company)\s+Equity[^\d]{0,10}([\d]{3,}\.?\d*)"
            ],
            "debt": [
                r"TOTAL\s+LIABILITIES[^\d]{0,10}([\d]{3,}\.?\d*)",
                r"Borrowings\s+and\s+lease\s+liabilities[^\d]{0,10}([\d]{3,}\.?\d*)",
                r"liabilities[^\d]{0,10}([\d]{3,}\.?\d*)",
                r"Debt[^\d]{0,10}([\d]{3,}\.?\d*)"
            ],
        }


        data = {key: find_value(patterns[key], text) for key in patterns}

        # --- GPT Fallback ---
        missing = [k for k, v in data.items() if v is None]
        if len(missing) >= 3:  # if too many missing, call GPT
            print(f"⚠️ Regex missed many fields ({missing}) → using GPT fallback")
            try:
                client = get_gpt_client()
                prompt = f"""
                Extract these key figures from the following financial text.
                Give only numeric values (no currency signs or text).

                - Total Assets
                - Total Debt
                - Total Equity
                - Net Profit
                - Total Revenue

                Text:
                {text[:8000]}
                """

                completion = client.chat.completions.create(
                    model="gpt-5",
                    messages=[
                        {"role": "system", "content": "You are a financial data extraction model."},
                        {"role": "user", "content": prompt}
                    ]
                )

                gpt_response = completion.choices[0].message.content
                print("🤖 GPT Extraction:", gpt_response)

                for line in gpt_response.splitlines():
                    match = re.match(r"(.+?):\s*([\d\.]+)", line)
                    if match:
                        key = match.group(1).lower()
                        val = float(match.group(2))
                        if "asset" in key:
                            data["assets"] = val
                        elif "debt" in key or "liabilit" in key:
                            data["debt"] = val
                        elif "equity" in key:
                            data["equity"] = val
                        elif "profit" in key or "income" in key:
                            data["profit"] = val
                        elif "revenue" in key or "sales" in key:
                            data["revenue"] = val
            except Exception as e:
                print("❌ GPT fallback failed:", e)

        # --- Final Output ---
        print("✅ Extracted Values:", data)
        data["raw_text"] = text[:10000]
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

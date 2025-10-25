import os
import re
from pdfminer.high_level import extract_text
import pandas as pd
from io import BytesIO
from docx import Document
from openai import OpenAI


def get_gpt_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY environment variable")
    return OpenAI(api_key=api_key)


def clean_text(raw_text: str) -> str:
    """Light clean-up for financial PDFs."""
    text = re.sub(r"\s{2,}", " ", raw_text)
    text = text.replace("€", "").replace(",", "")
    text = re.sub(r"Note\d+", "", text)
    return text.strip()


def extract_financial_data_with_ai(raw_text: str):
    """Use GPT to semantically extract key financial metrics."""
    client = get_gpt_client()

    prompt = f"""
    Extract the following financial figures as pure numeric values (in millions if stated) 
    from the text below. Return the result strictly as JSON, with keys:
    ["assets", "debt", "equity", "profit", "revenue"]

    If a value is missing, set it to null.
    Do not include any explanations, just JSON.

    Text:
    {raw_text[:8000]}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are a precise financial data extractor."},
                {"role": "user", "content": prompt},
            ],
        )
        text = response.choices[0].message.content.strip()
        import json
        return json.loads(text)
    except Exception as e:
        print("❌ AI extraction failed:", str(e))
        return {
            "assets": None,
            "debt": None,
            "equity": None,
            "profit": None,
            "revenue": None
        }


def parse_file(file):
    """
    Parses uploaded financial documents (PDF, CSV, Excel, DOCX).
    Uses AI-based extraction instead of regex for reliability.
    """

    filename = file.filename.lower()
    content = file.file.read()

    try:
        # --- PDF Handling ---
        if filename.endswith(".pdf"):
            text = extract_text(BytesIO(content))
            clean = clean_text(text)

            data = extract_financial_data_with_ai(clean)
            data["raw_text"] = clean[:10000]
            print("✅ Parsed via AI:", data)
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

    except Exception as e:
        import traceback
        print("❌ Parser crashed:", e)
        traceback.print_exc()
        return {"status": "failed", "error": str(e)}

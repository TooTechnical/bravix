"""
Braivix – Report Generation & PDF Download
------------------------------------------
Generates a downloadable PDF of the last AI report.
"""
import os, json, datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from fpdf import FPDF

router = APIRouter()
TMP_PATH = "/tmp/last_analysis.json"
PDF_PATH = "/tmp/report.pdf"

class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Braivix Credit Evaluation Report", ln=True, align="C")
        self.ln(5)
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

@router.get("/report/download")
def download_report():
    if not os.path.exists(TMP_PATH):
        raise HTTPException(status_code=404, detail="No report found. Please analyze first.")

    with open(TMP_PATH) as f:
        data = json.load(f)

    structured = data.get("structured_report", {})
    summary = structured.get("summary") or data.get("analysis_raw") or "No summary available."
    scores = data.get("scores", {})
    company = data.get("data", {}).get("indicators", {}).get("company_name") or "Unknown_Company"

    pdf = PDF(); pdf.add_page(); pdf.set_font("Helvetica", "", 12)
    pdf.cell(0,10,f"Company: {company}",ln=True)
    pdf.cell(0,10,f"Date: {datetime.date.today()}",ln=True)
    pdf.cell(0,10,f"Evaluation Score: {scores.get('evaluation_score','N/A')}",ln=True)
    pdf.cell(0,10,f"Risk Category: {scores.get('risk_category','N/A')}",ln=True)
    pdf.cell(0,10,f"Credit Decision: {scores.get('credit_decision','N/A')}",ln=True)
    pdf.ln(10); pdf.multi_cell(0,8,summary); pdf.ln(10)
    pdf.set_font("Helvetica","B",12); pdf.cell(0,10,"Indicator Grades",ln=True)
    pdf.set_font("Helvetica","",10)
    for k,v in scores.get("grades",{}).items():
        pdf.cell(0,8,f"{k}: {v}/5",ln=True)
    pdf.output(PDF_PATH)

    name = "".join(c if c.isalnum() else "_" for c in company)[:30]
    filename = f"{name}_Report_{datetime.date.today()}.pdf"
    return FileResponse(PDF_PATH, filename=filename, media_type="application/pdf",
                        headers={"Cache-Control":"no-store","Access-Control-Allow-Origin":"*"})

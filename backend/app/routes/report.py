"""
Braivix – Report Generation & PDF Download
------------------------------------------
Generates downloadable AI credit reports (PDF) from the last analysis.
"""
import os, json, datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from fpdf import FPDF

router = APIRouter()

TMP_REPORT_PATH = "/tmp/last_analysis.json"
PDF_OUTPUT_PATH = "/tmp/report.pdf"

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
    """Generate and return the last AI report as a downloadable PDF."""
    if not os.path.exists(TMP_REPORT_PATH):
        raise HTTPException(status_code=404, detail="No report found. Please analyze a file first.")

    with open(TMP_REPORT_PATH, "r") as f:
        report_data = json.load(f)

    summary = report_data.get("structured_report", {}).get("summary", "No summary available.")
    scores = report_data.get("scores", {})
    eval_score = scores.get("evaluation_score", "N/A")
    risk = scores.get("risk_category", "N/A")
    decision = scores.get("credit_decision", "N/A")

    # Prepare PDF
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 12)

    pdf.cell(0, 10, f"Date: {datetime.date.today()}", ln=True)
    pdf.cell(0, 10, f"Evaluation Score: {eval_score}", ln=True)
    pdf.cell(0, 10, f"Risk Category: {risk}", ln=True)
    pdf.cell(0, 10, f"Credit Decision: {decision}", ln=True)
    pdf.ln(10)

    pdf.multi_cell(0, 8, summary)

    # Add section for indicator scores
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Indicator Grades", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for k, v in scores.get("grades", {}).items():
        pdf.cell(0, 8, f"{k}: {v}/5", ln=True)

    pdf.output(PDF_OUTPUT_PATH)

    return FileResponse(
        path=PDF_OUTPUT_PATH,
        filename=f"Braivix_Report_{datetime.date.today()}.pdf",
        media_type="application/pdf"
    )

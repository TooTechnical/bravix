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

# Paths for temporary report files (Vercel-compatible)
TMP_DIR = "/tmp"
TMP_REPORT_PATH = os.path.join(TMP_DIR, "last_analysis.json")
PDF_OUTPUT_PATH = os.path.join(TMP_DIR, "report.pdf")


# -------------------------------------------------------
# 🧾 Custom PDF Layout
# -------------------------------------------------------
class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Braivix Credit Evaluation Report", ln=True, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


# -------------------------------------------------------
# 📄 Generate & Download the Last AI Report
# -------------------------------------------------------
@router.get("/report/download")
def download_report():
    """Generate and return the last AI report as a downloadable PDF."""
    # Ensure tmp directory exists
    os.makedirs(TMP_DIR, exist_ok=True)

    if not os.path.exists(TMP_REPORT_PATH):
        raise HTTPException(status_code=404, detail="No report found. Please analyze a file first.")

    # Load last AI report data
    with open(TMP_REPORT_PATH, "r") as f:
        report_data = json.load(f)

    # Extract fields safely
    structured = report_data.get("structured_report", {})
    summary = structured.get("summary") or report_data.get("analysis_raw") or "No summary available."
    scores = report_data.get("scores", {})

    company_name = (
        report_data.get("data", {}).get("indicators", {}).get("company_name")
        or "Unknown_Company"
    )

    eval_score = scores.get("evaluation_score", "N/A")
    risk = scores.get("risk_category", "N/A")
    decision = scores.get("credit_decision", "N/A")

    # Create PDF
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 12)

    pdf.cell(0, 10, f"Company: {company_name}", ln=True)
    pdf.cell(0, 10, f"Date: {datetime.date.today()}", ln=True)
    pdf.cell(0, 10, f"Evaluation Score: {eval_score}", ln=True)
    pdf.cell(0, 10, f"Risk Category: {risk}", ln=True)
    pdf.cell(0, 10, f"Credit Decision: {decision}", ln=True)
    pdf.ln(10)

    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 8, summary)

    # Add indicator section
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Indicator Grades", ln=True)
    pdf.set_font("Helvetica", "", 10)

    for k, v in scores.get("grades", {}).items():
        pdf.cell(0, 8, f"{k}: {v}/5", ln=True)

    # Save the file
    pdf.output(PDF_OUTPUT_PATH)

    # Sanitize company name for filename
    clean_name = "".join(c if c.isalnum() else "_" for c in company_name)[:30]
    filename = f"{clean_name}_Report_{datetime.date.today()}.pdf"

    # Return downloadable PDF
    return FileResponse(
        path=PDF_OUTPUT_PATH,
        filename=filename,
        media_type="application/pdf",
        headers={
            "Cache-Control": "no-store",
            "Access-Control-Allow-Origin": "*",
        },
    )

import React, { useState } from "react";
import { jsPDF } from "jspdf";
import ReactMarkdown from "react-markdown";
import { uploadFile, analyzeData } from "../bravixApi";

// 🧩 Import Braivix report components
import FullReport from "./FullReport";

export default function Dashboard() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // 📄 Upload + AI analyze workflow
  async function handleAIAnalyze(e) {
    e.preventDefault();
    if (!file) {
      setError("Please select a file first.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Step 1️⃣ Upload to backend
      const uploadRes = await uploadFile(file);
      const parsed = uploadRes.data || uploadRes.parsed_data || {};
      if (!parsed || Object.keys(parsed).length === 0)
        throw new Error("Upload succeeded but no parsed data was returned.");

      // Step 2️⃣ Run GPT analysis
      const analyzeRes = await analyzeData(parsed, parsed.raw_text || "");
      setResult(analyzeRes);
    } catch (err) {
      console.error("AI analysis error:", err);
      setError(err.message || "Something went wrong during analysis.");
    } finally {
      setLoading(false);
    }
  }

  // 🧾 PDF export for investors
  function handleDownloadReport() {
    const doc = new jsPDF({ orientation: "portrait", unit: "pt", format: "a4" });
    doc.setFont("times", "bold");
    doc.setFontSize(20);
    doc.text("Braivix Credit Intelligence Report", 40, 60);

    doc.setFont("times", "normal");
    doc.setFontSize(12);
    const reportText = JSON.stringify(result, null, 2);
    const splitText = doc.splitTextToSize(reportText, 520);
    doc.text(splitText, 40, 90);
    doc.save("Braivix-Financial-Report.pdf");
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "#F5F7FA",
        color: "#0C2340",
        fontFamily: "'Merriweather', serif",
        padding: "3rem 1rem",
      }}
    >
      {/* HEADER */}
      <header
        style={{
          textAlign: "center",
          marginBottom: "2.5rem",
        }}
      >
        <h1 style={{ fontSize: "2.3rem", fontWeight: "700", color: "#0C2340" }}>
          Braivix AI Credit Analysis Dashboard
        </h1>
        <p
          style={{
            color: "#4B5563",
            fontSize: "1rem",
            maxWidth: "600px",
            margin: "0 auto",
            fontFamily: "'Inter', sans-serif",
          }}
        >
          Upload a company’s financial statement and let Braivix AI generate a full weighted credit
          score, benchmark, and investment-grade analysis.
        </p>
      </header>

      {/* UPLOAD PANEL */}
      <section
        style={{
          background: "#FFFFFF",
          borderRadius: "12px",
          border: "1px solid #E5E7EB",
          boxShadow: "0 2px 12px rgba(0,0,0,0.05)",
          padding: "2rem",
          maxWidth: "600px",
          margin: "0 auto 3rem",
        }}
      >
        <form onSubmit={handleAIAnalyze} style={{ textAlign: "center" }}>
          <label
            style={{
              display: "block",
              fontWeight: "600",
              marginBottom: "0.5rem",
              color: "#1F2937",
              fontFamily: "'Inter', sans-serif",
            }}
          >
            Upload Financial Document (PDF, Excel, CSV, Word)
          </label>
          <input
            type="file"
            accept=".pdf,.csv,.xls,.xlsx,.doc,.docx"
            onChange={(e) => setFile(e.target.files[0])}
            style={{
              display: "block",
              margin: "0 auto 1rem",
              padding: "0.6rem",
              width: "100%",
              border: "1px solid #D1D5DB",
              borderRadius: "8px",
              background: "#F9FAFB",
              color: "#111827",
              fontFamily: "'Inter', sans-serif",
            }}
          />
          <button
            type="submit"
            disabled={loading}
            style={{
              backgroundColor: "#0C2340",
              color: "white",
              fontWeight: "600",
              padding: "12px 36px",
              borderRadius: "10px",
              border: "none",
              cursor: "pointer",
              width: "100%",
              transition: "opacity 0.2s ease",
              fontFamily: "'Inter', sans-serif",
              opacity: loading ? 0.6 : 1,
            }}
          >
            {loading ? "Analyzing..." : "Upload & Analyze"}
          </button>
        </form>

        {error && (
          <div style={{ color: "#B23A48", marginTop: "1rem", fontWeight: "500" }}>{error}</div>
        )}
      </section>

      {/* REPORT PANEL */}
      {result && (
        <section
          style={{
            background: "#FFFFFF",
            borderRadius: "14px",
            border: "1px solid #E5E7EB",
            boxShadow: "0 4px 20px rgba(0,0,0,0.05)",
            maxWidth: "900px",
            margin: "0 auto",
            padding: "2rem",
          }}
        >
          {/* Render the structured AI Report */}
          <FullReport data={result} />

          <div style={{ textAlign: "center", marginTop: "2rem" }}>
            <button
              onClick={handleDownloadReport}
              style={{
                backgroundColor: "#0C2340",
                color: "white",
                fontWeight: "600",
                padding: "12px 24px",
                borderRadius: "8px",
                border: "none",
                cursor: "pointer",
                fontFamily: "'Inter', sans-serif",
              }}
            >
              ⬇️ Download Report (PDF)
            </button>
          </div>
        </section>
      )}

      {/* FOOTER */}
      <footer
        style={{
          marginTop: "3rem",
          textAlign: "center",
          fontSize: "0.9rem",
          color: "#6B7280",
          fontFamily: "'Inter', sans-serif",
        }}
      >
        © {new Date().getFullYear()} Braivix — AI-Assisted Financial Intelligence
      </footer>
    </div>
  );
}

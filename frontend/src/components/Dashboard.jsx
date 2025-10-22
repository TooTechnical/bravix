import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import { jsPDF } from "jspdf";
import { uploadFile, analyzeData } from "../bravixApi";

export default function Dashboard() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showIndicators, setShowIndicators] = useState(false);

  // 🧠 Handles file upload + AI analysis
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
      // 1️⃣ Upload file to backend
      const uploadRes = await uploadFile(file);
      const parsed = uploadRes.data || uploadRes.parsed_data || {};

      if (!parsed || Object.keys(parsed).length === 0) {
        throw new Error("Upload succeeded but no parsed data was returned.");
      }

      // 2️⃣ Analyze parsed data using AI
      const analyzeRes = await analyzeData(parsed, parsed.raw_text || "");
      setResult(analyzeRes);
    } catch (err) {
      console.error("AI analysis error:", err);
      setError(err.message || "Something went wrong during analysis.");
    } finally {
      setLoading(false);
    }
  }

  // ✅ Extract AI analysis text
  const aiText =
    result?.summary ||
    result?.ai_analysis ||
    result?.result?.summary ||
    result?.result?.analysis ||
    "";

  // ✅ Extract 18 indicator data if present
  const indicators = result?.financial_indicators || [];

  // ✅ Extract risk score
  const riskValue = result?.overall_health_score || null;

  function getStatusColor(status) {
    switch (status) {
      case "good":
        return "#10b981"; // green
      case "caution":
        return "#f59e0b"; // orange
      case "poor":
        return "#dc2626"; // red
      default:
        return "#6b7280"; // grey
    }
  }

  // 🧾 Generate downloadable PDF
  function handleDownloadReport() {
    const doc = new jsPDF({
      orientation: "portrait",
      unit: "pt",
      format: "a4",
    });

    doc.setFont("helvetica", "bold");
    doc.setFontSize(18);
    doc.text("Bravix AI Financial Report", 40, 50);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(12);
    const splitText = doc.splitTextToSize(aiText || "No report data available.", 520);
    doc.text(splitText, 40, 90);

    if (riskValue !== null) {
      doc.setFont("helvetica", "bold");
      doc.text(`Overall Health Score: ${riskValue}/100`, 40, 750);
    }

    doc.save("Bravix-Financial-Report.pdf");
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(180deg, #0F172A 0%, #1E293B 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        fontFamily: "'Inter', sans-serif",
        padding: "3rem 2rem",
        color: "white",
      }}
    >
      {/* Header */}
      <header style={{ textAlign: "center", marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "2.5rem", fontWeight: "700", color: "#00FFD0" }}>
          Bravix AI Financial Analyzer
        </h1>
        <p style={{ color: "#CBD5E1", fontSize: "1.1rem", maxWidth: "600px", margin: "0 auto" }}>
          Upload your company’s financial documents and let GPT-5 evaluate 18 key financial
          indicators to generate a full credit risk report.
        </p>
      </header>

      {/* Upload Panel */}
      <section
        style={{
          background: "#1E293B",
          padding: "2rem",
          borderRadius: "12px",
          boxShadow: "0 4px 25px rgba(0, 0, 0, 0.3)",
          width: "100%",
          maxWidth: "600px",
          marginBottom: "2rem",
        }}
      >
        <form onSubmit={handleAIAnalyze} style={{ textAlign: "center" }}>
          <label
            style={{
              display: "block",
              fontWeight: "600",
              color: "#E2E8F0",
              marginBottom: "0.5rem",
            }}
          >
            Upload Financial Document (PDF, CSV, Excel, Word)
          </label>
          <input
            type="file"
            accept=".pdf,.csv,.xls,.xlsx,.doc,.docx"
            onChange={(e) => setFile(e.target.files[0])}
            style={{
              display: "block",
              margin: "0 auto 1rem",
              padding: "0.5rem",
              width: "100%",
              border: "1px solid #334155",
              borderRadius: "8px",
              background: "#0F172A",
              color: "#E2E8F0",
            }}
          />
          <button
            type="submit"
            disabled={loading}
            style={{
              background: "linear-gradient(90deg, #00C48C 0%, #00FFD0 100%)",
              color: "#0F172A",
              fontWeight: "600",
              padding: "12px 36px",
              borderRadius: "10px",
              border: "none",
              cursor: "pointer",
              width: "100%",
              transition: "transform 0.2s ease, box-shadow 0.2s ease",
            }}
          >
            {loading ? "Analyzing with AI..." : "Upload & Analyze with AI"}
          </button>
        </form>

        {error && (
          <div style={{ color: "#f87171", marginTop: "1rem", fontWeight: "500" }}>
            {error}
          </div>
        )}
      </section>

      {/* Result Panel */}
      {aiText && (
        <section
          style={{
            background: "#0F172A",
            padding: "2rem",
            borderRadius: "14px",
            boxShadow: "0 6px 30px rgba(0, 0, 0, 0.4)",
            width: "100%",
            maxWidth: "800px",
            lineHeight: "1.7",
            position: "relative",
          }}
        >
          <h3 style={{ color: "#00FFD0", fontSize: "1.5rem", marginBottom: "1rem" }}>
            AI Financial Report
          </h3>

          <ReactMarkdown>{aiText}</ReactMarkdown>

          {/* Health Score Bar */}
          {riskValue !== null && (
            <div style={{ marginTop: "2rem" }}>
              <strong>Overall Health Score: </strong>
              <span
                style={{
                  fontWeight: "bold",
                  color: riskValue >= 70 ? "#10b981" : riskValue >= 40 ? "#f59e0b" : "#dc2626",
                }}
              >
                {riskValue}/100
              </span>
              <div
                style={{
                  width: "100%",
                  height: "10px",
                  background: "#1E293B",
                  borderRadius: "5px",
                  marginTop: "8px",
                }}
              >
                <div
                  style={{
                    width: `${riskValue}%`,
                    height: "100%",
                    background:
                      riskValue >= 70 ? "#10b981" : riskValue >= 40 ? "#f59e0b" : "#dc2626",
                    borderRadius: "5px",
                    transition: "width 0.5s ease",
                  }}
                />
              </div>
            </div>
          )}

          {/* Collapsible Indicator Summary */}
          {indicators.length > 0 && (
            <div style={{ marginTop: "2rem" }}>
              <button
                onClick={() => setShowIndicators(!showIndicators)}
                style={{
                  background: "linear-gradient(90deg, #00FFD0 0%, #00C48C 100%)",
                  color: "#0F172A",
                  fontWeight: "600",
                  padding: "10px 20px",
                  borderRadius: "8px",
                  border: "none",
                  cursor: "pointer",
                  width: "100%",
                  marginBottom: "1rem",
                }}
              >
                {showIndicators ? "Hide Indicator Summary" : "Show 18 Indicator Summary"}
              </button>

              {showIndicators && (
                <div
                  style={{
                    background: "#1E293B",
                    borderRadius: "10px",
                    padding: "1rem",
                    overflowY: "auto",
                    maxHeight: "400px",
                  }}
                >
                  {indicators.map((item, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "0.5rem 0",
                        borderBottom: "1px solid #334155",
                      }}
                    >
                      <span>{item.name}</span>
                      <span style={{ color: getStatusColor(item.status), fontWeight: "600" }}>
                        {item.value !== null ? item.value : "N/A"} ({item.status})
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Download Button */}
          <button
            onClick={handleDownloadReport}
            style={{
              background: "linear-gradient(90deg, #00C48C 0%, #00FFD0 100%)",
              color: "#0F172A",
              fontWeight: "600",
              padding: "10px 24px",
              borderRadius: "8px",
              border: "none",
              cursor: "pointer",
              marginTop: "1.5rem",
              width: "100%",
            }}
          >
            ⬇️ Download Report (PDF)
          </button>
        </section>
      )}

      <footer
        style={{
          marginTop: "3rem",
          fontSize: "0.9rem",
          color: "#94A3B8",
          textAlign: "center",
        }}
      >
        Prototype © Bravix – Powered by GPT-5
      </footer>
    </div>
  );
}

import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import { jsPDF } from "jspdf";
import { uploadFile, analyzeData } from "../bravixApi";

export default function Dashboard() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

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
      const uploadRes = await uploadFile(file);
      const parsed = uploadRes.data || uploadRes.parsed_data || {};

      if (!parsed || Object.keys(parsed).length === 0) {
        throw new Error("Upload succeeded but no parsed data was returned.");
      }

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
    typeof result?.ai_analysis === "string"
      ? result.ai_analysis
      : result?.ai_analysis?.analysis_raw ||
        result?.result?.summary ||
        result?.result?.analysis ||
        "";

  // ✅ Extract Risk Score
  const riskMatch = aiText.match(/(\b\d{1,3})\/?100/i);
  const riskValue = riskMatch ? parseInt(riskMatch[1], 10) : null;

  function getRiskColor(score) {
    if (score >= 70) return "#dc2626"; // red
    if (score >= 40) return "#f59e0b"; // orange
    return "#10b981"; // green
  }

  // 🧾 PDF Generator
  function handleDownloadReport() {
    const doc = new jsPDF({ orientation: "portrait", unit: "pt", format: "a4" });
    doc.setFont("helvetica", "bold");
    doc.setFontSize(18);
    doc.text("Bravix AI Financial Risk Report", 40, 50);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(12);
    const splitText = doc.splitTextToSize(aiText || "No report data available.", 520);
    doc.text(splitText, 40, 90);

    if (riskValue !== null) {
      doc.setFont("helvetica", "bold");
      doc.text(`Risk Score: ${riskValue}/100`, 40, 750);
    }

    doc.save("Bravix-Financial-Report.pdf");
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(180deg, #F9FAFB 0%, #EEF2F3 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        fontFamily: "'Inter', sans-serif",
        padding: "3rem 2rem",
      }}
    >
      {/* Header */}
      <header style={{ textAlign: "center", marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "2.5rem", fontWeight: "700", color: "#111827" }}>
          Bravix AI Financial Analyzer
        </h1>
        <p
          style={{
            color: "#4B5563",
            fontSize: "1.1rem",
            maxWidth: "600px",
            margin: "0 auto",
          }}
        >
          Upload your company’s financial data and let GPT-5 evaluate 18 key
          financial indicators to produce a full credit risk report.
        </p>
      </header>

      {/* Upload Panel */}
      <section
        style={{
          background: "#fff",
          padding: "2rem",
          borderRadius: "12px",
          boxShadow: "0 4px 20px rgba(0, 0, 0, 0.05)",
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
              color: "#374151",
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
              border: "1px solid #D1D5DB",
              borderRadius: "8px",
            }}
          />
          <button
            type="submit"
            disabled={loading}
            style={{
              background: "linear-gradient(90deg, #00C48C 0%, #00FFD0 100%)",
              color: "#fff",
              fontWeight: "600",
              padding: "12px 36px",
              borderRadius: "10px",
              border: "none",
              cursor: "pointer",
              width: "100%",
            }}
          >
            {loading ? "Analyzing with AI..." : "Upload & Analyze with AI"}
          </button>
        </form>

        {error && <div style={{ color: "red", marginTop: "1rem" }}>{error}</div>}
      </section>

      {/* Result Panel */}
      <section style={{ width: "100%", maxWidth: "800px" }}>
        {loading && (
          <div
            style={{
              textAlign: "center",
              fontWeight: "600",
              color: "#2563EB",
              marginTop: "1rem",
            }}
          >
            Processing...
          </div>
        )}

        {aiText && (
          <div
            style={{
              background: "#ffffff",
              color: "#1e293b",
              padding: "2.5rem",
              borderRadius: "14px",
              boxShadow: "0 10px 40px rgba(0,0,0,0.08)",
              lineHeight: "1.8",
              position: "relative",
              maxWidth: "800px",
              margin: "0 auto",
            }}
          >
            <h2
              style={{
                color: "#00C48C",
                marginBottom: "1rem",
                fontWeight: 700,
              }}
            >
              Bravix AI Financial Risk Report
            </h2>

            <ReactMarkdown
              components={{
                h2: ({ node, ...props }) => (
                  <h3
                    style={{
                      color: "#111827",
                      marginTop: "1.2rem",
                      borderBottom: "1px solid #e5e7eb",
                      paddingBottom: "0.4rem",
                    }}
                    {...props}
                  />
                ),
                li: ({ node, ...props }) => (
                  <li
                    style={{
                      marginLeft: "1.5rem",
                      marginBottom: "0.3rem",
                    }}
                    {...props}
                  />
                ),
              }}
            >
              {aiText}
            </ReactMarkdown>

            {/* 🟩 Risk Score Bar */}
            {riskValue !== null && (
              <div style={{ marginTop: "2rem" }}>
                <h4
                  style={{
                    fontWeight: "600",
                    color: "#334155",
                    marginBottom: "0.5rem",
                  }}
                >
                  Credit Risk Score:{" "}
                  <span
                    style={{
                      color: getRiskColor(riskValue),
                      fontWeight: "700",
                    }}
                  >
                    {riskValue}/100
                  </span>
                </h4>

                <div
                  style={{
                    width: "100%",
                    height: "16px",
                    background:
                      "linear-gradient(90deg, #10b981 0%, #f59e0b 60%, #dc2626 100%)",
                    borderRadius: "8px",
                    overflow: "hidden",
                    boxShadow: "inset 0 0 4px rgba(0,0,0,0.2)",
                  }}
                >
                  <div
                    style={{
                      width: `${riskValue}%`,
                      height: "100%",
                      background: "rgba(255,255,255,0.8)",
                      transition: "width 0.8s ease-in-out",
                    }}
                  />
                </div>

                <p
                  style={{
                    fontSize: "0.9rem",
                    color: "#64748b",
                    marginTop: "0.5rem",
                    textAlign: "right",
                  }}
                >
                  {riskValue <= 40
                    ? "🟢 Low Risk — Stable financials"
                    : riskValue <= 69
                    ? "🟠 Moderate Risk — Some caution advised"
                    : "🔴 High Risk — Review debt exposure"}
                </p>
              </div>
            )}

            {/* Download Button */}
            <div style={{ marginTop: "2rem", textAlign: "right" }}>
              <button
                onClick={handleDownloadReport}
                style={{
                  background:
                    "linear-gradient(90deg, #00C48C 0%, #00FFD0 100%)",
                  color: "#fff",
                  fontWeight: "600",
                  padding: "10px 24px",
                  borderRadius: "8px",
                  border: "none",
                  cursor: "pointer",
                  transition: "transform 0.2s ease",
                }}
                onMouseEnter={(e) =>
                  (e.target.style.transform = "translateY(-2px)")
                }
                onMouseLeave={(e) =>
                  (e.target.style.transform = "translateY(0)")
                }
              >
                ⬇️ Download Report (PDF)
              </button>
            </div>

            <div style={{ marginTop: "1.5rem", textAlign: "right" }}>
              <em style={{ color: "#64748b" }}>
                Generated by GPT-5 (Bravix AI Engine)
              </em>
            </div>
          </div>
        )}
      </section>

      <footer
        style={{
          marginTop: "3rem",
          fontSize: "0.9rem",
          color: "#6B7280",
        }}
      >
        Prototype © Bravix Powered by GPT-5
      </footer>
    </div>
  );
}

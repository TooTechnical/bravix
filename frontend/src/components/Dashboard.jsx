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
      // 1️⃣ Upload file to backend
      const uploadRes = await uploadFile(file);

      // The backend returns { status, message, data }
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

  // ✅ Safely extract AI analysis text
  const aiText =
    typeof result?.ai_analysis === "string"
      ? result.ai_analysis
      : result?.ai_analysis?.analysis_raw ||
        result?.result?.summary ||
        result?.result?.analysis ||
        "";

  // ✅ Extract risk score if present
  const riskMatch = aiText.match(/Risk Score.*?(\d+)/i);
  const riskValue = riskMatch ? parseInt(riskMatch[1], 10) : null;

  function getRiskColor(score) {
    if (score >= 70) return "#dc2626"; // red
    if (score >= 40) return "#f59e0b"; // orange
    return "#10b981"; // green
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
    doc.text("Braivix AI Financial Risk Report", 40, 50);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(12);
    const splitText = doc.splitTextToSize(
      aiText || "No report data available.",
      520
    );
    doc.text(splitText, 40, 90);

    if (riskValue !== null) {
      doc.setFont("helvetica", "bold");
      doc.text(`Risk Score: ${riskValue}/100`, 40, 750);
    }

    doc.save("Braivix-Financial-Report.pdf");
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
      {/* 🔹 Header */}
      <header style={{ textAlign: "center", marginBottom: "2rem" }}>
        <h1
          style={{
            fontSize: "2.5rem",
            fontWeight: "700",
            color: "#00FFD0",
            textShadow: "0 0 10px rgba(0, 255, 208, 0.5)",
            marginBottom: "0.5rem",
          }}
        >
          Braivix AI Financial Analyzer
        </h1>
        <p
          style={{
            color: "#9CA3AF",
            fontSize: "1.1rem",
            maxWidth: "600px",
            margin: "0 auto",
          }}
        >
          Upload your company’s financial data and let GPT-5 evaluate 18 key
          financial indicators to produce a full credit risk report.
        </p>
      </header>

      {/* 🔹 Upload Panel */}
      <section
        className="input-panel"
        style={{
          background: "#1E293B",
          padding: "2rem",
          borderRadius: "12px",
          boxShadow: "0 0 20px rgba(0, 255, 208, 0.08)",
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
              color: "#E5E7EB",
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
              border: "1px solid #374151",
              borderRadius: "8px",
              backgroundColor: "#111827",
              color: "#E5E7EB",
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
              transition: "transform 0.2s ease, box-shadow 0.2s ease",
              width: "100%",
            }}
            onMouseEnter={(e) => (e.target.style.transform = "translateY(-3px)")}
            onMouseLeave={(e) => (e.target.style.transform = "translateY(0)")}
          >
            {loading ? "Analyzing with AI..." : "Upload & Analyze with AI"}
          </button>
        </form>

        {error && (
          <div
            style={{
              color: "red",
              marginTop: "1rem",
              fontWeight: "500",
            }}
          >
            {error}
          </div>
        )}
      </section>

      {/* 🔹 Result Panel */}
      <section className="result-panel" style={{ width: "100%", maxWidth: "800px" }}>
        {loading && (
          <div
            style={{
              textAlign: "center",
              fontWeight: "600",
              color: "#00FFD0",
              marginTop: "1rem",
            }}
          >
            Processing...
          </div>
        )}

        {aiText && (
          <div
            style={{
              background: "linear-gradient(180deg, #0F172A 0%, #1E293B 100%)",
              color: "white",
              padding: "2rem",
              borderRadius: "16px",
              boxShadow:
                "0 0 25px rgba(0, 255, 208, 0.08), 0 0 60px rgba(0, 255, 208, 0.12), 0 10px 30px rgba(0,0,0,0.5)",
              lineHeight: "1.7",
              whiteSpace: "pre-wrap",
              position: "relative",
              transition: "transform 0.3s ease, box-shadow 0.3s ease",
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.boxShadow =
                "0 0 35px rgba(0, 255, 208, 0.15), 0 0 70px rgba(0, 255, 208, 0.2), 0 10px 30px rgba(0,0,0,0.6)")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.boxShadow =
                "0 0 25px rgba(0, 255, 208, 0.08), 0 0 60px rgba(0, 255, 208, 0.12), 0 10px 30px rgba(0,0,0,0.5)")
            }
          >
            <h3
              style={{
                color: "#00FFD0",
                marginBottom: "1rem",
                fontSize: "1.5rem",
                textShadow: "0 0 8px rgba(0, 255, 208, 0.5)",
              }}
            >
              AI Financial Report
            </h3>

            <ReactMarkdown>{aiText}</ReactMarkdown>

            {/* Download Button */}
            <button
              onClick={handleDownloadReport}
              style={{
                background: "linear-gradient(90deg, #00C48C 0%, #00FFD0 100%)",
                color: "#fff",
                fontWeight: "600",
                padding: "10px 24px",
                borderRadius: "8px",
                border: "none",
                cursor: "pointer",
                marginTop: "1.5rem",
                transition: "transform 0.2s ease",
              }}
              onMouseEnter={(e) => (e.target.style.transform = "translateY(-2px)")}
              onMouseLeave={(e) => (e.target.style.transform = "translateY(0)")}
            >
              ⬇️ Download Report (PDF)
            </button>

            {/* Risk Meter */}
            {riskValue !== null && (
              <div style={{ marginTop: "2rem" }}>
                <strong>Risk Score: </strong>
                <span
                  style={{
                    fontWeight: "bold",
                    color: getRiskColor(riskValue),
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
                      background: getRiskColor(riskValue),
                      borderRadius: "5px",
                      transition: "width 0.5s ease",
                    }}
                  />
                </div>
              </div>
            )}
          </div>
        )}
      </section>

      {/* 🔹 Footer */}
      <footer
        style={{
          marginTop: "3rem",
          fontSize: "0.9rem",
          color: "#9CA3AF",
        }}
      >
        Prototype © Braivix Powered by GPT-5
      </footer>
    </div>
  );
}

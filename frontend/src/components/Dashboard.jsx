import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import { uploadFile, analyzeData } from "../bravixApi";

export default function Dashboard() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleAIAnalyze(e) {
    e.preventDefault();
    if (!file) return setError("Please select a file first.");
    setLoading(true);
    setError(null);

    try {
      const uploadRes = await uploadFile(file);
      const parsed = uploadRes.parsed_data;
      const analyzeRes = await analyzeData(parsed, parsed.raw_text || "");
      setResult(analyzeRes);
    } catch (err) {
      console.error(err);
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  // Extract AI text (handles both string or object)
  const aiText =
    typeof result?.ai_analysis === "string"
      ? result.ai_analysis
      : result?.ai_analysis?.analysis_raw || "";

  // 🔍 Robust regex: catches “Risk Score: 85”, “Risk Score – 85/100”, “Risk Score (0–100): 85”
  const riskMatch = aiText.match(/Risk\s*Score[^0-9]{0,10}(\d{1,3})/i);
  const riskValue = riskMatch ? parseInt(riskMatch[1], 10) : null;

  // ✅ Color logic (modern crypto theme)
  function getRiskColor(score) {
    if (score >= 70) return "#00C48C"; // green - low risk
    if (score >= 40) return "#FFB100"; // amber - medium risk
    return "#FF5C5C"; // red - high risk
  }

  return (
    <div
      className="page dashboard"
      style={{
        background: "#F8F9FA",
        color: "#1F2937",
        minHeight: "100vh",
        padding: "40px",
        fontFamily: "'Inter', sans-serif",
      }}
    >
      <h1
        style={{
          fontSize: "2rem",
          fontWeight: "600",
          color: "#00C48C",
          marginBottom: "20px",
        }}
      >
        Braivix Financial Risk Analyzer
      </h1>

      {/* Upload Section */}
      <section
        style={{
          background: "white",
          border: "1px solid #E5E7EB",
          borderRadius: "12px",
          padding: "24px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
          maxWidth: "700px",
        }}
      >
        <form onSubmit={handleAIAnalyze}>
          <label
            style={{
              display: "block",
              fontWeight: "500",
              color: "#374151",
              marginBottom: "10px",
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
              marginBottom: "15px",
              border: "1px solid #D1D5DB",
              borderRadius: "8px",
              padding: "8px",
              width: "100%",
            }}
          />
          <button
            className="btn"
            type="submit"
            disabled={loading}
            style={{
              background: "#00C48C",
              color: "white",
              fontWeight: "600",
              padding: "10px 18px",
              borderRadius: "8px",
              border: "none",
              cursor: "pointer",
            }}
          >
            {loading ? "Analyzing with AI..." : "Upload & Analyze with AI"}
          </button>
        </form>

        {error && (
          <div
            style={{
              color: "#DC2626",
              background: "#FEE2E2",
              borderRadius: "6px",
              padding: "8px 12px",
              marginTop: "10px",
            }}
          >
            {error}
          </div>
        )}
      </section>

      {/* Results */}
      <section style={{ marginTop: "40px" }}>
        {loading && <div>Processing...</div>}

        {aiText && (
          <div
            style={{
              background: "white",
              border: "1px solid #E5E7EB",
              borderRadius: "12px",
              padding: "30px",
              boxShadow: "0 2px 10px rgba(0,0,0,0.06)",
              maxWidth: "900px",
              lineHeight: "1.75",
              marginTop: "20px",
            }}
          >
            <h3
              style={{
                fontSize: "1.25rem",
                color: "#00C48C",
                fontWeight: "600",
                marginBottom: "15px",
              }}
            >
              AI Financial Report
            </h3>

            <div
              style={{
                color: "#374151",
                fontSize: "1rem",
                whiteSpace: "pre-wrap",
              }}
            >
              <ReactMarkdown>{aiText}</ReactMarkdown>

              {/* ✅ Risk Bar Section */}
              {riskValue !== null && (
                <div
                  style={{
                    marginTop: "30px",
                    borderTop: "1px solid #E5E7EB",
                    paddingTop: "20px",
                  }}
                >
                  <strong
                    style={{
                      fontSize: "1.1rem",
                      color: "#111827",
                      display: "block",
                      marginBottom: "8px",
                    }}
                  >
                    Risk Score:{" "}
                    <span style={{ color: getRiskColor(riskValue) }}>
                      {riskValue}/100
                    </span>
                  </strong>

                  <div
                    style={{
                      width: "100%",
                      height: "14px",
                      background: "#E5E7EB",
                      borderRadius: "8px",
                      overflow: "hidden",
                      position: "relative",
                    }}
                  >
                    <div
                      style={{
                        width: `${riskValue}%`,
                        height: "100%",
                        background: `linear-gradient(90deg, ${getRiskColor(
                          riskValue
                        )}, #00FFD0)`,
                        borderRadius: "8px",
                        transition: "width 0.6s ease, background 0.4s ease",
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

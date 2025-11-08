import React, { useState } from "react";
import ScoreChart from "./ScoreChart";
import { marked } from "marked";

// Dynamically use environment variable or fallback to Fly.io backend
const API_BASE =
  import.meta.env.VITE_API_URL && import.meta.env.VITE_API_URL.trim() !== ""
    ? `${import.meta.env.VITE_API_URL}/api`
    : "https://bravix.fly.dev/api";

export default function Dashboard() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [downloading, setDownloading] = useState(false);

  // ------------------ Upload + Analyze ------------------
  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return alert("Please select a file first!");
    setLoading(true);

    try {
      const form = new FormData();
      form.append("file", file);

      // Upload the file
      const up = await fetch(`${API_BASE}/upload`, { method: "POST", body: form });
      const parsed = await up.json();

      // Run analysis
      const ai = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsed.data),
      });

      const result = await ai.json();
      console.log("✅ Analysis result:", result);
      setReport(result);
    } catch (err) {
      console.error("❌ Upload/Analysis error:", err);
      alert("Something went wrong while processing the file.");
    } finally {
      setLoading(false);
    }
  };

  // ------------------ Improved PDF Download ------------------
  const handleDownload = async () => {
    setDownloading(true);
    try {
      const response = await fetch(`${API_BASE}/report/download`);
      if (!response.ok) throw new Error("Failed to fetch PDF");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;

      // filename based on date or company class
      const filename = `Braivix_Report_${new Date().toISOString().split("T")[0]}.pdf`;
      a.download = filename;

      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("❌ PDF download failed:", err);
      alert("Failed to download PDF. Please make sure analysis was completed first.");
    } finally {
      setDownloading(false);
    }
  };

  // ------------------ Risk Color Mapping ------------------
  const riskColor = (risk) => {
    switch (risk) {
      case "Excellent":
        return "text-green-400";
      case "Good":
        return "text-lime-400";
      case "Average":
        return "text-yellow-400";
      case "Weak":
        return "text-orange-400";
      case "Critical":
        return "text-red-500";
      default:
        return "text-gray-300";
    }
  };

  const scores = report?.classification || report?.scores || {}; // ✅ Works for both new + old backend

  return (
    <div className="max-w-5xl mx-auto p-6 text-gray-200">
      <h1 className="text-3xl font-bold mb-4 text-white">Company Analysis Dashboard</h1>

      {/* Upload Form */}
      <form onSubmit={handleUpload} className="flex gap-3 items-center mb-6">
        <input
          type="file"
          accept=".pdf,.docx,.csv,.xlsx,.txt"
          onChange={(e) => setFile(e.target.files[0])}
          className="p-2 bg-gray-800 rounded-lg border border-gray-700"
        />
        <button
          type="submit"
          disabled={loading}
          className={`px-4 py-2 rounded-lg text-white ${
            loading ? "bg-gray-600 cursor-wait" : "bg-blue-600 hover:bg-blue-500"
          }`}
        >
          {loading ? "Analyzing..." : "Upload & Analyze"}
        </button>
      </form>

      {/* Report Output */}
      {report && (
        <>
          <div className="bg-gray-900 p-5 rounded-lg shadow-lg mb-6">
            <h2 className="text-xl font-semibold mb-2 text-cyan-400">
              Credit Evaluation Summary
            </h2>

            <p>
              <strong>Overall Health Score:</strong>{" "}
              {report.overall_health_score || "N/A"}
            </p>
            <p>
              <strong>Risk Category:</strong>{" "}
              <span className={riskColor(scores?.risk_category)}>
                {scores?.risk_category || "N/A"}
              </span>
            </p>
            <p>
              <strong>Credit Decision:</strong> {scores?.credit_decision || "N/A"}
            </p>
            <p>
              <strong>Company Class:</strong>{" "}
              <span className="text-indigo-400 font-semibold">
                {scores?.company_class || "N/A"}
              </span>
            </p>
            <p>
              <strong>Moody’s Rating:</strong>{" "}
              <span className="text-blue-400">
                {scores?.ratings?.Moodys || "N/A"}
              </span>
            </p>
            <p>
              <strong>S&P Rating:</strong>{" "}
              <span className="text-blue-400">
                {scores?.ratings?.["S&P"] || "N/A"}
              </span>
            </p>
          </div>

          {/* Chart */}
          <ScoreChart scores={scores?.grades} />

          {/* AI Summary */}
          <div className="mt-6 bg-gray-900 p-5 rounded-lg shadow-lg">
            <h3 className="text-lg font-semibold mb-3 text-cyan-400">Full Report</h3>
            <div
              className="prose prose-invert max-w-none"
              dangerouslySetInnerHTML={{
                __html: marked.parse(
                  report?.structured_report?.summary ||
                    report?.ai_report ||
                    report?.analysis_raw ||
                    "No report available."
                ),
              }}
            />
          </div>

          {/* Download Button */}
          <div className="flex justify-center mt-6">
            <button
              onClick={handleDownload}
              disabled={downloading}
              className={`px-5 py-2 rounded-md font-semibold transition ${
                downloading
                  ? "bg-gray-600 text-gray-300 cursor-wait"
                  : "bg-indigo-600 hover:bg-indigo-700 text-white"
              }`}
            >
              {downloading ? "📄 Preparing PDF..." : "📄 Download Report"}
            </button>
          </div>
        </>
      )}
    </div>
  );
}

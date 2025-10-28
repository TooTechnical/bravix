import React, { useState } from "react";
import ScoreChart from "./ScoreChart";

const API_BASE = "https://braivix.vercel.app/api"; // ✅ your deployed backend

export default function Dashboard() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [downloading, setDownloading] = useState(false);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return alert("Please select a file first!");
    setLoading(true);

    try {
      // Upload file
      const formData = new FormData();
      formData.append("file", file);

      const uploadRes = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData,
      });
      const uploadJson = await uploadRes.json();
      console.log("✅ File upload response:", uploadJson);

      // Run AI analysis
      const analyzeRes = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(uploadJson.data),
      });
      const analyzeJson = await analyzeRes.json();
      console.log("✅ AI analysis response:", analyzeJson);

      setReport(analyzeJson);
    } catch (err) {
      console.error("❌ Error analyzing:", err);
      alert("Something went wrong while processing the file.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    setDownloading(true);
    try {
      // Open the generated report directly
      window.open(`${API_BASE}/report/download`, "_blank");
    } catch (err) {
      console.error("❌ PDF download failed:", err);
      alert("Could not download the report.");
    } finally {
      // short timeout so the loading button isn't instant
      setTimeout(() => setDownloading(false), 2000);
    }
  };

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

      {/* Report Display */}
      {report && (
        <>
          <div className="bg-gray-900 p-5 rounded-lg shadow-lg mb-6">
            <h2 className="text-xl font-semibold mb-2 text-cyan-400">
              Credit Evaluation Summary
            </h2>
            <p>
              <strong>Weighted Credit Score:</strong>{" "}
              {report.scores?.weighted_credit_score}
            </p>
            <p>
              <strong>Evaluation Score:</strong> {report.scores?.evaluation_score} / 100
            </p>
            <p>
              <strong>Risk Category:</strong> {report.scores?.risk_category}
            </p>
            <p>
              <strong>Credit Decision:</strong> {report.scores?.credit_decision}
            </p>
          </div>

          {/* Chart Visualization */}
          <ScoreChart scores={report.scores?.grades} />

          {/* Full AI Text Report */}
          <div className="mt-6 bg-gray-900 p-5 rounded-lg shadow-lg whitespace-pre-wrap">
            <h3 className="text-lg font-semibold mb-3 text-cyan-400">Full Report</h3>
            <p>{report.analysis_raw}</p>
          </div>

          {/* 📄 Download Report Button */}
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

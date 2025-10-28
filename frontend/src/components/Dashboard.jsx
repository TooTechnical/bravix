import React, { useState } from "react";
import ScoreChart from "./ScoreChart";
import { marked } from "marked";

const API_BASE = "https://braivix.vercel.app/api";

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
      const form = new FormData();
      form.append("file", file);
      const up = await fetch(`${API_BASE}/upload`, { method: "POST", body: form });
      const parsed = await up.json();
      const ai = await fetch(`${API_BASE}/analyze`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsed.data)
      });
      const result = await ai.json();
      setReport(result);
    } catch (err) {
      console.error(err);
      alert("Something went wrong while processing the file.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    setDownloading(true);
    window.open(`${API_BASE}/report/download`, "_blank");
    setTimeout(() => setDownloading(false), 2000);
  };

  return (
    <div className="max-w-5xl mx-auto p-6 text-gray-200">
      <h1 className="text-3xl font-bold mb-4 text-white">Company Analysis Dashboard</h1>

      <form onSubmit={handleUpload} className="flex gap-3 items-center mb-6">
        <input type="file" accept=".pdf,.docx,.csv,.xlsx,.txt"
               onChange={(e)=>setFile(e.target.files[0])}
               className="p-2 bg-gray-800 rounded-lg border border-gray-700"/>
        <button type="submit" disabled={loading}
          className={`px-4 py-2 rounded-lg text-white ${
            loading ? "bg-gray-600 cursor-wait":"bg-blue-600 hover:bg-blue-500"}`}>
          {loading ? "Analyzing..." : "Upload & Analyze"}
        </button>
      </form>

      {report && (
        <>
          <div className="bg-gray-900 p-5 rounded-lg shadow-lg mb-6">
            <h2 className="text-xl font-semibold mb-2 text-cyan-400">Credit Evaluation Summary</h2>
            <p><strong>Weighted Credit Score:</strong> {report.scores?.weighted_credit_score}</p>
            <p><strong>Evaluation Score:</strong> {report.scores?.evaluation_score} / 100</p>
            <p><strong>Risk Category:</strong> {report.scores?.risk_category}</p>
            <p><strong>Credit Decision:</strong> {report.scores?.credit_decision}</p>
          </div>

          <ScoreChart scores={report.scores?.grades} />

          <div className="mt-6 bg-gray-900 p-5 rounded-lg shadow-lg">
            <h3 className="text-lg font-semibold mb-3 text-cyan-400">Full Report</h3>
            <div className="prose prose-invert max-w-none"
                 dangerouslySetInnerHTML={{
                   __html: marked.parse(
                     report?.structured_report?.summary ||
                     report?.analysis_raw || "No report available."
                   )
                 }}/>
          </div>

          <div className="flex justify-center mt-6">
            <button onClick={handleDownload} disabled={downloading}
              className={`px-5 py-2 rounded-md font-semibold transition ${
                downloading
                  ? "bg-gray-600 text-gray-300 cursor-wait"
                  : "bg-indigo-600 hover:bg-indigo-700 text-white"}`}>
              {downloading ? "📄 Preparing PDF..." : "📄 Download Report"}
            </button>
          </div>
        </>
      )}
    </div>
  );
}

import React from "react";

/**
 * FullReport Component
 * --------------------
 * Displays a clean, institutional-grade company analysis report
 * using the structured JSON returned by the backend.
 *
 * Props:
 * - report (object): structured_report from the backend response
 * - onDownload (function): optional callback for PDF download
 */

export default function FullReport({ report = {}, onDownload }) {
  if (!report || Object.keys(report).length === 0) {
    return (
      <div className="text-center text-gray-500 mt-8">
        No report data available. Please upload a financial document and analyze it.
      </div>
    );
  }

  const {
    company_name,
    analysis_timestamp,
    scores = {},
    summary = {},
    final_evaluation = {},
  } = report;

  const { weighted_credit_score, evaluation_score, risk_category, credit_decision } = scores;

  return (
    <div
      className="w-full max-w-4xl mx-auto mt-10 bg-white text-gray-800 rounded-2xl shadow-md p-8 border border-gray-200"
      style={{ fontFamily: "'Inter', sans-serif" }}
    >
      {/* Header */}
      <h2 className="text-3xl font-bold text-gray-900 mb-2">
        Company Analysis Report
      </h2>
      <p className="text-sm text-gray-500 mb-6">
        Analysis generated on{" "}
        {analysis_timestamp
          ? new Date(analysis_timestamp).toLocaleDateString()
          : "Unavailable"}
      </p>

      {/* Credit Summary */}
      <section className="bg-gray-50 rounded-xl p-6 mb-8 border border-gray-200">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">
          Credit Evaluation Summary
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <p className="text-sm text-gray-500">Weighted Credit Score</p>
            <p className="text-2xl font-semibold text-gray-900">
              {weighted_credit_score || "-"}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Evaluation Score</p>
            <p className="text-2xl font-semibold text-gray-900">
              {evaluation_score ? `${evaluation_score} / 100` : "- / 100"}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Risk Category</p>
            <p
              className={`text-2xl font-semibold ${
                risk_category === "Excellent"
                  ? "text-green-600"
                  : risk_category === "Good"
                  ? "text-green-500"
                  : risk_category === "Average"
                  ? "text-yellow-500"
                  : risk_category === "Weak"
                  ? "text-orange-500"
                  : "text-red-600"
              }`}
            >
              {risk_category || "-"}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Credit Decision</p>
            <p className="text-2xl font-semibold text-gray-900">
              {credit_decision || "-"}
            </p>
          </div>
        </div>
      </section>

      {/* Executive Overview */}
      {summary?.executive_overview && (
        <section className="mb-8">
          <h3 className="text-xl font-semibold mb-2 text-gray-800">
            Executive Overview
          </h3>
          <p className="text-gray-700 leading-relaxed">
            {summary.executive_overview}
          </p>
        </section>
      )}

      {/* Strengths and Weaknesses */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-10">
        <div>
          <h4 className="text-lg font-semibold text-green-700 mb-2">
            Key Strengths
          </h4>
          <ul className="list-disc list-inside text-gray-700 space-y-1">
            {(summary.primary_strengths || []).map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
        <div>
          <h4 className="text-lg font-semibold text-red-700 mb-2">
            Key Weaknesses
          </h4>
          <ul className="list-disc list-inside text-gray-700 space-y-1">
            {(summary.primary_weaknesses || []).map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      </section>

      {/* Final Evaluation */}
      <section className="bg-gray-50 border border-gray-200 rounded-xl p-6 mb-8">
        <h3 className="text-xl font-semibold text-gray-800 mb-3">
          Final Evaluation Summary
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <p className="text-sm text-gray-500">Weighted Score</p>
            <p className="text-lg font-semibold text-gray-800">
              {final_evaluation.weighted_credit_score || "-"}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Evaluation</p>
            <p className="text-lg font-semibold text-gray-800">
              {final_evaluation.evaluation_score || "-"}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Risk</p>
            <p className="text-lg font-semibold text-gray-800">
              {final_evaluation.risk_category || "-"}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Decision</p>
            <p className="text-lg font-semibold text-gray-800">
              {final_evaluation.credit_decision || "-"}
            </p>
          </div>
        </div>
      </section>

      {/* Download Button */}
      {onDownload && (
        <div className="text-center">
          <button
            onClick={onDownload}
            className="bg-indigo-700 text-white px-5 py-2 rounded-lg shadow hover:bg-indigo-800 transition"
          >
            ⬇️ Download Report (PDF)
          </button>
        </div>
      )}
    </div>
  );
}

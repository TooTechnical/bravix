import React from "react";

export default function ScoreSummaryCard({
  weightedScore,
  evaluationScore,
  riskCategory,
  creditDecision,
  summary,
}) {
  return (
    <section
      style={{
        background: "#F9FAFB",
        border: "1px solid #E5E7EB",
        borderRadius: "10px",
        padding: "1.5rem",
      }}
    >
      <h3
        style={{
          fontSize: "1.25rem",
          fontWeight: "700",
          color: "#0C2340",
          marginBottom: "1rem",
        }}
      >
        Credit Evaluation Summary
      </h3>

      <p style={{ color: "#374151", lineHeight: 1.6 }}>{summary?.executive_overview}</p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
          gap: "1rem",
          marginTop: "1.5rem",
          textAlign: "center",
        }}
      >
        <div>
          <div style={{ fontSize: "1.6rem", fontWeight: "700", color: "#0C2340" }}>
            {weightedScore?.toFixed(2) || "-"}
          </div>
          <div style={{ color: "#6B7280", fontSize: "0.9rem" }}>Weighted Credit Score</div>
        </div>

        <div>
          <div style={{ fontSize: "1.6rem", fontWeight: "700", color: "#0C2340" }}>
            {evaluationScore?.toFixed(0) || "-"} / 100
          </div>
          <div style={{ color: "#6B7280", fontSize: "0.9rem" }}>Evaluation Score</div>
        </div>

        <div>
          <div
            style={{
              fontSize: "1.2rem",
              fontWeight: "600",
              color:
                riskCategory === "Excellent"
                  ? "#16A34A"
                  : riskCategory === "Good"
                  ? "#059669"
                  : riskCategory === "Average"
                  ? "#CA8A04"
                  : riskCategory === "Weak"
                  ? "#DC2626"
                  : "#6B7280",
            }}
          >
            {riskCategory || "—"}
          </div>
          <div style={{ color: "#6B7280", fontSize: "0.9rem" }}>Risk Category</div>
        </div>

        <div>
          <div
            style={{
              fontWeight: "700",
              color: "#0C2340",
            }}
          >
            {creditDecision || "—"}
          </div>
          <div style={{ color: "#6B7280", fontSize: "0.9rem" }}>Credit Decision</div>
        </div>
      </div>
    </section>
  );
}

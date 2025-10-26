import React from "react";

export default function AnalystMetricsGrid({ metrics }) {
  const entries = Object.entries(metrics).filter(
    ([key]) => key !== "comment"
  );

  return (
    <section
      style={{
        background: "#F9FAFB",
        border: "1px solid #E5E7EB",
        borderRadius: "10px",
        padding: "1.5rem",
      }}
    >
      <h3 style={{ fontSize: "1.25rem", fontWeight: "700", color: "#0C2340", marginBottom: "1rem" }}>
        Analyst Metrics
      </h3>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "1rem",
        }}
      >
        {entries.map(([key, val]) => (
          <div
            key={key}
            style={{
              background: "#FFFFFF",
              border: "1px solid #E5E7EB",
              borderRadius: "8px",
              padding: "0.8rem 1rem",
              boxShadow: "0 1px 2px rgba(0,0,0,0.05)",
            }}
          >
            <div style={{ fontWeight: "600", color: "#1F2937" }}>
              {key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
            </div>
            <div style={{ color: "#0C2340", fontWeight: "700", fontSize: "1rem" }}>
              {typeof val === "number" ? val.toFixed(2) : val}
            </div>
          </div>
        ))}
      </div>

      {metrics.comment && (
        <p style={{ marginTop: "1rem", color: "#6B7280", fontSize: "0.9rem" }}>
          {metrics.comment}
        </p>
      )}
    </section>
  );
}

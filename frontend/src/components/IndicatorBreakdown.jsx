import React from "react";

export default function IndicatorBreakdown({ breakdown }) {
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
        Quantitative Breakdown
      </h3>

      {breakdown.map((cat, i) => (
        <div key={i} style={{ marginBottom: "1.5rem" }}>
          <h4 style={{ fontWeight: "600", color: "#1F2937", marginBottom: "0.3rem" }}>
            {cat.category}
          </h4>
          <p style={{ color: "#6B7280", fontSize: "0.9rem", marginBottom: "0.5rem" }}>
            {cat.comment}
          </p>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#E5E7EB" }}>
                <th style={thStyle}>Indicator</th>
                <th style={thStyle}>Grade</th>
                <th style={thStyle}>Value</th>
              </tr>
            </thead>
            <tbody>
              {cat.indicators.map((ind, j) => (
                <tr key={j} style={{ borderBottom: "1px solid #E5E7EB" }}>
                  <td style={tdStyle}>{ind.name}</td>
                  <td style={tdStyle}>{ind.grade}</td>
                  <td style={tdStyle}>{ind.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </section>
  );
}

const thStyle = {
  textAlign: "left",
  padding: "8px",
  fontWeight: "600",
  fontSize: "0.9rem",
  color: "#0C2340",
};

const tdStyle = {
  padding: "8px",
  fontSize: "0.9rem",
  color: "#374151",
};

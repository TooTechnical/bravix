import React from "react";

export default function StrategicActions({ actions, final }) {
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
        Strategic Recommendations
      </h3>

      <ul style={{ marginLeft: "1.2rem", color: "#374151", lineHeight: 1.6 }}>
        {actions.map((act, i) => (
          <li key={i} style={{ marginBottom: "0.3rem" }}>
            {act}
          </li>
        ))}
      </ul>

      <div
        style={{
          borderTop: "1px solid #E5E7EB",
          marginTop: "1.5rem",
          paddingTop: "1rem",
        }}
      >
        <h4 style={{ fontWeight: "600", color: "#0C2340" }}>Final Evaluation</h4>
        <p style={{ color: "#374151", marginTop: "0.3rem" }}>
          <strong>Credit Decision:</strong> {final?.credit_decision || "—"}
        </p>
        <p style={{ color: "#374151" }}>
          <strong>Outlook:</strong> {final?.outlook || "—"}
        </p>
      </div>
    </section>
  );
}

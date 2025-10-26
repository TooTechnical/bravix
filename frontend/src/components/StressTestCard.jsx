import React from "react";

export default function StressTestCard({ stress }) {
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
        Stress Test Scenario
      </h3>

      <p style={{ marginBottom: "0.6rem" }}>
        <strong>Scenario:</strong> {stress.scenario}
      </p>
      <p>
        <strong>Base Score:</strong> {stress.base_score} →{" "}
        <strong>Stressed Score:</strong> {stress.stressed_score}
      </p>
      <p>
        <strong>Impact:</strong> {stress.impact_percent}% ({stress.comment})
      </p>
    </section>
  );
}

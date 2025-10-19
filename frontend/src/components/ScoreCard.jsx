import React from 'react'

export default function ScoreCard({ score = 0, insights = [] }) {
  // ✅ Ensure insights is always an array
  const safeInsights = Array.isArray(insights)
    ? insights
    : insights
    ? [String(insights)]
    : ["No insights available."]

  // ✅ Basic color logic for visual cue
  const getScoreColor = () => {
    if (score >= 80) return "#22c55e"   // Green
    if (score >= 50) return "#eab308"   // Yellow
    return "#ef4444"                    // Red
  }

  return (
    <div
      className="score-card"
      style={{
        background: "#111",
        borderRadius: "10px",
        padding: "1.5rem",
        marginTop: "1rem",
        color: "#fff",
        boxShadow: "0 0 12px rgba(0, 255, 255, 0.1)"
      }}
    >
      {/* Score Section */}
      <div className="score-meter" style={{ textAlign: "center" }}>
        <div
          className="score-number"
          style={{
            fontSize: "3rem",
            fontWeight: "bold",
            color: getScoreColor(),
          }}
        >
          {score}
        </div>
        <div className="score-label" style={{ color: "#aaa" }}>
          Readiness Score
        </div>
      </div>

      {/* Insights Section */}
      <div className="insights" style={{ marginTop: "1.5rem" }}>
        <h4 style={{ color: "#00ffff", marginBottom: "0.5rem" }}>Key Insights</h4>
        <ul style={{ listStyle: "disc", paddingLeft: "1.5rem", lineHeight: "1.6" }}>
          {safeInsights.map((i, idx) => (
            <li key={idx}>{i}</li>
          ))}
        </ul>
      </div>
    </div>
  )
}

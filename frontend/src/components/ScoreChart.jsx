import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LabelList,
} from "recharts";

/**
 * Braivix ScoreChart.jsx
 * ------------------------------------------------------------
 * Displays category-level credit analysis results visually.
 * Ideal for Liquidity / Leverage / Profitability / Solvency.
 */
export default function ScoreChart({ scores = {} }) {
  // Example input (auto adapts to available keys)
  // scores = { Liquidity: 3.0, Leverage: 3.9, Profitability: 3.0, Solvency: 4.1 }

  const chartData = Object.entries(scores).map(([name, value]) => ({
    name,
    score: value,
  }));

  if (chartData.length === 0) return null;

  return (
    <div
      style={{
        background: "#F9FAFB",
        borderRadius: "12px",
        border: "1px solid #E5E7EB",
        padding: "1.5rem",
        marginTop: "2rem",
      }}
    >
      <h3
        style={{
          fontFamily: "'Merriweather', serif",
          fontSize: "1.3rem",
          fontWeight: "700",
          color: "#0C2340",
          textAlign: "center",
          marginBottom: "1rem",
        }}
      >
        Credit Category Breakdown
      </h3>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 0, bottom: 10 }}
          barSize={50}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis
            dataKey="name"
            stroke="#374151"
            style={{ fontFamily: "'Inter', sans-serif", fontSize: "0.9rem" }}
          />
          <YAxis
            domain={[0, 5]}
            ticks={[1, 2, 3, 4, 5]}
            stroke="#374151"
            style={{ fontFamily: "'Inter', sans-serif", fontSize: "0.9rem" }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#FFFFFF",
              border: "1px solid #E5E7EB",
              borderRadius: "8px",
              fontFamily: "'Inter', sans-serif",
            }}
            formatter={(value) => [`${value.toFixed(2)} / 5`, "Score"]}
          />
          <Bar dataKey="score" fill="#0C2340" radius={[6, 6, 0, 0]}>
            <LabelList
              dataKey="score"
              position="top"
              formatter={(v) => v.toFixed(2)}
              style={{
                fill: "#0C2340",
                fontWeight: "600",
                fontFamily: "'Inter', sans-serif",
              }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <p
        style={{
          textAlign: "center",
          color: "#4B5563",
          fontFamily: "'Inter', sans-serif",
          fontSize: "0.9rem",
          marginTop: "1rem",
        }}
      >
        Ratings shown on a 1–5 scale (A = 5, B = 4, C = 3, D = 2, E = 1)
      </p>
    </div>
  );
}

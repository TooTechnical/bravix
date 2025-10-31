import React, { useMemo } from "react";
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
 * Braivix ScoreChart.jsx v3.0
 * ------------------------------------------------------------
 * Visualizes grouped credit categories with dynamic colors,
 * smooth animation, and category health indicators.
 */

export default function ScoreChart({ scores = {} }) {
  // Compute grouped averages
  const chartData = useMemo(() => {
    if (!scores || Object.keys(scores).length === 0) return [];

    const groupAvg = (keys) =>
      keys.reduce((sum, k) => sum + (scores[k] || 0), 0) / keys.length;

    return [
      {
        name: "Liquidity",
        score: groupAvg(["current_ratio", "quick_ratio", "cash_ratio"]),
      },
      {
        name: "Leverage",
        score: groupAvg([
          "debt_ratio",
          "debt_to_equity_ratio",
          "interest_coverage_ratio",
        ]),
      },
      {
        name: "Profitability",
        score: groupAvg([
          "gross_profit_margin",
          "operating_profit_margin",
          "net_profit_margin",
          "return_on_assets",
          "return_on_equity",
          "return_on_investment",
        ]),
      },
      {
        name: "Solvency",
        score: groupAvg([
          "asset_turnover_ratio",
          "inventory_turnover",
          "accounts_receivable_turnover",
          "earnings_per_share",
          "price_to_earnings_ratio",
          "altman_z_score",
        ]),
      },
    ].map((x) => ({
      ...x,
      score: Number(x.score.toFixed(2)),
    }));
  }, [scores]);

  if (chartData.length === 0) return null;

  // Dynamic color based on score
  const getColor = (score) => {
    if (score >= 4.5) return "#22C55E"; // Excellent (green)
    if (score >= 3.5) return "#84CC16"; // Good
    if (score >= 2.5) return "#EAB308"; // Average
    if (score >= 1.5) return "#F97316"; // Weak
    return "#EF4444"; // Critical
  };

  // Category health text
  const healthLabel = (score) => {
    if (score >= 4.5) return "Excellent";
    if (score >= 3.5) return "Good";
    if (score >= 2.5) return "Average";
    if (score >= 1.5) return "Weak";
    return "Critical";
  };

  return (
    <div
      style={{
        background: "linear-gradient(to bottom right, #0F172A, #1E293B)",
        borderRadius: "16px",
        padding: "1.8rem",
        marginTop: "2rem",
        boxShadow: "0 4px 20px rgba(0,0,0,0.25)",
      }}
    >
      <h3
        style={{
          fontFamily: "'Inter Tight', sans-serif",
          fontSize: "1.4rem",
          fontWeight: "700",
          color: "#00E1FF",
          textAlign: "center",
          marginBottom: "1.5rem",
          letterSpacing: "0.5px",
        }}
      >
        Credit Category Breakdown
      </h3>

      <ResponsiveContainer width="100%" height={320}>
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 0, bottom: 10 }}
          barSize={55}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="name"
            stroke="#E2E8F0"
            style={{
              fontFamily: "'Inter', sans-serif",
              fontSize: "0.95rem",
              letterSpacing: "0.3px",
            }}
          />
          <YAxis
            domain={[0, 5]}
            ticks={[1, 2, 3, 4, 5]}
            stroke="#E2E8F0"
            style={{
              fontFamily: "'Inter', sans-serif",
              fontSize: "0.9rem",
            }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1E293B",
              border: "1px solid #334155",
              borderRadius: "8px",
              color: "#E2E8F0",
              fontFamily: "'Inter', sans-serif",
            }}
            formatter={(value) => [`${value.toFixed(2)} / 5`, "Score"]}
          />
          <Bar
            dataKey="score"
            radius={[8, 8, 0, 0]}
            animationDuration={1200}
            animationEasing="ease-out"
            fill="#22C55E"
            // dynamically adjust fill color per bar
            isAnimationActive={true}
          >
            <LabelList
              dataKey="score"
              position="top"
              formatter={(v) => v.toFixed(2)}
              style={{
                fill: "#E2E8F0",
                fontWeight: "600",
                fontFamily: "'Inter', sans-serif",
              }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Legend with Health Labels */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          textAlign: "center",
          marginTop: "1.5rem",
          color: "#CBD5E1",
          fontFamily: "'Inter', sans-serif",
        }}
      >
        {chartData.map((d, i) => (
          <div key={i}>
            <p style={{ fontWeight: "600", marginBottom: "0.25rem" }}>
              {healthLabel(d.score)}
            </p>
            <div
              style={{
                height: "8px",
                width: "80%",
                backgroundColor: getColor(d.score),
                borderRadius: "6px",
                margin: "0 auto",
              }}
            />
          </div>
        ))}
      </div>

      <p
        style={{
          textAlign: "center",
          color: "#94A3B8",
          fontFamily: "'Inter', sans-serif",
          fontSize: "0.85rem",
          marginTop: "1.5rem",
        }}
      >
        Ratings shown on a 1–5 scale (A = 5, B = 4, C = 3, D = 2, E = 1)
      </p>
    </div>
  );
}

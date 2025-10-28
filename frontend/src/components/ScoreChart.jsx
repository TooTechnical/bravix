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
 * Braivix ScoreChart.jsx
 * ------------------------------------------------------------
 * Groups the 18 backend indicators into 4 credit categories
 * (Liquidity, Leverage, Profitability, Solvency)
 * and visualizes them on a 1–5 rating scale.
 */
export default function ScoreChart({ scores = {} }) {
  // Compute 4 category averages based on Mariya’s model
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
    ].map((x) => ({ ...x, score: Number(x.score.toFixed(2)) }));
  }, [scores]);

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

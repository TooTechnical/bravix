import React from "react";
import ScoreSummaryCard from "./ScoreSummaryCard";
import IndicatorBreakdown from "./IndicatorBreakdown";
import StressTestCard from "./StressTestCard";
import AnalystMetricsGrid from "./AnalystMetricsGrid";
import StrategicActions from "./StrategicActions";

export default function FullReport({ data }) {
  if (!data) {
    return <div style={{ textAlign: "center", color: "#6B7280" }}>No data available.</div>;
  }

  const {
    company_name,
    analysis_timestamp,
    scores,
    summary,
    quantitative_breakdown,
    stress_test,
    analyst_metrics,
    strategic_implications,
    final_evaluation,
  } = data;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
      {/* Header */}
      <div style={{ borderBottom: "1px solid #E5E7EB", paddingBottom: "1rem" }}>
        <h2 style={{ fontSize: "1.75rem", fontWeight: "700", color: "#0C2340" }}>
          {company_name || "Company Analysis Report"}
        </h2>
        <p style={{ color: "#6B7280", fontSize: "0.9rem" }}>
          Analysis generated on {new Date(analysis_timestamp).toLocaleString()}
        </p>
      </div>

      {/* Score Summary */}
      <ScoreSummaryCard
        weightedScore={scores?.weighted_credit_score}
        evaluationScore={scores?.evaluation_score}
        riskCategory={scores?.risk_category}
        creditDecision={scores?.credit_decision}
        summary={summary}
      />

      {/* Indicator Breakdown */}
      {quantitative_breakdown && quantitative_breakdown.length > 0 && (
        <IndicatorBreakdown breakdown={quantitative_breakdown} />
      )}

      {/* Stress Test */}
      {stress_test && <StressTestCard stress={stress_test} />}

      {/* Analyst Metrics */}
      {analyst_metrics && <AnalystMetricsGrid metrics={analyst_metrics} />}

      {/* Strategic Actions */}
      {strategic_implications && (
        <StrategicActions actions={strategic_implications} final={final_evaluation} />
      )}
    </div>
  );
}

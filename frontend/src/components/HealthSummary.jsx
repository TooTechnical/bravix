export default function HealthSummary({ ratios }) {
  if (!ratios || ratios.length === 0) return null;

  // Count statuses
  const total = ratios.length;
  const good = ratios.filter((r) => r.status === "good").length;
  const caution = ratios.filter((r) => r.status === "caution").length;
  const poor = ratios.filter((r) => r.status === "poor").length;

  // Weighted score (good=1, caution=0.5, poor=0)
  const score = Math.round(((good * 1 + caution * 0.5) / total) * 100);

  let summaryText = "";
  let summaryClass = "";

  if (score >= 80) {
    summaryText = "Excellent Financial Health";
    summaryClass = "good";
  } else if (score >= 60) {
    summaryText = "Stable Financial Health";
    summaryClass = "caution";
  } else {
    summaryText = "High Financial Risk";
    summaryClass = "poor";
  }

  return (
    <div className={`summary-card ${summaryClass}`}>
      <h2>Overall Financial Health</h2>
      <p className="score">{score}%</p>
      <p>{summaryText}</p>
    </div>
  );
}

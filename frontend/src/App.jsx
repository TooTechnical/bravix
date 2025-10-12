import HealthSummary from "./components/HealthSummary";
import { useState } from "react";
import FinancialTable from "./components/FinancialTable";
import "./styles/ratios.css";

function App() {
  const [data, setData] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const payload = Object.fromEntries(new FormData(e.target));
    // Convert all inputs to float
    Object.keys(payload).forEach((k) => {
      const val = parseFloat(payload[k]);
      payload[k] = isNaN(val) ? null : val;
    });

  const res = await fetch(`${import.meta.env.VITE_API_URL}/api/financial-analysis`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const json = await res.json();
    setData(json);
  }

  return (
    <div className="container">
      <h1>Bravix Financial Analysis</h1>
      <form onSubmit={handleSubmit} className="grid-form">
        {/* LIQUIDITY */}
        <h3>Liquidity</h3>
        <input name="current_assets" placeholder="Current Assets (€)" required />
        <input name="current_liabilities" placeholder="Current Liabilities (€)" required />
        <input name="stocks" placeholder="Stocks / Inventory (€)" />
        <input name="cash" placeholder="Cash (€)" />
        <input name="short_term_investments" placeholder="Short-term Investments (€)" />
        <input name="short_term_liabilities" placeholder="Short-term Liabilities (€)" />

        {/* TURNOVER */}
        <h3>Turnover</h3>
        <input name="cost_of_sales" placeholder="Cost of Sales (€)" />
        <input name="avg_inventory" placeholder="Average Inventory (€)" />
        <input name="net_sales" placeholder="Net Sales (€)" />
        <input name="avg_receivables" placeholder="Average Receivables (€)" />
        <input name="revenue" placeholder="Revenue (€)" required />

        {/* PROFITABILITY */}
        <h3>Profitability</h3>
        <input name="net_profit" placeholder="Net Profit (€)" required />
        <input name="avg_assets" placeholder="Average Assets (€)" />
        <input name="avg_equity" placeholder="Average Equity (€)" />
        <input name="equity" placeholder="Equity (€)" />
        <input name="total_capital" placeholder="Total Capital (€)" />

        {/* DEBT & RISK */}
        <h3>Debt & Risk</h3>
        <input name="total_liabilities" placeholder="Total Liabilities (€)" />
        <input name="total_income" placeholder="Total Income (€)" />
        <input name="monthly_income" placeholder="Monthly Income (€)" />
        <input name="monthly_debt_payments" placeholder="Monthly Debt Payments (€)" />
        <input name="profit_from_investment" placeholder="Profit from Investment (€)" />
        <input name="investment_cost" placeholder="Investment Cost (€)" />
        <input name="general_debt" placeholder="General Debt (€)" />
        <input name="ebitda" placeholder="EBITDA (€)" />
        <input name="ebit" placeholder="EBIT (€)" />
        <input name="debt_service" placeholder="Debt Service (€)" />

        <button type="submit">Analyze</button>
      </form>

      {data && (
  <>
    <HealthSummary ratios={data.ratios} />
    <FinancialTable data={data.ratios} />
  </>
)}

    </div>
  );
}

export default App;

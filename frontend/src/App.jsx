import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import HealthSummary from "./components/HealthSummary";
import FinancialTable from "./components/FinancialTable";
import "./styles/ratios.css";

function FinancialForm() {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload = Object.fromEntries(new FormData(e.target));
      Object.keys(payload).forEach((k) => {
        const val = parseFloat(payload[k]);
        payload[k] = isNaN(val) ? null : val;
      });

      const res = await fetch(
        `${import.meta.env.VITE_API_URL}/api/financial-analysis`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-API-Key": import.meta.env.VITE_API_KEY,
          },
          body: JSON.stringify(payload),
        }
      );

      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const json = await res.json();
      setData(json);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(180deg, #F9FAFB 0%, #EEF2F3 100%)",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        fontFamily: "'Inter', sans-serif",
        padding: "2rem",
      }}
    >
      <h1
        style={{
          fontSize: "2.8rem",
          fontWeight: "700",
          color: "#111827",
          marginBottom: "0.5rem",
        }}
      >
        Braivix Financial Analysis
      </h1>
      <p
        style={{
          fontSize: "1.1rem",
          color: "#374151",
          maxWidth: "600px",
          textAlign: "center",
          marginBottom: "2rem",
        }}
      >
        Upload your company’s key financials and let Braivix evaluate liquidity,
        profitability, and creditworthiness using 18 performance indicators —
        powered by GPT-5.
      </p>

      <Link
        to="/dashboard"
        style={{
          background: "linear-gradient(90deg, #00C48C 0%, #00FFD0 100%)",
          color: "#fff",
          fontWeight: "600",
          padding: "14px 36px",
          fontSize: "1.1rem",
          borderRadius: "12px",
          border: "none",
          boxShadow: "0 4px 15px rgba(0, 196, 140, 0.3)",
          textDecoration: "none",
          marginBottom: "1.5rem",
          transition: "transform 0.2s ease, box-shadow 0.2s ease",
        }}
        onMouseEnter={(e) => (e.target.style.transform = "translateY(-3px)")}
        onMouseLeave={(e) => (e.target.style.transform = "translateY(0)")}
      >
        Launch AI Analyzer
      </Link>

      <form
        onSubmit={handleSubmit}
        className="grid-form"
        style={{ marginTop: "2rem", width: "100%", maxWidth: "600px" }}
      >
        {/* Example input fields */}
        <label>Annual Revenue (€)</label>
        <input type="number" name="revenue" step="any" required />

        <label>Profit (€)</label>
        <input type="number" name="profit" step="any" required />

        <label>Outstanding Debt (€)</label>
        <input type="number" name="debt" step="any" required />

        <button
          type="submit"
          disabled={loading}
          style={{
            background: "#2563EB",
            color: "white",
            fontWeight: "600",
            border: "none",
            padding: "12px 30px",
            borderRadius: "8px",
            width: "100%",
            marginTop: "1rem",
            cursor: "pointer",
            transition: "background 0.2s ease",
          }}
          onMouseEnter={(e) => (e.target.style.background = "#1E40AF")}
          onMouseLeave={(e) => (e.target.style.background = "#2563EB")}
        >
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </form>

      {error && <p style={{ color: "red", marginTop: "1rem" }}>{error}</p>}
      {data && (
        <>
          <HealthSummary ratios={data.ratios} />
          <FinancialTable data={data.ratios} />
        </>
      )}

      <footer
        style={{
          position: "absolute",
          bottom: "1.5rem",
          fontSize: "0.9rem",
          color: "#6B7280",
        }}
      >
        Prototype © Braivix — Powered by GPT-5
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<FinancialForm />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </Router>
  );
}

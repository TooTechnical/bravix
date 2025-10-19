import React from "react"
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom"
import Dashboard from "./components/Dashboard"
import HealthSummary from "./components/HealthSummary"
import FinancialTable from "./components/FinancialTable"
import "./styles/ratios.css"

function FinancialForm() {
  const [data, setData] = React.useState(null)
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const payload = Object.fromEntries(new FormData(e.target))
      Object.keys(payload).forEach(k => {
        const val = parseFloat(payload[k])
        payload[k] = isNaN(val) ? null : val
      })

      const res = await fetch(`${import.meta.env.VITE_API_URL}/api/financial-analysis`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": import.meta.env.VITE_API_KEY,
        },
        body: JSON.stringify(payload),
      })

      if (!res.ok) throw new Error(`Server error ${res.status}`)
      const json = await res.json()
      setData(json)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <h1>Bravix Financial Analysis</h1>
      <Link to="/dashboard" className="link-button">Launch AI Analyzer</Link>

      <form onSubmit={handleSubmit} className="grid-form">
        {/* (your form fields stay unchanged) */}
        <button type="submit" disabled={loading}>
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </form>

      {error && <p style={{ color: "red" }}>{error}</p>}
      {data && (
        <>
          <HealthSummary ratios={data.ratios} />
          <FinancialTable data={data.ratios} />
        </>
      )}
    </div>
  )
}

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<FinancialForm />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </Router>
  )
}

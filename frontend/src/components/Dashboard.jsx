import React, { useState } from 'react'
import { getScore, postCsv } from '../api'
import ScoreCard from './ScoreCard'

export default function Dashboard({ onBack, setDemoData, demoData }){
  const [revenue, setRevenue] = useState('')
  const [profit, setProfit] = useState('')
  const [debt, setDebt] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [file, setFile] = useState(null)
  const [error, setError] = useState(null)

  async function handleCalc(e){
    e.preventDefault()
    setLoading(true); setError(null)
    try {
      const res = await getScore({ revenue: parseFloat(revenue), profit: parseFloat(profit), debt: parseFloat(debt) })
      setResult(res)
      setDemoData(res)
    } catch(err){
      setError(err?.response?.data?.detail || err.message)
    } finally { setLoading(false) }
  }

  async function handleUpload(e){
    e.preventDefault()
    if(!file) return setError("Please select a CSV file first")
    setLoading(true); setError(null)
    try {
      const res = await postCsv(file)
      setResult(res)
      setDemoData(res)
    } catch(err){
      setError(err?.response?.data?.detail || err.message)
    } finally { setLoading(false) }
  }

  return (
    <div className="page dashboard">
      <button className="link" onClick={onBack}>← Back</button>
      <h2>Demo Dashboard</h2>

      <section className="input-panel">
        <form onSubmit={handleCalc}>
          <label>Annual Revenue (€)</label>
          <input type="number" value={revenue} onChange={e=>setRevenue(e.target.value)} required />

          <label>Profit (€)</label>
          <input type="number" value={profit} onChange={e=>setProfit(e.target.value)} required />

          <label>Outstanding Debt (€)</label>
          <input type="number" value={debt} onChange={e=>setDebt(e.target.value)} required />

          <button className="btn" type="submit" disabled={loading}>Generate Readiness Score</button>
        </form>

        <div className="divider">OR</div>

        <form onSubmit={handleUpload}>
          <label>Upload CSV (columns: revenue, profit, debt)</label>
          <input type="file" accept=".csv" onChange={e=>setFile(e.target.files[0])} />
          <button className="btn" type="submit" disabled={loading}>Upload CSV & Score</button>
        </form>

        {error && <div className="error">{error}</div>}
      </section>

      <section className="result-panel">
        {loading && <div>Calculating…</div>}
        {result && <ScoreCard score={result.score} insights={result.insights} />}
      </section>
    </div>
  )
}

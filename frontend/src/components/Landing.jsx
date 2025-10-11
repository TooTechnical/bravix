import React from 'react'

export default function Landing({ onStart }){
  return (
    <div className="page landing">
      <header>
        <h1>Bravix — SME Financial Readiness</h1>
        <p className="tag">AI-style scoring demo — prototype hosted by Bravix</p>
      </header>
      <main>
        <p>Quick demo: upload financials or enter revenue/profit/debt to generate a readiness score.</p>
        <button className="btn" onClick={onStart}>Launch Demo</button>
      </main>
      <footer>Prototype © Bravix — For demonstration purposes only</footer>
    </div>
  )
}

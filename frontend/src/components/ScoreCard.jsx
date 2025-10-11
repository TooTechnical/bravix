import React from 'react'

export default function ScoreCard({score, insights}){
  return (
    <div className="score-card">
      <div className="score-meter">
        <div className="score-number">{score}</div>
        <div className="score-label">Readiness Score</div>
      </div>
      <div className="insights">
        <h4>Key insights</h4>
        <ul>
          {insights.map((i, idx) => <li key={idx}>{i}</li>)}
        </ul>
      </div>
    </div>
  )
}

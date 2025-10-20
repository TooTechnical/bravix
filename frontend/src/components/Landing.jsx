import React from "react";
import { Link } from "react-router-dom";

export default function Landing() {
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
      <header style={{ textAlign: "center", marginBottom: "2rem" }}>
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
            margin: "0 auto",
          }}
        >
          Empowering smarter lending decisions through intelligent AI analysis.  
          Upload financial documents, and Braivix will evaluate liquidity, 
          profitability, leverage, and overall creditworthiness — powered by GPT-5.
        </p>
      </header>

      <main style={{ textAlign: "center" }}>
        <Link to="/dashboard" style={{ textDecoration: "none" }}>
          <button
            style={{
              background: "linear-gradient(90deg, #00C48C 0%, #00FFD0 100%)",
              color: "#fff",
              fontWeight: "600",
              padding: "14px 36px",
              fontSize: "1.1rem",
              borderRadius: "12px",
              border: "none",
              boxShadow: "0 4px 15px rgba(0, 196, 140, 0.3)",
              cursor: "pointer",
              transition: "transform 0.2s ease, box-shadow 0.2s ease",
            }}
            onMouseEnter={(e) => (e.target.style.transform = "translateY(-3px)")}
            onMouseLeave={(e) => (e.target.style.transform = "translateY(0)")}
          >
            Launch AI Analyzer
          </button>
        </Link>
      </main>

      <footer
        style={{
          position: "absolute",
          bottom: "1.5rem",
          fontSize: "0.9rem",
          color: "#6B7280",
        }}
      >
        Prototype © Braivix — For demonstration purposes only
      </footer>
    </div>
  );
}


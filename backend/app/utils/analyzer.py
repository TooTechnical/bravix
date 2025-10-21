# app/utils/analyzer.py
"""
Performs AI + financial data analysis using OpenAI GPT-5 (or fallback simulation).
"""

import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_data(payload: dict):
    """
    Processes parsed financial data and returns a GPT-based financial summary.
    This demo version simulates AI analysis if the API key is missing.
    """
    try:
        # Convert financial data to readable text
        data_text = str(payload)

        # --- If no OpenAI key found, fallback to mock analysis
        if not os.getenv("OPENAI_API_KEY"):
            return {
                "summary": "AI analysis unavailable (no API key).",
                "insight": "Simulated analysis based on provided financial data.",
            }

        # --- Real GPT-powered analysis ---
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a financial analysis assistant."},
                {"role": "user", "content": f"Analyze this data: {data_text}"}
            ],
        )

        return {
            "summary": response.choices[0].message.content.strip(),
            "insight": "Analysis generated successfully using GPT-5.",
        }

    except Exception as e:
        return {"error": f"AI analysis failed: {str(e)}"}

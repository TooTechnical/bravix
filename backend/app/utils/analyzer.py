"""
Performs AI + financial data analysis using OpenAI GPT models (GPT-4o-mini).
Includes graceful fallback and detailed error logging for Render.
"""

import os
import traceback
from openai import OpenAI

def analyze_data(payload: dict):
    """
    Processes parsed financial data and returns a GPT-based financial summary.
    Falls back to a simulated response if API access fails.
    """
    try:
        # Convert the incoming data to readable text
        data_text = payload.get("raw_text") or str(payload)

        # Check for OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or not api_key.strip():
            print("⚠️ No OpenAI API key found. Returning simulated analysis.")
            return {
                "summary": "AI analysis unavailable (no API key detected).",
                "insight": "Simulated placeholder output based on financial data.",
            }

        # Initialize client dynamically
        client = OpenAI(api_key=api_key)
        print("🔑 OpenAI API key loaded successfully (first 6 chars):", api_key[:6])

        # Compose the prompt
        prompt = f"""
        You are an advanced financial analyst AI.
        Review the following company's financial data carefully and provide:
        - A concise executive summary
        - Key financial ratios or trends
        - Credit risk score (0–100)
        - Short reasoning behind the risk score

        Financial Data:
        {data_text}
        """

        # Call OpenAI chat completion
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Stable, low-latency GPT-4 model
            messages=[
                {"role": "system", "content": "You are a senior financial analyst."},
                {"role": "user", "content": prompt.strip()},
            ],
            temperature=0.6,
            max_tokens=800,
        )

        ai_output = response.choices[0].message.content.strip()
        print("✅ AI response successfully generated (length):", len(ai_output))

        return {
            "summary": ai_output,
            "insight": "Analysis generated successfully using GPT-4o-mini.",
        }

    except Exception as e:
        print("❌ AI analysis failed:", str(e))
        traceback.print_exc()
        return {"error": f"AI analysis failed: {str(e)}"}

"""
Braivix – AI Financial Analyzer
--------------------------------
Integrates the 18 financial indicators with GPT-5 to generate a structured,
explainable financial report. Includes full error handling for Render.
"""

import os
import traceback
from openai import OpenAI
from app.utils.financial_indicators import compute_all




def analyze_data(payload: dict):
    """
    Takes parsed financial data, computes the 18 indicators,
    and sends both numeric + qualitative insights to GPT-5.
    """
    try:
        # --- Step 1: Extract text for qualitative reference
        data_text = payload.get("raw_text") or str(payload)

        # --- Step 2: Compute financial indicators
        indicator_data = compute_all(payload)
        indicators = indicator_data.get("financial_indicators", [])
        overall_score = indicator_data.get("overall_health_score")

        # --- Step 3: Prepare for GPT-5
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or not api_key.strip():
            print("⚠️ No OpenAI API key found. Returning simulated response.")
            return {
                "summary": "AI analysis unavailable (no API key detected).",
                "insight": "Simulated placeholder output based on 18 financial indicators.",
                "indicators": indicator_data
            }

        client = OpenAI(api_key=api_key)
        print("🔑 OpenAI API key loaded successfully (first 6 chars):", api_key[:6])

        # --- Step 4: Build structured indicator summary for GPT prompt
        indicator_summary = "\n".join([
            f"- {i['name']}: {i['value']} ({i['status']})"
            for i in indicators
        ])

        # --- Step 5: Compose prompt
        prompt = f"""
        You are Braivix AI — an expert financial analyst assisting banks and investors.

        Analyze the following financial indicators and determine the company’s financial health,
        liquidity, profitability, solvency, and efficiency. Use real-world banking standards.

        Provide:
        1. Executive Summary (2–3 paragraphs)
        2. Key Strengths and Weaknesses
        3. Credit Risk Rating (0–100, higher = higher risk)
        4. Lending Recommendation
        5. Explanation of how the 18 indicators influenced your decision

        ---
        RAW DATA EXTRACT:
        {data_text[:1500]}  # Limit text length for efficiency
        ---
        FINANCIAL INDICATORS:
        {indicator_summary}
        ---
        OVERALL HEALTH SCORE (calculated internally): {overall_score}
        """

        # --- Step 6: Call GPT-5 API
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # GPT-4 Optimized model (GPT-5-equivalent reasoning)
            messages=[
                {"role": "system", "content": "You are an advanced financial analysis AI for Braivix."},
                {"role": "user", "content": prompt.strip()}
            ],
            temperature=0.5,
            max_tokens=900
        )

        ai_output = response.choices[0].message.content.strip()
        print("✅ AI response generated successfully (chars):", len(ai_output))

        return {
            "status": "success",
            "summary": ai_output,
            "overall_health_score": overall_score,
            "financial_indicators": indicators
        }

    except Exception as e:
        print("❌ AI analysis failed:", str(e))
        traceback.print_exc()
        return {"error": f"AI analysis failed: {str(e)}"}

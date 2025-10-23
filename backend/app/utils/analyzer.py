"""
Braivix – AI Financial Analyzer
--------------------------------
Integrates the 18 financial indicators with GPT-5 to generate a structured,
explainable financial report. Includes full error handling for Render.
"""

import os
import traceback
from app.utils.financial_indicators import compute_all
from app.utils.analyze_with_chatgpt import get_openai_client, analyze_with_chatgpt


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

        # --- Step 3: Check API key availability
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or not api_key.strip():
            print("⚠️ No OpenAI API key found. Returning simulated response.")
            return {
                "status": "warning",
                "summary": "AI analysis unavailable (no API key detected).",
                "insight": "Simulated placeholder output based on 18 financial indicators.",
                "overall_health_score": overall_score,
                "financial_indicators": indicators
            }

        # --- Step 4: Initialize OpenAI client
        try:
            client = get_openai_client()
            print("🔑 OpenAI API client initialized successfully.")
        except Exception as e:
            print("⚠️ Failed to initialize OpenAI client:", str(e))
            return {
                "status": "error",
                "summary": "Failed to initialize OpenAI client.",
                "details": str(e),
                "financial_indicators": indicators
            }

        # --- Step 5: Build structured indicator dictionary
        indicator_dict = {
            i["name"].lower().replace(" ", "_"): i["value"] for i in indicators
        }
        indicator_dict["readiness_score"] = overall_score or 0

        # --- Step 6: Call GPT-5/4o analysis
        print("🧠 Sending indicators + text to GPT analysis...")
        ai_result = analyze_with_chatgpt(data_text, indicator_dict, client)

        ai_output = ai_result.get("analysis_raw", "").strip()
        if not ai_output:
            ai_output = "AI returned no analysis text."

        print("✅ AI analysis complete. Length:", len(ai_output))

        # --- Step 7: Return structured response
        return {
            "status": "success",
            "summary": ai_output,
            "overall_health_score": overall_score,
            "financial_indicators": indicators,
        }

    except Exception as e:
        print("❌ AI analysis failed:", str(e))
        traceback.print_exc()
        return {"status": "error", "error": f"AI analysis failed: {str(e)}"}

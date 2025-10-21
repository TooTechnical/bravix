"""
Performs AI + financial data analysis using OpenAI GPT models (GPT-4o-mini).
Includes graceful fallback, key sanitization, and detailed error logging for Render.
"""

import os
import traceback
from openai import OpenAI
from openai import APIConnectionError, APIError, RateLimitError, APITimeoutError

def analyze_data(payload: dict):
    """
    Processes parsed financial data and returns a GPT-based financial summary.
    Falls back to a simulated response if API access fails or key is invalid.
    """
    try:
        # 🧾 Convert the incoming data to readable text
        data_text = payload.get("raw_text") or str(payload)

        # 🔑 Sanitize the OpenAI API key (remove newlines/spaces)
        api_key = (os.getenv("OPENAI_API_KEY") or "").strip()

        if not api_key:
            print("⚠️ No valid OpenAI API key found. Returning simulated response.")
            return {
                "summary": "AI analysis unavailable (missing or invalid API key).",
                "insight": "Simulated placeholder output based on parsed data.",
            }

        # 🚀 Initialize OpenAI client with sanitized key
        client = OpenAI(api_key=api_key)
        print(f"🔑 OpenAI key active (first 6 chars): {api_key[:6]}")

                # 🧠 Compose AI prompt
        prompt = f"""
        You are a senior financial analyst preparing a professional report for a corporate client.
        Use the data below to produce a concise, structured report with the following sections:

        === Bravix AI Financial Analysis Report ===
        1️⃣ Executive Summary — 4–6 sentences describing overall financial health.
        2️⃣ Key Ratios & Indicators — bullet points showing important metrics, such as:
            • Profit margin
            • Debt-to-equity ratio
            • Liquidity or solvency trend
        3️⃣ Risk Evaluation — assign a Credit Risk Score (0–100), where higher = greater risk.
            Explain briefly why this score was chosen.
        4️⃣ AI Recommendations — 2–3 action points or strategic advice to improve stability.

        Return your answer using **clear markdown formatting**, including headings (##) and bullet lists.

        Company Financial Data:
        {data_text}
        """


        # 💬 Send request to OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a precise and senior financial analyst."},
                {"role": "user", "content": prompt.strip()},
            ],
            temperature=0.6,
            max_tokens=800,
            timeout=30,  # seconds
        )

        # ✅ Extract AI output safely
        ai_output = response.choices[0].message.content.strip()
        print("✅ AI analysis generated successfully (length):", len(ai_output))

        return {
            "summary": ai_output,
            "insight": "Analysis generated successfully using GPT-4o-mini.",
        }

    # 🛑 Specific error handling for better debugging on Render
    except (APIConnectionError, APITimeoutError) as e:
        print("⏱️ Network or timeout error during OpenAI request:", str(e))
        return {"error": "Connection timeout while contacting OpenAI API."}

    except (RateLimitError, APIError) as e:
        print("⚠️ OpenAI API error:", str(e))
        return {"error": f"OpenAI API returned an error: {str(e)}"}

    except Exception as e:
        print("❌ AI analysis failed:", str(e))
        traceback.print_exc()
        return {"error": f"AI analysis failed: {str(e)}"}

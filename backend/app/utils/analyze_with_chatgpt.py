import os
import json
from openai import OpenAI

def get_openai_client():
    """
    Creates an OpenAI client that automatically detects your environment.
    Supports both the default OpenAI API and custom proxy URLs (like api.openai-proxy.com).
    """
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    if not api_key:
        raise ValueError("❌ Missing OPENAI_API_KEY environment variable.")

    print(f"🔑 OpenAI API key loaded (first 8 chars): {api_key[:8]}...")
    print(f"🌐 Using OpenAI Base URL: {base_url}")

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        print("✅ OpenAI client initialized successfully.")
        return client
    except Exception as e:
        print(f"⚠️ Failed to initialize OpenAI client: {e}")
        raise


def analyze_with_chatgpt(raw_text: str, indicators: dict, client: OpenAI = None):
    """
    Uses GPT-5 (preferred) or GPT-4o (fallback) to analyze financial risk
    using the 18 key financial indicators.
    """

    # ✅ Ensure we have a working OpenAI client
    if client is None:
        client = get_openai_client()

    if not raw_text or raw_text.strip() == "":
        raw_text = "No extracted financial text available."

    # --- Build structured expert prompt ---
    prompt = f"""
You are a senior financial risk analyst at Bravix. 
You must evaluate the company’s financial stability using the **official Bravix Credit Scoring Framework**, 
which is based on 18 financial indicators and their normalized weights (sum of all weights = 1.0).

Each indicator is rated A–E:
A = 5 points (Excellent)
B = 4 points (Good)
C = 3 points (Average)
D = 2 points (Weak)
E = 1 point (Critical)

--- WEIGHTING TABLE (wᵢ) ---
1. Current Ratio (0.08)
2. Quick Ratio (0.08)
3. Cash Ratio (0.08)
4. Debt-to-Equity Ratio (0.10)
5. Debt Ratio (0.10)
6. Interest Coverage Ratio (0.10)
7. Gross Profit Margin (0.05)
8. Operating Profit Margin (0.05)
9. Net Profit Margin (0.05)
10. Return on Assets (ROA) (0.05)
11. Return on Equity (ROE) (0.05)
12. Return on Investment (ROI) (0.05)
13. Asset Turnover Ratio (0.05)
14. Inventory Turnover (0.05)
15. Accounts Receivable Turnover (0.05)
16. Earnings Per Share (EPS) (0.025)
17. Price-to-Earnings Ratio (P/E) (0.025)
18. Altman Z-Score (0.06)

The **overall credit score** is calculated as:
Score = Σ (wᵢ × sᵢ), where sᵢ ∈ [1–5]

--- EXTRACTED DOCUMENT DATA ---
{raw_text[:2500]}

--- COMPUTED INDICATORS ---
{json.dumps(indicators, indent=2)}

Your task:
1. Evaluate each indicator and assign a grade (A–E) based on how the company compares to healthy ranges.
2. Compute the weighted credit score (1–5 scale).
3. Classify the company into one of five categories:
   - Excellent (4.5–5.0)
   - Good (3.8–4.49)
   - Average (3.0–3.79)
   - Weak (2.0–2.99)
   - Critical (below 2.0)
4. Provide a clear explanation of *why* the company fits that category.

Return your analysis in this structure:

**Overview:** (short paragraph)
**Indicator Ratings:** (A–E per indicator)
**Weighted Credit Score:** (show numeric score)
**Risk Category:** (Excellent / Good / Average / Weak / Critical)
**Key Strengths:** (3–5 bullet points)
**Key Weaknesses:** (3–5 bullet points)
**Final Credit Decision:** (Approve / Review / Reject)
"""

    # ✅ Try GPT-5 first, fallback to GPT-4o
    for model in ["gpt-5", "gpt-4o"]:
        try:
            print(f"\n🧠 Sending financial summary to {model.upper()}...\n{'-'*60}")

            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert financial and credit risk analyst."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=1200,
            )

            response_text = completion.choices[0].message.content.strip()
            if response_text:
                print(f"✅ Analysis successfully generated using {model.upper()}.")
                return {"analysis_raw": response_text}

        except Exception as e:
            print(f"⚠️ {model.upper()} failed: {e}")
            continue

    # ❌ If all attempts fail
    print("❌ Both GPT models failed to return a response.")
    return {"analysis_raw": "No analysis returned by GPT-5 or GPT-4o."}

from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import os
import requests
from dotenv import load_dotenv

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

if not HF_API_KEY:
    raise RuntimeError("HUGGINGFACE_API_KEY not found in environment variables")

# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI(title="InsightFlow API")

# -----------------------------
# Utility: Load datasets (reload-safe)
# -----------------------------
def load_data():
    return {
        "revenue_by_category": pd.read_csv("../data/revenue_by_category.csv"),
        "monthly_revenue": pd.read_csv("../data/monthly_revenue.csv"),
        "customer_segments": pd.read_csv("../data/customer_segments.csv"),
    }

# -----------------------------
# Request schema
# -----------------------------
class QueryRequest(BaseModel):
    question: str

# -----------------------------
# Health check
# -----------------------------
@app.get("/")
def root():
    return {"message": "InsightFlow API is running"}

# -----------------------------
# Core analytics endpoints
# -----------------------------
@app.get("/revenue/category")
def get_revenue_by_category():
    data = load_data()["revenue_by_category"]
    return data.to_dict(orient="records")

@app.get("/revenue/monthly")
def get_monthly_revenue():
    data = load_data()["monthly_revenue"]
    return data.to_dict(orient="records")

@app.get("/customers/segments")
def get_customer_segments():
    data = load_data()["customer_segments"]
    return data.to_dict(orient="records")
# -----------------------------
# Structured Insights Endpoint (for Power BI)
# -----------------------------
@app.get("/insights")
def get_insights():
    data = load_data()

    revenue_df = data["monthly_revenue"]
    category_df = data["revenue_by_category"]

    first = revenue_df.iloc[0]["Total Amount"]
    last = revenue_df.iloc[-1]["Total Amount"]

    change_pct = round(((last - first) / first) * 100, 2)

    trend = "stable"
    if change_pct > 5:
        trend = "growing"
    elif change_pct < -5:
        trend = "declining"

    top_cat = category_df.sort_values(
        "Total Amount", ascending=False
    ).iloc[0]

    return {
        "revenue_trend": trend,
        "revenue_change_percent": change_pct,
        "top_category": top_cat["Product Category"]
    }

# -----------------------------
# LLM-powered query endpoint
# -----------------------------
@app.post("/query")
def query_insights(req: QueryRequest):
    question = req.question.lower()
    data = load_data()

    intent = None
    context = ""
    fallback_insight = ""
    visualization = None

    # -----------------------------
    # Intent detection (rule-based v1)
    # -----------------------------
    if "category" in question:
        intent = "revenue_by_category"
        df = data["revenue_by_category"]

        from insight_engine import analyze_revenue_by_category
        result = analyze_revenue_by_category(df)
        context = result["context"]
        fallback_insight = result["fallback"]
        visualization = result["visualization"]

    elif "month" in question or "trend" in question:
        intent = "monthly_revenue"
        df = data["monthly_revenue"]

        latest = df.iloc[-1]

        context = f"""
Month: {latest['Month']}
Revenue: {latest['Total Amount']}
"""

        fallback_insight = (
            "Revenue shows a stable month-over-month trend, "
            "suggesting consistent business performance."
        )

        visualization = "line_chart"

    elif "customer" in question or "gender" in question:
        intent = "customer_segments"
        df = data["customer_segments"]

        context = df.head(5).to_string(index=False)

        fallback_insight = (
            "Customer segmentation highlights differences in spending behavior, "
            "which can be leveraged for targeted marketing."
        )

        visualization = "stacked_bar"

    else:
        return {
            "error": "Query not understood",
            "hint": "Try asking about revenue, monthly trends, or customer segments"
        }

    # -----------------------------
    # Hugging Face LLM call
    # -----------------------------
    insight_text = fallback_insight
    source = "fallback"

    try:
        headers = {
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "inputs": f"""
You are a senior business analyst.

Given the data below, write ONE concise executive-level insight.
Do NOT repeat the numbers.
Focus on implications and decisions.

DATA:
{context}

INSIGHT:
""",
            "options": {"use_cache": False},
        }

        HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"

        response = requests.post(
            f"https://router.huggingface.co/hf-inference/models/{HF_MODEL}",
            headers=headers,
            json=payload,
            timeout=30,
        )
        print("HF STATUS:", response.status_code)
        print("HF RESPONSE:", response.text)

        if response.status_code == 200:
            data = response.json()

            # Handle HF response formats safely
            if isinstance(data, list) and "generated_text" in data[0]:
                insight_text = data[0]["generated_text"].strip()
                source = "huggingface"
            elif isinstance(data, dict) and "generated_text" in data:
                insight_text = data["generated_text"].strip()
                source = "huggingface"

    except Exception:
        pass  # fallback already set

    # -----------------------------
    # Final structured response
    # -----------------------------
    return {
        "question": req.question,
        "intent": intent,
        "insight": insight_text,
        "recommended_visualization": visualization,
        "source": source,
    }

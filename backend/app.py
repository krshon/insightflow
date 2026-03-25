from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import os
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
import requests

# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI(title="InsightFlow API")


# -----------------------------
# Utility: Load datasets
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
# Structured Insights Endpoint
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

    top_cat = category_df.sort_values("Total Amount", ascending=False).iloc[0]

    return {
        "revenue_trend": trend,
        "revenue_change_percent": change_pct,
        "top_category": top_cat["Product Category"],
    }


# -----------------------------
# LLM-powered query endpoint (Gemini)
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
    # Intent detection
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

        recent = df.tail(5)

        context = f"""
Month: {latest['Month']}
Revenue: {latest['Total Amount']}
"""

        fallback_insight = "Revenue shows a stable trend, indicating consistent performance but limited growth."

        visualization = "line_chart"

    elif "customer" in question or "gender" in question:
        intent = "customer_segments"
        df = data["customer_segments"]

        context = df.head(5).to_string(index=False)

        fallback_insight = "Customer segmentation reveals varying spending patterns, enabling targeted marketing strategies."

        visualization = "stacked_bar"

    else:
        return {
            "error": "Query not understood",
            "hint": "Try asking about revenue, monthly trends, or customer segments",
        }

    # -----------------------------
    # OpenRouter LLM call
    # -----------------------------
    insight_text = fallback_insight
    source = "fallback"

    try:
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "google/gemma-3-27b-it:free",
            "messages": [
                {
                    "role": "user",
                    "content": f"""You are a business analyst.
Rules:
- Use ONLY the given data
- Do NOT invent new metrics
- Do NOT ask for more data, provide helpful insights based on what you have


Data:
{context}

Insight:""",
                }
            ],
            "temperature": 0.7,
            "max_tokens": 100,
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )

        print("OPENROUTER STATUS:", response.status_code)
        print("OPENROUTER RESPONSE:", response.text)

        if response.status_code == 200:
            result = response.json()
            generated = result["choices"][0]["message"]["content"].strip()

            if generated:
                insight_text = generated
                source = "openrouter"

    except Exception as e:
        print("OPENROUTER ERROR:", e)

    # -----------------------------
    # Final response
    # -----------------------------
    return {
        "question": req.question,
        "intent": intent,
        "insight": insight_text,
        "recommended_visualization": visualization,
        "source": source,
    }


print("API KEY:", os.getenv("OPENROUTER_API_KEY"))

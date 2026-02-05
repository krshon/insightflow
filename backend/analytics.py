import pandas as pd

# -----------------------------
# Load business transaction data
# -----------------------------
df = pd.read_csv("../data/retail_sales_dataset.csv")

# Clean column names (important)
df.columns = df.columns.str.strip()

# Convert Date column to datetime
df["Date"] = pd.to_datetime(df["Date"])

# -----------------------------
# 1. Revenue by Product Category
# -----------------------------
revenue_by_category = (
    df.groupby("Product Category")["Total Amount"]
    .sum()
    .reset_index()
)

revenue_by_category.to_csv(
    "../data/revenue_by_category.csv",
    index=False
)

# -----------------------------
# 2. Monthly Revenue Trend
# -----------------------------
df["Month"] = df["Date"].dt.to_period("M")

monthly_revenue = (
    df.groupby("Month")["Total Amount"]
    .sum()
    .reset_index()
)

monthly_revenue["Month"] = monthly_revenue["Month"].astype(str)

monthly_revenue.to_csv(
    "../data/monthly_revenue.csv",
    index=False
)

# -----------------------------
# 3. Customer Segmentation (Gender x Category)
# -----------------------------
customer_segments = (
    df.groupby(["Gender", "Product Category"])["Total Amount"]
    .sum()
    .reset_index()
)

customer_segments.to_csv(
    "../data/customer_segments.csv",
    index=False
)

print("Analytics datasets generated successfully.")
def generate_business_insights():
    insights = {}

    # -----------------------------
    # Revenue trend insight
    # -----------------------------
    monthly = monthly_revenue.copy()
    monthly["Total Amount"] = monthly["Total Amount"].astype(float)

    first = monthly.iloc[0]["Total Amount"]
    last = monthly.iloc[-1]["Total Amount"]

    change_pct = ((last - first) / first) * 100

    insights["revenue_change_percent"] = round(change_pct, 2)

    if change_pct < -5:
        insights["revenue_trend"] = "declining"
    elif change_pct > 5:
        insights["revenue_trend"] = "growing"
    else:
        insights["revenue_trend"] = "stable"

    # -----------------------------
    # Category performance insight
    # -----------------------------
    top_cat = revenue_by_category.sort_values(
        "Total Amount", ascending=False
    ).iloc[0]

    worst_cat = revenue_by_category.sort_values(
        "Total Amount", ascending=True
    ).iloc[0]

    insights["top_category"] = top_cat["Product Category"]
    insights["worst_category"] = worst_cat["Product Category"]

    # -----------------------------
    # Customer segment insight
    # -----------------------------
    top_segment = customer_segments.sort_values(
        "Total Amount", ascending=False
    ).iloc[0]

    insights["top_customer_segment"] = (
        f"{top_segment['Gender']} - {top_segment['Product Category']}"
    )

    # -----------------------------
    # Alerts & recommendation seeds
    # -----------------------------
    alerts = []
    recommendations = []

    if insights["revenue_trend"] == "declining":
        alerts.append("Revenue has declined significantly over the observed period.")
        recommendations.append(
            "Investigate pricing, demand shifts, or marketing effectiveness."
        )

    recommendations.append(
        f"Double down on high-performing category: {insights['top_category']}."
    )

    recommendations.append(
        f"Analyze issues in underperforming category: {insights['worst_category']}."
    )

    insights["alerts"] = alerts
    insights["recommendation_seeds"] = recommendations

    return insights
if __name__ == "__main__":
    insights = generate_business_insights()
    print(insights)

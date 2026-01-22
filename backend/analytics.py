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

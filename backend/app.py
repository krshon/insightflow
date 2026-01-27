from fastapi import FastAPI
import pandas as pd

app = FastAPI(title="Insight Flow API")

# Load preprocessed datasets
revenue_by_category = pd.read_csv("../data/revenue_by_category.csv")
monthly_revenue = pd.read_csv("../data/monthly_revenue.csv")
customer_segments = pd.read_csv("../data/customer_segments.csv")


@app.get("/")
def root():
    return {"message": "Insight Flow API is running"}


@app.get("/revenue/category")
def get_revenue_by_category():
    return revenue_by_category.to_dict(orient="records")


@app.get("/revenue/monthly")
def get_monthly_revenue():
    return monthly_revenue.to_dict(orient="records")


@app.get("/customers/segments")
def get_customer_segments():
    return customer_segments.to_dict(orient="records")

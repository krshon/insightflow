def analyze_revenue_by_category(df):
    top = df.sort_values("Total Amount", ascending=False).iloc[0]

    return {
        "context": f"""
Category: {top['Product Category']}
Revenue: {top['Total Amount']}
""",
        "fallback": (
            f"{top['Product Category']} is the highest revenue-generating category, "
            "indicating strong product-market fit."
        ),
        "visualization": "bar_chart",
    }

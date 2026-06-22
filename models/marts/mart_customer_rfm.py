import pandas as pd
from datetime import date


def model(dbt, session):
    """
    RFM customer analysis using Pandas.

    Python shines here because pd.qcut() (quantile binning) and .apply()
    (row-wise Python functions) would require many lines of SQL window functions.

    dbt.ref() returns a DuckDBPyRelation — call .df() to convert to Pandas.
    """
    dbt.config(materialized="table")

    # Load upstream model — same dbt.ref() you know from SQL models
    orders = dbt.ref("int_orders_enriched").df() # now its a pandas dataframe

    # Python filtering: clean and familiar
    completed = orders[orders["status"] == "completed"].copy()
    completed["order_date"] = pd.to_datetime(completed["order_date"])

    reference_date = pd.Timestamp(date.today())

    # Step 1 — calculate Recency, Frequency, Monetary per customer
    rfm = (
        completed
        .groupby("customer_id")
        .agg(
            last_order_date=("order_date", "max"),
            frequency=("order_id", "count"),
            monetary=("total_amount", "sum"),
        )
        .reset_index()
    )

    rfm["recency_days"] = (reference_date - rfm["last_order_date"]).dt.days

    # Step 2 — assign 1-5 quintile scores (5 = best for all three metrics)
    # rank() before qcut() prevents duplicate bin edges when values repeat
    rfm["r_score"] = pd.qcut(
        rfm["recency_days"].rank(method="first"), q=5, labels=[5, 4, 3, 2, 1]
    ).astype(int)
    rfm["f_score"] = pd.qcut(
        rfm["frequency"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    rfm["m_score"] = pd.qcut(
        rfm["monetary"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]
    ).astype(int)

    rfm["rfm_score"] = rfm["r_score"] + rfm["f_score"] + rfm["m_score"]

    # Step 3 — classify into segments using a plain Python function
    # This multi-condition branching is exactly what Python is better at than SQL
    def classify_segment(score):
        if score >= 13:
            return "champion"
        elif score >= 10:
            return "loyal"
        elif score >= 7:
            return "at_risk"
        else:
            return "lost"

    rfm["segment"] = rfm["rfm_score"].apply(classify_segment)

    return rfm[[
        "customer_id",
        "recency_days",
        "frequency",
        "monetary",
        "r_score",
        "f_score",
        "m_score",
        "rfm_score",
        "segment",
    ]]

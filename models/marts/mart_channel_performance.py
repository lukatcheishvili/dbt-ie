import pandas as pd


def model(dbt, session):
    dbt.config(materialized="table")

    sessions = dbt.ref("stg_website_sessions").df()

    summary = (
        sessions
        .groupby(["source", "device_type"])
        .agg(
            total_sessions=("session_id", "count"),
            conversions=("converted", "sum"),
            avg_page_views=("page_views", "mean"),
            avg_duration_seconds=("session_duration_seconds", "mean"),
            bounce_rate=("is_bounce", "mean"),
        )
        .reset_index()
    )

    summary["conversion_rate"] = (
        summary["conversions"] / summary["total_sessions"] * 100
    ).round(2)

    def classify_channel(conversion_rate):
        if conversion_rate >= 10:
            return "high_performing"
        elif conversion_rate >= 5:
            return "average"
        else:
            return "low_performing"

    summary["channel_quality"] = summary["conversion_rate"].apply(classify_channel)

    return summary.round({"avg_page_views": 1, "avg_duration_seconds": 0, "bounce_rate": 3})

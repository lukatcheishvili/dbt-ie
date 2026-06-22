def model(dbt, session):
    """
    Website traffic performance aggregated by source and device type.

    Python is useful here because:
    - groupby/agg in Pandas is readable for multi-metric aggregations
    - channel_quality classification with .apply() avoids nested CASE logic
    """
    dbt.config(materialized="table")

    sessions = dbt.ref("stg_website_sessions").df()

    perf = (
        sessions
        .groupby(["source", "device_type"])
        .agg(
            total_sessions=("session_id", "count"),
            conversions=("converted", "sum"),
            avg_page_views=("page_views", "mean"),
            avg_duration_seconds=("session_duration_seconds", "mean"),
            bounces=("is_bounce", "sum"),
        )
        .reset_index()
    )

    perf["bounce_rate"] = (
        perf["bounces"] / perf["total_sessions"] * 100
    ).round(2)
    perf["conversion_rate"] = (
        perf["conversions"] / perf["total_sessions"] * 100
    ).round(2)

    def classify_channel(conversion_rate):
        if conversion_rate >= 10:
            return "high_performing"
        if conversion_rate >= 5:
            return "average"
        return "low_performing"

    perf["channel_quality"] = perf["conversion_rate"].apply(classify_channel)
    for column in ["source", "device_type", "channel_quality"]:
        perf[column] = perf[column].astype("object")

    return perf[[
        "source",
        "device_type",
        "total_sessions",
        "conversions",
        "avg_page_views",
        "avg_duration_seconds",
        "bounce_rate",
        "conversion_rate",
        "channel_quality",
    ]].round({
        "avg_page_views": 1,
        "avg_duration_seconds": 0,
    })

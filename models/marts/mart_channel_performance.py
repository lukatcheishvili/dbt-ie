def model(dbt, session):
    """
    Website traffic performance aggregated by source and device type.

    Python is useful here because:
    - groupby/agg in Pandas is more readable than GROUP BY with many aggregations
    - channel_quality classification with .apply() is cleaner than nested CASE WHEN
    """
    dbt.config(materialized="table")

    # Load upstream staging model — .df() converts DuckDB relation to Pandas DataFrame
    sessions = dbt.ref("stg_website_sessions").df()

    # Group by source and device_type, compute all aggregations in one step
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

    # Derived metrics — calculated after aggregation
    perf["bounce_rate"] = perf["bounces"] / perf["total_sessions"] * 100
    perf["conversion_rate"] = perf["conversions"] / perf["total_sessions"] * 100

    # Classify channel quality based on conversion_rate threshold
    # Python .apply() shines here vs deeply nested SQL CASE expressions
    def classify_channel(conversion_rate):
        if conversion_rate >= 10:
            return "high_performing"
        elif conversion_rate >= 5:
            return "average"
        else:
            return "low_performing"

    perf["channel_quality"] = perf["conversion_rate"].apply(classify_channel)

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
    ]]
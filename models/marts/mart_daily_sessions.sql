{{ config(
    materialized='incremental',
    unique_key='session_day',
    on_schema_change='append_new_columns'
) }}

with sessions as (
    select
        cast(session_date as date) as session_day,
        converted,
        source
    from {{ ref('stg_website_sessions') }}
    {% if is_incremental() %}
    where cast(session_date as date) > (select max(session_day) from {{ this }})
    {% endif %}
),

aggregated as (
    select
        session_day,
        count(*) as sessions,
        sum(case when converted then 1 else 0 end) as conversions,
        round(
            sum(case when converted then 1 else 0 end) * 100.0 / count(*),
            2
        ) as conversion_rate,
        count(distinct source) as unique_sources
    from sessions
    group by session_day
)

select
    session_day,
    sessions,
    conversions,
    conversion_rate,
    unique_sources
from aggregated
order by session_day

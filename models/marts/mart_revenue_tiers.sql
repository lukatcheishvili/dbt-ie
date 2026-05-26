with completed_orders as (

    select
        order_id,
        customer_id,
        order_date,
        status,
        total_amount
    from {{ ref('int_orders_enriched') }}
    where status = 'completed'

)

select
    order_id,
    customer_id,
    order_date,
    status,
    total_amount,

    -- default thresholds: low < 100, medium < 500, high >= 500
    {{ classify_revenue('total_amount') }}
        as revenue_tier,

    -- strict thresholds as lists: low < 50, medium < 200, high >= 200
    {{ classify_revenue('total_amount', thresholds=[50, 200], labels=['low', 'medium', 'high']) }}
        as revenue_tier_strict,

    -- bonus: four tiers — no macro change needed, just pass longer lists
    {{ classify_revenue('total_amount', thresholds=[100, 500, 1000], labels=['bronze', 'silver', 'gold', 'platinum']) }}
        as revenue_tier_four

from completed_orders
select
    order_id,
    customer_id,
    order_date,
    status,
    total_amount,
    {{ classify_revenue('total_amount') }} as revenue_tier,
    {{ classify_revenue('total_amount', low=50, high=200) }} as revenue_tier_strict
from {{ ref('int_orders_enriched') }}
where is_completed_order

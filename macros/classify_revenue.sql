-- =============================================================================
-- MACRO: classify_revenue
-- =============================================================================
-- Generates a CASE expression for revenue tiers.
-- Supports the baseline low/high arguments and the bonus list-based thresholds.
--
-- Default call:
--   {{ classify_revenue('total_amount') }}
--
-- Baseline overrides:
--   {{ classify_revenue('total_amount', low=50, high=200) }}
--
-- List-based overrides:
--   {{ classify_revenue('total_amount', thresholds=[100, 500, 1000], labels=['bronze', 'silver', 'gold', 'platinum']) }}
-- =============================================================================

{% macro classify_revenue(amount_col, low=100, high=500, thresholds=none, labels=none) %}
    {%- set tier_thresholds = thresholds if thresholds is not none else [low, high] -%}
    {%- set tier_labels = labels if labels is not none else ['low', 'medium', 'high'] -%}
    case
        {% for i in range(tier_thresholds | length) %}
        when {{ amount_col }} < {{ tier_thresholds[i] }}
            then '{{ tier_labels[i] }}'
        {% endfor %}
        else '{{ tier_labels[tier_thresholds | length] }}'
    end
{% endmacro %}

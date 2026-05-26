-- =============================================================================
-- MACRO: classify_revenue (bonus — list-based version)
-- =============================================================================
-- Generates a CASE expression dynamically from threshold and label lists.
-- A Jinja for loop builds one WHEN branch per threshold.
-- The last label is always the ELSE branch.
--
-- Arguments:
--   amount_col  (required) — column to classify, e.g. 'total_amount'
--   thresholds  (default=[100, 500])              — N upper bounds (ascending)
--   labels      (default=['low','medium','high'])  — N+1 labels (one per tier)
--
-- Default call — identical output to the original macro:
--   {{ classify_revenue('total_amount') }}
--
-- Custom thresholds at the call site:
--   {{ classify_revenue('total_amount', thresholds=[50, 200], labels=['low', 'medium', 'high']) }}
--
-- Any number of tiers — no macro change needed:
--   {{ classify_revenue('total_amount', thresholds=[100, 500, 1000], labels=['bronze', 'silver', 'gold', 'platinum']) }}
-- =============================================================================

{% macro classify_revenue(amount_col, thresholds=[100, 500], labels=['low', 'medium', 'high']) %}
    case
        {% for i in range(thresholds | length) %}
        when {{ amount_col }} < {{ thresholds[i] }}
            then '{{ labels[i] }}'
        {% endfor %}
        else '{{ labels[thresholds | length] }}'
    end
{% endmacro %}
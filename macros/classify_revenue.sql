-- Exercise 1 solution: macro with if/elif/else + default arguments.
-- Default thresholds: low < 100, medium 100–500, high >= 500.
-- Callers can override thresholds: {{ classify_revenue('col', low=50, high=200) }}
{% macro classify_revenue(amount_col, low=100, high=500) %}
    case
        when {{ amount_col }} < {{ low }}  then 'low'
        when {{ amount_col }} < {{ high }} then 'medium'
        else                                    'high'
    end
{% endmacro %}

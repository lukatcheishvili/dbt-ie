{% snapshot customer_snapshot %}

{{ config(
    target_schema='snapshots',
    unique_key='customer_id',
    strategy='check',
    check_cols=['customer_segment', 'country']
) }}

select * from {{ source('raw', 'customers') }}

{% endsnapshot %}

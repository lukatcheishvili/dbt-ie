-- Singular test: conversion_rate must be between 0 and 100
-- dbt expects this query to return 0 rows — any rows returned = test failure
select
    source,
    device_type,
    conversion_rate
from {{ ref('mart_channel_performance') }}
where conversion_rate < 0
   or conversion_rate > 100
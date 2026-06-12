-- Singular test: conversion_rate must be a valid percentage (0–100).
-- Returns rows only when the rule is violated — any result means a failure.
select
    source,
    device_type,
    conversion_rate
from {{ ref('mart_channel_performance') }}
where
    conversion_rate < 0
    or conversion_rate > 100

---
marp: true
theme: ie-class
paginate: true
size: 16:9
math: katex
author:
  - name: Daniel Garcia
  - email: dgarciah@faculty.ie.edu
  - url: www.linkedin.com/in/dgarhdez
header: '<img src="../img/ie_logo.png" width="60"><span>Session 11 &mdash; Contracts, Versions &amp; Access &middot; <a href="mailto:dgarciah@faculty.ie.edu">dgarciah@faculty.ie.edu</a></span>'
---

<style>
section.tight h2,
section.compact-code h2,
section.fit-code h2,
section.two-column h2 {
  margin-bottom: 0.35em;
}

section.tight p,
section.compact-code p,
section.fit-code p,
section.two-column p {
  margin: 0.35em 0;
}

section.tight ul,
section.tight ol {
  margin: 0.35em 0;
}

section.tight li {
  margin: 0.18em 0;
}

section.compact-table table {
  font-size: 0.76em;
  margin: 0.45em auto;
}

section.compact-table thead th {
  padding: 0.45em 0.8em;
}

section.compact-table tbody td {
  padding: 0.35em 0.8em;
}

section.compact-code pre {
  font-size: 0.58em;
  line-height: 1.28;
  margin: 0.45em 0;
  padding: 0.6em 0.9em;
}

section.fit-code pre {
  font-size: 0.46em;
  line-height: 1.18;
  margin: 0.35em 0;
  padding: 0.5em 0.8em;
}

section.two-column .columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 34px;
  align-items: start;
}

section.two-column .columns > div > :first-child {
  margin-top: 0;
}

section.two-column pre {
  font-size: 0.50em;
  line-height: 1.22;
  margin: 0.35em 0;
  padding: 0.55em 0.75em;
}

section.two-column ul {
  font-size: 0.88em;
}

section.small {
  font-size: 22px;
}

section.small h2 {
  font-size: 31px;
}

section.small pre {
  font-size: 0.56em;
}
</style>

<!-- _class: lead -->

# Analytics Engineering: Session 11

## Model Governance: Contracts, Versions & Access

---

## Today

- Move from "models that build" to **models others can safely depend on**
- Use contracts to define model shape
- Use versions to manage breaking changes
- Use access levels to protect internal implementation details
- Practice with examples from this ecommerce dbt project

---

<!-- _class: tight -->

## Governance In This Repo

The project already has a layered contract, even before explicit model contracts.

- **Sources**: 14 raw DuckDB tables loaded from Parquet
- **Staging**: thin `stg_*` models over raw data
- **Intermediate**: joins and business logic in `int_*`
- **Marts**: reporting models like `dim_customers` and `mart_orders`

*Governance makes those boundaries explicit.*

---

## Why Model Governance?

As dbt projects grow, teams need rules to prevent downstream breakage.

- **Contracts**: Guarantee the shape of your data
- **Versions**: Allow breaking changes without breaking consumers immediately
- **Access**: Control who can reference which models

*Governance = Contracts + Versions + Access*

---

<!-- _class: compact-code -->

## Existing Example: `dim_customers`

The model already documents its public shape:

```yaml
models:
  - name: dim_customers
    description: Customer dimension...
    columns:
      - name: customer_id
        tests: [unique, not_null]
      - name: email
        tests: [unique, not_null]
      - name: customer_segment
        tests:
          - accepted_values:
              values: ['Bronze', 'Silver', 'Gold', 'Platinum']
```

This is governance material waiting to become a stronger contract.

---

<!-- _class: two-column -->

## Contracts vs Tests

<div class="columns">
<div>

**Contracts check the model interface**

- Does the output have the declared columns?
- Do column data types match the YAML?
- Are enforced constraints part of the built relation?
- Fails while dbt is building the model

</div>
<div>

**Tests check the rows inside it**

- Is `customer_id` unique and not null?
- Does every order link to `dim_customers`?
- Are statuses only `completed`, `cancelled`, etc.?
- Runs after the model exists

</div>
</div>

**Short version:** contracts protect the table shape; tests protect the data quality.

---

<!-- _class: compact-code -->

## Contract Example: `dim_customers`

Start with the columns consumers rely on most:

```yaml
models:
  - name: dim_customers
    access: public
    config:
      contract: {enforced: true}
    columns:
      - name: customer_id
        data_type: integer
        constraints:
          - type: not_null
      - name: email
        data_type: varchar
      - name: is_repeat_customer
        data_type: boolean
```

If SQL stops returning `email`, the model build fails.

---

<!-- _class: compact-code compact-table -->

## Constraint Examples

| Constraint | Good fit in this project |
| :--- | :--- |
| `not_null` | `customer_id`, `order_id`, `status` |
| `unique` | `dim_customers.customer_id` |
| `primary_key` | `mart_orders.order_id` |
| `check` | `total_amount >= 0` |

```yaml
- name: total_amount
  data_type: numeric
  constraints:
    - type: check
      expression: "total_amount >= 0"
```

---

<!-- _class: compact-code -->

## Test Example: `mart_orders`

`mart_orders.yml` already declares a core referential rule:

```yaml
- name: customer_id
  description: Foreign key to dim_customers.
  tests:
    - not_null
    - relationships:
        to: ref('dim_customers')
        field: customer_id
```

This says every order must belong to a known customer.

---

<!-- _class: compact-code -->

## Business Domain Example: Order Status

The project uses the same status domain in staging and marts:

```yaml
- name: status
  description: Fulfillment status of the order.
  tests:
    - not_null
    - accepted_values:
        values:
          - pending
          - shipped
          - completed
          - cancelled
          - refunded
```

This is a lightweight business contract.

---

<!-- _class: compact-code -->

## Custom Test Example: Positive Amounts

`stg_orders.yml` uses the project macro `test_is_positive`:

```yaml
- name: total_amount
  description: Final amount charged to the customer.
  tests:
    - not_null
    - is_positive:
        where: "status in ('completed', 'shipped')"
```

The rule is conditional: drafts and cancelled orders may behave differently.

---

<!-- _class: compact-code -->

## Model Versions

Versions let consumers choose when to migrate:

```yaml
models:
  - name: dim_customers
    latest_version: 2
    versions:
      - v: 1
        columns:
          - include: all
      - v: 2
        columns:
          - include: all
          - name: loyalty_tier
            data_type: varchar
```

Consumers can still call `{{ ref('dim_customers', v=1) }}`.

---

<!-- _class: two-column -->

## Versioning Example: Customer Dimension

<div class="columns">
<div>

**Version 1**

```sql
select
  customer_id,
  full_name,
  email,
  customer_segment,
  total_orders,
  total_spent
from final
```

</div>
<div>

**Version 2**

```sql
select
  customer_id,
  full_name,
  email,
  customer_segment,
  segment_id,
  average_order_value,
  is_repeat_customer
from final
```

</div>
</div>

Adding columns is usually safe; changing expectations may still need coordination.

---

<!-- _class: tight -->

## Breaking Change Example: `mart_orders`

`mart_orders` is one row per order today.

Breaking changes would include:

- Renaming `total_amount` to `order_total`
- Removing `payment_status_summary`
- Changing `order_date` from date to timestamp
- Changing grain from **one row per order** to **one row per order item**

If the grain changes, every downstream metric can change.

---

<!-- _class: compact-code -->

## Deprecation

Use deprecation to make migration visible:

```yaml
models:
  - name: mart_orders
    latest_version: 2
    versions:
      - v: 1
        deprecation_date: 2026-12-31
      - v: 2
```

- dbt warns users referencing v1
- Teams get a concrete migration deadline
- Deprecation communicates; it does not redesign the model for you

---

<!-- _class: compact-table -->

## Model Access

Control which models can be referenced by other projects or groups.

| Level | Who can `ref()` it? | Good use |
| :--- | :--- | :--- |
| **public** | Any project or group | `dim_customers`, `mart_orders` |
| **protected** | Same project only | default for course models |
| **private** | Same group only | internal intermediate logic |

*Access is about dependency boundaries, not data security.*

---

<!-- _class: compact-code -->

## Access Example For This DAG

Expose marts. Hide implementation details.

```yaml
models:
  - name: dim_customers
    access: public

  - name: mart_orders
    access: public

  - name: int_orders_enriched
    access: private

  - name: int_payments_by_order
    access: private
```

Dashboards depend on marts, not intermediate plumbing.

---

<!-- _class: two-column -->

## Why Hide Intermediate Models?

<div class="columns">
<div>

`int_orders_enriched` joins:

- order item summaries
- shipping status
- payment status
- generated order flags

</div>
<div>

It produces convenience fields:

```sql
is_completed_order,
is_cancelled_order,
is_refunded_order,
is_paid
```

</div>
</div>

Consumers should depend on the stable mart, not this implementation layer.

---

<!-- _class: compact-code -->

## Existing Logic: Shipping Buckets

`int_order_shipping_status` turns dates into a business label:

```sql
case
  when shipping.ship_date is null then 'not_shipped'
  when shipping.actual_delivery < shipping.estimated_delivery then 'early'
  when shipping.actual_delivery = shipping.estimated_delivery then 'on_time'
  when shipping.actual_delivery > shipping.estimated_delivery then 'late'
  else 'unknown'
end as shipping_performance_bucket
```

That label is governed with an `accepted_values` test.

---

<!-- _class: compact-code -->

## Existing Logic: Payment Summary

`int_payments_by_order` defines the payment contract for marts:

```sql
case
  when count(payment_id) = 0 then 'unknown'
  when sum(case when status = 'completed' then 1 else 0 end)
       = count(payment_id) then 'paid'
  when sum(case when status = 'completed' then 1 else 0 end) > 0
       then 'partially_paid'
  else 'unpaid'
end as payment_status_summary
```

Governed values: `paid`, `partially_paid`, `unpaid`, `unknown`.

---

<!-- _class: compact-code -->

## Python Model Governance: RFM

`mart_customer_rfm.py` creates scored customer segments:

```python
def classify_segment(score):
    if score >= 13:
        return "champion"
    elif score >= 10:
        return "loyal"
    elif score >= 7:
        return "at_risk"
    else:
        return "lost"
```

The YAML test protects the output domain for `segment`.

---

<!-- _class: compact-table -->

## Breaking vs Non-breaking Changes

| Change | Example from this project | Action |
| :--- | :--- | :--- |
| Add a column | add `loyalty_tier` to `dim_customers` | usually safe |
| Add a test | require `status` not null | safe but may fail build |
| Rename a column | `total_amount` -> `order_total` | version |
| Remove a column | drop `email` from `dim_customers` | version |
| Change grain | order grain -> order item grain | version |

---

<!-- _class: fit-code -->

## Putting It All Together

Govern a real mart model with contract, version, and access:

```yaml
models:
  - name: mart_orders
    access: public
    latest_version: 1
    config:
      contract: {enforced: true}
    columns:
      - name: order_id
        data_type: integer
        constraints:
          - type: not_null
      - name: customer_id
        data_type: integer
        constraints:
          - type: not_null
        tests:
          - relationships:
              to: ref('dim_customers')
              field: customer_id
      - name: payment_status_summary
        data_type: varchar
        tests:
          - accepted_values:
              values: ['paid', 'partially_paid', 'unpaid', 'unknown']
```

---

<!-- _class: tight -->

## In-class Walkthrough

For any mart model, ask:

1. What is the grain?
2. What columns are part of the public API?
3. Which columns need `not_null`, `unique`, or relationship tests?
4. Which business labels need `accepted_values`?
5. Would a proposed change break downstream consumers?
6. Should consumers reference this model directly?

---

## What Have We Learned?

- Governance turns model ownership into explicit rules
- Contracts protect shape; tests protect values
- Versions let teams ship breaking changes responsibly
- Access levels protect project boundaries
- Existing models already contain strong governance examples

**Next Session:** Practice Session III: Production-Ready Data Quality.

# Deterministic candidate rejection diagnostics

Issue #22 adds a descriptive, deterministic diagnostics layer for AI-proposed grocery-offer candidates that fail canonical validation.

## Authority boundary

The authority remains unchanged:

```text
candidate
   ↓
validate_offers()
   ↓
accepted / rejected
          ↓
   diagnostics
```

Diagnostics explain schema failures. They do not repair candidates, change validation results, or create canonical data.

## API

```python
from grocery_deal_intelligence.diagnostics import diagnose_candidate_rejection

diagnostics = diagnose_candidate_rejection(candidate)
```

A valid candidate returns:

```python
[]
```

An invalid candidate returns one or more deterministic records shaped as:

```text
category
path
validator
message
```

## Stable categories

The current deterministic categories are:

- `missing_required_field` — a required canonical field is absent;
- `wrong_canonical_shape` — a field expected to be an object or array has the wrong structural shape;
- `wrong_field_type` — a scalar field has the wrong JSON type;
- `unexpected_field` — the candidate contains a field forbidden by the canonical schema at that path;
- `invalid_enum_or_value` — a value violates a deterministic enum, pattern, range, length, or uniqueness constraint;
- `schema_constraint_violation` — fallback for another JSON Schema constraint not mapped above.

Multiple failures are preserved and sorted deterministically by path, category, validator, and normalized message.

## What diagnostics do not claim

Schema diagnostics cannot prove semantic hallucination from the candidate alone.

For example, the #20 experiment produced:

```text
retailer: Forst
locality: Italy
provenance: Supplier
```

Some of those values are suspicious relative to the retailer source, but #22 does not label them as hallucinations because doing so would require source-aware semantic reasoning beyond the canonical schema.

What #22 can prove deterministically for the same candidate is that these fields have invalid canonical shapes:

```text
locality     expected object; got string
promotion    expected object; got string
provenance   expected object; got string
validity     expected object; got string
verification expected object; got string
```

This distinction is intentional.

## Design rule

```text
Validation decides.
Diagnostics explain deterministically.
Diagnostics never repair or authorize.
```

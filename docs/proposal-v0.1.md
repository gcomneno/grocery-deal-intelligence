# Proposal v0.1

Proposal v0.1 is the grocery-owned partial shape contract defined by the architecture decision in Issue #47.

Canonical rule:

> A proposal represents only claims the AI proposes from the evidence available to it. It need not be complete, it is not canonical, and absence of a field is valid information.

## Shape semantics

- The top-level object may be empty. `{}` means that no claims are being proposed.
- Every top-level claim field is optional.
- Nested objects may be partial.
- Empty nested objects are invalid because they introduce structure without making a claim.
- Unknown top-level and nested properties are invalid in v0.1.
- Authority-like fields are not part of the schema and are therefore invalid.

Examples:

```json
{}
```

Valid: no claims.

```json
{
  "price": 1.83,
  "validity": {
    "from": "2026-08-24T00:00:00Z"
  }
}
```

Valid: two claims.

```json
{
  "provenance": {
    "source_url": "https://example.invalid/source"
  }
}
```

Valid: the proposal does not need to fabricate `source_type` or `observed_at` merely because canonical Grocery Offer v0.1 requires them.

```json
{
  "validity": {}
}
```

Invalid: empty nested objects make no claim.

## Validation boundary

`validate_proposal()` validates Proposal v0.1 shape only.

It does not establish:

- source support;
- truth;
- canonical completeness;
- canonical structural validity;
- admission eligibility;
- canonical authority.

A proposal can therefore be valid while the same object is invalid under Grocery Offer v0.1.

## Relationship to canonical schema

Proposal v0.1 is separately versioned and deliberately not derived mechanically from Grocery Offer v0.1. Its vocabulary is intentionally closed in this first version so that schema-constrained inference cannot add arbitrary locality, verification, or provenance metadata.

The canonical schema is unchanged.

## Runtime status

Issue #50 adds only the proposal contract and deterministic validator. Existing AI capability, adapter, ingestion, source evidence, canonical validation, and admission behavior remain unchanged.

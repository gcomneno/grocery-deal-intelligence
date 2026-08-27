# Deterministic Proposal v0.1 → canonical projection

Issue #54 introduces a pure deterministic projection layer between Proposal v0.1 claim verification and canonical Grocery Offer validation.

## Authority rule

```text
No evidence -> no canonical fact.
```

Projection may use only:

- Proposal v0.1 leaf claims classified as `supported`;
- deterministic source evidence.

A Proposal claim classified as `contradicted` or `unverifiable` is reported in `rejected_claims` and cannot contribute to canonical completion.

An absent Proposal claim may be supplied by deterministic source evidence. If a required canonical fact is absent from both usable sources, the result is `not_projectable`.

## Result

`project_proposal_to_canonical()` returns:

```text
projectable
candidate
missing_required_claims
rejected_claims
```

When `projectable` is false, `candidate` is always `null`.

Required missing facts are reported as deterministic canonical paths, including nested leaf paths such as:

```text
["provenance", "observed_at"]
["validity", "from"]
["validity", "to"]
```

## Separation of gates

Projection proves only that every canonical-required fact can be assembled from allowed deterministic inputs. It does not call canonical validation internally.

Therefore:

```text
projectable
    !=
canonical structurally valid
```

A projectable candidate must still pass the existing Grocery Offer v0.1 validator and, later, the existing admission policy.

## Non-repair guarantee

Projection does not:

- call AI;
- infer missing values;
- invent provenance, locality, verification, or promotion facts;
- apply retailer-specific repair;
- add placeholders merely to satisfy the canonical schema;
- weaken canonical validation.

It is deterministic composition plus completeness checking only.

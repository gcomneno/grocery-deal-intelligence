# Lidl deterministic completion rules

## Status

Implementation rationale for Issue #62.

## Objective

Complete the two remaining canonical-required Lidl facts identified by the #60 audit using explicit deterministic source-evidence rules rather than redundant AI Proposal claims.

The two facts are:

```text
locality.scope
verification.evidence_status
```

The generic Proposal -> canonical projection remains unchanged.

## Rule 1: locality.scope

Canonical `locality.scope = "store"` is emitted only when both conditions hold:

1. the Lidl source contains a non-empty `locality.stores` list made entirely of non-empty string store identifiers;
2. source verification explicitly states `verification.locality == "verified"`.

Rationale:

- explicit store identifiers establish that applicability is represented at store level;
- the independent verified-locality signal is required before promoting that representation into canonical locality scope;
- mere presence of region metadata, an empty store list, malformed store identifiers, or unverified locality is insufficient.

No fallback to `regional`, `national`, or `unknown` is synthesized.

If the conditions are not met, `locality.scope` remains absent and canonical projection may remain `not_projectable`.

## Rule 2: verification.evidence_status

Lidl `verification.flyer_match` is mapped through this finite table:

| Source `flyer_match` | Canonical `verification.evidence_status` |
| --- | --- |
| `exact` | `verified` |
| `partial` | `partial` |
| `unmatched` | `unmatched` |
| `unverified` | `unverified` |

Any missing or unrecognized source state produces no canonical `evidence_status` evidence.

Rationale:

- the mapping preserves rather than strengthens the source verification state;
- `exact` is the only source state promoted to canonical `verified`;
- unknown states are never treated as verified by default.

## Authority boundary

These rules belong in retailer-specific deterministic source-evidence projection:

```text
Lidl source
   ↓
project_source_evidence()
   ↓
canonical-addressable deterministic evidence
   ↓
generic Proposal verification/projection
```

They do not belong in:

- the AI prompt;
- Proposal v0.1 schema;
- `project_proposal_to_canonical()`;
- admission policy;
- retailer-specific post-inference repair.

## Invariant

```text
deterministically established -> evidence
not established -> absent
absent required canonical fact -> not_projectable
```

The two fixed Lidl records from #58 must be rerun after merge-quality regression checks. Their outcome is evidence about these rules, not a target that may justify weakening them.

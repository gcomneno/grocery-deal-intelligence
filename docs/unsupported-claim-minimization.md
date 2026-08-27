# Unsupported claim minimization

## Objective

Reduce AI-generated claims that cannot be verified against deterministic source evidence while preserving:

- zero contradicted claims on the fixed corpus;
- positive support for all critical admission claims;
- the canonical schema;
- deterministic validation, claim verification, and admission authority.

Baseline from the post-grounding fixed corpus:

```text
contradicted claims: 0
supported claims: 42
unverifiable claims: 29
critical supported: 20/20
canonical records: 4/4
```

## Constraint discovered before implementation

The current Grocery Offer v0.1 schema requires `promotion`, `locality`, `verification`, and `provenance`. In particular, provenance requires non-empty `source_type`, `source_url`, and `observed_at` strings.

Therefore the capability cannot generally satisfy both of these requirements at once:

1. emit a structurally valid Grocery Offer v0.1 object; and
2. omit every claim for which deterministic evidence is unavailable.

Some uncertainty can be represented conservatively (`locality.scope = "unknown"`, empty stores, verification states such as `unknown`/`unverified`), but required provenance strings have no equivalent unknown/null representation.

## Fixed-corpus classification

The 29 post-grounding unverifiable claims split conservatively into two practical groups under the current schema.

### Safely avoidable optional claims: 5

These were extra model-produced details not required by Grocery Offer v0.1 and absent from deterministic source evidence:

- Esselunga fixture 1: three additional provenance metadata properties beyond the required provenance core;
- Esselunga fixture 2: one additional provenance verification metadata property;
- Lidl fixture 1: `locality.region`.

These five claims may be omitted without changing the canonical schema or weakening any downstream gate.

### Required / contract-constrained claims: 24

The remaining unverifiable claims are associated with fields or nested properties required for structural validity, including combinations of:

- `currency` where deterministic evidence does not expose it;
- required `promotion.type` and `promotion.requires_loyalty`;
- required `locality.scope` and `locality.stores`;
- required `verification.locality_status` and `verification.evidence_status`;
- required provenance `source_type`, `source_url`, and `observed_at`.

Some of these can use conservative schema-defined states such as `unknown` or `unverified`, but they remain unverifiable unless deterministic evidence supports those values. The required provenance core is stricter: it currently has no schema-defined unknown/null representation.

Accordingly, the first realistic minimization target is approximately:

```text
unverifiable: 29 -> 24
```

not `29 -> 0`.

The actual runtime delta must still be measured; this count is a contract-based upper bound for clearly removable optional claims on the observed corpus, not an encoded expected result.

## Decision

Do not solve this by:

- inventing placeholder provenance;
- expanding deterministic evidence with unsupported facts;
- weakening claim verification;
- weakening admission policy;
- silently changing the canonical schema;
- adding retailer-specific repair after inference.

Before changing runtime behavior, classify unverifiable claims into:

```text
avoidable optional/specific claim
required claim with conservative uncertainty representation
required claim with no schema-valid uncertainty representation
```

Only the first two categories are legitimate capability-minimization targets under the current schema. The third category is a schema/evidence-contract tension and must be made explicit rather than hidden by prompt tuning.

## Candidate capability rule

For grounded proposals, the rule is now:

```text
known deterministic fact -> reproduce grounded evidence
unknown optional fact -> omit when schema permits
unknown required fact -> use only a schema-defined uncertainty value when one exists
unknown required fact without uncertainty representation -> use raw source only when directly supported; never fabricate
```

This rule applies only to grounded proposal prompting. Legacy source-only proposal behavior remains unchanged.

## Authority boundary

Claim minimization changes proposal quality only. It does not grant authority:

```text
AI proposal
  -> structural validation
  -> deterministic source-support verification
  -> deterministic admission policy
  -> canonical eligibility
```

The fixed corpus must be rerun after this capability change. Success is measured by fewer unverifiable claims without increasing contradictions or reducing support for critical claims.
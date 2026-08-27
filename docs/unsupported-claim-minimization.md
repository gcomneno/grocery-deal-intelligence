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

## Decision

Do not solve this by:

- inventing placeholder provenance;
- expanding deterministic evidence with unsupported facts;
- weakening claim verification;
- weakening admission policy;
- silently changing the canonical schema;
- adding retailer-specific repair after inference.

Before changing runtime behavior, classify the 29 unverifiable claims into:

```text
avoidable optional/specific claim
required claim with conservative uncertainty representation
required claim with no schema-valid uncertainty representation
```

Only the first two categories are legitimate capability-minimization targets under the current schema. The third category is a schema/evidence-contract tension and must be made explicit rather than hidden by prompt tuning.

## Candidate capability rule

For grounded proposals, the intended rule is:

```text
known deterministic fact -> reproduce grounded evidence
unknown optional fact -> omit when schema permits
unknown required fact -> use only a schema-defined uncertainty value when one exists
unknown required fact without uncertainty representation -> do not fabricate; surface the contract tension
```

## Authority boundary

Claim minimization changes proposal quality only. It does not grant authority:

```text
AI proposal
  -> structural validation
  -> deterministic source-support verification
  -> deterministic admission policy
  -> canonical eligibility
```

The fixed corpus must be rerun after any capability change. Success is measured by fewer unverifiable claims without increasing contradictions or reducing support for critical claims.
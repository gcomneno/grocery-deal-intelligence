# Direct deterministic canonical projection audit

## Status

Architectural audit for Issue #60. This document does not change runtime behavior.

## Decision

`project_proposal_to_canonical()` already projects every schema-compatible leaf from deterministic source evidence before it considers Proposal claims. Therefore the `missing_required_claims` observed in the fixed Proposal v0.1 corpus experiment are genuine evidence gaps, not redundant Proposal requirements imposed by projection.

The next implementation work must focus on deterministic evidence enrichment where justified. Projection itself must not synthesize or repair missing values.

## Classification vocabulary

Every canonical-required path is classified per source family as one of:

- `direct_evidence`: already emitted deterministically by `project_source_evidence()` and therefore directly projectable without any AI Proposal claim;
- `deterministic_rule_candidate`: not currently emitted, but a deterministic rule may be justified from explicit trusted source/acquisition context; such a rule requires its own contract and tests before becoming evidence;
- `unsupported`: current trusted inputs do not establish the fact; it must remain missing and keep the record `not_projectable`.

A value is not a deterministic-rule candidate merely because it is plausible or obvious to a human.

## Canonical-required field matrix

| Canonical path | Lidl | Esselunga | Rationale |
| --- | --- | --- | --- |
| `retailer` | direct_evidence | direct_evidence | Trusted retailer context is supplied to source-evidence projection. |
| `product_name` | direct_evidence | direct_evidence | Lidl copies `product_name`; Esselunga maps `title`. |
| `price` | direct_evidence | direct_evidence | Lidl copies `price`; Esselunga maps first promo price. |
| `currency` | direct_evidence | deterministic_rule_candidate | Lidl source carries currency. Esselunga record does not; a feed/acquisition-level currency contract could establish it, but no such evidence rule exists today. |
| `promotion.type` | direct_evidence | deterministic_rule_candidate | Lidl source carries `promotion_type`. Esselunga has mechanism codes/descriptions, but no canonical mapping contract currently establishes `type`. |
| `promotion.requires_loyalty` | direct_evidence | deterministic_rule_candidate | Lidl source carries it. Esselunga promotion metadata may encode loyalty semantics, but a tested deterministic mapping is required before this becomes evidence. |
| `validity.from` | direct_evidence | direct_evidence | Both source projections deterministically map source validity fields. |
| `validity.to` | direct_evidence | direct_evidence | Both source projections deterministically map source validity fields. |
| `locality.scope` | deterministic_rule_candidate | unsupported | Lidl carries region/store context from which canonical scope may be derivable only after explicit scope semantics are defined. Current Esselunga record/context does not establish offer locality scope. |
| `locality.stores` | direct_evidence | unsupported | Lidl explicitly carries store IDs. Current Esselunga record/context does not carry canonical store identity. |
| `verification.locality_status` | direct_evidence | unsupported | Lidl maps source verification locality. No equivalent deterministic Esselunga fact exists in current inputs. |
| `verification.evidence_status` | deterministic_rule_candidate | unsupported | Lidl `flyer_match` may support an explicit mapping such as exact/unmatched to canonical evidence status, but that mapping is not currently defined. Esselunga has no equivalent current evidence. |
| `provenance.source_type` | direct_evidence | deterministic_rule_candidate | Lidl source provenance carries it. For Esselunga this should come from trusted acquisition context, not AI, if such context is made explicit. |
| `provenance.source_url` | direct_evidence | deterministic_rule_candidate | Lidl campaign URL is mapped. Esselunga source URL could be acquisition metadata, but it is not currently part of deterministic evidence. |
| `provenance.observed_at` | direct_evidence | deterministic_rule_candidate | Lidl carries observation time. Esselunga needs an explicit acquisition-time fact; model-generated timestamps are not evidence. |

## Key result from #58

The fixed Proposal v0.1 run produced:

```text
proposal_total_claims: 9
proposal_supported_claims: 3
proposal_contradicted_claims: 1
proposal_unverifiable_claims: 5
projectable_records: 0
not_projectable_records: 4
canonical_records: 0
```

This is consistent with the matrix above.

### Lidl

For both Lidl records the projection already has almost every required canonical fact directly from evidence. The two systematic gaps are:

```text
locality.scope
verification.evidence_status
```

One Lidl Proposal also contradicted `provenance.source_type`; projection correctly rejected that claim and retained no AI authority from it.

This means Lidl is the best next source family for deterministic evidence enrichment. If, and only if, explicit grocery-owned rules can establish `locality.scope` and `verification.evidence_status`, Lidl may become projectable without asking AI to repeat any required fact.

### Esselunga

The current deterministic evidence establishes only:

```text
retailer
product_name
price
validity.from
validity.to
```

The remaining canonical-required gaps are materially broader. Some may be establishable from explicit acquisition or retailer feed contracts (`currency`, provenance); promotion semantics may be establishable from documented mechanism mappings. Locality and verification remain unsupported by the current inputs.

Esselunga must therefore remain `not_projectable` until those facts have explicit deterministic support. Prompt tuning or AI-filled canonical fields are not valid substitutes.

## Projection contract finding

No projection-contract correction is required for direct evidence use.

The projection currently performs the correct ordering:

```text
1. copy schema-compatible deterministic evidence leaves
2. overlay only Proposal claims classified supported
3. compute missing canonical-required paths
4. return candidate only when complete
```

Therefore:

```text
#58 missing required claim
        =
missing deterministic evidence after supported Proposal composition
```

not:

```text
projection requires AI to repeat deterministic evidence
```

## Runtime/acquisition context as evidence

Some canonical facts do not belong in the raw retailer record but may still be deterministic facts owned by ingestion/acquisition. Provenance is the clearest example.

A future evidence API may therefore need to distinguish:

```text
record-derived evidence
+
trusted acquisition-context evidence
        ↓
canonical source evidence
```

This must remain explicit. Runtime context is evidence only when it contains a concrete trusted fact, not when code invents a convenient default.

Examples:

- source URL captured by the fetcher: potentially valid acquisition evidence;
- observation timestamp captured at acquisition: potentially valid acquisition evidence;
- source type fixed by a typed retailer source adapter: potentially valid acquisition evidence;
- `EUR` inferred merely because the retailer is Italian: not evidence unless the source/feed contract explicitly guarantees that currency.

## Follow-up split

The audit recommends separate implementation issues.

### A. Lidl deterministic completion rules

Study and, if justified, implement explicit deterministic mappings for:

```text
locality.scope
verification.evidence_status
```

No AI involvement.

### B. Acquisition-context evidence contract

Define how trusted ingestion metadata may contribute deterministic evidence for canonical provenance and other source-level facts.

This is likely required before Esselunga can provide trustworthy provenance without AI fabrication.

### C. Esselunga promotion semantics audit

Determine whether the current Esselunga mechanism codes/descriptions have a documented, stable mapping to:

```text
promotion.type
promotion.requires_loyalty
```

Until established, both remain unsupported by deterministic evidence.

### D. Esselunga locality/verification evidence

Do not invent defaults. Identify whether retailer/store/campaign acquisition context can establish locality and verification semantics. If not, these remain true blockers and Esselunga remains `not_projectable`.

## Invariants

```text
deterministically known fact -> project directly
explicit deterministic rule -> may enrich evidence after separate validation
AI repetition -> never required for an already known fact
AI-only unsupported claim -> never grants canonical authority
missing deterministic fact -> not_projectable
```

## Non-goals

This audit does not:

- modify Proposal v0.1;
- modify the canonical schema;
- modify projection;
- enrich evidence yet;
- change admission policy;
- tune prompts;
- attempt to restore 4/4 canonical output.

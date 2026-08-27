# Evidence-grounded offer proposals

AI offer proposals may use deterministic `source_evidence` as grounding context before inference.

The grounding path is only used when canonical admission is explicitly requested. Legacy source-only proposal behavior remains available and unchanged.

```text
raw source
   ↓
project_source_evidence()
   ↓
partial deterministic evidence
   ├──────────────┐
   ↓              ↓
AI proposal   later verifier
   ↓              ↓
candidate ────────┘
   ↓
validate_offers()
   ↓
verify_candidate_claims()
   ↓
evaluate_canonical_admission()
```

Grounding does not grant authority. The AI candidate must still pass structural validation, deterministic claim verification, and canonical admission.

Adapters may implement `propose_grounded(source_record, source_evidence=...)`. The base adapter contract provides a backward-compatible fallback to the legacy `propose(source_record)` behavior, so existing adapters do not gain hidden requirements.

The GiadaWare AI adapter passes detached copies of both raw source and deterministic evidence into the grocery proposal capability. The capability keeps the two inputs visibly separate in the prompt and continues to use the unchanged Grocery Offer v0.1 response schema.

No retailer-specific prompt rule is introduced by this feature. Known deterministic facts are supplied as evidence instead of being re-inferred from retailer-specific raw shapes.

The follow-up measurement must rerun the same four-record real corpus and compare contradicted claims and canonical admission against the pre-grounding baseline:

```text
4 structurally valid
2 admission eligible
2 admission ineligible
5 contradicted claims
2 canonical
```

The target is lower contradiction under unchanged deterministic authority, not an artificial 4/4 canonical result.

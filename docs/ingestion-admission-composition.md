# Ingestion admission composition

Canonical admission is an explicit opt-in path layered on top of the existing ingestion contract.

The three deterministic questions remain separate:

```text
validate_offers()
    -> structural validation

project_source_evidence() + verify_candidate_claims()
    -> source-support evidence

evaluate_canonical_admission()
    -> canonical authority decision
```

The legacy call:

```python
ingest_offer(source, ai=adapter, validate=True)
```

keeps its existing structural-only behavior for backward compatibility.

Semantic admission must be requested explicitly:

```python
ingest_offer(
    source,
    ai=adapter,
    validate=True,
    admission=True,
    retailer="lidl",
)
```

`admission=True` requires both `validate=True` and a non-empty trusted retailer context. Invalid configuration fails explicitly.

The admission-enabled result keeps all evidence layers visible:

```text
candidate
validated
structural_validation
source_evidence
claim_verification
admission
canonical
```

`validated` continues to report structural validity. Therefore an admission-enabled result may legitimately contain:

```text
validated: true
admission.eligible: false
canonical: null
```

This distinction is intentional. A candidate can have canonical shape while still containing contradicted or insufficiently supported critical facts.

Only `admission.eligible == true` authorizes `canonical` in the admission-enabled path.

Source evidence is always projected from the original source record plus trusted retailer context, never from the AI candidate. The AI remains advisory and cannot influence the admission decision directly.

Design rule:

```text
Validation answers: does it have canonical shape?
Verification answers: what does the source support?
Admission answers: may this become canonical?
Keep all three answers visible.
```

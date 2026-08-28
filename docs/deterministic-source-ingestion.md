# Deterministic source-record ingestion

## Purpose

`ingest_deterministic_source_record()` is the first-class AI-free ingestion path for retailer adapter output.

It centralizes the authority sequence that was previously reconstructed inside the deterministic road test:

```text
retailer adapter
      ↓
deterministic source record
      ↓
project_source_evidence()
      ↓
evidence-derived candidate
      ↓
verify_candidate_claims()
      ↓
validate_offers()
      ↓
evaluate_canonical_admission()
      ↓
canonical or null
```

The road test now verifies this core path instead of defining a second implementation of it.

## Contract

```python
ingest_deterministic_source_record(source_record, *, retailer)
```

The function:

- requires a non-empty retailer;
- deep-copies caller input;
- projects retailer-specific deterministic source evidence;
- copies only the established canonical/evidence candidate fields from that projection;
- verifies every candidate claim against the projected evidence;
- performs canonical structural validation;
- evaluates canonical admission;
- returns all intermediate layers;
- returns canonical data only when admission is eligible;
- never invokes AI;
- requires no network access.

## Returned authority layers

The result keeps the layers separate:

```text
candidate
source_evidence
claim_verification
structural_validation
admission
canonical
```

`canonical` is `None` whenever admission is ineligible.

The function also reports `ai_used: false` explicitly.

## Evidence-derived candidate boundary

The deterministic candidate is copied only from the same evidence-projection fields already exercised by the road test:

- retailer;
- product name;
- price and currency;
- reference price when explicitly supported;
- packaging text;
- base-price text;
- promotion evidence;
- validity;
- locality;
- verification metadata;
- provenance.

No missing canonical fact is synthesized to make structural validation pass.

## Real-fixture behavior

The committed Carrefour and Despar fixtures intentionally exercise different outcomes through the same function.

### Carrefour

The captured Carrefour fixture supplies enough evidence for its three records to remain:

```text
source-supported
structurally valid
admission eligible
canonical present
```

### Despar

The captured Despar fixture supplies source-supported claims but does not prove all canonical promotion semantics required by the schema. Its three records therefore remain:

```text
source-supported
structurally invalid
admission ineligible
canonical null
```

This is expected fail-closed behavior, not an ingestion failure.

## Architectural invariant

The core rule remains:

```text
source evidence decides what may be claimed
structural validation decides whether canonical shape is complete
admission decides whether canonical data may enter the trusted set
```

Neither the road test nor any future caller should independently reconstruct or weaken that sequence.

## Non-goals

This change introduces no:

- schema modification;
- admission-policy modification;
- source-evidence projection change;
- retailer-adapter semantic change;
- network fetching;
- AI behavior;
- source repair;
- synthetic fact completion.

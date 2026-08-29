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

The road test verifies this core path instead of defining a second implementation of it.

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
- promotion claims when explicitly supported;
- validity;
- locality;
- verification metadata;
- provenance.

No missing canonical fact is synthesized to make structural validation pass.

For promotion specifically, omission means only that no promotion claim is asserted. If a promotion object is present, every leaf that appears remains subject to the same source-evidence verification as every other canonical claim. No loyalty value or promotion type is defaulted.

## Real-fixture behavior

The committed Carrefour and Despar fixtures now both demonstrate successful deterministic admission through the same authority path, with different promotion evidence shapes.

### Carrefour

The captured Carrefour fixture supplies explicit promotion and loyalty evidence for its three records. They remain:

```text
source-supported
structurally valid
admission eligible
canonical present
```

### Despar

The captured Despar fixture supplies enough evidence for all three records to be structurally complete without inventing missing promotion semantics:

- Riso: promotion omitted;
- Pedavena: promotion omitted;
- Olio: only the supported `promotion.discount_text` claim is present.

All three remain:

```text
source-supported
structurally valid
admission eligible
canonical present
```

This does not turn absence of promotion evidence into evidence of no promotion. It only prevents unrelated missing promotion dimensions from blocking an otherwise evidence-complete shopper offer.

## Architectural invariant

The core rule remains:

```text
source evidence decides what may be claimed
structural validation decides whether canonical shape is complete
admission decides whether canonical data may enter the trusted set
```

Neither the road test nor any future caller should independently reconstruct or weaken that sequence.

## Non-goals

This path introduces no:

- admission-policy modification;
- retailer-specific source-evidence exception;
- network fetching;
- AI behavior;
- source repair;
- synthetic fact completion;
- inferred `requires_loyalty = false`;
- promotion taxonomy invented from retailer wording.

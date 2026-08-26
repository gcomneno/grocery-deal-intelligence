# Capability / canonical-schema contract audit

Issue #26 audits the contract alignment between the grocery canonical schema, the consumer-owned `ProposeOfferCandidateCapability`, GiadaWare AI's provider-independent backend surface, the concrete Ollama backend, and the real candidate evidence from issues #20 and #24.

This document is analysis/design only. It intentionally changes no runtime behavior.

## Executive conclusion

The repeated `wrong_canonical_shape` pattern is enabled primarily by a contract gap between the target canonical schema and the AI generation primitive.

The current capability tells the model to return an object "shaped for the Grocery Offer v0.1 contract", but it only lists top-level field names. It does not provide the nested JSON shapes required for `promotion`, `validity`, `locality`, `verification`, and `provenance`.

The current GiadaWare AI backend protocol exposes:

```python
generate_json(*, system_prompt: str, user_prompt: str) -> Mapping[str, object]
```

and therefore has no provider-independent parameter through which a consumer capability can request schema-constrained structured output.

The pinned `OllamaBackend` maps that primitive to:

```json
"format": "json"
```

which asks Ollama for valid JSON but does not provide the Grocery Offer JSON Schema as the response format constraint.

The adapter is not the source of the mismatch: it only invokes the capability and defensively copies the returned mapping. Deterministic validation is also not the source: it correctly rejects candidates that do not satisfy the canonical schema.

## 1. Canonical target shapes

`schema/grocery-offer-v0.1.schema.json` requires the following five repeatedly failing fields to be objects.

### `promotion`

```json
{
  "type": "...",
  "requires_loyalty": false,
  "discount_text": null
}
```

Required keys:

- `type`: non-empty string;
- `requires_loyalty`: boolean.

### `validity`

```json
{
  "from": "...",
  "to": "..."
}
```

Both keys are required; values may be string or `null`.

### `locality`

```json
{
  "scope": "national|regional|store|unknown",
  "stores": []
}
```

Required keys:

- `scope` from the canonical enum;
- `stores` as a unique string array.

### `verification`

```json
{
  "locality_status": "verified|unverified|unknown",
  "evidence_status": "verified|partial|unmatched|unverified"
}
```

Both keys are required.

### `provenance`

```json
{
  "source_type": "...",
  "source_url": "...",
  "observed_at": "..."
}
```

All three keys are required and non-empty strings.

## 2. What the proposal capability currently asks for

`ProposeOfferCandidateCapability` instructs the backend/model to:

- propose candidate canonical grocery-offer data;
- avoid authority claims;
- use only source-supported information;
- return JSON only;
- shape the object for Grocery Offer v0.1;
- use a listed set of top-level field names.

The prompt does **not** serialize or embed the canonical JSON Schema and does **not** describe the nested shapes of the five object-valued fields.

Therefore the phrase "shaped for the Grocery Offer v0.1 contract" is meaningful to the application codebase but under-specified to the model. The model receives the contract name and field names, not the actual structural contract.

## 3. What GiadaWare AI currently enforces

### Provider-independent protocol

`AIBackend.generate_json()` accepts only:

```text
system_prompt
user_prompt
```

and promises a mapping result.

There is no current backend-contract argument for a JSON Schema, typed response specification, or other structural constraint.

### Pinned Ollama backend

The concrete `OllamaBackend` sends:

```json
{
  "stream": false,
  "format": "json"
}
```

It then:

1. parses the Ollama response envelope;
2. parses `message.content` as JSON;
3. requires the parsed value to be a JSON object;
4. returns that object.

It does not compare the result against a consumer-provided schema and cannot receive one through the current `AIBackend` protocol.

## 4. Does GiadaWare AI expose schema-constrained output today?

No, not through the pinned provider-independent public backend contract used by Grocery Deal Intelligence.

The current surface can request JSON-object output, but it cannot express "generate JSON conforming to this JSON Schema".

This is a GiadaWare AI abstraction limitation, not an Ollama transport impossibility. Ollama's structured-output API supports supplying a JSON Schema in the `format` field; the current GiadaWare AI `OllamaBackend` simply does not expose that capability through `AIBackend`.

## 5. Observed evidence from #20 and #24

The real #24 experiment used four deterministic fixtures:

```text
2 Esselunga
2 Lidl
```

Observed summary:

```text
total_records: 4
accepted_records: 0
rejected_records: 4
wrong_canonical_shape: 20
```

Every candidate flattened the same five canonical object fields into strings or `null`:

```text
locality
promotion
provenance
validity
verification
```

This pattern is cross-retailer.

It also occurs on Lidl source records where structured locality, provenance, and verification evidence already exists in the source. Therefore the mismatch cannot be explained solely by Esselunga's raw source shape.

The evidence does **not** prove that the reference model is incapable of producing the required nested schema. The model was never given the full schema as an enforced structured-output contract. Model limitation therefore remains possible but unproven and should not be treated as the primary cause before a constrained experiment exists.

## 6. Responsibility analysis

### Canonical schema

**Not responsible for the observed flattening.**

The schema already expresses the required shapes explicitly and deterministic validation enforces them correctly.

Recommendation: **leave unchanged**.

### Deterministic validation

**Not responsible.**

It correctly rejects structurally invalid candidates and remains the canonical authority gate.

Recommendation: **leave unchanged**.

### `GiadaWareAIAdapter`

**Not responsible.**

The adapter intentionally performs no semantic translation or repair. It invokes the capability, verifies that the result is mapping-like, and returns a detached copy.

Recommendation: **leave unchanged**.

### `ProposeOfferCandidateCapability`

**Partially responsible / enables the gap.**

It owns grocery-specific proposal semantics but currently communicates only field names rather than the actual target schema.

A future implementation should make the target structural contract explicit to the generation layer. However, prompt-only duplication of the schema should not become the sole long-term enforcement mechanism if a provider-independent structured-output constraint can be expressed.

### GiadaWare AI `AIBackend`

**Primary abstraction gap.**

The provider-independent primitive can request "JSON" but cannot carry a structured response schema.

This prevents consumer-owned semantic capabilities from requesting provider-independent schema-constrained JSON even when the concrete backend supports it.

### GiadaWare AI `OllamaBackend`

**Concrete enforcement gap.**

It hard-codes `format: "json"` instead of being able to map a provider-independent response schema to Ollama's schema-valued `format` field.

## 7. Recommended ownership of the future fix

The best next implementation boundary is **GiadaWare AI first, Grocery Deal Intelligence second**.

### Phase A — GiadaWare AI

Introduce a provider-independent optional structured-output contract, conceptually:

```python
generate_json(
    *,
    system_prompt: str,
    user_prompt: str,
    response_schema: Mapping[str, object] | None = None,
) -> Mapping[str, object]
```

Exact naming/API design should be decided in the GiadaWare AI issue, not assumed by this audit.

The Ollama backend would map a supplied schema to Ollama's schema-valued `format` field, while retaining the existing JSON-object behavior when no schema is supplied.

This is not a promotion of AI authority. It constrains generation shape only.

### Phase B — Grocery Deal Intelligence

After GiadaWare AI exposes the provider-independent mechanism, `ProposeOfferCandidateCapability` should supply the Grocery Offer v0.1 schema to the backend and preferably also ground the prompt with the same schema or an equivalent generated structural description.

The returned candidate must still pass the existing deterministic `validate_offers()` gate. Schema-constrained generation improves proposal quality; it does not grant canonical status.

## 8. Layers that must remain unchanged

The following boundaries should survive any implementation that follows this audit:

```text
AI output = candidate data
```

not:

```text
AI output = canonical data
```

Specifically:

- `validate_offers()` remains the canonical authority;
- diagnostics remain descriptive only;
- `GiadaWareAIAdapter` must not become an auto-repair layer;
- no retailer-specific coercion should enter the deterministic core;
- schema-constrained generation must not bypass post-generation validation;
- model/provider details remain outside Grocery Deal Intelligence core semantics.

## 9. Why prompt tuning is not the first fix

Prompt clarification could reduce failures, but the evidence shows a structural contract that can be expressed machine-readably and that the current backend abstraction cannot carry.

Tuning prose before exposing the available structural constraint would optimize an under-specified interface rather than close the interface gap.

The correct order is:

```text
locate contract gap
        ↓
expose provider-independent structured-output constraint
        ↓
pass canonical target schema from consumer capability
        ↓
run the same deterministic experiment again
        ↓
only then evaluate residual model limitations / prompt refinement
```

## Decision

Issue #26 concludes:

> The repeated #20/#24 structural failures are primarily enabled by an under-specified proposal contract plus the absence of schema-constrained structured output in the current GiadaWare AI backend abstraction. The adapter and deterministic validator are behaving correctly. The reference model must not be blamed or tuned before the application supplies and enforces the target structural contract.

The next implementation work should therefore begin in GiadaWare AI with a provider-independent schema-constrained JSON generation capability, followed by Grocery Deal Intelligence wiring its canonical schema into `ProposeOfferCandidateCapability` and rerunning the same evidence experiment.

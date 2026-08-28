# Eurospin selected-store transport verdict (#113)

## Verdict

`watch`

## Objective

Resolve the remaining transport gate from #90 for the concrete Eurospin point of sale:

- locality: `Lucca`
- address: `Via Sarzanese, 673`
- postal code: `55100`
- official store URL: `https://www.eurospin.it/punti-vendita/lucca-via-sarzanese/`

The promotion gate requires one public, replayable, same-chain mapping from this store to the current flyer/promotion payload before any store-scoped fixture or deterministic adapter is introduced.

## What is now confirmed

### Public store identity is stable at the URL level

The official Eurospin store page is public and replayable at a stable slug:

```text
https://www.eurospin.it/punti-vendita/lucca-via-sarzanese/
```

The page identifies the concrete store as:

```text
Lucca
Via Sarzanese, 673
55100
```

It also exposes store-specific operational metadata such as opening hours, services and departments.

### Eurospin explicitly makes flyer semantics depend on store selection

The official point-of-sale finder tells users to select a point of sale and then download the corresponding flyer.

The official flyer page likewise asks users to select a point of sale to discover the promotions for that selected store.

This is strong retailer-controlled evidence that locality/store selection is semantically relevant to the flyer.

### Current promotion surfaces are rich

The official Eurospin promotion/home surfaces expose current campaign validity and product rows with promotion-relevant data such as product name, current/base price text, package quantity and, where applicable, unit/reference price.

The current campaign observed during this spike is:

```text
2026-08-24 → 2026-09-06
```

This confirms that Eurospin remains a valuable deterministic source candidate if the store-to-flyer transport can be pinned.

## Transport investigation result

The required chain is still not reproducibly pinned:

```text
Lucca / Via Sarzanese 673
        ↓
public selected-store identity/context
        ↓
current flyer/promotion payload proven applicable to that store
```

The public rendered store page exposes the concrete store but does not expose a stable flyer identifier, request parameter, payload URL or equivalent deterministic binding.

The public flyer page demonstrates store-selection semantics, but its replayable representation does not reveal a stable selected-store token for Via Sarzanese 673 nor a current flyer target that can be tied back to that store without inference.

No public retailer-controlled search result inspected during this spike supplied a deterministic association between the Lucca store slug and a specific current flyer payload/variant.

## Important boundary

The following would be invalid evidence construction and was deliberately not performed:

```text
store page for Via Sarzanese 673
        +
generic/current Eurospin promotion rows
        ↓
synthetic claim that those rows apply to this store
```

Eurospin itself states that flyer/promotions depend on the selected store. Therefore a generic promotion listing cannot be promoted to store-scoped evidence merely because the store exists and the campaign dates overlap.

Similarly, third-party flyer aggregators may indicate that Eurospin campaigns are available in Lucca, but they do not replace the required Eurospin-controlled same-chain provenance and are not admissible as the deterministic transport proof for this adapter gate.

## App evidence

Eurospin's app documentation further confirms that users can select/change a preferred store and consult flyers/offers for that preferred store.

This strengthens the semantic conclusion that store context matters, but app state/geolocation/private application transport is capability evidence only. It is not treated as a public deterministic web retrieval recipe and was not reverse engineered for this spike.

## Fixture decision

No Lucca-specific raw fixture was created.

Reason:

```text
store applicability transport not pinned
        ↓
no trustworthy store-scoped payload
        ↓
no fixture
        ↓
no parser
        ↓
no adapter implementation
```

Creating a fixture by joining unrelated public surfaces would manufacture locality and violate the GDI evidence boundary.

## Verdict rationale

The correct verdict is:

`watch`

Eurospin remains technically promising because:

- a stable public store URL exists;
- the retailer explicitly states selected-store flyer semantics;
- promotion data is rich enough to justify future adapter work;
- current campaign validity is explicit.

But promotion to `promote_to_adapter_implementation` is blocked by one fundamental provenance gap: the exact public replayable selected-store → current flyer/promotion payload mapping is still missing.

This is not a `reject` because the source is valuable and the missing gate could plausibly become observable through a future public transport change or better retailer-controlled representation.

## Promotion condition

Eurospin may be reconsidered for deterministic adapter implementation only when a public reproducible chain equivalent to the following is captured:

```text
Via Sarzanese 673 store identity
        ↓
stable public store parameter / flyer identifier / equivalent binding
        ↓
current Eurospin-controlled flyer or promotion payload
        ↓
proof that payload applies to the selected store
        ↓
raw fixture + SHA-256
        ↓
deterministic parser
```

Until then, classification remains `watch`.

## Non-goals preserved

This spike introduces no production scraper, AI dependency, canonical schema change, admission-policy change, access-control bypass, private authenticated API reverse engineering, inferred locality, synthetic fixture or parser.

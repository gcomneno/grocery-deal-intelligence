# Bennet selected-store transport verdict (#119)

## Verdict

`watch`

## Objective

Resolve the remaining selected-store transport gate from #96 for the concrete Bennet point of sale:

- locality: `Montano Lucino (CO)`
- address: `via Enzo Ratti, 4`
- official store URL: `https://www.bennet.com/storefinder/iper/0033`
- stable public store identifier: `0033`

Promotion to deterministic adapter implementation requires a public, replayable, same-chain mapping from store `0033` to the current Bennet flyer/promotion payload before any store-scoped fixture is introduced.

## What is now confirmed

### Stable public store identity exists

Bennet exposes Montano Lucino through the public store URL:

```text
https://www.bennet.com/storefinder/iper/0033
```

The page identifies the store as Montano Lucino (CO), via Enzo Ratti 4, and therefore supplies a stable retailer-controlled store identifier in the path: `0033`.

This materially improves #96, where a replayable store identifier had not yet been pinned.

### The flyer surface is explicitly selected-store aware

The official flyer surface at:

```text
https://www.bennet.com/flyer
```

renders the currently selected Bennet point of sale and, at observation time, shows Montano Lucino as that selected store.

The flyer surface also exposes currently active flyer campaigns with explicit validity intervals.

This confirms again that flyer semantics depend on selected-store context.

### Bennet store selection is persistent application state

Other public store pages can be opened while the page header still renders Montano Lucino as the currently selected point of sale. This demonstrates that the selected-store context is application/session state distinct from the store page currently being viewed.

That observation is important because it prevents an invalid inference that simply opening `/storefinder/iper/<id>` deterministically sets the flyer scope to that same `<id>`.

## Transport investigation result

The required public chain is still not pinned:

```text
store 0033 / Montano Lucino
        ↓
public replayable store-selection transport
        ↓
current flyer set/payload proven applicable to 0033
```

The store identifier `0033` is public and stable, but the generic `/flyer` URL does not expose `0033` in its path or query string.

The public rendered flyer page shows Montano Lucino as selected, but this by itself does not prove a cookie-independent or session-independent recipe for reproducing that selection from a fresh client.

No retailer-controlled public URL, query parameter, embedded token, or equivalent replayable request mapping inspected during this spike supplied the missing deterministic binding from `0033` to the current flyer payload.

## Important boundary

The following would be invalid evidence construction and was not performed:

```text
/storefinder/iper/0033
        +
/flyer currently rendering Montano Lucino in this session
        ↓
claim that /flyer is intrinsically scoped to 0033
```

The two observations are compatible, but without a replayable selection transport they are not sufficient to establish a deterministic source contract.

Likewise, visiting another store detail page while the header still shows Montano Lucino confirms that store-detail navigation and selected-store state are separate concerns.

## Fixture decision

No Montano-Lucino-specific raw fixture was created.

Reason:

```text
public store id pinned
        ↓
selected-store flyer transport still session-dependent / unpinned
        ↓
no deterministic payload identity
        ↓
no trustworthy store-scoped fixture
        ↓
no parser
        ↓
no adapter implementation
```

## Loyalty and personalization boundary

Bennet Club coupons, dedicated benefits, app offers, and other personalized surfaces remain outside the public deterministic flyer evidence class.

The evidence classes remain separate:

```text
public selected-store flyer evidence
!= Bennet Club coupon evidence
!= personalized/dedicated app offers
```

No loyalty-only or personalized content is harvested or used to fill the transport gap.

## Verdict rationale

The correct verdict is:

`watch`

This is a **strong watch** because Bennet now satisfies several important preconditions:

- a stable public store identifier (`0033`) is pinned;
- the concrete Montano Lucino store page is replayable;
- the public flyer page is explicitly selected-store aware;
- active flyer campaigns expose explicit validity intervals;
- Bennet promotion surfaces are semantically rich enough for deterministic ingestion once scope is proven.

However, one fundamental provenance gap remains: there is still no public replayable store-selection transport connecting `0033` to the current flyer payload independently of existing application/session state.

This is not a `reject` because the retailer exposes enough stable public structure that the missing binding may become observable through a future public URL, request parameter, or inspectable retailer-controlled transport.

## Promotion condition

Bennet may be promoted to `promote_to_adapter_implementation` only when a public reproducible chain equivalent to the following is captured:

```text
Montano Lucino store 0033
        ↓
stable public store-selection parameter / token / equivalent binding
        ↓
current Bennet flyer or promotion payload
        ↓
proof that payload applies to store 0033
        ↓
raw fixture + SHA-256
        ↓
deterministic parser
```

Until then, classification remains `watch`.

## Non-goals preserved

This spike introduces no production scraper, AI dependency, schema change, admission-policy change, access-control bypass, private authenticated API reverse engineering, loyalty harvesting, personalized-offer harvesting, inferred locality, synthetic fixture, parser, or adapter implementation.

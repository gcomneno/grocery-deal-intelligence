# Todis selected-store transport verdict (#115)

## Verdict

`watch`

## Objective

Resolve the remaining selected-store transport gate from #92 for the concrete Todis point of sale:

- locality: `Baia Domizia (CE)`
- address: `Via delle Pietre Bianche`

The promotion gate requires a public, replayable, same-chain mapping from the store entry to an applicability-proven flyer payload whose raw bytes can be captured and hashed before any deterministic parser or adapter is introduced.

## What is now confirmed

### The store-to-flyer relationship is publicly replayable

The Todis homepage currently exposes the Baia Domizia store/new-opening entry together with a retailer-controlled `Sfoglia il volantino` action.

Following that exact action yields the dedicated public Todis page:

```text
https://www.todis.it/volantini/todis-baia-domizia/
```

The rendered page identifies itself as:

```text
Volantino Todis Baia Domizia
```

This is materially stronger evidence than #92 because the selected-store binding is no longer merely semantic or inferred from geography: the retailer itself publishes a distinct Baia Domizia flyer page.

A second current store entry, Sessa Aurunca, resolves to a different dedicated flyer page. This further supports that the homepage actions are store-specific rather than generic regional links.

### The dedicated page exposes a Todis-hosted PDF target

The Baia Domizia flyer page exposes a `Scarica il volantino in PDF` action targeting a Todis-controlled URL:

```text
https://www.todis.it/wp-content/uploads/2026/03/Vol-Apertura-BAIA-DOMIZIA.pdf
```

This produces the following retailer-controlled chain:

```text
Todis homepage
        ↓
Baia Domizia / Via delle Pietre Bianche
        ↓
Sfoglia il volantino
        ↓
/todis-baia-domizia/
        ↓
Todis-hosted Baia Domizia PDF target
```

Store applicability for this flyer page is therefore directly supported by Todis and does not need to be manufactured by joining unrelated regional evidence.

## Remaining fixture gate

The raw PDF fixture was not committed in this spike.

The URL is publicly identified and Todis-controlled, but the investigation environment could not retrieve the PDF bytes reproducibly enough to record a trustworthy SHA-256. A failed byte capture must not be replaced by indexed snippets, rendered metadata, synthetic text, or a guessed digest.

The deterministic implementation boundary therefore remains:

```text
public store-specific flyer target
        ↓
reproducible raw byte capture
        ↓
SHA-256
        ↓
parser
        ↓
adapter
```

The first half is now proven; the byte-identity half is still open.

## Freshness boundary

The PDF filename is explicitly an opening flyer (`Vol-Apertura-BAIA-DOMIZIA.pdf`) and its upload path contains `2026/03`.

The Todis homepage still exposes the Baia Domizia store action at observation time, but that fact alone does not prove that the linked opening flyer represents current August 2026 offers.

Accordingly this spike distinguishes two claims:

- **store applicability transport:** now directly proven by the Todis-controlled same-chain link;
- **current campaign freshness:** not established from the flyer target alone.

No opening flyer is relabeled as a current campaign without explicit validity evidence.

## Regional flyer evidence remains separate

Todis also publishes regional flyer surfaces and accessible PDFs with rich product, price, unit-price, validity and promotion semantics.

That evidence remains useful for understanding source richness, but it is not automatically store-scoped to Baia Domizia. Regional geography is not substituted for the dedicated store-to-flyer provenance chain.

## Why the verdict is still `watch`

Todis is now substantially closer to deterministic adapter implementation than it was after #92:

- the concrete store entry is public;
- the homepage exposes a store-associated flyer action;
- that action resolves to a dedicated Baia Domizia flyer page;
- the page exposes a Todis-hosted Baia Domizia PDF target;
- no inferred locality is needed to establish applicability of that dedicated flyer page.

However, implementation promotion still requires the actual source artifact to be captured reproducibly and identity-pinned.

The exact blocking conditions are now narrow:

1. retrieve the dedicated PDF bytes reproducibly;
2. record SHA-256;
3. establish the flyer validity period from the source artifact;
4. only then decide whether the captured flyer is suitable as a current fixture or as a historical parser fixture;
5. introduce a deterministic parser only after those gates pass.

Therefore the correct verdict is:

`watch`

This is a **strong watch**, not a rejection and not a return to broad source discovery.

## Promotion condition

Todis may be promoted to `promote_to_adapter_implementation` when the following chain is completed:

```text
Baia Domizia store entry
        ↓
public dedicated flyer page
        ↓
Todis-hosted flyer payload
        ↓
reproducible raw bytes
        ↓
SHA-256 + explicit validity
        ↓
deterministic parser candidate
```

The selected-store provenance gate is now solved. The remaining work is raw fixture identity and temporal suitability.

## Non-goals preserved

This spike introduces no production scraper, AI dependency, schema change, admission-policy change, access-control bypass, private API reverse engineering, inferred regional applicability, synthetic fixture, guessed digest, parser or adapter implementation.

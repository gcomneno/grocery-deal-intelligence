# Carrefour public promotion source spike

Issue: #70

## Decision

`promote_to_adapter_spike`

## Scope

This spike evaluates Carrefour Italia official public flyer and promotion surfaces as potential deterministic source evidence for Grocery Deal Intelligence. It does not implement a production scraper or adapter.

## Observed official surfaces

The generic official flyer page is explicitly point-of-sale oriented: it asks the user to search by CAP, city, or address to discover offers for a selected store.

More importantly, individual flyer URLs are directly store-addressable. A concrete observed example is Carrefour Express Milano, Viale Abruzzi 54, whose URL contains both a store slug and store identifier `5190`, followed by flyer identifier `56879`.

That page itself establishes, in one public retrieval:

- banner: Carrefour Express;
- store address: Viale Abruzzi, 54 - Milano;
- city: Milano;
- multiple available flyer campaigns with explicit date ranges;
- selected campaign identity (`Offerte d'estate`);
- promotion validity (`3/08` to `31/08`);
- product rows grouped by grocery categories.

This is materially stronger locality evidence than a global promotion page plus a separately selected store: the store identity and flyer identity are encoded in the public URL and repeated in the rendered source.

## Product and promotion evidence

Observed store-scoped flyer rows expose combinations of:

- product name;
- package quantity where applicable;
- discount percentage;
- previous/base price where shown;
- promotional price;
- unit/reference price;
- loyalty marker `SPESAMICA PAYBACK` for some offers.

Examples observed on official store-scoped flyer pages include grocery products with ordinary percentage discounts and products whose promotional price is explicitly conditional on SpesAmica PAYBACK.

The source therefore exposes canonical-relevant evidence without requiring inference from imagery alone.

## Store and flyer identity

Observed URL shape:

`/volantino/<store-slug>/<store-id>/<flyer-slug>/<flyer-id>`

Concrete observed identities include store IDs `5190`, `5020`, `5012`, `5069`, and flyer ID `56879` for the same campaign across different Carrefour Express stores in Milano. Carrefour Market examples expose their own store IDs and flyer IDs.

These identifiers are stable-looking and, crucially, are part of a publicly replayable URL shape. Stability across time has not yet been proven and must not be assumed.

## Public versus personalized boundary

Carrefour also offers `Volantino Per Te`, which prepends personalized offers based on recent purchases and requires profile/PAYBACK profiling context. Carrefour states that the complete ordinary promotional flyer remains available after the personalized pages.

Grocery Deal Intelligence must keep this boundary explicit:

- ordinary public store-scoped flyers are candidate source evidence;
- personalized `Per Te` offers are outside this spike and must not be silently mixed into public deterministic evidence.

## Freshness

Current official store-scoped pages expose overlapping current and upcoming campaigns with explicit validity windows. This gives the source a useful freshness signal directly in the retrieval rather than relying only on crawl timestamps.

## Provenance assessment

Strong evidence:

- official `carrefour.it` source;
- store identity in URL and page;
- store address and city in page;
- flyer/campaign identity in URL and page;
- explicit validity;
- structured textual promotion rows;
- explicit loyalty labels where applicable.

Not yet established:

- a lower-level JSON/API retrieval surface;
- deterministic pagination/load-more behavior for every flyer;
- long-term identifier stability;
- a committed raw fixture and SHA-256;
- parser behavior over a captured fixture;
- terms/usage review sufficient for a production ingestion decision.

## Why promote

Unlike sources whose locality is hidden in cookies/session state, Carrefour exposes a concrete public store-scoped flyer retrieval whose URL carries both store and flyer identity and whose response repeats the store locality and promotion validity. That is enough evidence to justify a separate capture/parser spike.

It is not enough evidence to ship a production adapter.

## Next spike

Capture one official Carrefour store-scoped flyer response as a raw fixture, record its retrieval identity and SHA-256, and implement the smallest deterministic parser necessary to extract source evidence while preserving loyalty and price semantics without canonical inference.

Recommended decision for #70: `promote_to_adapter_spike`.

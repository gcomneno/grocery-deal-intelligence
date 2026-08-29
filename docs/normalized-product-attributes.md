# Evidence-grounded normalized product attributes

GDI normalizes product attributes only after an offer has already been admitted as canonical.

The boundary is:

```text
already-admitted canonical offer
    -> product-attribute candidate
    -> attribute evidence verification
    -> deterministic normalization
    -> normalized verified product attributes | unknown
    -> comparison policy
```

This layer does not modify canonical admission and does not create evidence.

## v0.1 scope

The first contract supports:

- `product_family`;
- normalized quantity;
- `weight_g` for verified mass quantities;
- `volume_ml` for verified volume quantities;
- explicit composite packs through `pack_count`, `unit_quantity`, and `total_quantity`.

The JSON contract is `schema/normalized-product-attributes-v0.1.schema.json`.

## Quantity evidence

Quantity is derived deterministically from observed canonical `packaging_text` and/or `product_name`.

The initial conversion set is intentionally small:

```text
g  -> g
kg -> g
ml -> ml
l  -> ml
```

Mass and volume remain separate dimensions. GDI never converts volume into mass or vice versa.

Examples:

```text
100 g      -> weight_g = 100
1 kg       -> weight_g = 1000
1 l        -> volume_ml = 1000
2 x 100 g  -> pack_count = 2
              unit_quantity = 100 g
              total_quantity = 200 g
              weight_g = 200
```

If independently observed canonical fields contain conflicting quantities, quantity admission fails closed instead of selecting the most convenient value.

Unsupported or absent quantity evidence likewise remains unavailable.

## Product-family evidence

`product_family` is not inferred authoritatively from AI confidence or generic fuzzy matching.

A caller may supply a candidate family plus the canonical field that supposedly supports it. The candidate is then checked against a deliberately small, versioned lexical evidence policy.

Initial families are:

- `dark_chocolate`;
- `milk_chocolate`;
- `passata`;
- `whole_milk`.

This vocabulary is deliberately incomplete. An unsupported family stays unknown.

The current lexical policy is pragmatic and narrow. It is not a global grocery taxonomy and it is not source evidence by itself. Its role is to state which explicit observed words are sufficient for this v0.1 admission boundary.

For example, a `dark_chocolate` candidate is supported only when the selected observed field contains the required `fondente` marker and no configured contradictory marker. AI metadata such as confidence or model identity is ignored by admission.

## Provenance

Every supported normalized claim records:

- normalized path;
- `supported` status;
- canonical evidence path;
- raw observed value;
- normalized value;
- deterministic normalization/policy identifier.

This keeps the distinction visible:

```text
source text
!= proposed interpretation
!= verified fact
!= deterministic normalized fact
!= comparison decision
```

## Comparison-policy composition

`comparison_verification_from_attributes(...)` projects only already-supported normalized attribute claims into the bilateral verification shape consumed by the comparison-policy evaluator.

It grants no new authority. If one side lacks a supported normalized claim, that side is `unverifiable` and a required comparison rule fails closed.

For the current chocolate default:

```text
verified product_family = dark_chocolate
+ verified weight_g = same value on both offers
+ chocolate_bar comparison policy
-> comparable
```

Missing family or weight remains `unknown`.

## AI boundary

GiadaWare AI may propose a family candidate or help identify which observed field deserves inspection.

It may not:

- create normalized quantity evidence;
- bypass the family evidence policy;
- mark unsupported attributes as verified;
- authorize `comparable`.

The deterministic core requires neither AI nor network access.

## Out of scope

This layer does not implement:

- exhaustive grocery taxonomy;
- fuzzy matching or embeddings as authority;
- GTIN/EAN resolution;
- price-per-unit calculation;
- ranking;
- recommendation;
- natural-language answering;
- retailer-specific exceptions in generic normalization.

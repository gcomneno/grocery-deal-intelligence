# Overridable comparison policies

GDI comparison policies express which already-verified product facts matter for
comparability.

They are not source evidence, semantic truth, or AI authority.

The policy hierarchy is:

```text
built-in global default
    -> built-in category default
    -> user category override
    -> user product-family override
    -> user specific-product override
```

More specific layers override only fields they explicitly redefine. Every
effective rule field retains provenance identifying the policy layer that
supplied it.

## Pragmatic defaults

Built-in defaults are deliberately pragmatic. They encode useful everyday
shopping assumptions without claiming universal semantic correctness.

They must remain:

- deterministic;
- inspectable;
- versioned;
- documented;
- explicitly identified as built-in defaults;
- overridable by users;
- separate from source evidence and canonical admission.

The initial built-in category is `chocolate_bar`.

Its default rules are:

```text
same product family  -> require equal
same weight          -> require equal
brand                -> ignore
cocoa percentage     -> ignore
sugar percentage     -> ignore
```

This means two verified dark-chocolate bars with the same verified weight may
be considered comparable even when their brand, cocoa percentage, or sugar
percentage differ.

The policy does not itself extract or verify `product_family`, `weight_g`,
`brand`, `cocoa_percentage`, or `sugar_percentage`. Those facts must already
have been established by an evidence/verification boundary before policy
evaluation.

## Rule vocabulary

Each rule has a stable rule identifier and an `effect`:

- `require`: the bilateral verified values must exist and be equal;
- `ignore`: the fact is explicitly irrelevant to comparability;
- `prefer`: the fact may matter later for ranking/recommendation, but cannot
  authorize comparability;
- `exclude`: an explicitly configured verified value makes the candidate
  unacceptable.

`ignore` and `prefer` are non-authoritative for comparison admission.

A policy containing only `ignore` and/or `prefer` rules fails closed rather than
making every pair comparable by vacuous truth.

## Policy provenance

Resolved policies expose:

- all applied policy layers;
- effective rules;
- field-level provenance for inherited and overridden rule fields.

For example, a user product override may disable the built-in `same_weight`
rule while preserving its built-in path/operator. The effective result records
that the rule meaning came from the built-in category while the `enabled`
field came from the user product override.

This makes silent policy drift observable.

## Authority boundary

The intended authority chain is:

```text
already-admitted canonical offers
    -> comparison proposal
    -> bilateral verified facts
    -> resolved comparison policy
    -> deterministic policy evaluation
    -> comparable | unknown
```

Policy evaluation consumes verified facts. It must never:

- create missing product facts;
- reinterpret source text as evidence;
- borrow evidence between offers;
- mutate canonical offers;
- rerun or weaken canonical admission;
- make retailer-specific exceptions in generic comparison logic;
- use AI confidence as comparison authority.

Missing required verified facts fail closed to `unknown`.

## GiadaWare AI boundary

GiadaWare AI may later propose:

- category/product-family assignments;
- candidate policy templates;
- possible user overrides.

Those proposals remain advisory until explicitly adopted by deterministic
configuration or user intent.

AI must not silently select the effective policy or authorize `same_product` or
`comparable`.

## Product-attribute boundary

The canonical grocery-offer schema itself still does not expose normalized
`product_family` or `weight_g` fields. GDI now provides a separate downstream
[evidence-grounded normalized product-attribute boundary](normalized-product-attributes.md)
that can derive those comparison-ready facts from already-admitted offers while
preserving evidence, provenance, deterministic normalization, and fail-closed
semantics.

The comparison-policy evaluator consumes only supported normalized claims from
that boundary. It does not inherit parsing or semantic-classification authority.

This preserves the separation:

```text
canonical offer
    -> verified normalized product attributes
    -> comparison policy
    -> comparable | unknown
```

Comparison policy remains separate from:

- same-product identity policy;
- quantity/unit normalization;
- price-per-unit calculation;
- cheapest/best ranking;
- recommendation;
- natural-language question answering.

In short:

```text
heuristic default != evidence

verified fact + explicit policy -> deterministic comparability decision

prefer != comparison authority

AI proposal != policy authority
```

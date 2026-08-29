# Economic normalization

GDI derives a common economic price basis only after product comparability has
already been admitted and only from quantity facts that remain bound to
supported normalized-product-attribute claims.

```text
canonical offer
    -> verified normalized product attributes
    -> comparison policy
    -> comparable
    -> economic normalization
    -> comparable price basis | unknown
```

Economic normalization is deterministic derivation. It is not source evidence,
does not make products comparable, and does not rank or recommend offers.

## Price semantics

The numerator is always the canonical `price`: the current/promotional price
shown to the shopper. `reference_price` remains the ordinary/original comparison
price and is never substituted for `price`. `base_price_text` is not reparsed as
a current price.

The initial contract supports EUR only. Currency conversion is out of scope.

## Quantity authority

The economic layer does not parse `product_name` or `packaging_text`. It consumes
`weight_g` or `volume_ml` from the normalized product-attribute result introduced
by #136. The exact current value must still match the `normalized_value` of a
`supported` claim for the same path.

A stale, forged, missing, or contradictory claim therefore yields `unknown`.
If both mass and volume bases are simultaneously authoritative, the layer also
fails closed instead of choosing one.

Composite packages use the verified total quantity exposed by #136. For example,
`2 x 100 g` produces `weight_g = 200`, so economic normalization uses 200 g rather
than the 100 g unit quantity.

## Initial bases

- verified mass in grams -> EUR/kg;
- verified volume in millilitres -> EUR/l.

Mass and volume are never converted into each other.

## Decimal representation

Calculations use `Decimal`. Authoritative numeric output is serialized as a
canonical decimal string without presentation rounding. For example, `2.49 EUR`
over `100 g` yields the exact comparable value `24.9` EUR/kg. A UI may display
`24.90 EUR/kg`, but that formatting must not become comparison authority.

## Fail-closed reasons

The boundary reports `unknown` for conditions including:

- comparability not admitted;
- missing or invalid current price;
- unsupported currency;
- missing normalized quantity;
- normalized value not bound to its supported claim;
- multiple incompatible authoritative quantity dimensions.

## Non-goals

This boundary does not:

- decide comparability;
- compare two economic values;
- select the cheapest offer;
- rank or recommend offers;
- apply user preferences;
- perform FX or density conversions;
- reinterpret retailer-specific source text;
- use AI or network access.

The next downstream authority boundary can compare common economic bases, but
only for offers whose comparability has already been admitted.

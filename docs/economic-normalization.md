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

## Comparability authority

The economic layer does not accept a free `true/false` comparability flag. It
consumes the structured result of the comparison-policy boundary and proceeds
only when that result is self-consistent with an admitted `comparable` outcome,
contains no rejection reasons, and includes at least one satisfied authoritative
`require` or `exclude` rule.

This layer still grants no comparability authority of its own.

## Price semantics

The numerator is always the canonical `price`: the current/promotional price
shown to the shopper. `reference_price` remains the ordinary/original comparison
price and is never substituted for `price`. `base_price_text` is not reparsed as
a current price.

The initial contract supports EUR only. Currency conversion is out of scope.
Non-finite or otherwise invalid numeric prices fail closed.

## Quantity authority

The economic layer does not parse `product_name` or `packaging_text`. It consumes
`weight_g` or `volume_ml` from the normalized product-attribute result introduced
by #136. The exact current value must still match the `normalized_value` of a
`supported` claim for the same path.

A stale, forged, missing, contradictory, or conflicting duplicate claim therefore
yields `unknown`. If both mass and volume bases are simultaneously authoritative,
the layer also fails closed instead of choosing one.

Composite packages use the verified total quantity exposed by #136. For example,
`2 x 100 g` produces `weight_g = 200`, so economic normalization uses 200 g rather
than the 100 g unit quantity.

## Initial bases

- verified mass in grams -> EUR/kg;
- verified volume in millilitres -> EUR/l.

Mass and volume are never converted into each other. The schema couples each
quantity dimension to its legal basis, per-unit label, derivation rule, and
formula; structurally inconsistent combinations are invalid.

## Exact economic representation

Canonical inputs are converted to `Decimal`, but division is not used as the
authoritative persisted representation because some results are non-terminating
in decimal notation.

The comparable price is therefore stored as an exact reduced rational:

```text
exact_ratio.numerator
exact_ratio.denominator
```

For example:

```text
2.49 EUR / 100 g -> 249 / 10 EUR/kg -> display may render 24.90 EUR/kg
1.00 EUR / 300 g -> 10 / 3 EUR/kg
```

A downstream price-comparison layer can compare these rational values exactly by
cross-multiplication. Any decimal rendering or rounding is presentation only and
must not become ordering authority.

## Result-state contract

The versioned schema binds state and payload:

- `supported` requires a non-null economic result and zero reasons;
- `unknown` requires `result = null` and at least one reason.

This prevents structurally contradictory results such as `supported` with no
comparable-price payload.

## Fail-closed reasons

The boundary reports `unknown` for conditions including:

- comparability not admitted;
- missing or invalid current price;
- unsupported currency;
- missing normalized quantity;
- normalized value not bound to its supported claim;
- conflicting duplicate normalized claims;
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

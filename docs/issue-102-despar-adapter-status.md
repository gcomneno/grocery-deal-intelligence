# Issue #102 implementation status

The deterministic Despar adapter implementation is carried by `grocery_deal_intelligence.despar_adapter`, with source-evidence projection support in `grocery_deal_intelligence.source_evidence` and focused tests under `tests/`.

The implementation intentionally fails closed when canonical-required promotion semantics are not present in the captured source evidence.

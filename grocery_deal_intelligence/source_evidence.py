from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


SUPPORTED = "supported"
CONTRADICTED = "contradicted"
UNVERIFIABLE = "unverifiable"


_LIDL_FLYER_MATCH_TO_EVIDENCE_STATUS = {
    "exact": "verified",
    "partial": "partial",
    "unmatched": "unmatched",
    "unverified": "unverified",
}


def project_source_evidence(
    source_record: Mapping[str, Any],
    *,
    retailer: str,
) -> dict[str, Any]:
    """Project only canonical claims deterministically supported by source evidence."""
    if not isinstance(source_record, Mapping):
        raise TypeError("source_record must be a mapping")
    if not isinstance(retailer, str) or not retailer:
        raise TypeError("retailer must be a non-empty string")

    source = deepcopy(dict(source_record))
    normalized_retailer = retailer.strip().lower()

    if normalized_retailer == "lidl":
        return _project_lidl(source)
    if normalized_retailer == "esselunga":
        return _project_esselunga(source)
    if normalized_retailer == "despar":
        return _project_despar(source)
    if normalized_retailer == "carrefour":
        return _project_carrefour(source)

    return {"retailer": normalized_retailer}


def verify_candidate_claims(
    candidate: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Classify candidate leaf claims against deterministic projected evidence."""
    if not isinstance(candidate, Mapping):
        raise TypeError("candidate must be a mapping")
    if not isinstance(evidence, Mapping):
        raise TypeError("evidence must be a mapping")

    candidate_copy = deepcopy(dict(candidate))
    evidence_copy = deepcopy(dict(evidence))
    evidence_leaves = dict(_leaf_items(evidence_copy))

    results: list[dict[str, Any]] = []
    for path, candidate_value in sorted(_leaf_items(candidate_copy), key=lambda item: item[0]):
        result: dict[str, Any] = {
            "path": list(path),
            "candidate_value": deepcopy(candidate_value),
        }
        if path not in evidence_leaves:
            result["status"] = UNVERIFIABLE
        else:
            evidence_value = evidence_leaves[path]
            result["evidence_value"] = deepcopy(evidence_value)
            result["status"] = (
                SUPPORTED if candidate_value == evidence_value else CONTRADICTED
            )
        results.append(result)

    return results


def summarize_claim_verification(results: list[Mapping[str, Any]]) -> dict[str, int]:
    summary = {SUPPORTED: 0, CONTRADICTED: 0, UNVERIFIABLE: 0}
    for result in results:
        status = result.get("status")
        if status not in summary:
            raise ValueError(f"unknown claim verification status: {status!r}")
        summary[status] += 1
    return summary


def _project_lidl(source: dict[str, Any]) -> dict[str, Any]:
    evidence: dict[str, Any] = {"retailer": "lidl"}

    _copy_if_present(source, evidence, "product_name")
    _copy_if_present(source, evidence, "price")
    _copy_if_present(source, evidence, "currency")
    _copy_if_present(source, evidence, "reference_price")
    _copy_if_present(source, evidence, "packaging_text")
    _copy_if_present(source, evidence, "base_price_text")

    promotion: dict[str, Any] = {}
    if "promotion_type" in source:
        promotion["type"] = deepcopy(source["promotion_type"])
    if "requires_loyalty" in source:
        promotion["requires_loyalty"] = deepcopy(source["requires_loyalty"])
    if "discount_text" in source:
        promotion["discount_text"] = deepcopy(source["discount_text"])
    if promotion:
        evidence["promotion"] = promotion

    validity: dict[str, Any] = {}
    if "valid_from" in source:
        validity["from"] = deepcopy(source["valid_from"])
    if "valid_to" in source:
        validity["to"] = deepcopy(source["valid_to"])
    if validity:
        evidence["validity"] = validity

    source_verification = source.get("verification")
    locality_verified = (
        isinstance(source_verification, Mapping)
        and source_verification.get("locality") == "verified"
    )

    source_locality = source.get("locality")
    if isinstance(source_locality, Mapping) and "stores" in source_locality:
        locality: dict[str, Any] = {"stores": deepcopy(source_locality["stores"])}
        stores = source_locality.get("stores")
        if (
            locality_verified
            and isinstance(stores, list)
            and bool(stores)
            and all(isinstance(store, str) and bool(store) for store in stores)
        ):
            locality["scope"] = "store"
        evidence["locality"] = locality

    if isinstance(source_verification, Mapping):
        verification: dict[str, Any] = {}
        if "locality" in source_verification:
            verification["locality_status"] = deepcopy(source_verification["locality"])
        flyer_match = source_verification.get("flyer_match")
        if flyer_match in _LIDL_FLYER_MATCH_TO_EVIDENCE_STATUS:
            verification["evidence_status"] = _LIDL_FLYER_MATCH_TO_EVIDENCE_STATUS[flyer_match]
        if "flyer_match" in source_verification:
            verification["flyer_match"] = deepcopy(source_verification["flyer_match"])
        if verification:
            evidence["verification"] = verification

    source_provenance = source.get("provenance")
    if isinstance(source_provenance, Mapping):
        provenance: dict[str, Any] = {}
        if "source_type" in source_provenance:
            provenance["source_type"] = deepcopy(source_provenance["source_type"])
        if "campaign_url" in source_provenance:
            provenance["source_url"] = deepcopy(source_provenance["campaign_url"])
        if "observed_at" in source_provenance:
            provenance["observed_at"] = deepcopy(source_provenance["observed_at"])
        if "flyer_id" in source_provenance:
            provenance["flyer_id"] = deepcopy(source_provenance["flyer_id"])
        if provenance:
            evidence["provenance"] = provenance

    return evidence


def _project_esselunga(source: dict[str, Any]) -> dict[str, Any]:
    evidence: dict[str, Any] = {"retailer": "esselunga"}

    if "title" in source:
        evidence["product_name"] = deepcopy(source["title"])

    promo_prices = source.get("promozioni_prezzoPromo")
    if isinstance(promo_prices, list) and promo_prices:
        evidence["price"] = deepcopy(promo_prices[0])

    if "prezzo" in source:
        evidence["reference_price"] = deepcopy(source["prezzo"])

    starts = source.get("promozioni_dataInizioPromoArticolo")
    ends = source.get("promozioni_dataFinePromoArticolo")
    validity: dict[str, Any] = {}
    if isinstance(starts, list) and starts:
        validity["from"] = deepcopy(starts[0])
    if isinstance(ends, list) and ends:
        validity["to"] = deepcopy(ends[0])
    if validity:
        evidence["validity"] = validity

    descriptions = source.get("promozioni_desMeccanica")
    if isinstance(descriptions, list) and descriptions:
        evidence["promotion"] = {"discount_text": deepcopy(descriptions[0])}

    return evidence


def _project_despar(source: dict[str, Any]) -> dict[str, Any]:
    evidence: dict[str, Any] = {"retailer": "despar"}

    for key in (
        "product_name",
        "price",
        "currency",
        "reference_price",
        "packaging_text",
        "base_price_text",
    ):
        _copy_if_present(source, evidence, key)

    if "discount_text" in source:
        evidence["promotion"] = {"discount_text": deepcopy(source["discount_text"])}

    validity: dict[str, Any] = {}
    if "valid_from" in source:
        validity["from"] = deepcopy(source["valid_from"])
    if "valid_to" in source:
        validity["to"] = deepcopy(source["valid_to"])
    if validity:
        evidence["validity"] = validity

    source_locality = source.get("locality")
    if isinstance(source_locality, Mapping):
        locality: dict[str, Any] = {}
        for key in ("scope", "stores", "store_name", "store_address", "store_locality"):
            if key in source_locality:
                locality[key] = deepcopy(source_locality[key])
        if locality:
            evidence["locality"] = locality

    source_verification = source.get("verification")
    if isinstance(source_verification, Mapping):
        verification: dict[str, Any] = {}
        for key in ("locality_status", "evidence_status"):
            if key in source_verification:
                verification[key] = deepcopy(source_verification[key])
        if verification:
            evidence["verification"] = verification

    source_provenance = source.get("provenance")
    if isinstance(source_provenance, Mapping):
        provenance: dict[str, Any] = {}
        for key in (
            "source_type",
            "source_url",
            "observed_at",
            "fixture_sha256",
            "campaign_title",
        ):
            if key in source_provenance:
                provenance[key] = deepcopy(source_provenance[key])
        if provenance:
            evidence["provenance"] = provenance

    return evidence


def _project_carrefour(source: dict[str, Any]) -> dict[str, Any]:
    evidence: dict[str, Any] = {"retailer": "carrefour"}

    for key in (
        "product_name",
        "price",
        "currency",
        "reference_price",
        "packaging_text",
        "base_price_text",
    ):
        _copy_if_present(source, evidence, key)

    promotion: dict[str, Any] = {}
    if "promotion_type" in source:
        promotion["type"] = deepcopy(source["promotion_type"])
    if "requires_loyalty" in source:
        promotion["requires_loyalty"] = deepcopy(source["requires_loyalty"])
    if "discount_text" in source:
        promotion["discount_text"] = deepcopy(source["discount_text"])
    if promotion:
        evidence["promotion"] = promotion

    validity: dict[str, Any] = {}
    if "valid_from" in source:
        validity["from"] = deepcopy(source["valid_from"])
    if "valid_to" in source:
        validity["to"] = deepcopy(source["valid_to"])
    if validity:
        evidence["validity"] = validity

    source_locality = source.get("locality")
    if isinstance(source_locality, Mapping):
        locality: dict[str, Any] = {}
        for key in ("scope", "stores", "store_name", "store_address", "store_locality"):
            if key in source_locality:
                locality[key] = deepcopy(source_locality[key])
        if locality:
            evidence["locality"] = locality

    source_verification = source.get("verification")
    if isinstance(source_verification, Mapping):
        verification: dict[str, Any] = {}
        for key in ("locality_status", "evidence_status"):
            if key in source_verification:
                verification[key] = deepcopy(source_verification[key])
        if verification:
            evidence["verification"] = verification

    source_provenance = source.get("provenance")
    if isinstance(source_provenance, Mapping):
        provenance: dict[str, Any] = {}
        for key in (
            "source_type",
            "source_url",
            "observed_at",
            "fixture_sha256",
            "flyer_id",
            "campaign_title",
        ):
            if key in source_provenance:
                provenance[key] = deepcopy(source_provenance[key])
        if provenance:
            evidence["provenance"] = provenance

    return evidence


def _copy_if_present(source: dict[str, Any], target: dict[str, Any], key: str) -> None:
    if key in source:
        target[key] = deepcopy(source[key])


def _leaf_items(value: Any, path: tuple[str, ...] = ()):
    if isinstance(value, Mapping):
        for key in sorted(value):
            yield from _leaf_items(value[key], path + (str(key),))
        return
    yield path, value

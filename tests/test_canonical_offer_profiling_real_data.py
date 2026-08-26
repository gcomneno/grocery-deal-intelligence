import json
from pathlib import Path

from grocery_deal_intelligence.profiling import profile_offers


ROOT = Path(__file__).resolve().parent.parent


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def find_offer_datasets():
    datasets = []

    for path in ROOT.rglob("*-retailer-neutral.json"):
        try:
            payload = load_json(path)
        except (OSError, json.JSONDecodeError):
            continue

        if isinstance(payload, list) and payload:
            datasets.append((path, payload))

    return datasets


def test_real_canonical_datasets_can_be_profiled():
    datasets = find_offer_datasets()

    assert datasets, "No canonical offer dataset found"

    for path, records in datasets:
        result = profile_offers(records)

        assert result["total_records"] == len(records)

        distributions = (
            result["retailers"],
            result["currencies"],
            result["promotion_types"],
            result["loyalty_distribution"],
            result["locality_scope_distribution"],
            result["locality_verification_distribution"],
            result["evidence_verification_distribution"],
            result["reference_price_presence"],
            result["base_price_text_presence"],
        )

        for distribution in distributions:
            assert sum(distribution.values()) == len(records), path


def test_real_canonical_datasets_are_order_independent():
    datasets = find_offer_datasets()

    assert datasets, "No canonical offer dataset found"

    for path, records in datasets:
        assert profile_offers(records) == profile_offers(
            list(reversed(records))
        ), path


def test_real_canonical_datasets_are_read_only():
    datasets = find_offer_datasets()

    assert datasets, "No canonical offer dataset found"

    for path, records in datasets:
        before = json.loads(json.dumps(records))

        profile_offers(records)

        assert records == before, path


def test_real_canonical_profiles_have_expected_retailers():
    datasets = find_offer_datasets()

    assert datasets, "No canonical offer dataset found"

    retailers = set()

    for _, records in datasets:
        retailers.update(profile_offers(records)["retailers"])

    assert {"lidl", "esselunga"} <= retailers

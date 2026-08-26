import json
from pathlib import Path

from grocery_deal_intelligence.summary import summarize_offers


ROOT = Path(__file__).resolve().parent.parent

DATASETS = {
    "lidl": ROOT / "lidl/data/output/lidl-lucca-current-retailer-neutral.json",
    "esselunga": (
        ROOT
        / "esselunga/data/output/"
        "esselunga-porcari-current-retailer-neutral.json"
    ),
}


def load_dataset(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_real_lidl_dataset_can_be_summarized():
    dataset = load_dataset(DATASETS["lidl"])

    summary = summarize_offers(dataset)

    assert summary["total_offers"] == len(dataset)
    assert summary["retailers"] == ["lidl"]
    assert summary["offers_by_retailer"] == {"lidl": len(dataset)}
    assert summary["currencies"] == ["EUR"]
    assert summary["minimum_price"] is not None
    assert summary["maximum_price"] is not None


def test_real_esselunga_dataset_can_be_summarized():
    dataset = load_dataset(DATASETS["esselunga"])

    summary = summarize_offers(dataset)

    assert summary["total_offers"] == len(dataset)
    assert summary["retailers"] == ["esselunga"]
    assert summary["offers_by_retailer"] == {"esselunga": len(dataset)}
    assert summary["currencies"] == ["EUR"]
    assert summary["minimum_price"] is not None
    assert summary["maximum_price"] is not None


def test_real_datasets_share_the_same_summary_interface():
    summaries = {
        retailer: summarize_offers(load_dataset(path))
        for retailer, path in DATASETS.items()
    }

    assert summaries["lidl"]["retailers"] == ["lidl"]
    assert summaries["esselunga"]["retailers"] == ["esselunga"]

    for retailer, summary in summaries.items():
        assert summary["offers_by_retailer"][retailer] == summary["total_offers"]


def test_real_summary_is_independent_of_source_order():
    dataset = load_dataset(DATASETS["esselunga"])

    forward = summarize_offers(dataset)
    reverse = summarize_offers(list(reversed(dataset)))

    assert forward == reverse


def test_real_summary_does_not_mutate_dataset():
    dataset = load_dataset(DATASETS["lidl"])
    original = json.loads(json.dumps(dataset))

    summarize_offers(dataset)

    assert dataset == original


def test_real_summary_retailer_counts_sum_to_total():
    for path in DATASETS.values():
        dataset = load_dataset(path)
        summary = summarize_offers(dataset)

        assert sum(summary["offers_by_retailer"].values()) == summary["total_offers"]


def test_real_summary_retailers_match_retailer_count_keys():
    for path in DATASETS.values():
        dataset = load_dataset(path)
        summary = summarize_offers(dataset)

        assert sorted(summary["retailers"]) == sorted(
            summary["offers_by_retailer"]
        )


def test_real_summary_distributions_sum_to_total():
    for path in DATASETS.values():
        dataset = load_dataset(path)
        summary = summarize_offers(dataset)

        assert sum(summary["promotion_types"].values()) == summary["total_offers"]
        assert sum(summary["locality_scopes"].values()) == summary["total_offers"]
        assert (
            sum(summary["locality_verification_status"].values())
            == summary["total_offers"]
        )
        assert (
            sum(summary["evidence_verification_status"].values())
            == summary["total_offers"]
        )


def test_real_summary_price_extrema_are_ordered():
    for path in DATASETS.values():
        dataset = load_dataset(path)
        summary = summarize_offers(dataset)

        assert summary["minimum_price"] <= summary["maximum_price"]


def test_real_summary_loyalty_count_is_bounded():
    for path in DATASETS.values():
        dataset = load_dataset(path)
        summary = summarize_offers(dataset)

        assert 0 <= summary["loyalty_required_offers"] <= summary["total_offers"]


def test_real_summary_optional_field_counts_are_bounded():
    for path in DATASETS.values():
        dataset = load_dataset(path)
        summary = summarize_offers(dataset)

        assert (
            0
            <= summary["offers_with_reference_price"]
            <= summary["total_offers"]
        )
        assert (
            0
            <= summary["offers_with_base_price_text"]
            <= summary["total_offers"]
        )

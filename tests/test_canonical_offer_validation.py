import copy
import json
from pathlib import Path

import pytest

from grocery_deal_intelligence.validation import validate_offers

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schema/grocery-offer-v0.1.schema.json"


def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def make_record():
    return {
        "retailer": "lidl",
        "product_name": "Latte Fresco",
        "price": 1.49,
        "currency": "EUR",
        "promotion": {
            "type": "test",
            "requires_loyalty": False,
        },
        "validity": {
            "from": None,
            "to": None,
        },
        "locality": {
            "scope": "national",
            "stores": [],
        },
        "verification": {
            "locality_status": "verified",
            "evidence_status": "verified",
        },
        "provenance": {
            "source_type": "test",
            "source_url": "https://example.test/offer",
            "observed_at": "2026-08-26T00:00:00Z",
        },
    }


def test_valid_dataset_is_reported_as_valid():
    result = validate_offers([make_record()])

    assert result == {
        "valid": True,
        "total_records": 1,
        "valid_records": 1,
        "invalid_records": 0,
        "errors": [],
    }


def test_canonical_validation_accepts_eur_currency():
    record = make_record()
    record["currency"] = "EUR"

    result = validate_offers([record])

    assert result["valid"] is True


def test_canonical_validation_rejects_uppercase_usd_currency():
    record = make_record()
    record["currency"] = "USD"

    result = validate_offers([record])

    assert result["valid"] is False
    assert result["errors"][0]["path"] == ["currency"]


def test_offer_without_promotion_is_valid_and_asserts_no_loyalty_default():
    record = make_record()
    del record["promotion"]

    result = validate_offers([record])

    assert result["valid"] is True
    assert "promotion" not in record
    assert "requires_loyalty" not in record


@pytest.mark.parametrize(
    "promotion",
    [
        {"discount_text": "-20%"},
        {"type": "app offer"},
        {"requires_loyalty": True},
        {"requires_loyalty": False},
    ],
)
def test_independent_non_empty_promotion_claims_are_valid(promotion):
    record = make_record()
    record["promotion"] = promotion

    result = validate_offers([record])

    assert result["valid"] is True


def test_empty_promotion_object_is_invalid():
    record = make_record()
    record["promotion"] = {}

    result = validate_offers([record])

    assert result["valid"] is False
    assert any(error["path"] == ["promotion"] for error in result["errors"])


@pytest.mark.parametrize(
    "promotion",
    [
        {"type": ""},
        {"requires_loyalty": "false"},
        {"discount_text": 20},
    ],
)
def test_invalid_promotion_leaf_values_remain_rejected(promotion):
    record = make_record()
    record["promotion"] = promotion

    result = validate_offers([record])

    assert result["valid"] is False


def test_empty_dataset_is_valid():
    result = validate_offers([])

    assert result == {
        "valid": True,
        "total_records": 0,
        "valid_records": 0,
        "invalid_records": 0,
        "errors": [],
    }


def test_missing_required_property_is_invalid():
    record = make_record()
    del record["product_name"]

    result = validate_offers([record])

    assert result["valid"] is False
    assert result["total_records"] == 1
    assert result["valid_records"] == 0
    assert result["invalid_records"] == 1
    assert result["errors"]


def test_wrong_property_type_is_invalid():
    record = make_record()
    record["price"] = "1.49"

    result = validate_offers([record])

    assert result["valid"] is False
    assert result["invalid_records"] == 1
    assert result["errors"]


def test_additional_property_is_invalid():
    record = make_record()
    record["unexpected"] = True

    result = validate_offers([record])

    assert result["valid"] is False
    assert result["invalid_records"] == 1
    assert result["errors"]


def test_schema_enum_constraint_is_enforced():
    record = make_record()
    record["locality"]["scope"] = "city"

    result = validate_offers([record])

    assert result["valid"] is False
    assert result["errors"]


def test_schema_currency_const_constraint_is_enforced():
    record = make_record()
    record["currency"] = "eur"

    result = validate_offers([record])

    assert result["valid"] is False
    assert result["errors"]


def test_validation_reports_record_position_and_field_path():
    valid = make_record()
    invalid = make_record()
    invalid["product_name"] = None

    result = validate_offers([valid, invalid])

    assert result["valid"] is False
    assert result["total_records"] == 2
    assert result["valid_records"] == 1
    assert result["invalid_records"] == 1

    error = result["errors"][0]

    assert error["record_index"] == 1
    assert error["path"] == ["product_name"]
    assert error["message"]


def test_multiple_invalid_records_are_counted():
    first = make_record()
    first["price"] = "invalid"

    second = make_record()
    del second["retailer"]

    result = validate_offers([first, second])

    assert result["valid"] is False
    assert result["total_records"] == 2
    assert result["valid_records"] == 0
    assert result["invalid_records"] == 2
    assert len(result["errors"]) >= 2


def test_validation_does_not_mutate_source_dataset():
    records = [make_record()]
    original = copy.deepcopy(records)

    validate_offers(records)

    assert records == original


def test_validation_does_not_change_record_order():
    first = make_record()
    first["product_name"] = "Zeta"

    second = make_record()
    second["product_name"] = "Alpha"

    records = [first, second]
    original = copy.deepcopy(records)

    validate_offers(records)

    assert records == original


def test_validation_result_is_deterministic():
    first = make_record()
    first["price"] = "invalid"

    second = make_record()
    del second["product_name"]

    records = [first, second]

    assert validate_offers(records) == validate_offers(records)


def test_validation_rejects_non_record_values():
    result = validate_offers([make_record(), "not a record"])

    assert result["valid"] is False
    assert result["total_records"] == 2
    assert result["valid_records"] == 1
    assert result["invalid_records"] == 1
    assert result["errors"]


def test_active_at_is_not_part_of_version_01():
    with pytest.raises(TypeError):
        validate_offers(
            [make_record()],
            active_at="2026-08-26T12:00:00Z",
        )

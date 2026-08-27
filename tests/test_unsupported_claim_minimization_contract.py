import json

from grocery_deal_intelligence.validation import SCHEMA_PATH


def test_schema_requires_structures_that_cannot_always_be_omitted():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    required = set(schema["required"])
    assert {"promotion", "locality", "verification", "provenance"} <= required


def test_required_provenance_has_no_unknown_or_null_representation():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    provenance = schema["properties"]["provenance"]

    assert set(provenance["required"]) == {"source_type", "source_url", "observed_at"}
    for field in provenance["required"]:
        field_schema = provenance["properties"][field]
        assert field_schema["type"] == "string"
        assert field_schema["minLength"] == 1


def test_locality_and_verification_expose_conservative_uncertainty_values():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    locality_scope = schema["properties"]["locality"]["properties"]["scope"]["enum"]
    locality_status = schema["properties"]["verification"]["properties"]["locality_status"]["enum"]
    evidence_status = schema["properties"]["verification"]["properties"]["evidence_status"]["enum"]

    assert "unknown" in locality_scope
    assert "unknown" in locality_status
    assert "unverified" in evidence_status

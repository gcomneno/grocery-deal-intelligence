"""Tests for the pinned deterministic Lidl fixture loader."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from grocery_deal_intelligence import lidl_fixture
from grocery_deal_intelligence.lidl_fixture import (
    LIDL_LUCCA_CURRENT_FIXTURE_SHA256,
    load_lidl_fixture,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent
_FIXTURE = _REPO_ROOT / "lidl/data/output/lidl-lucca-current.json"


def test_committed_lidl_fixture_has_pinned_identity() -> None:
    """The committed source-shaped fixture must retain its reviewed identity."""
    payload = _FIXTURE.read_bytes()

    assert hashlib.sha256(payload).hexdigest() == LIDL_LUCCA_CURRENT_FIXTURE_SHA256


def test_load_lidl_fixture_returns_all_ordered_source_records() -> None:
    """The loader must preserve the source-shaped JSON record order."""
    expected = json.loads(_FIXTURE.read_text(encoding="utf-8"))

    actual = load_lidl_fixture(
        _FIXTURE,
        expected_sha256=LIDL_LUCCA_CURRENT_FIXTURE_SHA256,
    )

    assert len(actual) == 58
    assert actual == expected
    assert all(record["retailer"] == "lidl" for record in actual)


def test_load_lidl_fixture_does_not_modify_fixture_bytes() -> None:
    """Loading must leave the evidence artifact byte-for-byte unchanged."""
    before = _FIXTURE.read_bytes()

    load_lidl_fixture(
        _FIXTURE,
        expected_sha256=LIDL_LUCCA_CURRENT_FIXTURE_SHA256,
    )

    assert _FIXTURE.read_bytes() == before


def test_sha_mismatch_fails_before_json_parsing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Identity failure must occur before the payload is parsed as JSON."""
    path = tmp_path / "fixture.json"
    path.write_bytes(b"{ definitely not json")

    def forbidden_json_loads(_payload: str) -> object:
        raise AssertionError("JSON parsing must not run after SHA mismatch")

    monkeypatch.setattr(lidl_fixture.json, "loads", forbidden_json_loads)

    with pytest.raises(ValueError, match="Lidl fixture SHA-256 mismatch"):
        load_lidl_fixture(path, expected_sha256="0" * 64)


@pytest.mark.parametrize(
    "expected_sha256",
    [
        "",
        "abc",
        "g" * 64,
        "0" * 63,
        "0" * 65,
    ],
)
def test_invalid_expected_sha_is_rejected(expected_sha256: str) -> None:
    """Expected fixture identity must itself be a valid SHA-256 digest."""
    with pytest.raises(
        ValueError,
        match="expected_sha256 must be a 64-character SHA-256 hex digest",
    ):
        load_lidl_fixture(_FIXTURE, expected_sha256=expected_sha256)


def test_invalid_path_type_is_rejected() -> None:
    """Only string and Path fixture locations are accepted."""
    with pytest.raises(TypeError, match="path must be a string or Path"):
        load_lidl_fixture(123, expected_sha256=LIDL_LUCCA_CURRENT_FIXTURE_SHA256)  # type: ignore[arg-type]


def test_malformed_json_surfaces_after_matching_identity(tmp_path: Path) -> None:
    """Malformed JSON must be reported only after its bytes pass identity."""
    payload = b"{ not valid json"
    path = tmp_path / "malformed.json"
    path.write_bytes(payload)
    expected_sha256 = hashlib.sha256(payload).hexdigest()

    with pytest.raises(json.JSONDecodeError):
        load_lidl_fixture(path, expected_sha256=expected_sha256)


def test_non_list_top_level_is_rejected(tmp_path: Path) -> None:
    """A trusted fixture must still contain the expected ordered collection."""
    payload = b'{"retailer":"lidl"}'
    path = tmp_path / "object.json"
    path.write_bytes(payload)

    with pytest.raises(
        ValueError,
        match="Lidl fixture must contain a top-level JSON list",
    ):
        load_lidl_fixture(
            path,
            expected_sha256=hashlib.sha256(payload).hexdigest(),
        )


def test_non_object_record_is_rejected(tmp_path: Path) -> None:
    """Every fixture element must remain a source-shaped JSON object."""
    payload = b'[{"retailer":"lidl"},42]'
    path = tmp_path / "invalid-record.json"
    path.write_bytes(payload)

    with pytest.raises(
        ValueError,
        match="Lidl fixture record at index 1 must be a JSON object",
    ):
        load_lidl_fixture(
            path,
            expected_sha256=hashlib.sha256(payload).hexdigest(),
        )

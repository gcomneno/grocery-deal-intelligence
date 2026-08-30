from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ADAPTER_DIR = Path(__file__).resolve().parents[1] / "esselunga" / "adapter"


def _import_adapter_module(monkeypatch, module_name: str):
    monkeypatch.syspath_prepend(str(ADAPTER_DIR))
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def test_accepts_canonical_esselunga_https_url_unchanged(monkeypatch):
    module = _import_adapter_module(monkeypatch, "url_validation")
    url = "https://www.esselunga.it/services/istituzionale35/digital-grid.json"

    assert module.validate_esselunga_url(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "http://www.esselunga.it/services/istituzionale35/digital-grid.json",
        "https://esselunga.it/services/istituzionale35/digital-grid.json",
        "https://www.esselunga.it.evil.example/services/istituzionale35/digital-grid.json",
        "https://user@www.esselunga.it/services/istituzionale35/digital-grid.json",
        "https://www.esselunga.it:443/services/istituzionale35/digital-grid.json",
    ],
)
def test_rejects_unexpected_esselunga_url_shapes(monkeypatch, url):
    module = _import_adapter_module(monkeypatch, "url_validation")

    with pytest.raises(ValueError, match="unexpected Esselunga URL"):
        module.validate_esselunga_url(url)


def test_rejects_malformed_port(monkeypatch):
    module = _import_adapter_module(monkeypatch, "url_validation")

    with pytest.raises(ValueError, match="malformed Esselunga URL"):
        module.validate_esselunga_url(
            "https://www.esselunga.it:not-a-port/"
            "services/istituzionale35/digital-grid.json"
        )


def test_rejects_non_string_url(monkeypatch):
    module = _import_adapter_module(monkeypatch, "url_validation")

    with pytest.raises(TypeError, match="url must be a string"):
        module.validate_esselunga_url(None)


@pytest.mark.parametrize(
    "module_name",
    [
        "discover_stores",
        "extract_offers",
        "resolve_campaign",
        "resolve_town_stores",
    ],
)
def test_standalone_adapter_modules_keep_sibling_import_compatibility(
    monkeypatch,
    module_name,
):
    assert _import_adapter_module(monkeypatch, module_name)

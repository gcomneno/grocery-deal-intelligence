from collections.abc import Iterable, Mapping
from typing import Any


def list_available_retailers(records: Iterable[Mapping[str, Any]]) -> list[str]:
    """List exact retailer identities represented in canonical offer records."""
    retailers = set()

    for record in records:
        if not isinstance(record, Mapping):
            raise TypeError("canonical offer records must be mappings")

        if "retailer" not in record:
            raise ValueError("canonical offer retailer is required")

        retailer = record["retailer"]

        if not isinstance(retailer, str):
            raise TypeError("canonical offer retailer must be a string")

        if not retailer.strip():
            raise ValueError("canonical offer retailer must be a non-empty string")

        retailers.add(retailer)

    return sorted(retailers)

_SUPPORTED_DIMENSIONS = {
    "retailer",
    "currency",
    "promotion.type",
    "promotion.requires_loyalty",
    "locality.scope",
    "verification.locality_status",
    "verification.evidence_status",
    "reference_price",
    "base_price_text",
}


def _dimension_value(record, dimension):
    if dimension == "retailer":
        return record["retailer"]

    if dimension == "currency":
        return record["currency"]

    if dimension == "promotion.type":
        return record["promotion"]["type"]

    if dimension == "promotion.requires_loyalty":
        return record["promotion"]["requires_loyalty"]

    if dimension == "locality.scope":
        return record["locality"]["scope"]

    if dimension == "verification.locality_status":
        return record["verification"]["locality_status"]

    if dimension == "verification.evidence_status":
        return record["verification"]["evidence_status"]

    if dimension == "reference_price":
        return "present" if record.get("reference_price") is not None else "absent"

    if dimension == "base_price_text":
        return "present" if record.get("base_price_text") is not None else "absent"

    raise ValueError(f"unsupported aggregation dimension: {dimension}")


def aggregate_offers(records, *, dimension):
    if dimension not in _SUPPORTED_DIMENSIONS:
        raise ValueError(f"unsupported aggregation dimension: {dimension}")

    counts = {}

    for record in records:
        value = _dimension_value(record, dimension)
        counts[value] = counts.get(value, 0) + 1

    return {
        "dimension": dimension,
        "groups": dict(sorted(counts.items(), key=lambda item: str(item[0]))),
    }

def filter_offers(
    records,
    *,
    retailer=None,
    locality_scope=None,
    locality_status=None,
    evidence_status=None,
    requires_loyalty=None,
):
    matches = [
        record
        for record in records
        if (
            retailer is None
            or record["retailer"] == retailer
        )
        and (
            locality_scope is None
            or record["locality"]["scope"] == locality_scope
        )
        and (
            locality_status is None
            or record["verification"]["locality_status"] == locality_status
        )
        and (
            evidence_status is None
            or record["verification"]["evidence_status"] == evidence_status
        )
        and (
            requires_loyalty is None
            or record["promotion"]["requires_loyalty"] == requires_loyalty
        )
    ]

    return sorted(
        matches,
        key=lambda record: (
            record["retailer"],
            record["product_name"],
            record["price"],
            record["currency"],
        ),
    )

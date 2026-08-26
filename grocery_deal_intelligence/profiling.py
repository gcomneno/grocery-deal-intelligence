def _increment(groups, value):
    groups[value] = groups.get(value, 0) + 1


def _presence(record, field):
    return "present" if record.get(field) is not None else "absent"


def _sorted_groups(groups):
    return dict(sorted(groups.items(), key=lambda item: str(item[0])))


def profile_offers(records):
    records = list(records)

    retailers = {}
    currencies = {}
    promotion_types = {}
    loyalty_distribution = {}
    locality_scope_distribution = {}
    locality_verification_distribution = {}
    evidence_verification_distribution = {}
    reference_price_presence = {}
    base_price_text_presence = {}

    for record in records:
        _increment(retailers, record["retailer"])
        _increment(currencies, record["currency"])
        _increment(promotion_types, record["promotion"]["type"])
        _increment(
            loyalty_distribution,
            record["promotion"]["requires_loyalty"],
        )
        _increment(
            locality_scope_distribution,
            record["locality"]["scope"],
        )
        _increment(
            locality_verification_distribution,
            record["verification"]["locality_status"],
        )
        _increment(
            evidence_verification_distribution,
            record["verification"]["evidence_status"],
        )
        _increment(
            reference_price_presence,
            _presence(record, "reference_price"),
        )
        _increment(
            base_price_text_presence,
            _presence(record, "base_price_text"),
        )

    return {
        "total_records": len(records),
        "retailers": _sorted_groups(retailers),
        "currencies": _sorted_groups(currencies),
        "promotion_types": _sorted_groups(promotion_types),
        "loyalty_distribution": _sorted_groups(loyalty_distribution),
        "locality_scope_distribution": _sorted_groups(
            locality_scope_distribution
        ),
        "locality_verification_distribution": _sorted_groups(
            locality_verification_distribution
        ),
        "evidence_verification_distribution": _sorted_groups(
            evidence_verification_distribution
        ),
        "reference_price_presence": _sorted_groups(
            reference_price_presence
        ),
        "base_price_text_presence": _sorted_groups(
            base_price_text_presence
        ),
    }

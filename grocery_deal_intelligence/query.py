def search_offers(records, query, retailer=None):
    if not query or not query.strip():
        raise ValueError("query must not be empty")

    normalized_query = query.casefold()

    matches = [
        record
        for record in records
        if (
            retailer is None or record["retailer"] == retailer
        )
        and normalized_query in record["product_name"].casefold()
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

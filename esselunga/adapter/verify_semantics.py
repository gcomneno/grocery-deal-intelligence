from extract_offers import (
    extract_mechanics,
    extract_price,
    extract_promotion_details,
    extract_validity,
)


def sample(code, description, regular, promo):
    return {
        "prezzo": regular,
        "prezzoAl": regular,
        "promozioni_prezzoPromo": [promo],
        "promozioni_codMeccanica": [code],
        "promozioni_desMeccanica": [description],
        "promozioni_dataInizioPromoArticolo": ["2026-08-13T00:00:00Z"],
        "promozioni_dataFinePromoArticolo": ["2026-08-26T00:00:00Z"],
    }


cases = [
    ("M001", "EVIDENZIAZIONE PREZZO FISSO", "fixed_price", False),
    ("M002", "Sconto %", "percentage_discount", False),
    ("M003", "Prezzo Corto", "short_price", False),
    ("M004", "P. Fragola", "fragola_points", True),
    ("M005", "Sc % Fidaty", "fidaty_percentage_discount", True),
    ("M009", "1 + 1", "buy_one_get_one", False),
    ("M014", "Sc + Facile val", "facile_val_discount", True),
]


for code, description, expected_type, loyalty in cases:
    item = sample(code, description, 10.0, 8.0)

    mechanics = extract_mechanics(item)
    prices = extract_price(item)
    validity = extract_validity(item)
    details = extract_promotion_details(item)

    assert mechanics["code"] == code
    assert mechanics["type"] == expected_type
    assert mechanics["requires_loyalty"] is loyalty
    assert mechanics["is_offer"] is True

    assert prices["regular_price"] == 10.0
    assert prices["promo_price"] == 8.0
    assert prices["reference_price"] == 10.0

    assert validity["from"] == "2026-08-13T00:00:00Z"
    assert validity["to"] == "2026-08-26T00:00:00Z"

    assert isinstance(details, dict)


# M000 è evidenza editoriale, non un'offerta.
highlight = sample(
    "M000",
    "EVIDENZIAZIONE SENZA OFFERTA",
    6.90,
    6.90,
)

mechanics = extract_mechanics(highlight)

assert mechanics["type"] == "highlight"
assert mechanics["is_offer"] is False
assert mechanics["requires_loyalty"] is False


print("verify_semantics: PASS")
print(f"mechanics verified: {len(cases) + 1}")

import re
import unicodedata


def normalize_text(text):
    text = (text or "").lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        c for c in text
        if not unicodedata.combining(c)
    )
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def find_product_pages(product_name, pages):
    needle = normalize_text(product_name)

    matches = []

    for page in pages:
        haystack = normalize_text(
            " ".join([
                page.get("keyWords") or "",
                page.get("altText") or "",
            ])
        )

        if needle in haystack:
            matches.append(page.get("number"))

    return matches


if __name__ == "__main__":
    pages = [
        {
            "number": 5,
            "keyWords": "Peperone Corno Sweet Palermo Lidl Plus",
            "altText": "Offerta sul peperone.",
        },
        {
            "number": 8,
            "keyWords": "Petto di pollo disossato",
            "altText": "",
        },
    ]

    assert find_product_pages(
        "Peperone Corno Sweet Palermo",
        pages,
    ) == [5]

    assert find_product_pages(
        "Petto di pollo disossato",
        pages,
    ) == [8]

    assert find_product_pages(
        "Prodotto inesistente",
        pages,
    ) == []

    print("verify_flyer: PASS")

# Grocery Deal Intelligence

Grocery Deal Intelligence is a verifiable learning laboratory for collecting,
normalizing, validating, and comparing grocery offers across retailers.

The project is retailer-neutral at the canonical data boundary.

Current retailer adapters include:

- Lidl
- Esselunga

The canonical normalized contract is:

`schema/grocery-offer-v0.1.schema.json`

The project follows a verification-first workflow:

`discover → resolve → extract → verify → normalize → validate`

Automation must preserve evidence and remain independently verifiable.

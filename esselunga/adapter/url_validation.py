from urllib.parse import urlsplit

ESSELUNGA_ALLOWED_URL_HOSTS = frozenset(("www.esselunga.it",))


def validate_esselunga_url(url: str) -> str:
    if not isinstance(url, str):
        raise TypeError("url must be a string")

    try:
        parts = urlsplit(url)
        _ = parts.port
    except ValueError as exc:
        raise ValueError(f"malformed Esselunga URL: {url!r}") from exc

    if (
        parts.scheme != "https"
        or parts.hostname not in ESSELUNGA_ALLOWED_URL_HOSTS
        or parts.username is not None
        or parts.password is not None
        or parts.port is not None
    ):
        raise ValueError(f"unexpected Esselunga URL: {url!r}")

    return url

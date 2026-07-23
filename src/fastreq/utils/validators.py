import re
from typing import Any

from ..exceptions import ValidationError


def validate_url(url: str) -> bool:
    """Validate URL format.

    Args:
        url: URL string to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If URL is invalid

    Example:
        >>> validate_url("https://example.com")
        True
        >>> validate_url("ftp://example.com")
        ValidationError: Invalid URL: ftp://example.com. Must start with http:// or https://
    """
    pattern = r"^https?://.+"
    if not re.match(pattern, url):
        raise ValidationError(
            f"Invalid URL: {url}. Must start with http:// or https://", field_name="url"
        )
    return True


def validate_proxy(proxy: str) -> bool:
    """Validate proxy URL format.

    Args:
        proxy: Proxy URL string to validate

    Returns:
        True if valid format, False otherwise

    Valid formats:
        - IP:PORT (e.g., "192.168.1.1:8080")
        - IP:PORT:USER:PASS (e.g., "192.168.1.1:8080:admin:pass")
        - http://user:pass@host:port
        - https://user:pass@host:port
    """
    if not proxy:
        return False

    ip_port_with_auth = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+:\w+:\w+$"
    ip_port_simple = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$"
    http_url = r"^https?://.+"

    return bool(
        re.match(ip_port_with_auth, proxy)
        or re.match(ip_port_simple, proxy)
        or re.match(http_url, proxy)
    )


def validate_headers(headers: dict[str, Any]) -> bool:
    """Validate headers dictionary.

    Args:
        headers: Headers dictionary to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If headers are invalid

    Example:
        >>> validate_headers({"Content-Type": "application/json"})
        True
    """
    if not isinstance(headers, dict):
        raise ValidationError("Headers must be a dictionary", field_name="headers")

    for key, value in headers.items():
        if not isinstance(key, str):
            raise ValidationError(
                f"Header key must be a string, got {type(key).__name__}", field_name="headers"
            )
        if not isinstance(value, str):
            raise ValidationError(
                f"Header value for key '{key}' must be a string, got {type(value).__name__}",
                field_name="headers",
            )

    return True


def normalize_urls(urls: str | list[str] | None) -> list[str] | None:
    """Normalize URLs to list format.

    Args:
        urls: Single URL string, list of URLs, or None

    Returns:
        List of URLs or None

    Example:
        >>> normalize_urls("https://example.com")
        ['https://example.com']
        >>> normalize_urls(["https://a.com", "https://b.com"])
        ['https://a.com', 'https://b.com']
    """
    if urls is None:
        return None
    if isinstance(urls, str):
        return [urls]
    return urls

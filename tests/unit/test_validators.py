import pytest

from fastreq.exceptions import ValidationError
from fastreq.utils.validators import (
    normalize_urls,
    validate_headers,
    validate_proxy,
    validate_url,
)


def test_valid_http_url() -> None:
    result = validate_url("https://example.com/path")
    assert result is True


def test_valid_url_with_query_params() -> None:
    result = validate_url("https://example.com?key=value")
    assert result is True


def test_valid_http_scheme() -> None:
    result = validate_url("http://example.com")
    assert result is True


def test_invalid_url_no_scheme() -> None:
    with pytest.raises(ValidationError) as exc_info:
        validate_url("example.com")

    assert "Invalid URL" in str(exc_info.value)
    assert exc_info.value.field_name == "url"


def test_invalid_url_unsupported_scheme() -> None:
    with pytest.raises(ValidationError) as exc_info:
        validate_url("ftp://example.com")

    assert "Invalid URL" in str(exc_info.value)


def test_valid_proxy_ip_port() -> None:
    result = validate_proxy("192.168.1.1:8080")
    assert result is True


def test_valid_proxy_with_authentication() -> None:
    result = validate_proxy("192.168.1.1:8080:user:pass")
    assert result is True


def test_valid_http_proxy_url() -> None:
    result = validate_proxy("http://user:pass@192.168.1.1:8080")
    assert result is True


def test_valid_https_proxy_url() -> None:
    result = validate_proxy("https://proxy.example.com:8080")
    assert result is True


def test_invalid_proxy_format() -> None:
    result = validate_proxy("invalid")
    assert result is False


def test_empty_proxy_string() -> None:
    result = validate_proxy("")
    assert result is False


def test_valid_headers() -> None:
    headers = {"User-Agent": "test", "Accept": "application/json"}
    result = validate_headers(headers)
    assert result is True


def test_invalid_header_non_string_value() -> None:
    with pytest.raises(ValidationError) as exc_info:
        validate_headers({"X-Count": 123})

    assert "Header value for key 'X-Count' must be a string" in str(exc_info.value)
    assert exc_info.value.field_name == "headers"


def test_invalid_header_non_string_key() -> None:
    with pytest.raises(ValidationError) as exc_info:
        validate_headers({123: "value"})

    assert "Header key must be a string" in str(exc_info.value)
    assert exc_info.value.field_name == "headers"


def test_invalid_header_not_dict() -> None:
    with pytest.raises(ValidationError) as exc_info:
        validate_headers("not a dict")

    assert "Headers must be a dictionary" in str(exc_info.value)
    assert exc_info.value.field_name == "headers"


def test_empty_headers() -> None:
    result = validate_headers({})
    assert result is True


def test_normalize_urls_single_string() -> None:
    result = normalize_urls("https://example.com")
    assert result == ["https://example.com"]


def test_normalize_urls_list_of_urls() -> None:
    urls = ["https://a.com", "https://b.com"]
    result = normalize_urls(urls)
    assert result == ["https://a.com", "https://b.com"]


def test_normalize_urls_none() -> None:
    result = normalize_urls(None)
    assert result is None

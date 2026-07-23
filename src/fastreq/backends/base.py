"""Base transport protocol and shared types for fastreq.

Defines the narrow async backend contract implemented only by the retained
transports (niquests and httpx), plus the normalized request/response
data structures shared between the client and transports.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any


@dataclass
class RequestConfig:
    """Configuration for a single HTTP request.

    Used internally by transports to normalize request parameters.

    Attributes:
        url: Request URL
        method: HTTP method (GET, POST, etc.)
        params: Query parameters
        data: Request body data
        json: JSON body (serialized automatically)
        headers: Request headers
        cookies: Request cookies
        timeout: Per-request timeout in seconds
        proxy: Proxy URL
        http2: Enable HTTP/2
        stream: Enable streaming mode
        follow_redirects: Follow HTTP redirects
        verify_ssl: Verify SSL certificates
    """

    url: str
    method: str = "GET"
    params: dict[str, Any] | None = None
    data: Any = None
    json: Any = None
    headers: dict[str, str] | None = None
    cookies: dict[str, str] | None = None
    timeout: float | None = None
    proxy: str | None = None
    http2: bool = True
    stream: bool = False
    follow_redirects: bool = True
    verify_ssl: bool = True


@dataclass
class NormalizedResponse:
    """Normalized response from HTTP transports.

    Provides a consistent interface across different transport implementations.

    Attributes:
        status_code: HTTP status code
        headers: Response headers (normalized to lowercase)
        content: Raw response body as bytes
        text: Decoded response body as string
        json_data: Parsed JSON data (if applicable)
        url: Final URL (after redirects)
        is_json: Whether response contains valid JSON
    """

    status_code: int
    headers: dict[str, str]
    content: bytes
    text: str
    json_data: Any
    url: str
    is_json: bool = False

    def __post_init__(self) -> None:
        if self.is_json and self.json_data is None:
            import contextlib
            import json

            with contextlib.suppress(json.JSONDecodeError, UnicodeDecodeError):
                self.json_data = json.loads(self.text)

    @staticmethod
    def _normalize_headers(headers: Mapping[str, str] | dict[str, str]) -> dict[str, str]:
        """Normalize headers by converting all keys to lowercase.

        Args:
            headers: Original headers dictionary

        Returns:
            Headers with all keys lowercase
        """
        return {key.lower(): value for key, value in headers.items()}

    @classmethod
    def from_backend(
        cls,
        status_code: int,
        headers: dict[str, str],
        content: bytes,
        url: str,
        is_json: bool = False,
    ) -> NormalizedResponse:
        """Create NormalizedResponse from transport response.

        Args:
            status_code: HTTP status code
            headers: Response headers
            content: Response content as bytes
            url: Final URL
            is_json: Whether response is JSON

        Returns:
            NormalizedResponse instance
        """
        text = content.decode("utf-8", errors="replace")
        normalized_headers = cls._normalize_headers(headers)
        return cls(
            status_code=status_code,
            headers=normalized_headers,
            content=content,
            text=text,
            json_data=None,
            url=url,
            is_json=is_json,
        )


@dataclass(frozen=True)
class TransportKey:
    """Immutable key for caching proxy-scoped transport clients.

    HTTPX 0.28+ configures proxies at client construction time, so we must
    maintain separate clients per (proxy, verify_ssl, follow_redirects, http2) tuple.
    Niquests sessions are similarly kept per proxy key for cookie isolation.

    Attributes:
        proxy: Proxy URL or None for direct connections
        verify_ssl: Whether SSL certificates are verified
        follow_redirects: Whether HTTP redirects are followed
        http2: Whether HTTP/2 is enabled
    """

    proxy: str | None = None
    verify_ssl: bool = True
    follow_redirects: bool = True
    http2: bool = True


class Backend(ABC):
    """Abstract base class for HTTP transports.

    All transports must implement this interface to provide a consistent
    experience across different HTTP client libraries.

    Transports do NOT own concurrency — that is managed by the client.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the transport identifier.

        Returns:
            Transport name string (e.g., "niquests", "httpx")
        """
        ...

    @abstractmethod
    async def request(
        self,
        config: RequestConfig,
        stream_callback: Callable[[bytes], Any] | None = None,
    ) -> NormalizedResponse:
        """Execute an HTTP request and return a normalized response.

        Args:
            config: Request configuration
            stream_callback: Optional callback for streaming chunks.
                When provided with a streaming request, chunks are delivered
                as they arrive, before the full body is accumulated.

        Returns:
            NormalizedResponse with status, headers, and content.
            For streaming requests, content may be empty after callback delivery.
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Clean up transport resources.

        Called when closing the client or exiting context manager.
        All proxy-scoped clients/sessions SHALL be closed.
        """
        ...

    @abstractmethod
    async def __aenter__(self) -> Backend:
        """Enter context manager and initialize transport session.

        Returns:
            Self for use in async with statement
        """
        ...

    @abstractmethod
    async def __aexit__(self, *args: Any) -> None:
        """Exit context manager and cleanup resources."""
        ...

    @abstractmethod
    def supports_http2(self) -> bool:
        """Return True if transport supports HTTP/2.

        Returns:
            True if HTTP/2 is supported, False otherwise
        """
        ...

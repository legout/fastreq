"""httpx transport — the optional alternative backend for fastreq.

Implements the Backend contract using httpx.AsyncClient with proxy-scoped
client caching (HTTPX 0.28+ configures proxies at client construction time),
real chunked streaming, TLS configuration, and redirect support.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import httpx

from fastreq.backends.base import Backend, NormalizedResponse, RequestConfig, TransportKey
from fastreq.exceptions import BackendError


class HttpxBackend(Backend):
    """httpx-based transport with proxy-scoped clients.

    Clients are cached by TransportKey because HTTPX 0.28+ configures proxies
    at client construction time. Each unique (proxy, verify_ssl, follow_redirects, http2)
    combination gets its own AsyncClient for cookie isolation.

    HTTP/2 is supported when the h2 extra is installed.
    """

    def __init__(self) -> None:
        self._clients: dict[TransportKey, httpx.AsyncClient] = {}
        self._h2_available: bool | None = None

    @property
    def name(self) -> str:
        return "httpx"

    def _check_h2_available(self) -> bool:
        """Check whether the h2 package is available for HTTP/2 support."""
        if self._h2_available is not None:
            return self._h2_available
        try:
            import h2  # noqa: F401

            self._h2_available = True
        except ImportError:
            self._h2_available = False
        return self._h2_available

    def _get_client(self, key: TransportKey) -> httpx.AsyncClient:
        """Get or create a client for the given transport key.

        HTTPX 0.28+ requires proxies to be set at client construction,
        so we maintain one client per proxy key.
        """
        client = self._clients.get(key)
        if client is not None:
            return client

        effective_http2 = key.http2 and self._check_h2_available()
        client_kwargs: dict[str, Any] = {
            "http2": effective_http2,
            "follow_redirects": key.follow_redirects,
            "verify": key.verify_ssl,
        }

        # HTTPX 0.28: proxy is set at client level via the 'proxy' parameter
        if key.proxy is not None:
            client_kwargs["proxy"] = key.proxy

        client = httpx.AsyncClient(**client_kwargs)
        self._clients[key] = client
        return client

    async def request(
        self,
        config: RequestConfig,
        stream_callback: Callable[[bytes], Any] | None = None,
    ) -> NormalizedResponse:
        """Execute a request through httpx."""
        key = TransportKey(
            proxy=config.proxy,
            verify_ssl=config.verify_ssl,
            follow_redirects=config.follow_redirects,
            http2=config.http2,
        )
        client = self._get_client(key)

        kwargs: dict[str, Any] = {
            "method": config.method,
            "url": config.url,
            "params": config.params,
            "headers": config.headers,
        }

        # Set cookies on the client instance (httpx 0.28 best practice)
        if config.cookies:
            for name, value in config.cookies.items():
                client.cookies.set(name, value)

        if config.timeout is not None:
            kwargs["timeout"] = config.timeout

        if config.data is not None:
            kwargs["content"] = config.data

        if config.json is not None:
            kwargs["json"] = config.json

        is_streaming = config.stream and stream_callback is not None

        try:
            if is_streaming and stream_callback is not None:
                return await self._stream_request(client, kwargs, stream_callback)
            return await self._normal_request(client, kwargs)
        except httpx.HTTPError as e:
            raise BackendError(f"Request failed: {e}", backend_name=self.name) from e

    async def _normal_request(
        self, client: httpx.AsyncClient, kwargs: dict[str, Any]
    ) -> NormalizedResponse:
        """Execute a non-streaming request."""
        response = await client.request(**kwargs)

        headers: dict[str, str] = {}
        for k, v in response.headers.items():
            headers[str(k)] = str(v)

        content_type = response.headers.get("content-type", "").lower()
        is_json = "application/json" in content_type

        return NormalizedResponse.from_backend(
            status_code=response.status_code,
            headers=headers,
            content=response.content,
            url=str(response.url),
            is_json=is_json,
        )

    async def _stream_request(
        self,
        client: httpx.AsyncClient,
        kwargs: dict[str, Any],
        stream_callback: Callable[[bytes], Any],
    ) -> NormalizedResponse:
        """Execute a streaming request, delivering chunks to the callback."""
        async with client.stream(**kwargs) as response:
            headers: dict[str, str] = {}
            for k, v in response.headers.items():
                headers[str(k)] = str(v)

            content_type = response.headers.get("content-type", "").lower()
            is_json = "application/json" in content_type

            chunks: list[bytes] = []
            async for chunk in response.aiter_raw(chunk_size=8192):
                if chunk:
                    chunks.append(chunk)
                    stream_callback(chunk)

            return NormalizedResponse.from_backend(
                status_code=response.status_code,
                headers=headers,
                content=b"".join(chunks),
                url=str(response.url),
                is_json=is_json,
            )

    async def close(self) -> None:
        """Close all cached clients."""
        for client in self._clients.values():
            await client.aclose()
        self._clients.clear()

    async def __aenter__(self) -> HttpxBackend:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    def supports_http2(self) -> bool:
        """httpx supports HTTP/2 when h2 is installed."""
        return self._check_h2_available()

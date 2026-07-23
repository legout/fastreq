"""niquests transport — the default and required backend for fastreq.

Implements the Backend contract using niquests.AsyncSession with proxy-keyed
session caching for cookie isolation, real chunked streaming, TLS configuration,
and redirect support.
"""

from __future__ import annotations

from typing import Any
from collections.abc import Callable

import niquests

from fastreq.backends.base import Backend, NormalizedResponse, RequestConfig, TransportKey
from fastreq.exceptions import BackendError


class NiquestsBackend(Backend):
    """niquests-based transport with proxy-scoped sessions.

    Sessions are cached by TransportKey so that cookies are physically
    isolated per proxy. A single direct-connection session is used when
    no proxy is selected.

    HTTP/2 is supported and controlled by the http2 flag on TransportKey.
    """

    def __init__(self) -> None:
        self._sessions: dict[TransportKey, niquests.AsyncSession] = {}

    @property
    def name(self) -> str:
        return "niquests"

    def _get_session(self, key: TransportKey) -> niquests.AsyncSession:
        """Get or create a session for the given transport key."""
        session = self._sessions.get(key)
        if session is not None:
            return session

        session = niquests.AsyncSession(
            disable_http2=not key.http2,
        )
        self._sessions[key] = session
        return session

    async def request(
        self,
        config: RequestConfig,
        stream_callback: Callable[[bytes], Any] | None = None,
    ) -> NormalizedResponse:
        """Execute a request through niquests."""
        key = TransportKey(
            proxy=config.proxy,
            verify_ssl=config.verify_ssl,
            follow_redirects=config.follow_redirects,
            http2=config.http2,
        )
        session = self._get_session(key)

        kwargs: dict[str, Any] = {
            "method": config.method,
            "url": config.url,
            "params": config.params,
            "headers": config.headers,
            "cookies": config.cookies,
            "timeout": config.timeout,
            "allow_redirects": config.follow_redirects,
            "verify": config.verify_ssl,
        }

        if config.data is not None:
            kwargs["data"] = config.data

        if config.json is not None:
            kwargs["json"] = config.json

        if config.proxy is not None:
            kwargs["proxies"] = {"http": config.proxy, "https": config.proxy}

        is_streaming = config.stream and stream_callback is not None
        kwargs["stream"] = is_streaming

        try:
            response = await session.request(**kwargs)
        except niquests.RequestException as e:
            raise BackendError(f"Request failed: {e}", backend_name=self.name) from e

        headers: dict[str, str] = {}
        for k, v in response.headers.items():
            headers[str(k)] = str(v)

        content_type = response.headers.get("content-type", "").lower()
        is_json = "application/json" in content_type

        if is_streaming:
            # Deliver chunks as they arrive — genuine streaming
            chunks: list[bytes] = []
            async for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    chunks.append(chunk)
                    stream_callback(chunk)
            content = b"".join(chunks)
        else:
            content = response.content

        return NormalizedResponse.from_backend(
            status_code=response.status_code,
            headers=headers,
            content=content,
            url=str(response.url),
            is_json=is_json,
        )

    async def close(self) -> None:
        """Close all cached sessions."""
        for session in self._sessions.values():
            await session.close()
        self._sessions.clear()

    async def __aenter__(self) -> NiquestsBackend:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    def supports_http2(self) -> bool:
        """niquests supports HTTP/2 via qh3."""
        return True

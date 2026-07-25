"""curl_cffi transport — browser TLS/JA3 impersonation backend for fastreq.

Implements the Backend contract using ``curl_cffi.requests.AsyncSession``.
The killer feature is ``impersonate``: curl_cffi replicates a real browser's
TLS fingerprint (JA3/JA4), HTTP/2 SETTINGS, and default headers, which defeats
bot detection that blocks plain httpx/niquests clients (e.g. Yahoo Finance).

Sessions are cached per :class:`TransportKey` (one AsyncSession per proxy
combination) so cookie jars stay isolated per network route.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from typing import Any

from curl_cffi import CurlHttpVersion
from curl_cffi.requests import AsyncSession

from fastreq.backends.base import Backend, NormalizedResponse, RequestConfig, TransportKey
from fastreq.exceptions import BackendError

# Recent browser impersonation targets available in curl_cffi >= 0.13.
# Used when impersonate="random". Kept to desktop targets released in the
# last few Chrome/Safari/Firefox generations.
IMPERSONATE_TARGETS: list[str] = [
    "chrome131",
    "chrome133a",
    "chrome136",
    "safari180",
    "safari184",
    "firefox133",
    "firefox135",
]


def resolve_impersonate(impersonate: str | None) -> str | None:
    """Resolve an impersonate setting to a concrete curl_cffi target.

    ``None`` disables impersonation; ``"random"`` picks a random target from
    :data:`IMPERSONATE_TARGETS`; anything else is passed through unchanged
    (curl_cffi validates the target itself).
    """
    if impersonate is None:
        return None
    if impersonate == "random":
        return random.choice(IMPERSONATE_TARGETS)
    return impersonate


class CurlCffiBackend(Backend):
    """curl_cffi-based transport with optional browser impersonation.

    Parameters
    ----------
    impersonate
        Browser to impersonate (e.g. ``"chrome"``, ``"chrome131"``,
        ``"safari184"``), ``"random"`` for a random recent target, or
        ``None`` to disable impersonation. When set, curl_cffi also supplies
        the matching default browser headers — do not override User-Agent
        with a mismatched one.
    """

    def __init__(self, impersonate: str | None = None) -> None:
        self._impersonate = impersonate
        self._resolved_impersonate = resolve_impersonate(impersonate)
        self._sessions: dict[TransportKey, AsyncSession] = {}

    @property
    def name(self) -> str:
        return "curl_cffi"

    def _get_session(self, key: TransportKey) -> AsyncSession:
        """Get or create an AsyncSession for the given transport key.

        One session per key keeps cookie jars isolated per proxy route and
        lets proxy/verify/redirect settings live at session level.
        """
        session = self._sessions.get(key)
        if session is not None:
            return session

        kwargs: dict[str, Any] = {
            "verify": key.verify_ssl,
            "allow_redirects": key.follow_redirects,
        }
        if self._resolved_impersonate is not None:
            kwargs["impersonate"] = self._resolved_impersonate
        elif not key.http2:
            # Without impersonation the fingerprint is ours to choose.
            kwargs["http_version"] = CurlHttpVersion.V1_1

        if key.proxy is not None:
            kwargs["proxy"] = key.proxy

        session = AsyncSession(**kwargs)
        self._sessions[key] = session
        return session

    async def request(
        self,
        config: RequestConfig,
        stream_callback: Callable[[bytes], Any] | None = None,
    ) -> NormalizedResponse:
        """Execute a request through curl_cffi."""
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
            "data": config.data,
            "json": config.json,
            "timeout": config.timeout,
            "allow_redirects": config.follow_redirects,
            "verify": config.verify_ssl,
        }

        is_streaming = config.stream and stream_callback is not None

        try:
            if is_streaming:
                return await self._stream_request(session, kwargs, stream_callback)
            response = await session.request(**kwargs)
            return self._normalize(response)
        except Exception as e:
            # curl_cffi raises RequestException (a CurlError subclass) for
            # transport failures; avoid a hard import for the type check.
            if type(e).__module__.startswith("curl_cffi"):
                raise BackendError(f"Request failed: {e}", backend_name=self.name) from e
            raise

    async def _stream_request(
        self,
        session: Any,
        kwargs: dict[str, Any],
        stream_callback: Callable[[bytes], Any],
    ) -> NormalizedResponse:
        """Execute a streaming request, delivering chunks to the callback."""
        async with session.stream(kwargs.pop("method"), kwargs.pop("url"), **kwargs) as response:
            chunks: list[bytes] = []
            async for chunk in response.aiter_content():
                if chunk:
                    chunks.append(chunk)
                    stream_callback(chunk)
            return self._normalize(response, content=b"".join(chunks))

    @staticmethod
    def _normalize(response: Any, content: bytes | None = None) -> NormalizedResponse:
        headers: dict[str, str] = {str(k): str(v) for k, v in response.headers.items()}
        content_type = response.headers.get("content-type", "").lower()
        is_json = "application/json" in content_type
        body = content if content is not None else response.content
        return NormalizedResponse.from_backend(
            status_code=response.status_code,
            headers=headers,
            content=body,
            url=str(response.url),
            is_json=is_json,
        )

    async def close(self) -> None:
        """Close all cached sessions."""
        for session in self._sessions.values():
            await session.close()
        self._sessions.clear()

    async def __aenter__(self) -> CurlCffiBackend:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    def supports_http2(self) -> bool:
        """curl_cffi always supports HTTP/2 (it is libcurl)."""
        return True

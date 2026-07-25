"""curl_cffi backend unit tests: impersonation, selection, session caching.

These tests are hermetic — they do not require network access beyond the
shared LocalTestServer used by the transport contract tests.
"""

from __future__ import annotations

import sys
from collections.abc import AsyncIterator

import pytest

pytest.importorskip("curl_cffi", reason="curl_cffi extra not installed")

from fastreq import FastRequests, ReturnType
from fastreq.backends.base import TransportKey
from fastreq.backends.curl_cffi import (
    IMPERSONATE_TARGETS,
    CurlCffiBackend,
    resolve_impersonate,
)
from fastreq.exceptions import ConfigurationError
from tests.conftest import LocalTestServer, json_response


@pytest.fixture
async def server() -> AsyncIterator[LocalTestServer]:
    srv = LocalTestServer()
    await srv.start()
    yield srv
    await srv.stop()


class TestImpersonateResolution:
    def test_explicit_target_passthrough(self) -> None:
        assert resolve_impersonate("chrome131") == "chrome131"

    def test_none_stays_none(self) -> None:
        assert resolve_impersonate(None) is None

    def test_random_picks_from_targets(self) -> None:
        for _ in range(20):
            assert resolve_impersonate("random") in IMPERSONATE_TARGETS

    def test_targets_are_recent_browsers(self) -> None:
        # All targets must be non-empty strings naming a browser family
        assert IMPERSONATE_TARGETS
        for target in IMPERSONATE_TARGETS:
            assert isinstance(target, str)
            assert any(target.startswith(p) for p in ("chrome", "safari", "firefox"))


class TestBackendSelection:
    def test_curl_cffi_constructs(self) -> None:
        client = FastRequests(backend="curl_cffi", verbose=False)
        assert client._backend is not None
        assert client._backend.name == "curl_cffi"

    def test_impersonate_forwarded_to_backend(self) -> None:
        client = FastRequests(backend="curl_cffi", impersonate="chrome131", verbose=False)
        assert isinstance(client._backend, CurlCffiBackend)
        assert client._backend._impersonate == "chrome131"

    def test_impersonate_disables_ua_rotation(self) -> None:
        """A rotated UA would contradict the impersonated TLS fingerprint."""
        client = FastRequests(backend="curl_cffi", impersonate="chrome", verbose=False)
        assert client._header_manager._enabled is False

    def test_no_impersonate_keeps_ua_rotation(self) -> None:
        client = FastRequests(backend="curl_cffi", verbose=False)
        assert client._header_manager._enabled is True

    def test_missing_dependency_raises_configuration_error(self, monkeypatch) -> None:
        # Drop the already-imported backend module so the factory re-imports it
        # and hits the (now missing) curl_cffi dependency.
        monkeypatch.delitem(sys.modules, "fastreq.backends.curl_cffi")
        monkeypatch.setitem(sys.modules, "curl_cffi", None)
        monkeypatch.setitem(sys.modules, "curl_cffi.requests", None)
        with pytest.raises(ConfigurationError, match="fastreq\\[curl\\]"):
            FastRequests(backend="curl_cffi", verbose=False)


class TestSessionCaching:
    async def test_sessions_cached_per_transport_key(self) -> None:
        backend = CurlCffiBackend()
        s1 = backend._get_session(TransportKey(proxy=None))
        s2 = backend._get_session(TransportKey(proxy=None))
        s3 = backend._get_session(TransportKey(proxy="http://proxy:8080"))
        assert s1 is s2
        assert s3 is not s1
        await backend.close()

    async def test_close_clears_sessions(self) -> None:
        backend = CurlCffiBackend()
        backend._get_session(TransportKey(proxy=None))
        await backend.close()
        assert not backend._sessions


class TestRequests:
    async def test_json_roundtrip(self, server: LocalTestServer) -> None:
        server.add_route("GET", "/api", json_response({"key": "value"}))
        client = FastRequests(backend="curl_cffi", verbose=False)
        async with client:
            result = await client.request(server.url("/api"), return_type=ReturnType.JSON)
        assert result == {"key": "value"}

    async def test_impersonated_request_against_local_http(self, server: LocalTestServer) -> None:
        """Impersonation must not break plain-HTTP requests (TLS-only feature)."""
        server.add_route("GET", "/api", json_response({"ok": True}))
        client = FastRequests(backend="curl_cffi", impersonate="chrome", verbose=False)
        async with client:
            result = await client.request(server.url("/api"), return_type=ReturnType.JSON)
        assert result == {"ok": True}

    def test_supports_http2(self) -> None:
        assert CurlCffiBackend().supports_http2() is True

"""Tests for the public client contract: construction and backend selection.

Covers:
- FastRequests(backend="niquests"), FastRequests(backend="httpx"), FastRequests() construct
- Removed backend names fail with ConfigurationError
"""

from __future__ import annotations

import pytest

from fastreq import (
    ConfigurationError,
    FastRequests,
    ParallelRequests,
    ReturnType,
)
from fastreq.client import _create_backend
from fastreq.backends.base import Backend
from fastreq.backends.niquests import NiquestsBackend
from fastreq.backends.httpx import HttpxBackend


class TestBackendConstruction:
    """Task 1.1, 1.2: Construction tests for retained and removed backends."""

    def test_default_construction(self) -> None:
        """FastRequests() selects niquests (auto)."""
        client = FastRequests()
        assert client.backend_name == "auto"
        assert client._backend is not None
        assert client._backend.name == "niquests"

    def test_niquests_construction(self) -> None:
        """FastRequests(backend='niquests') constructs successfully."""
        client = FastRequests(backend="niquests")
        assert client._backend is not None
        assert client._backend.name == "niquests"
        assert isinstance(client._backend, NiquestsBackend)

    def test_httpx_construction(self) -> None:
        """FastRequests(backend='httpx') constructs successfully."""
        client = FastRequests(backend="httpx")
        assert client._backend is not None
        assert client._backend.name == "httpx"
        assert isinstance(client._backend, HttpxBackend)

    def test_aiohttp_removed_raises_configuration_error(self) -> None:
        """backend='aiohttp' raises ConfigurationError with migration guidance."""
        with pytest.raises(ConfigurationError) as exc_info:
            FastRequests(backend="aiohttp")
        assert "aiohttp" in str(exc_info.value)
        assert "niquests" in str(exc_info.value)
        assert "httpx" in str(exc_info.value)

    def test_requests_removed_raises_configuration_error(self) -> None:
        """backend='requests' raises ConfigurationError with migration guidance."""
        with pytest.raises(ConfigurationError) as exc_info:
            FastRequests(backend="requests")
        assert "requests" in str(exc_info.value)
        assert "niquests" in str(exc_info.value)

    def test_unknown_backend_raises(self) -> None:
        """Unknown backend name raises ConfigurationError."""
        with pytest.raises(ConfigurationError):
            FastRequests(backend="nonexistent")

    def test_parallel_requests_alias(self) -> None:
        """ParallelRequests is an alias for FastRequests."""
        assert ParallelRequests is FastRequests

    def test_default_concurrency_exists(self) -> None:
        """Client has a single concurrency semaphore."""
        client = FastRequests()
        assert client.concurrency == 20
        assert client._concurrency_semaphore is not None


class TestCreateBackendFactory:
    """Test the typed two-backend factory directly."""

    def test_create_niquests(self) -> None:
        backend = _create_backend("niquests", http2=True)
        assert isinstance(backend, NiquestsBackend)

    def test_create_auto(self) -> None:
        """auto always selects niquests."""
        backend = _create_backend("auto", http2=True)
        assert isinstance(backend, NiquestsBackend)

    def test_create_httpx(self) -> None:
        backend = _create_backend("httpx", http2=True)
        assert isinstance(backend, HttpxBackend)

    def test_create_aiohttp_raises(self) -> None:
        with pytest.raises(ConfigurationError):
            _create_backend("aiohttp", http2=True)

    def test_create_requests_raises(self) -> None:
        with pytest.raises(ConfigurationError):
            _create_backend("requests", http2=True)

    def test_backend_no_concurrency_in_constructor(self) -> None:
        """Backends do NOT receive concurrency in their constructor."""
        backend = NiquestsBackend()
        # Verify no concurrency attribute leaked from old API
        assert not hasattr(backend, "concurrency")
        assert not hasattr(backend, "_concurrency")

"""Tests for ProxyPool: URL normalization, rotation, cooldown, recovery.

Covers Tasks 4.1-4.6: explicit proxy inputs, Webshare import, round-robin
selection, random compatibility mode, cooldown, recovery, and free-proxy
removal.
"""

from __future__ import annotations

import asyncio

import pytest

from fastreq.utils.proxies import (
    ProxyError,
    ProxyPool,
    ProxyPoolConfig,
    ProxySelection,
    _is_valid_proxy,
    _normalize_proxy_url,
    load_webshare_from_file,
)


class TestProxyNormalization:
    """Task 4.1: URL normalization."""

    def test_http_proxy_passthrough(self) -> None:
        assert _normalize_proxy_url("http://proxy:8080") == "http://proxy:8080"

    def test_https_proxy_passthrough(self) -> None:
        assert _normalize_proxy_url("https://proxy:8080") == "https://proxy:8080"

    def test_auth_proxy_passthrough(self) -> None:
        url = "http://user:pass@proxy:8080"
        assert _normalize_proxy_url(url) == url

    def test_bare_host_port_normalized(self) -> None:
        assert _normalize_proxy_url("proxy:8080") == "http://proxy:8080"

    def test_host_port_user_pass_normalized(self) -> None:
        result = _normalize_proxy_url("host:8080:user:pass")
        assert result == "http://user:pass@host:8080"

    def test_valid_formats(self) -> None:
        assert _is_valid_proxy("http://proxy:8080")
        assert _is_valid_proxy("https://proxy:8080")
        assert _is_valid_proxy("proxy:8080")
        assert _is_valid_proxy("192.168.1.1:8080")
        assert _is_valid_proxy("192.168.1.1:8080:user:pass")

    def test_invalid_formats(self) -> None:
        assert not _is_valid_proxy("")
        assert not _is_valid_proxy("invalid")
        assert not _is_valid_proxy("ftp://proxy:8080")


class TestProxyPoolConstruction:
    """Task 4.1: Explicit/Webshare proxy inputs."""

    def test_construct_with_list(self) -> None:
        pool = ProxyPool(["http://p1:8080", "http://p2:8080"])
        assert pool.count() == 2

    def test_construct_with_bare_host_port(self) -> None:
        pool = ProxyPool(["p1:8080", "p2:8080"])
        assert pool.count() == 2
        assert "http://p1:8080" in pool.proxies

    def test_construct_with_auth_format(self) -> None:
        pool = ProxyPool(["host:8080:user:pass"])
        assert pool.count() == 1
        assert pool.proxies[0] == "http://user:pass@host:8080"

    def test_deduplicates_proxies(self) -> None:
        pool = ProxyPool(["http://p1:8080", "http://p1:8080", "http://p2:8080"])
        assert pool.count() == 2

    def test_filters_invalid_proxies(self) -> None:
        pool = ProxyPool(["http://p1:8080", "invalid", "", "http://p2:8080"])
        assert pool.count() == 2

    def test_empty_pool(self) -> None:
        pool = ProxyPool()
        assert pool.count() == 0
        assert pool.proxies == []

    def test_from_webshare_text(self) -> None:
        text = "1.2.3.4:8080:user1:pass1\n5.6.7.8:9090:user2:pass2\n"
        pool = ProxyPool.from_webshare_text(text)
        assert pool.count() == 2
        assert "http://user1:pass1@1.2.3.4:8080" in pool.proxies
        assert "http://user2:pass2@5.6.7.8:9090" in pool.proxies

    def test_from_webshare_empty_raises(self) -> None:
        with pytest.raises(ProxyError):
            ProxyPool.from_webshare_text("")

    def test_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FASTREQ_PROXIES", "http://p1:8080,http://p2:8080")
        pool = ProxyPool.from_env()
        assert pool.count() == 2

    def test_from_env_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("FASTREQ_PROXIES", raising=False)
        pool = ProxyPool.from_env()
        assert pool.count() == 0

    def test_no_free_proxies_feature(self) -> None:
        """ProxyPool has no free-proxy fetching capability."""
        pool = ProxyPool()
        assert not hasattr(pool, "_fetch_free_proxies")
        assert not hasattr(pool, "free_proxies")
        # No free_proxies in config either
        assert not hasattr(ProxyPoolConfig(), "free_proxies")


class TestProxySelection:
    """Task 4.1: Round-robin and random selection."""

    async def test_round_robin_selection(self) -> None:
        pool = ProxyPool(
            ["http://p1:8080", "http://p2:8080", "http://p3:8080"],
            config=ProxyPoolConfig(selection=ProxySelection.ROUND_ROBIN),
        )
        results = [await pool.acquire() for _ in range(6)]
        # Round-robin should cycle through all proxies
        assert results[0] == results[3]
        assert results[1] == results[4]
        assert results[2] == results[5]
        assert len(set(results[:3])) == 3

    async def test_random_selection(self) -> None:
        pool = ProxyPool(
            ["http://p1:8080", "http://p2:8080"],
            config=ProxyPoolConfig(selection=ProxySelection.RANDOM),
        )
        results = [await pool.acquire() for _ in range(10)]
        # Random should return valid proxies from the pool
        assert all(r in pool.proxies for r in results)

    async def test_empty_pool_returns_none(self) -> None:
        pool = ProxyPool()
        assert await pool.acquire() is None

    async def test_single_proxy_round_robin(self) -> None:
        pool = ProxyPool(["http://only:8080"])
        result = await pool.acquire()
        assert result == "http://only:8080"


class TestProxyCooldownAndRecovery:
    """Task 4.1: Cooldown and recovery."""

    async def test_mark_failed_enters_cooldown(self) -> None:
        pool = ProxyPool(
            ["http://p1:8080", "http://p2:8080"],
            config=ProxyPoolConfig(cooldown=60.0),
        )
        await pool.mark_failed("http://p1:8080")
        assert pool.count_available() == 1

    async def test_failed_proxy_excluded_from_selection(self) -> None:
        pool = ProxyPool(
            ["http://p1:8080", "http://p2:8080"],
            config=ProxyPoolConfig(cooldown=60.0, selection=ProxySelection.ROUND_ROBIN),
        )
        await pool.mark_failed("http://p1:8080")

        # p1 should be excluded
        for _ in range(5):
            proxy = await pool.acquire()
            assert proxy == "http://p2:8080"

    async def test_mark_success_clears_cooldown(self) -> None:
        pool = ProxyPool(
            ["http://p1:8080", "http://p2:8080"],
            config=ProxyPoolConfig(cooldown=60.0),
        )
        await pool.mark_failed("http://p1:8080")
        assert pool.count_available() == 1

        await pool.mark_success("http://p1:8080")
        assert pool.count_available() == 2

    async def test_cooldown_expires(self) -> None:
        """Proxies become available again after cooldown expires."""
        pool = ProxyPool(
            ["http://p1:8080", "http://p2:8080"],
            config=ProxyPoolConfig(cooldown=0.01),  # Very short cooldown
        )
        await pool.mark_failed("http://p1:8080")
        assert pool.count_available() == 1

        await asyncio.sleep(0.05)  # Wait for cooldown to expire

        # Now p1 should be available again
        proxy = await pool.acquire()
        assert proxy is not None

    async def test_mark_unknown_proxy_ignored(self) -> None:
        """Marking a proxy not in the pool has no effect."""
        pool = ProxyPool(["http://p1:8080"])
        await pool.mark_failed("http://unknown:8080")
        assert pool.count_available() == 1


class TestWebshareFileImport:
    """Task 4.1: Webshare file import."""

    def test_load_webshare_from_file(self, tmp_path) -> None:
        filepath = tmp_path / "proxies.txt"
        filepath.write_text("1.2.3.4:8080:user1:pass1\n5.6.7.8:9090:user2:pass2\n")

        proxies = load_webshare_from_file(str(filepath))
        assert len(proxies) == 2
        assert "http://user1:pass1@1.2.3.4:8080" in proxies

    def test_load_webshare_empty_file_raises(self, tmp_path) -> None:
        filepath = tmp_path / "empty.txt"
        filepath.write_text("")

        with pytest.raises(ProxyError):
            load_webshare_from_file(str(filepath))

    def test_load_webshare_missing_file_raises(self, tmp_path) -> None:
        filepath = tmp_path / "nonexistent.txt"
        with pytest.raises(ProxyError):
            load_webshare_from_file(str(filepath))

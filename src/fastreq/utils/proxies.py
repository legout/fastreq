"""Proxy pool management with health tracking and rotation.

Provides ProxyPool for rotating explicitly-supplied proxies with per-proxy
failure cooldown and success recovery. Free-proxy discovery is NOT supported.
"""

from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import Literal

from loguru import logger


class ProxyError(Exception):
    """Raised when proxy configuration or validation fails."""


class ProxySelection(str, Enum):
    """Proxy selection strategy."""

    ROUND_ROBIN = "round_robin"
    RANDOM = "random"


def _is_valid_proxy(url: str) -> bool:
    """Check if a proxy URL has a valid scheme and netloc.

    Accepts http:// and https:// URLs, as well as bare host:port.
    """
    if not url or not isinstance(url, str):
        return False
    if url.startswith(("http://", "https://")):
        return True
    # Accept bare host:port and host:port:user:pass forms
    parts = url.split(":")
    if len(parts) == 2:
        return bool(parts[0]) and parts[1].isdigit()
    if len(parts) == 4:
        return bool(parts[0]) and parts[1].isdigit()
    return False


def _normalize_proxy_url(url: str) -> str:
    """Normalize a proxy URL to a full http:// URL if it lacks a scheme.

    - host:port → http://host:port
    - host:port:user:pass → http://user:pass@host:port
    """
    if url.startswith(("http://", "https://")):
        return url
    parts = url.split(":")
    if len(parts) == 4:
        host, port, user, pw = parts
        return f"http://{user}:{pw}@{host}:{port}"
    return f"http://{url}"


@dataclass
class ProxyPoolConfig:
    """Configuration for proxy rotation.

    Attributes:
        proxies: List of proxy URLs
        selection: Selection strategy (round_robin or random)
        cooldown: Seconds before retrying a failed proxy
    """

    proxies: list[str] | None = None
    selection: ProxySelection = ProxySelection.ROUND_ROBIN
    cooldown: float = 60.0


class ProxyPool:
    """Dependency-free proxy pool with health tracking and rotation.

    Accepts normalized URLs from constructor arguments, FASTREQ_PROXIES
    environment variable, or an explicit Webshare text source. Does NOT
    fetch free proxies.

    Supports round-robin selection by default, optional random selection
    for compatibility, per-proxy failure cooldown, and success recovery.

    Example:
        >>> pool = ProxyPool(proxies=["http://proxy1:8080", "http://proxy2:8080"])
        >>> proxy = await pool.acquire()
        >>> await pool.mark_success(proxy)

    Proxy formats supported:
        - http://host:port
        - https://host:port
        - http://user:pass@host:port
        - host:port
        - host:port:user:pass
    """

    def __init__(
        self,
        proxies: Iterable[str] | None = None,
        *,
        config: ProxyPoolConfig | None = None,
    ) -> None:
        if config is None:
            config = ProxyPoolConfig()
        self._config = config
        self._proxies: list[str] = []
        self._failed: dict[str, float] = {}  # proxy → cooldown expiry timestamp
        self._lock = asyncio.Lock()
        self._rr_index = 0
        self._load_proxies(proxies or [])

    @classmethod
    def from_webshare_text(
        cls,
        text: str,
        *,
        selection: ProxySelection = ProxySelection.ROUND_ROBIN,
        cooldown: float = 60.0,
    ) -> ProxyPool:
        """Create a ProxyPool from Webshare plain-text format.

        Webshare exports proxies as lines of 'ip:port:user:password'.
        This method normalizes them to http://user:pass@ip:port URLs.

        Args:
            text: Webshare proxy list text (one proxy per line)
            selection: Proxy selection strategy (default round_robin)
            cooldown: Seconds before retrying a failed proxy (default 60)

        Returns:
            ProxyPool instance

        Raises:
            ProxyError: If no valid proxies are found
        """
        proxies: list[str] = []
        for line in text.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(":")
            if len(parts) >= 4:
                ip, port, user, pw = parts[:4]
                proxies.append(f"http://{user}:{pw}@{ip}:{port}")
            elif len(parts) == 2:
                host, port = parts
                proxies.append(f"http://{host}:{port}")
        if not proxies:
            raise ProxyError("No valid proxies found in Webshare text")
        return cls(proxies, config=ProxyPoolConfig(selection=selection, cooldown=cooldown))

    @classmethod
    def from_env(
        cls,
        env_var: str = "FASTREQ_PROXIES",
        *,
        selection: ProxySelection = ProxySelection.ROUND_ROBIN,
        cooldown: float = 60.0,
    ) -> ProxyPool:
        """Create a ProxyPool from a comma-separated environment variable.

        Args:
            env_var: Environment variable name (default FASTREQ_PROXIES)
            selection: Proxy selection strategy (default round_robin)
            cooldown: Seconds before retrying a failed proxy (default 60)

        Returns:
            ProxyPool instance (may be empty if env var is not set)
        """
        import os

        raw = os.getenv(env_var, "")
        proxies = [p.strip() for p in raw.split(",") if p.strip()]
        return cls(proxies, config=ProxyPoolConfig(selection=selection, cooldown=cooldown))

    def _load_proxies(self, proxies: Iterable[str]) -> None:
        """Load and normalize proxies, filtering invalid entries."""
        seen: set[str] = set()
        valid = 0
        invalid = 0

        for proxy in proxies:
            if not _is_valid_proxy(proxy):
                invalid += 1
                logger.debug(f"Filtered invalid proxy format: {proxy[:50]}")
                continue
            normalized = _normalize_proxy_url(proxy)
            if normalized in seen:
                continue
            seen.add(normalized)
            self._proxies.append(normalized)
            valid += 1

        if invalid > 0:
            logger.info(f"Loaded {valid} valid proxies, filtered {invalid} invalid proxies")

    @property
    def selection(self) -> ProxySelection:
        return self._config.selection

    @property
    def cooldown(self) -> float:
        return self._config.cooldown

    @property
    def proxies(self) -> list[str]:
        """Return a copy of the normalized proxy list."""
        return self._proxies.copy()

    def count(self) -> int:
        """Total number of proxies in the pool."""
        return len(self._proxies)

    def count_available(self) -> int:
        """Number of proxies not currently in cooldown."""
        now = time.monotonic()
        return sum(1 for p in self._proxies if p not in self._failed or self._failed[p] <= now)

    async def acquire(self) -> str | None:
        """Get the next available proxy.

        Excludes proxies currently in cooldown. Uses the configured selection
        strategy (round-robin or random).

        Returns:
            Proxy URL or None if no proxies are available.
        """
        if not self._proxies:
            return None

        async with self._lock:
            now = time.monotonic()
            # Purge expired cooldowns
            self._failed = {p: t for p, t in self._failed.items() if t > now}
            available = [p for p in self._proxies if p not in self._failed]

            if not available:
                return None

            if self._config.selection == ProxySelection.RANDOM:
                return random.choice(available)

            # Round-robin among available proxies
            self._rr_index = self._rr_index % len(available)
            proxy = available[self._rr_index]
            self._rr_index = (self._rr_index + 1) % len(available)
            return proxy

    async def mark_failed(self, proxy: str) -> None:
        """Mark a proxy as failed (enter cooldown).

        Args:
            proxy: Proxy URL to mark as failed
        """
        async with self._lock:
            if proxy in self._proxies:
                self._failed[proxy] = time.monotonic() + self._config.cooldown

    async def mark_success(self, proxy: str) -> None:
        """Mark a proxy as successful (clear cooldown).

        Args:
            proxy: Proxy URL to mark as successful
        """
        async with self._lock:
            self._failed.pop(proxy, None)


def load_webshare_from_file(path: str) -> list[str]:
    """Load proxy URLs from a Webshare text file.

    Args:
        path: Path to the Webshare text file

    Returns:
        List of normalized proxy URLs

    Raises:
        ProxyError: If the file cannot be read or contains no valid proxies
    """
    try:
        with open(path) as f:
            text = f.read()
    except OSError as e:
        raise ProxyError(f"Failed to read Webshare file: {e}") from e

    proxies: list[str] = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(":")
        if len(parts) >= 4:
            ip, port, user, pw = parts[:4]
            proxies.append(f"http://{user}:{pw}@{ip}:{port}")
        elif len(parts) == 2:
            host, port = parts
            proxies.append(f"http://{host}:{port}")
    if not proxies:
        raise ProxyError(f"No valid proxies found in {path}")
    return proxies


# Selection mode type alias for API compatibility
ProxySelectionMode = Literal["round_robin", "random"]

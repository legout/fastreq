"""HTTP header management with user-agent rotation."""

from __future__ import annotations

import os
import random
from collections.abc import Iterable


class HeaderManager:
    """Manager for HTTP headers with user-agent rotation.

    Provides automatic user-agent rotation and custom header management.

    User agent sources (in order of priority):
        1. Custom user agent (if set via set_custom_user_agent)
        2. Provided user_agents list
        3. USER_AGENTS environment variable (comma-separated)
        4. Default user agents

    Args:
        random_user_agent: Enable random user-agent selection
        user_agents: Custom list of user agents (overrides defaults)
        custom_user_agent: Fixed user agent to use (overrides rotation)
    """

    DEFAULT_USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    ]

    def __init__(
        self,
        random_user_agent: bool = True,
        user_agents: list[str] | None = None,
        custom_user_agent: str | None = None,
    ) -> None:
        self._enabled = random_user_agent
        self._custom_ua = custom_user_agent
        self._agents = self._load_user_agents(user_agents)

    def _load_user_agents(self, provided: Iterable[str] | None) -> list[str]:
        if provided:
            return list(provided)

        env_agents = os.getenv("USER_AGENTS", "")
        if env_agents:
            return env_agents.split(",")

        return self.DEFAULT_USER_AGENTS.copy()

    def get_headers(
        self,
        custom_headers: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """Get headers with optional user-agent.

        Args:
            custom_headers: Additional headers to include

        Returns:
            Dictionary of headers including user-agent if enabled
        """
        headers: dict[str, str] = {}

        if self._enabled:
            if self._custom_ua:
                headers["user-agent"] = self._custom_ua
            else:
                headers["user-agent"] = random.choice(self._agents)

        if custom_headers:
            headers.update(custom_headers)

        return headers

    def set_custom_user_agent(self, user_agent: str) -> None:
        """Set fixed custom user agent (disables rotation).

        Args:
            user_agent: User agent string to use
        """
        self._custom_ua = user_agent

    def get_user_agents(self) -> list[str]:
        """Get current list of user agents.

        Returns:
            Copy of user agent list
        """
        return self._agents.copy()

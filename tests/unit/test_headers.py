"""Tests for HeaderManager — user-agent rotation and header merging.

No remote URL fetching; only local list management and environment variable.
"""

from __future__ import annotations

import pytest

from fastreq.utils.headers import HeaderManager


class TestHeaderManagerInit:
    def test_init_default_user_agents(self) -> None:
        manager = HeaderManager()
        assert len(manager.get_user_agents()) >= 8

    def test_init_custom_user_agents(self) -> None:
        custom_agents = ["Agent1/1.0", "Agent2/2.0"]
        manager = HeaderManager(user_agents=custom_agents)
        assert manager.get_user_agents() == custom_agents

    def test_init_custom_user_agent_fixed(self) -> None:
        manager = HeaderManager(custom_user_agent="MyApp/1.0")
        assert manager._custom_ua == "MyApp/1.0"

    def test_init_disabled(self) -> None:
        manager = HeaderManager(random_user_agent=False)
        assert manager._enabled is False


class TestUserAgentRotation:
    def test_random_selection(self) -> None:
        manager = HeaderManager()
        headers1 = manager.get_headers()
        headers2 = manager.get_headers()
        assert "user-agent" in headers1
        assert "user-agent" in headers2

    def test_user_agent_present(self) -> None:
        manager = HeaderManager()
        headers = manager.get_headers()
        assert "user-agent" in headers

    def test_random_different_agents(self) -> None:
        manager = HeaderManager()
        agents = set()
        for _ in range(20):
            headers = manager.get_headers()
            agents.add(headers.get("user-agent"))
        assert len(agents) > 1


class TestCustomUserAgent:
    def test_custom_list_provided(self) -> None:
        custom_agents = ["Custom/1.0"]
        manager = HeaderManager(user_agents=custom_agents)
        headers = manager.get_headers()
        assert headers["user-agent"] == "Custom/1.0"

    def test_custom_user_agent_override(self) -> None:
        manager = HeaderManager(custom_user_agent="MyApp/1.0")
        headers = manager.get_headers()
        assert headers["user-agent"] == "MyApp/1.0"

    def test_custom_user_agent_fixed_no_rotation(self) -> None:
        manager = HeaderManager(custom_user_agent="MyApp/1.0")
        headers1 = manager.get_headers()
        headers2 = manager.get_headers()
        assert headers1["user-agent"] == headers2["user-agent"]

    def test_set_custom_user_agent(self) -> None:
        manager = HeaderManager()
        manager.set_custom_user_agent("NewApp/1.0")
        headers = manager.get_headers()
        assert headers["user-agent"] == "NewApp/1.0"


class TestEnvironmentVariable:
    def test_load_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("USER_AGENTS", "Agent1,Agent2,Agent3")
        manager = HeaderManager()
        assert len(manager.get_user_agents()) == 3
        assert "Agent1" in manager.get_user_agents()

    def test_env_override_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("USER_AGENTS", "Agent1,Agent2,Agent3")
        manager = HeaderManager()
        agents = manager.get_user_agents()
        assert "Agent1" in agents
        assert "Mozilla" not in str(agents)


class TestHeaderMerging:
    def test_custom_headers_override_defaults(self) -> None:
        manager = HeaderManager()
        headers = manager.get_headers({"Authorization": "Bearer token"})
        assert headers["Authorization"] == "Bearer token"

    def test_custom_headers_preserve_user_agent(self) -> None:
        manager = HeaderManager()
        headers = manager.get_headers({"Authorization": "Bearer token"})
        assert "user-agent" in headers
        assert headers["Authorization"] == "Bearer token"

    def test_custom_user_agent_override_rotation(self) -> None:
        manager = HeaderManager(custom_user_agent="MyApp/1.0")
        headers = manager.get_headers()
        assert headers["user-agent"] == "MyApp/1.0"

    def test_no_custom_headers(self) -> None:
        manager = HeaderManager()
        headers = manager.get_headers()
        assert "user-agent" in headers
        assert len(headers) == 1

    def test_multiple_custom_headers(self) -> None:
        manager = HeaderManager()
        headers = manager.get_headers({"Authorization": "Bearer token", "X-Custom": "value"})
        assert headers["Authorization"] == "Bearer token"
        assert headers["X-Custom"] == "value"
        assert "user-agent" in headers


class TestDisabledRotation:
    def test_disabled_no_user_agent(self) -> None:
        manager = HeaderManager(random_user_agent=False)
        headers = manager.get_headers()
        assert "user-agent" not in headers

    def test_disabled_with_custom_headers(self) -> None:
        manager = HeaderManager(random_user_agent=False)
        headers = manager.get_headers({"Authorization": "Bearer token"})
        assert "user-agent" not in headers
        assert headers["Authorization"] == "Bearer token"


class TestGetUserAgents:
    def test_get_user_agents_returns_copy(self) -> None:
        manager = HeaderManager()
        agents1 = manager.get_user_agents()
        agents2 = manager.get_user_agents()
        assert agents1 == agents2
        assert agents1 is not agents2


class TestNoRemoteFetch:
    def test_no_remote_url_feature(self) -> None:
        """HeaderManager does not fetch from remote URLs."""
        manager = HeaderManager()
        assert not hasattr(manager, "update_agents_from_remote")
        assert not hasattr(manager, "_fetch_remote_agents")

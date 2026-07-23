"""Tests for GlobalConfig with FASTREQ_ prefix and no free-proxy fields."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from fastreq.config import GlobalConfig


class TestGlobalConfigDefaults:
    def test_default_values(self) -> None:
        config = GlobalConfig()
        assert config.backend == "auto"
        assert config.default_concurrency == 20
        assert config.default_max_retries == 3
        assert config.rate_limit is None
        assert config.rate_limit_burst == 5
        assert config.http2_enabled is True
        assert config.random_user_agent is True
        assert config.random_proxy is False


class TestLoadFromEnv:
    def test_load_from_env_with_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("FASTREQ_BACKEND", raising=False)
        monkeypatch.delenv("FASTREQ_CONCURRENCY", raising=False)
        monkeypatch.delenv("FASTREQ_MAX_RETRIES", raising=False)
        monkeypatch.delenv("FASTREQ_HTTP2", raising=False)
        monkeypatch.delenv("FASTREQ_RANDOM_USER_AGENT", raising=False)
        monkeypatch.delenv("FASTREQ_RANDOM_PROXY", raising=False)

        config = GlobalConfig.load_from_env()

        assert config.backend == "auto"
        assert config.default_concurrency == 20
        assert config.default_max_retries == 3
        assert config.http2_enabled is True
        assert config.random_user_agent is True
        assert config.random_proxy is False

    def test_load_from_env_custom_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FASTREQ_BACKEND", "niquests")
        monkeypatch.setenv("FASTREQ_CONCURRENCY", "50")
        monkeypatch.setenv("FASTREQ_MAX_RETRIES", "5")
        monkeypatch.setenv("FASTREQ_HTTP2", "false")
        monkeypatch.setenv("FASTREQ_RANDOM_USER_AGENT", "false")
        monkeypatch.setenv("FASTREQ_RANDOM_PROXY", "true")

        config = GlobalConfig.load_from_env()

        assert config.backend == "niquests"
        assert config.default_concurrency == 50
        assert config.default_max_retries == 5
        assert config.http2_enabled is False
        assert config.random_user_agent is False
        assert config.random_proxy is True

    def test_load_from_env_rate_limit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FASTREQ_RATE_LIMIT", "10.5")
        monkeypatch.setenv("FASTREQ_RATE_LIMIT_BURST", "10")

        config = GlobalConfig.load_from_env()

        assert config.rate_limit == 10.5
        assert config.rate_limit_burst == 10


class TestToEnv:
    def test_to_env_contains_all_fields(self) -> None:
        config = GlobalConfig()
        env = config.to_env()

        assert "FASTREQ_BACKEND" in env
        assert "FASTREQ_CONCURRENCY" in env
        assert "FASTREQ_MAX_RETRIES" in env
        assert "FASTREQ_RATE_LIMIT" in env
        assert "FASTREQ_RATE_LIMIT_BURST" in env
        assert "FASTREQ_HTTP2" in env
        assert "FASTREQ_RANDOM_USER_AGENT" in env
        assert "FASTREQ_RANDOM_PROXY" in env
        assert "FASTREQ_PROXIES" in env

    def test_to_env_custom_values(self) -> None:
        config = GlobalConfig(
            backend="niquests",
            default_concurrency=50,
            http2_enabled=False,
            random_user_agent=False,
        )
        env = config.to_env()

        assert env["FASTREQ_BACKEND"] == "niquests"
        assert env["FASTREQ_CONCURRENCY"] == "50"
        assert env["FASTREQ_HTTP2"] == "false"
        assert env["FASTREQ_RANDOM_USER_AGENT"] == "false"

    def test_to_env_bool_values_are_lowercase(self) -> None:
        config = GlobalConfig()
        env = config.to_env()

        assert env["FASTREQ_HTTP2"] == "true"
        assert env["FASTREQ_RANDOM_USER_AGENT"] == "true"
        assert env["FASTREQ_RANDOM_PROXY"] == "false"

    def test_to_env_rate_limit_empty_when_none(self) -> None:
        config = GlobalConfig()
        env = config.to_env()

        assert env["FASTREQ_RATE_LIMIT"] == ""


class TestSaveToEnv:
    def test_save_to_env_creates_file(self) -> None:
        config = GlobalConfig(backend="niquests", default_concurrency=50)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            path = Path(f.name)

        try:
            config.save_to_env(path)
            content = path.read_text()
            assert "FASTREQ_BACKEND=niquests" in content
            assert "FASTREQ_CONCURRENCY=50" in content
        finally:
            path.unlink()

    def test_save_to_env_omits_empty_values(self) -> None:
        config = GlobalConfig(rate_limit=None)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            path = Path(f.name)

        try:
            config.save_to_env(path)
            content = path.read_text()
            lines = content.strip().split("\n")
            assert not any(line.startswith("FASTREQ_RATE_LIMIT=") for line in lines)
        finally:
            path.unlink()

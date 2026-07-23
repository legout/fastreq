"""Global configuration for fastreq.

Can be loaded from environment variables or created programmatically.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class GlobalConfig:
    """Global configuration for fastreq.

    Can be loaded from environment variables or created programmatically.

    Environment variables (prefix FASTREQ_):
        FASTREQ_BACKEND: Backend to use ("auto", "niquests", "httpx")
        FASTREQ_CONCURRENCY: Default concurrency limit
        FASTREQ_MAX_RETRIES: Default max retries
        FASTREQ_RATE_LIMIT: Rate limit (requests per second)
        FASTREQ_RATE_LIMIT_BURST: Rate limit burst size
        FASTREQ_HTTP2: Enable HTTP/2 (true/false)
        FASTREQ_RANDOM_USER_AGENT: Rotate user agents (true/false)
        FASTREQ_RANDOM_PROXY: Enable proxy rotation (true/false)
        FASTREQ_PROXIES: Comma-separated proxy URLs

    Attributes:
        backend: Default backend selection
        default_concurrency: Default concurrency limit
        default_max_retries: Default maximum retry attempts
        rate_limit: Rate limit in requests per second (None for no limit)
        rate_limit_burst: Burst size for rate limiter
        http2_enabled: Enable HTTP/2 support
        random_user_agent: Enable user agent rotation
        random_proxy: Enable proxy rotation
        proxies: Comma-separated proxy URLs
    """

    backend: str = "auto"
    default_concurrency: int = 20
    default_max_retries: int = 3
    rate_limit: float | None = None
    rate_limit_burst: int = 5
    http2_enabled: bool = True
    random_user_agent: bool = True
    random_proxy: bool = False
    proxies: str | None = None

    @classmethod
    def load_from_env(cls, prefix: str = "FASTREQ_") -> GlobalConfig:
        """Load configuration from environment variables.

        Args:
            prefix: Environment variable prefix (default FASTREQ_)

        Returns:
            GlobalConfig instance
        """
        import os

        def get_bool(key: str, default: bool) -> bool:
            value = os.getenv(f"{prefix}{key}", str(default).lower())
            return value.lower() == "true"

        def get_int(key: str, default: int) -> int:
            value = os.getenv(f"{prefix}{key}")
            return int(value) if value is not None else default

        def get_float(key: str, default: float | None) -> float | None:
            value = os.getenv(f"{prefix}{key}")
            return float(value) if value is not None else default

        return cls(
            backend=os.getenv(f"{prefix}BACKEND", "auto"),
            default_concurrency=get_int("CONCURRENCY", 20),
            default_max_retries=get_int("MAX_RETRIES", 3),
            rate_limit=get_float("RATE_LIMIT", None),
            rate_limit_burst=get_int("RATE_LIMIT_BURST", 5),
            http2_enabled=get_bool("HTTP2", True),
            random_user_agent=get_bool("RANDOM_USER_AGENT", True),
            random_proxy=get_bool("RANDOM_PROXY", False),
            proxies=os.getenv(f"{prefix}PROXIES"),
        )

    def to_env(self, prefix: str = "FASTREQ_") -> dict[str, str]:
        """Convert config to environment variable dictionary.

        Args:
            prefix: Prefix for environment variable names

        Returns:
            Dictionary of environment variable name to value
        """
        env: dict[str, str] = {
            f"{prefix}BACKEND": self.backend,
            f"{prefix}CONCURRENCY": str(self.default_concurrency),
            f"{prefix}MAX_RETRIES": str(self.default_max_retries),
            f"{prefix}RATE_LIMIT": str(self.rate_limit) if self.rate_limit else "",
            f"{prefix}RATE_LIMIT_BURST": str(self.rate_limit_burst),
            f"{prefix}HTTP2": str(self.http2_enabled).lower(),
            f"{prefix}RANDOM_USER_AGENT": str(self.random_user_agent).lower(),
            f"{prefix}RANDOM_PROXY": str(self.random_proxy).lower(),
            f"{prefix}PROXIES": self.proxies or "",
        }
        return env

    def save_to_env(self, path: Path | str, prefix: str = "FASTREQ_") -> None:
        """Save configuration to an environment file.

        Args:
            path: Path to save the .env file
            prefix: Prefix for environment variable names
        """
        p = Path(path) if isinstance(path, str) else path
        env_content = ""
        for key, value in self.to_env(prefix).items():
            if value:
                env_content += f"{key}={value}\n"
        p.write_text(env_content)

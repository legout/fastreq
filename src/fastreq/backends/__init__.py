from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

from .base import Backend, NormalizedResponse, RequestConfig, TransportKey

if TYPE_CHECKING:
    from .curl_cffi import CurlCffiBackend
    from .httpx import HttpxBackend
    from .niquests import NiquestsBackend


_LAZY_BACKENDS: dict[str, tuple[str, str]] = {
    "NiquestsBackend": ("niquests", "NiquestsBackend"),
    "HttpxBackend": ("httpx", "HttpxBackend"),
    "CurlCffiBackend": ("curl_cffi", "CurlCffiBackend"),
}

__all__ = [
    "Backend",
    "CurlCffiBackend",
    "HttpxBackend",
    "NiquestsBackend",
    "NormalizedResponse",
    "RequestConfig",
    "TransportKey",
]


def __getattr__(name: str) -> object:
    lazy_backend = _LAZY_BACKENDS.get(name)
    if lazy_backend is None:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    backend_module, backend_class = lazy_backend
    module = importlib.import_module(f"{__name__}.{backend_module}")
    return getattr(module, backend_class)


def __dir__() -> list[str]:
    return sorted(set(globals().keys()) | set(__all__))

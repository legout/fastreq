"""fastreq — High-performance async HTTP client built on niquests and httpx.

Basic usage:

    >>> from fastreq import fastreq
    >>> results = fastreq(urls=["https://api.github.com/repos/python/cpython"])

Async usage:

    >>> import asyncio
    >>> from fastreq import fastreq_async
    >>> async def main():
    ...     return await fastreq_async(urls=["https://httpbin.org/get"])
    >>> asyncio.run(main())

Features:
    - niquests (default) and httpx (optional) transports
    - HTTP/2 support
    - Exponential backoff with jitter
    - Token bucket rate limiting (rate token acquired before concurrency slot)
    - Explicit proxy pools with health tracking and cooldown
    - User-agent rotation
    - Session cookie management
    - Flexible response parsing (JSON, text, content, response, stream)
    - Custom parse functions
    - Keyed response mapping
    - Graceful failure handling
"""

from fastreq.backends.base import Backend, NormalizedResponse, RequestConfig, TransportKey
from fastreq.client import (
    FastRequests,
    RequestOptions,
    ReturnType,
    fastreq,
    fastreq_async,
)
from fastreq.config import GlobalConfig
from fastreq.exceptions import (
    BackendError,
    ConfigurationError,
    FailureDetails,
    FastRequestsError,
    PartialFailureError,
    ProxyError,
    RateLimitExceededError,
    RetryableResponse,
    RetryExhaustedError,
    ValidationError,
)

__version__ = "3.0.0"

__all__ = [
    "Backend",
    "BackendError",
    "ConfigurationError",
    "FailureDetails",
    "FastRequests",
    "FastRequestsError",
    "GlobalConfig",
    "NormalizedResponse",
    "ParallelRequests",
    "ParallelRequestsError",
    "PartialFailureError",
    "ProxyError",
    "RateLimitExceededError",
    "RequestConfig",
    "RequestOptions",
    "RetryExhaustedError",
    "RetryableResponse",
    "ReturnType",
    "TransportKey",
    "ValidationError",
    "__version__",
    "fastreq",
    "fastreq_async",
]

# Backwards-compatibility aliases
ParallelRequestsError = FastRequestsError
ParallelRequests = FastRequests

# fastreq 3.0.0

[![PyPI Version](https://img.shields.io/pypi/v/fastreq)](https://pypi.org/project/fastreq/)
[![Python Version](https://img.shields.io/pypi/pyversions/fastreq)](https://pypi.org/project/fastreq/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

High-performance async HTTP client built on **niquests** (default) and **httpx** (optional).

## Features

- **Two transports**: niquests (default, required) and httpx (optional extra)
- **HTTP/2 support** via niquests/qh3 (always) and httpx+hyper (when h2 installed)
- **Explicit proxy pools** with health tracking, cooldown, round-robin rotation, and Webshare import — no free-proxy discovery
- **Token-bucket rate limiting** — rate token acquired *before* the concurrency slot
- **Typed retry** — only transient transport errors and configured retryable status codes (429, 500, 502, 503, 504); honors `Retry-After`
- **User-agent rotation** from a built-in list or custom list
- **Cookie management** with session-scoped, proxy-isolated storage
- **Chunked streaming** via callbacks in both transports
- **Flexible response parsing** — JSON, text, content, response object, or stream
- **Keyed responses** for dict-style result mapping

## Installation

```bash
# Core library (niquests is the default and required transport)
pip install fastreq

# With HTTPX as an alternative transport
pip install fastreq[httpx]

# With HTTP/2 support for httpx (niquests supports HTTP/2 natively)
pip install fastreq[httpx,h2]
```

## Quick Start

### Sync Usage

```python
from fastreq import fastreq

result = fastreq("https://api.github.com/repos/python/cpython")
print(result)
```

### Async Usage

```python
import asyncio
from fastreq import fastreq_async

async def main():
    results = await fastreq_async([
        "https://api.github.com/repos/python/cpython",
        "https://api.github.com/repos/python/cpython/issues",
    ], concurrency=5)
    return results

results = asyncio.run(main())
```

### Context Manager

```python
from fastreq import FastRequests

async def main():
    async with FastRequests(concurrency=5) as client:
        result = await client.request("https://api.github.com/repos/python/cpython")
    return result
```

### Streaming

```python
from fastreq import FastRequests, ReturnType

async def main():
    async with FastRequests() as client:
        await client.request(
            "https://example.com/large-file.zip",
            return_type=ReturnType.STREAM,
            stream_callback=lambda chunk: print(f"Got {len(chunk)} bytes"),
        )
```

### Explicit Proxy Rotation

```python
from fastreq import FastRequests

# Provide a proxy list directly
proxies = [
    "http://user:pass@proxy1:8080",
    "http://user:pass@proxy2:8080",
]

async with FastRequests(
    proxies=proxies,
    random_proxy=True,
    proxy_selection="round_robin",
    proxy_cooldown=60.0,
) as client:
    result = await client.request("https://api.example.com/data")
```

You can also set proxies via the `FASTREQ_PROXIES` environment variable (comma-separated) or import from a Webshare text file via `webshare_file=`.

## Backend Selection

| Backend   | Status   | HTTP/2  | Install                     |
|-----------|----------|---------|-----------------------------|
| niquests  | Default  | Native  | `pip install fastreq`       |
| httpx     | Optional | h2 dep  | `pip install fastreq[httpx]`|
| curl_cffi | Optional | Native  | `pip install fastreq[curl]` |

`backend="auto"` (the default) always selects niquests. To use another backend explicitly:

```python
FastRequests(backend="httpx")
```

### Browser impersonation (curl_cffi backend)

The `curl_cffi` backend can replicate a real browser's TLS fingerprint
(JA3/JA4), HTTP/2 settings, and default headers via the `impersonate`
parameter. This defeats bot detection that blocks plain HTTP clients:

```python
async with FastRequests(backend="curl_cffi", impersonate="chrome") as client:
    result = await client.request("https://example.com/bot-protected")

# or a random recent browser target per client
FastRequests(backend="curl_cffi", impersonate="random")
```

When `impersonate` is set, user-agent rotation is disabled automatically —
curl_cffi supplies the browser-matching User-Agent itself. One session is
kept per proxy route, so cookies stay isolated between proxies.

## Migration from 2.x to 3.0

### Breaking changes

- **Removed backends**: `aiohttp` and `requests` transports are gone. Use `niquests` (default) or `httpx`.
- **Removed free proxies**: The library no longer discovers or fetches free proxies. Provide explicit proxies via `proxies=`, `FASTREQ_PROXIES`, or `webshare_file=`.
- **Canonical name**: The project is now `fastreq` (previously `parallel-requests`). `ParallelRequests` remains as a Python alias for backward compatibility.

### What to do

1. If you used `backend="aiohttp"` or `backend="requests"`, switch to the default niquests transport or install `fastreq[httpx]` and use `backend="httpx"`.
2. If you used `free_proxies=True`, remove it and provide an explicit proxy list or Webshare source instead.
3. If you imported `ParallelRequests`, it still works as an alias — but the canonical name is `FastRequests`.

## Proxy Policy

fastreq 3.0 does not fetch free proxies. Proxy sources in priority order:

1. `proxies=` constructor argument (list of URLs)
2. `FASTREQ_PROXIES` environment variable (comma-separated)
3. `webshare_file=` path to a Webshare plain-text proxy file (`ip:port:user:password` per line)

Failed proxies enter a configurable cooldown. Successful requests clear the cooldown. Selection strategies: `round_robin` (default) or `random`.

## Documentation

- [Full Documentation](https://legout.github.io/fastreq/)
- [Examples](https://github.com/legout/fastreq/tree/main/examples)

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management and packaging.

```bash
# Install all dependencies
uv sync --all-groups

# Run quality gates
uv run ruff format --check .
uv run ruff check .
uv run ty check src
uv run pytest -q

# Build
uv build
```

## License

MIT License — see [LICENSE](https://github.com/legout/fastreq/blob/main/LICENSE).

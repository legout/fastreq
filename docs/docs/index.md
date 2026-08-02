# fastreq

A high-performance async HTTP client built on [niquests](https://niquests.readthedocs.io/) and [httpx](https://www.python-httpx.org/), with optional [curl_cffi](https://github.com/yifeikong/curl_cffi) for browser TLS impersonation. Concurrent execution, exponential-backoff retries, proxy rotation, rate limiting, user-agent rotation, and flexible response parsing — sync or async.

## Features

- **Concurrent Execution**: Run many requests in parallel with a single async/sync gate. Sync wrapper uses `asyncio.run` under the hood; async wrapper returns an awaitable.
- **Three Backends**: `niquests` (default, required), `httpx` (optional, `pip install fastreq[httpx]`), `curl_cffi` (optional, `pip install fastreq[curl]`). Auto-detection picks `niquests`.
- **Retry with Backoff**: Exponential backoff with jitter, configurable per-request `retry_on` / `dont_retry_on` exception lists.
- **Proxy Rotation**: Explicit proxy pools with health tracking and cooldown. Optional Webshare.io text-file integration.
- **Rate Limiting**: Token bucket — a rate token is acquired *before* a concurrency slot, so rate limits are honored even under burst.
- **Browser TLS Impersonation**: `impersonate="chrome131"` etc. via curl_cffi to defeat JA3-based bot detection.
- **HTTP/2**: Built-in to niquests; opt-in for httpx via `pip install fastreq[h2]`.
- **User-Agent Rotation**: Disabled automatically when `impersonate` is set (curl_cffi supplies the matching UA).
- **Cookie Management**: Session-based `set_cookies()` / `reset_cookies()`.
- **Response Parsing**: JSON, text, content, response, stream, or a custom `parse_func`.
- **Graceful Failure**: `return_none_on_failure=True` and `keys=` for dict-mapped results.
- **Optional Progress Reporting**: `pip install fastreq[progress-rich]` (rich) or `pip install fastreq[progress-tqdm]` (tqdm).

## Installation

```bash
# Core: niquests-backed, sync + async
pip install fastreq

# Add httpx backend (HTTP/2 with the [h2] extra)
pip install fastreq[httpx,h2]

# Add curl_cffi backend (browser TLS impersonation)
pip install fastreq[curl]

# Optional progress bars
pip install fastreq[progress-rich]   # or progress-tqdm
```

## Quick Start

```python
from fastreq import fastreq

results = fastreq(
    urls=[
        "https://api.github.com/repos/python/cpython",
        "https://api.github.com/repos/python/cpython/issues",
        "https://api.github.com/repos/python/cpython/pulls",
    ],
    concurrency=3,
)

for r in results:
    print(r.json()["full_name"])
```

## Async Usage

```python
import asyncio
from fastreq import fastreq_async

async def main():
    return await fastreq_async(
        urls=["https://httpbin.org/delay/1"] * 3,
        concurrency=5,
        timeout=10,
    )

asyncio.run(main())
```

## When to Reach for curl_cffi

```python
from fastreq import fastreq

# Impersonate a real Chrome to bypass JA3-based bot detection
results = fastreq(
    urls=["https://finance.yahoo.com/quote/AAPL"] * 20,
    backend="curl_cffi",
    impersonate="chrome131",   # or "random"
    concurrency=10,
)
```

## Quick Links

### New Users

- [Getting Started Tutorial](tutorials/getting-started.md) — install + first parallel requests
- [Examples on GitHub](https://github.com/legout/fastreq/tree/main/examples) — runnable scripts

### Common Tasks

- [Make Parallel Requests](how-to-guides/make-parallel-requests.md)
- [Handle Rate Limits](how-to-guides/limit-request-rate.md)
- [Configure Retries](how-to-guides/handle-retries.md)
- [Use Proxies](how-to-guides/use-proxies.md)
- [Select a Backend](how-to-guides/select-backend.md)
- [Impersonate a Browser](how-to-guides/use-impersonate.md)
- [Show Progress Bars](how-to-guides/progress-reporting.md)

### API Reference

- [API Overview](reference/index.md)
- [`FastRequests` class](reference/api/fastrequests.md) &nbsp;·&nbsp; [`fastreq()`](reference/api/fastreq.md) &nbsp;·&nbsp; [`fastreq_async()`](reference/api/fastreq_async.md)
- [Backends](reference/backend.md) &nbsp;·&nbsp; [Exceptions](reference/exceptions.md) &nbsp;·&nbsp; [Configuration](reference/configuration.md)

# Backends

fastreq ships three pluggable HTTP backends behind one interface. They share the same surface so you can swap one for another without rewriting call sites.

## Why three?

The right HTTP client depends on the target:

- **niquests** — the required default. Best general performance, HTTP/2 built-in, both sync and async.
- **httpx** — opt-in alternative for codebases that already use httpx everywhere.
- **curl_cffi** — opt-in for TLS-fingerprint impersonation against sites that block plain HTTP clients.

All three implement the same [`Backend`][fastreq.backends.Backend] abstract class, so the rest of fastreq (concurrency gate, retry policy, rate limiter, proxy manager) is backend-agnostic.

## The contract

Every backend implements the same three methods (see [`Backend`][fastreq.backends.Backend]):

```python
class Backend(ABC):
    async def request(self, config: RequestConfig) -> NormalizedResponse: ...
    async def close(self) -> None: ...
    def supports_http2(self) -> bool: ...
```

Backends normalize their responses into a [`NormalizedResponse`][fastreq.backends.NormalizedResponse] that downstream code consumes uniformly. That means switching backends does not change return-type handling, retry behaviour, or response parsing.

## Auto-detection

```python
from fastreq import fastreq

results = fastreq(urls=["https://httpbin.org/get"], backend="auto")
```

`backend="auto"` (the default) selects **niquests**. niquests is a required dependency so it is always available; the other two are opt-in via extras.

| Extra | Backend | Install |
|---|---|---|
| (none — core) | `niquests` | `pip install fastreq` |
| `httpx` (+ `h2`) | `httpx` | `pip install fastreq[httpx,h2]` |
| `curl` | `curl_cffi` | `pip install fastreq[curl]` |

## HTTP/2

| Backend | HTTP/2 by default | Notes |
|---|---|---|
| `niquests` | ✅ | Always on for HTTPS endpoints |
| `httpx` | opt-in | Requires `pip install fastreq[h2]` |
| `curl_cffi` | ✅ | Via the impersonated browser's settings |

When `http2=True` is requested but the backend does not support it, fastreq downgrades silently and logs at DEBUG level.

## Browser impersonation (curl_cffi only)

Only the curl_cffi backend supports `impersonate=`. Pass a target like `"chrome131"`, `"safari184"`, or `"random"`. See [Impersonate a Browser](../how-to-guides/use-impersonate.md).

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://finance.yahoo.com/quote/AAPL"] * 20,
    backend="curl_cffi",
    impersonate="chrome131",
    concurrency=10,
)
```

User-agent rotation is disabled automatically when `impersonate` is set, since curl_cffi supplies a matching UA.

## Sync vs async

- `niquests` supports both sync and async natively.
- `httpx` and `curl_cffi` are async-only. fastreq's `fastreq()` sync wrapper runs the async client via `asyncio.run` for you, so both forms are exposed as a uniform API.

## Removed backends

`aiohttp` and `requests` were removed in fastreq 3.0. Selecting either raises `ConfigurationError` with a migration hint:

```
BackendError: Backend 'aiohttp' is no longer supported in fastreq 3.0.
Use 'niquests' (default) or 'httpx' instead.
Install with: pip install fastreq[httpx]
```

## When to choose which

- **Default to `niquests`** for APIs and clean-network targets. Fastest, simplest.
- **Choose `httpx`** if your codebase already speaks httpx or you need a transport that integrates with httpx's ecosystem (custom auth, retry helpers).
- **Choose `curl_cffi`** when sites reject plain HTTP clients based on TLS fingerprint (Cloudflare / Akamai / Yahoo Finance style detection). Slowest of the three.

## See also

- [Select Backend](../how-to-guides/select-backend.md)
- [Impersonate a Browser](../how-to-guides/use-impersonate.md)
- [Backend API reference](../reference/backend.md)

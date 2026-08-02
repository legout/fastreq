# Select Backend

How to choose between **niquests**, **httpx**, and **curl_cffi**.

## Quick decision

| If you need… | Use |
|---|---|
| HTTP/2, sync + async, best general performance | `niquests` (default — always available) |
| Same API as `httpx` elsewhere in your project | `httpx` (install `pip install fastreq[httpx]`) |
| Bypass JA3 / TLS-fingerprint bot detection | `curl_cffi` with `impersonate="..."` (install `pip install fastreq[curl]`) |

## Backend auto-detection

```python
from fastreq import fastreq

results = fastreq(urls=["https://httpbin.org/get"], backend="auto")
```

`backend="auto"` (the default) always selects **`niquests`**. niquests is a required dependency, so it is always present. To use another backend you must install its extra and pass the name explicitly.

The strings `"aiohttp"` and `"requests"` are **removed** in fastreq 3.x — passing them raises `ConfigurationError`.

## Explicit backend selection

```python
from fastreq import fastreq

# niquests (default; required)
results = fastreq(urls=["https://httpbin.org/get"], backend="niquests")

# httpx (install with: pip install fastreq[httpx])
results = fastreq(urls=["https://httpbin.org/get"], backend="httpx")

# curl_cffi (install with: pip install fastreq[curl])
results = fastreq(urls=["https://httpbin.org/get"], backend="curl_cffi")
```

## Feature comparison

| Feature | niquests | httpx | curl_cffi |
|---|---|---|---|
| HTTP/2 | ✅ built-in | ✅ with `pip install fastreq[h2]` | ✅ built-in |
| Async native | ✅ | ✅ | ✅ |
| Sync native | ✅ | ❌ use `fastreq()` wrapper | ❌ use `fastreq()` wrapper |
| Browser TLS impersonation | ❌ | ❌ | ✅ via `impersonate=` |
| Connection pooling | ✅ | ✅ | ✅ |
| Cookies | ✅ | ✅ | ✅ |
| Proxies | ✅ | ✅ | ✅ |
| Session reuse via context manager | ✅ | ✅ | ✅ |

## When to use each backend

### niquests — the default

Reach for niquests first. It is the only backend available without an extra install, supports HTTP/2 out of the box, and exposes the most mature async + sync story.

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://api.example.com/data"] * 100,
    backend="niquests",
    concurrency=50,
)
```

### httpx — drop-in for httpx-shaped code

Pick httpx if you already use httpx elsewhere and want one transport model across the codebase. HTTP/2 requires `pip install fastreq[h2]`.

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://api.example.com/data"] * 100,
    backend="httpx",
    concurrency=50,
)
```

### curl_cffi — bypass JA3 / TLS-fingerprint detection

Pick curl_cffi when sites reject plain HTTP clients based on TLS handshake fingerprint (Yahoo Finance, Cloudflare-protected endpoints, etc.). Combine with `impersonate` to replicate a real browser. See [Impersonate a Browser](use-impersonate.md).

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://finance.yahoo.com/quote/AAPL"] * 20,
    backend="curl_cffi",
    impersonate="chrome131",
    concurrency=10,
)
```

## HTTP/2

```python
from fastreq import fastreq

# niquests: HTTP/2 on by default
results = fastreq(urls=["https://httpbin.org/get"] * 10, backend="niquests")

# httpx: requires the [h2] extra
results = fastreq(urls=["https://httpbin.org/get"] * 10, backend="httpx")

# curl_cffi: HTTP/2 via the impersonated browser
results = fastreq(
    urls=["https://httpbin.org/get"] * 10,
    backend="curl_cffi",
    impersonate="chrome131",
)
```

**Why HTTP/2 helps:** multiplexing, header compression (HPACK), and better handling of many concurrent requests over a single connection.

## Detect-availability helper

There is no public `get_available_backends()` helper. Instead, attempt imports yourself or just rely on the error message — `fastreq` raises `BackendError` if you select a backend whose dependency is not installed.

```python
from importlib.util import find_spec

def available(name: str) -> bool:
    return find_spec(name) is not None

print("httpx:", available("httpx"))
print("curl_cffi:", available("curl_cffi"))
```

## Backend-specific configuration

Backends share the same `FastRequests` surface. There are no per-backend keyword arguments beyond `impersonate` (curl_cffi only).

```python
from fastreq import FastRequests

client = FastRequests(
    backend="curl_cffi",
    impersonate="safari184",
    concurrency=20,
)
```

## Session reuse with context manager

All three backends support session reuse — same connection pool across multiple `request()` calls inside one `async with`:

```python
import asyncio
from fastreq import FastRequests

async def reuse_session():
    async with FastRequests(backend="niquests") as client:
        r1 = await client.request(urls=["https://api.github.com/repos/python/cpython"])
        r2 = await client.request(urls=["https://api.github.com/repos/python/pypy"])
        return r1, r2

asyncio.run(reuse_session())
```

## Backend selection strategy

### Production

Let `auto` pick niquests, or pin `backend="niquests"` explicitly:

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://api.example.com/data"] * 100,
    backend="auto",
    concurrency=20,
)
```

### Bot-detection bypass

Pin curl_cffi with a concrete impersonation target:

```python
results = fastreq(
    urls=["https://finance.yahoo.com/quote/AAPL"] * 50,
    backend="curl_cffi",
    impersonate="chrome131",
    concurrency=10,
)
```

## Best practices

1. **Default to `niquests`** unless you have a concrete reason to swap.
2. **Install extras explicitly**: `pip install fastreq[httpx,h2]` or `pip install fastreq[curl]`.
3. **Use curl_cffi only when JA3 detection is the blocker** — it is the slowest of the three because every request sets up a fresh TLS fingerprint.
4. **Reuse sessions** with the async context manager for connection-pool benefits.
5. **Catch `BackendError`** if you support optional backends — it fires when a selected backend's dependency is missing.

## See also

- [Make Parallel Requests](make-parallel-requests.md) — request configuration
- [Impersonate a Browser](use-impersonate.md) — curl_cffi TLS fingerprints
- [Backend API reference](../reference/backend.md)

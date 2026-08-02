# Impersonate a Browser

How to use the **curl_cffi** backend to bypass JA3 / TLS-fingerprint bot detection.

## Why impersonation?

Plain HTTP clients (httpx, niquests, requests) advertise themselves with a TLS handshake that real browsers don't send. Sites running **Cloudflare**, **Akamai**, or in-house bot detection can reject these clients at the TLS layer before any HTTP traffic flows. This is *not* about User-Agent headers — those are easy to spoof. The fingerprint that matters is the JA3 / JA4 hash derived from the TLS handshake, the HTTP/2 SETTINGS frame, and a few other protocol-level details.

`curl_cffi` solves this by replicating a real browser's TLS fingerprint end-to-end. fastreq exposes it through a single parameter: `impersonate=`.

## Install

```bash
pip install fastreq[curl]
```

This pulls in `curl-cffi >= 0.13` alongside the core fastreq install.

## Basic impersonation

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://finance.yahoo.com/quote/AAPL"] * 20,
    backend="curl_cffi",
    impersonate="chrome131",
    concurrency=10,
)
```

When `impersonate` is set:

- User-agent rotation is **automatically disabled** — curl_cffi supplies the browser-matching User-Agent.
- HTTP/2 SETTINGS match the chosen browser.
- TLS cipher suites, extensions, and ALPN match.

## Choosing an impersonation target

You can pass any curl_cffi-supported target string. A small set of recent desktop targets is bundled in `IMPERSONATE_TARGETS`:

```python
from fastreq.backends.curl_cffi import IMPERSONATE_TARGETS
print(IMPERSONATE_TARGETS)
# ['chrome131', 'chrome133a', 'chrome136',
#  'safari180', 'safari184',
#  'firefox133', 'firefox135']
```

Or pass `"random"` to pick a different one per session:

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://example.com/"] * 50,
    backend="curl_cffi",
    impersonate="random",
    concurrency=10,
)
```

If you pass a string that is not in `IMPERSONATE_TARGETS` and not `"random"`, curl_cffi validates it on the wire — typos raise `curl_cffi.errors.ImpersonateError`.

## Environment variable

Set the default impersonation target globally without touching call sites:

```bash
export FASTREQ_IMPERSONATE=chrome131
```

```python
from fastreq import fastreq

# No impersonate= here — the env var supplies it
results = fastreq(urls=["https://example.com/"], backend="curl_cffi")
```

## Async API

Same surface, just async:

```python
import asyncio
from fastreq import fastreq_async, FastRequests

async def fetch():
    async with FastRequests(backend="curl_cffi", impersonate="chrome136") as client:
        return await client.request(urls=["https://example.com/data"])

asyncio.run(fetch())
```

## Combine with proxies

curl_cffi routes impersonated traffic through the same proxy pool as the rest of fastreq:

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://finance.yahoo.com/quote/AAPL"] * 30,
    backend="curl_cffi",
    impersonate="chrome131",
    proxies=["http://user:pass@proxy1:8080", "http://user:pass@proxy2:8080"],
    proxy_selection="round_robin",
    concurrency=15,
)
```

Sessions are cached per `(proxy, impersonate)` combination, so cookie jars stay isolated.

## When NOT to impersonate

- **APIs that already accept your real client** — curl_cffi is the slowest of the three backends because every request builds a real-browser TLS profile. Stick with `niquests` (default) for normal API work.
- **Authenticated browser flows** that depend on JavaScript — curl_cffi is a TLS-only mimic. It does not execute JavaScript.
- **Targets that fingerprint via IP reputation** — use `proxies=` rotation instead.

## Troubleshooting

**`ImportError: curl_cffi is not installed`** — you forgot `pip install fastreq[curl]`.

**`curl_cffi.errors.ImpersonateError`** — the target string is wrong. Run `IMPERSONATE_TARGETS` to see valid choices, or omit the value to disable impersonation.

**403 / 429 even with `impersonate`** — JA3 wasn't the only signal. Try rotating the target (`impersonate="random"`) and combining with proxy rotation.

## See also

- [Select Backend](select-backend.md) — when to reach for curl_cffi
- [Use Proxies](use-proxies.md) — proxy rotation
- [`FastRequests` reference](../reference/api/fastrequests.md) — full `impersonate=` documentation

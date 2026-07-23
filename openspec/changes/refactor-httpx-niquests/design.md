# Design: HTTPX/niquests transport core

## Context

fastreq has a valuable public API and useful policy primitives, but its four backends drifted. Client concurrency is currently passed into backend constructors that do not accept it. Proxy rotation and header rotation are unconnected utility modules. HTTPX 0.28 no longer accepts the current request-level `proxies=` parameter.

## Goals

- A small, reliable async client with niquests as default and HTTPX as the only alternative.
- Preserve useful API behavior without preserving broken internals.
- Make explicit proxy rotation production-safe: user-provided/Webshare sources only, health tracking, cooldowns, no free-proxy discovery.
- Support Python 3.14 and hermetic test execution.
- Provide an API suitable for yfin's stateful Yahoo cookie/crumb sessions.

## Non-goals

- aiohttp or requests support.
- Free-proxy scraping or automated anonymous-proxy discovery.
- Browser fingerprint impersonation or bypass-oriented behavior.
- A generic distributed rate limiter.
- Backward compatibility for removed backend names or free-proxy settings.

## Decisions

### One client owns policies

`FastRequests` owns a single semaphore and a token bucket. It awaits the token first, then acquires the concurrency slot, executes one request, and releases the slot. Transport classes only manage sessions and convert `RequestConfig` to a response or byte stream.

### Two explicit transports

`NiquestsBackend` is the default and required transport. `HttpxBackend` is a supported optional transport. Both implement the same async `Backend` protocol and accept only configuration they actually need. Backend selection is a closed `Literal`/enum, never dynamic module discovery.

### Proxy-pool behavior

`ProxyPool` accepts normalized URLs from constructor arguments, `FASTREQ_PROXIES`, or an explicit Webshare text source. It does not fetch free proxies. It supports round-robin selection by default, optional random selection for compatibility, per-proxy failure cooldown, and success recovery. The selected proxy is recorded with a request attempt.

HTTPX clients are cached by immutable transport key `(proxy, verify_ssl, follow_redirects, http2)` because HTTPX 0.28 configures proxies at client construction. Niquests sessions are similarly kept per proxy key. All cached clients close with the parent client. This keeps cookies physically isolated by proxy while still allowing one direct connection pool.

### Retry and error handling

Retry happens around one transport attempt. It applies only to timeout/connect/read errors and configured retryable responses. Status 429 uses a parsed `Retry-After` delay when present, otherwise exponential jittered delay. Non-retryable 4xx responses return normally to the caller; programmer/configuration errors do not retry. `return_none_on_failure` remains an explicit opt-in compatibility behavior; the default raises structured exceptions.

### Streaming

A stream callback receives chunks as they arrive. Streaming responses do not construct a whole `content` body. A normal response remains a normalized immutable value. The public `stream_callback` parameter is added consistently to async and synchronous convenience APIs.

### Modern packaging and quality gates

Use `uv_build`, `requires-python = ">=3.11"` with CI matrix through 3.14, `ruff`, `ty`, and pytest. `niquests` is required; `httpx` is an optional `httpx` extra; test/lint/docs tools live in PEP 735 dependency groups. Tests use HTTPX MockTransport and a local asynchronous test server; no default test depends on httpbin or external proxy services.

## Migration

- Release as fastreq 3.0.0 because removing two named backends and free-proxy settings is breaking.
- Preserve aliases and method signatures where their behavior remains meaningful.
- Raise `ConfigurationError` with migration guidance for `backend="aiohttp"`, `backend="requests"`, or free-proxy parameters.
- Document direct proxy lists, `FASTREQ_PROXIES`, and explicit Webshare import as replacements.

## Risks and mitigations

- niquests may have backend-specific streaming limitations: enforce the same contract with an integration test per retained backend.
- Yahoo may couple a cookie to a proxy: proxy-keyed sessions prevent cross-proxy cookie reuse.
- External Webshare availability: do not fetch during client construction; import is explicit and failure is a typed error.

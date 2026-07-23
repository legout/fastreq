# Change: Modernize fastreq around HTTPX and niquests

## Why

The current public client cannot construct any backend because its constructor contract is inconsistent. Proxy rotation, SSL configuration, streaming, and rate limiting are only partially wired. The library also carries three redundant transports and stale `parallel-requests` terminology.

## What Changes

- **BREAKING:** Support only `niquests` (default) and `httpx` transports; remove aiohttp and requests transports, extras, tests, and documentation.
- Keep the public `FastRequests`, `ParallelRequests`, `parallel_requests`, and `parallel_requests_async` compatibility names, but restrict `backend` to `"auto"`, `"niquests"`, and `"httpx"`.
- Make `niquests` a required runtime dependency and HTTPX an optional extra. `auto` always selects niquests; HTTPX is an explicit fallback.
- Replace the loose backend constructor convention with one transport contract. Concurrency is owned by the client, not transports.
- Keep configured proxy pools, Webshare import, proxy health/cooldown, explicit per-request proxy selection, random user-agent selection, retry, token-bucket pacing, cookies, redirects, SSL settings, and chunked streaming.
- Remove free-proxy configuration, fetching, tests, documentation, and environment variables. Free proxies are not a supported feature.
- Implement real HTTPX proxy behavior compatible with HTTPX 0.28+, using proxy-scoped clients rather than the removed request-level `proxies=` argument.
- Use one concurrency gate and one token bucket. A task acquires a rate token before occupying a concurrency slot.
- Retry only transient transport errors and explicitly configured retryable status codes (429, 500, 502, 503, 504); honor `Retry-After` when parseable.
- Modernize packaging for Python 3.14 using uv, `uv_build`, Ruff, ty, pytest, and hermetic HTTPX MockTransport/local-server tests.
- Canonicalize the public project and documentation name as `fastreq`; retain `ParallelRequests` only as a Python compatibility alias.

## Impact

- Affected specs: `backend-contract`, `backend-niquests`, `client-api`, `proxy-rotation`, `rate-limiting`, `retry-policy`, `public-api`, `documentation`, `ci-cd`.
- Affected code: `src/fastreq/client.py`, `src/fastreq/backends/`, `src/fastreq/utils/`, package metadata, tests, docs, CI.
- Consumers using aiohttp or requests backends must move to niquests (default) or HTTPX. Consumers using free proxies must provide an explicit proxy list or Webshare source.

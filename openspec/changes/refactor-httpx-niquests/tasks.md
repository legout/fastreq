# Implementation tasks

## 1. Baseline and public contract

- [ ] 1.1 Add regression tests proving `FastRequests(backend="niquests")`, `FastRequests(backend="httpx")`, and `FastRequests()` construct successfully.
- [ ] 1.2 Add tests proving removed backend names fail with a migration-oriented `ConfigurationError`.
- [ ] 1.3 Replace dynamic backend discovery in `src/fastreq/client.py` with a typed two-backend factory; remove `concurrency` from backend construction.
- [ ] 1.4 Run targeted construction tests and commit the contract repair.

## 2. Transport consolidation

- [ ] 2.1 Define the narrow retained transport protocol in `src/fastreq/backends/base.py`, including normal and streaming response paths.
- [ ] 2.2 Rebuild `src/fastreq/backends/niquests.py` against that contract with session lifecycle, redirects, TLS configuration, cookies, JSON normalization, and chunk iteration.
- [ ] 2.3 Rebuild `src/fastreq/backends/httpx.py` against the same contract using HTTPX 0.28 client-level proxy configuration.
- [ ] 2.4 Add hermetic contract tests shared by both retained transports.
- [ ] 2.5 Remove aiohttp/requests transports, their tests, optional extras, docs, and stale imports; commit the consolidation.

## 3. Request policy pipeline

- [ ] 3.1 Add tests that prove token acquisition precedes concurrency acquisition and that only one concurrency limit exists.
- [ ] 3.2 Simplify `RateLimitConfig`, `TokenBucket`, and `FastRequests._execute_request` to enforce that order.
- [ ] 3.3 Add tests for transport-error retry, retryable response statuses, non-retryable 4xx handling, retry exhaustion, and `Retry-After`.
- [ ] 3.4 Refactor retry policy into a typed classifier/delay calculator without broad `except Exception` retries.
- [ ] 3.5 Commit policy behavior with focused tests.

## 4. Explicit proxy and header policies

- [ ] 4.1 Write tests for URL normalization, explicit/Webshare proxy inputs, round-robin selection, random compatibility mode, cooldown, and recovery.
- [ ] 4.2 Replace `ProxyManager` with a dependency-free `ProxyPool`; remove `free_proxies` and its fetch stub entirely.
- [ ] 4.3 Integrate proxy selection and success/failure updates into each actual request attempt.
- [ ] 4.4 Cache transport clients by proxy/TLS/redirect/HTTP2 key and verify they close cleanly.
- [ ] 4.5 Wire existing header/user-agent policy into request construction and test it without network access.
- [ ] 4.6 Commit proxy and header integration.

## 5. Streaming, cookie behavior, and compatibility APIs

- [ ] 5.1 Add a local chunked-response fixture and tests proving callbacks see chunks before a full body is accumulated.
- [ ] 5.2 Implement streaming in both transports and expose `stream_callback` through all public async/sync methods.
- [ ] 5.3 Add tests for shared cookies, `set_cookies`, `reset_cookies`, redirects, and TLS configuration delegation.
- [ ] 5.4 Preserve `ParallelRequests` aliases and convenience functions; document removed backend/free-proxy behavior.
- [ ] 5.5 Commit streaming and compatibility API work.

## 6. Packaging, documentation, and release readiness

- [ ] 6.1 Convert package metadata to uv/`uv_build`, Python 3.14 support, PEP 735 groups, canonical 3.0.0 version, and required/optional dependencies.
- [ ] 6.2 Replace Black/isort/mypy configuration with Ruff and ty; remove unused dependencies.
- [ ] 6.3 Update README, API documentation, migration guide, and all stale `parallel-requests` naming.
- [ ] 6.4 Add CI matrix for supported Python versions including 3.14 and deterministic quality commands.
- [ ] 6.5 Run `uv sync --all-groups`, `ruff format --check .`, `ruff check .`, `ty check src`, `pytest`, `uv build`, and a local import/smoke test.
- [ ] 6.6 Commit the release-ready modernization.

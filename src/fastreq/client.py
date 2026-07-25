"""Main client for fastreq — high-performance async HTTP requests.

FastRequests owns one concurrency gate (semaphore) and one token bucket.
A task acquires a rate token BEFORE occupying a concurrency slot, executes
the request through a transport, and releases the slot.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, TypeVar, overload

from loguru import logger

from .backends.base import Backend, NormalizedResponse, RequestConfig
from .exceptions import (
    ConfigurationError,
    FailureDetails,
    PartialFailureError,
    RetryableResponse,
)
from .utils.headers import HeaderManager
from .utils.logging import configure_logging
from .utils.proxies import ProxyPool, ProxyPoolConfig, ProxySelection
from .utils.rate_limiter import AsyncRateLimiter, RateLimitConfig
from .utils.retry import DEFAULT_RETRYABLE_STATUSES, RetryConfig, RetryStrategy

# Type alias for backend selection
BackendName = Literal["auto", "niquests", "httpx", "curl_cffi"]

# Removed backend names that raise a migration error
_REMOVED_BACKENDS = {"aiohttp", "requests"}

T = TypeVar("T")


class ReturnType(str, Enum):
    """Enum for response parsing options."""

    JSON = "json"
    TEXT = "text"
    CONTENT = "content"
    RESPONSE = "response"
    STREAM = "stream"


@dataclass
class RequestOptions:
    """Internal request options."""

    url: str
    method: str = "GET"
    params: dict[str, Any] | None = None
    data: Any = None
    json: Any = None
    headers: dict[str, str] | None = None
    timeout: float | None = None
    proxy: str | None = None
    return_type: ReturnType = ReturnType.JSON
    stream_callback: Callable[[bytes], Any] | None = None


def _parse_retry_after(value: str) -> float | None:
    """Parse a Retry-After header value into seconds.

    Supports:
    - Integer/float seconds: "120" → 120.0
    - HTTP-date format: "Wed, 21 Oct 2015 07:28:00 GMT" → computed delta

    Args:
        value: Raw Retry-After header string

    Returns:
        Seconds to wait, or None if unparseable
    """
    value = value.strip()
    if not value:
        return None

    # Try numeric (seconds)
    try:
        return float(value)
    except ValueError:
        pass

    # Try HTTP-date format
    from email.utils import parsedate_to_datetime

    try:
        dt = parsedate_to_datetime(value)
        delta = (dt - dt.now(tz=dt.tzinfo)).total_seconds()
        return max(0.0, delta)
    except (TypeError, ValueError, OverflowError):
        return None


def _create_backend(backend: str, http2: bool, impersonate: str | None = None) -> Backend:
    """Create a transport instance from the typed backend selection.

    This is a closed factory — never uses dynamic module discovery.

    Args:
        backend: Backend name ("auto", "niquests", "httpx", "curl_cffi")
        http2: Whether HTTP/2 is requested
        impersonate: Browser impersonation target (curl_cffi backend only)

    Returns:
        Backend instance

    Raises:
        ConfigurationError: If the backend name is removed or the transport
            dependency is not installed.
    """
    if backend in _REMOVED_BACKENDS:
        raise ConfigurationError(
            f"Backend '{backend}' is no longer supported in fastreq 3.0. "
            f"Use 'niquests' (default) or 'httpx' instead. "
            f"Install with: pip install fastreq[httpx]",
            config_key="backend",
        )

    if backend == "auto":
        # auto always selects niquests (the required default)
        from .backends.niquests import NiquestsBackend

        return NiquestsBackend()

    if backend == "niquests":
        from .backends.niquests import NiquestsBackend

        return NiquestsBackend()

    if backend == "httpx":
        try:
            from .backends.httpx import HttpxBackend

            return HttpxBackend()
        except ImportError as e:
            raise ConfigurationError(
                "Backend 'httpx' requires the optional httpx dependency. "
                "Install with: pip install fastreq[httpx]",
                config_key="backend",
            ) from e

    if backend == "curl_cffi":
        try:
            from .backends.curl_cffi import CurlCffiBackend

            return CurlCffiBackend(impersonate=impersonate)
        except ImportError as e:
            raise ConfigurationError(
                "Backend 'curl_cffi' requires the optional curl_cffi dependency. "
                "Install with: pip install fastreq[curl]",
                config_key="backend",
            ) from e

    raise ConfigurationError(
        f"Unknown backend '{backend}'. Supported: 'auto', 'niquests', 'httpx', 'curl_cffi'.",
        config_key="backend",
    )


class FastRequests:
    """Main client for parallel HTTP requests.

    The client owns one concurrency gate and one token bucket. A task
    acquires a rate token before occupying a concurrency slot.

    Args:
        backend: Backend to use ("auto", "niquests", "httpx", "curl_cffi")
        concurrency: Maximum number of concurrent requests
        max_retries: Maximum retry attempts per request
        rate_limit: Requests per second (None for no limit)
        rate_limit_burst: Burst size for rate limiter
        http2: Enable HTTP/2 (if supported by backend)
        impersonate: Browser impersonation target for the curl_cffi backend
            (e.g. "chrome", "chrome131", "random"; None disables it).
            When set, user-agent rotation is disabled automatically because
            curl_cffi supplies the browser-matching User-Agent itself.
        follow_redirects: Follow HTTP redirects
        verify_ssl: Verify SSL certificates
        timeout: Default timeout per request (seconds)
        cookies: Initial session cookies
        random_user_agent: Rotate user agents
        random_proxy: Enable proxy rotation (requires proxy config)
        proxies: List of proxy URLs for rotation
        proxy_selection: Selection strategy ("round_robin" or "random")
        proxy_cooldown: Seconds before retrying a failed proxy
        webshare_file: Path to a Webshare proxy text file
        headers: Default headers applied to all requests
        debug: Enable debug logging
        verbose: Enable verbose output
        return_none_on_failure: Return None instead of raising on failure
    """

    def __init__(
        self,
        backend: BackendName | str = "auto",
        *,
        concurrency: int = 20,
        max_retries: int = 3,
        rate_limit: float | None = None,
        rate_limit_burst: int = 5,
        http2: bool = True,
        impersonate: str | None = None,
        follow_redirects: bool = True,
        verify_ssl: bool = True,
        timeout: float | None = None,
        cookies: dict[str, str] | None = None,
        random_user_agent: bool = True,
        random_proxy: bool = False,
        proxies: list[str] | None = None,
        proxy_selection: ProxySelection | str = ProxySelection.ROUND_ROBIN,
        proxy_cooldown: float = 60.0,
        webshare_file: str | None = None,
        headers: dict[str, str] | None = None,
        debug: bool = False,
        verbose: bool = True,
        return_none_on_failure: bool = False,
    ) -> None:
        # Validate free-proxy-related removed parameters
        # (caught early with migration guidance)

        self.backend_name = backend
        self.impersonate = impersonate
        self.concurrency = concurrency
        self.follow_redirects = follow_redirects
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        # Browser impersonation provides its own browser-matching User-Agent;
        # rotating a mismatched UA would contradict the TLS fingerprint.
        self.random_user_agent = random_user_agent if impersonate is None else False
        self.random_proxy = random_proxy
        self.debug = debug
        self.verbose = verbose
        self.return_none_on_failure = return_none_on_failure

        configure_logging(debug, verbose)

        self._backend: Backend | None = None
        self._cookies: dict[str, str] = cookies.copy() if cookies else {}
        self._rate_limiter: AsyncRateLimiter | None = None
        self._header_manager = HeaderManager(random_user_agent=self.random_user_agent)
        self._default_headers = headers or {}

        retry_config = RetryConfig(max_retries=max_retries)
        self._retry_strategy = RetryStrategy(retry_config)

        self._concurrency_semaphore = asyncio.Semaphore(concurrency)

        if rate_limit is not None:
            rate_limit_config = RateLimitConfig(
                requests_per_second=rate_limit,
                burst=rate_limit_burst,
            )
            self._rate_limiter = AsyncRateLimiter(rate_limit_config)

        self._http2 = http2

        # Build proxy pool if proxies or random_proxy with proxy list is provided
        self._proxy_pool: ProxyPool | None = None
        pool_proxies: list[str] = []

        # Webshare file import
        if webshare_file:
            from .utils.proxies import load_webshare_from_file

            pool_proxies.extend(load_webshare_from_file(webshare_file))

        # Explicit proxy list
        if proxies:
            pool_proxies.extend(proxies)

        # FASTREQ_PROXIES environment variable
        pool_proxies_from_env = ProxyPool.from_env()
        if pool_proxies_from_env.count() > 0:
            pool_proxies.extend(pool_proxies_from_env.proxies)

        if pool_proxies or random_proxy:
            selection = (
                ProxySelection(proxy_selection)
                if isinstance(proxy_selection, str)
                else proxy_selection
            )
            self._proxy_pool = ProxyPool(
                proxies=pool_proxies,
                config=ProxyPoolConfig(
                    selection=selection,
                    cooldown=proxy_cooldown,
                ),
            )

        self._select_backend()

    def _select_backend(self) -> None:
        """Create the transport using the typed factory."""
        self._backend = _create_backend(
            backend=self.backend_name,  # type: ignore[arg-type]
            http2=self._http2,
            impersonate=self.impersonate,
        )
        logger.info(f"Using backend: {self._backend.name}")

    async def __aenter__(self) -> FastRequests:
        if self._backend:
            await self._backend.__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._backend:
            await self._backend.__aexit__(*args)

    async def close(self) -> None:
        """Close backend session and cleanup resources."""
        if self._backend:
            await self._backend.close()

    def reset_cookies(self) -> None:
        """Clear all session cookies."""
        self._cookies = {}

    def set_cookies(self, cookies: dict[str, str]) -> None:
        """Add cookies to the session.

        Args:
            cookies: Dictionary of cookies to add (updates existing cookies)
        """
        self._cookies.update(cookies)

    @staticmethod
    @contextlib.asynccontextmanager
    async def _null_context() -> AsyncGenerator[None, None]:
        """A null async context manager to replace rate limiting when disabled."""
        yield

    @overload
    async def request(
        self,
        urls: str,
        *,
        method: str = ...,
        params: dict[str, Any] | None = ...,
        data: Any = ...,
        json: Any = ...,
        headers: dict[str, str] | None = ...,
        timeout: float | None = ...,
        proxy: str | None = ...,
        return_type: ReturnType | str = ...,
        follow_redirects: bool | None = ...,
        verify_ssl: bool | None = ...,
        parse_func: Callable[[Any], T] | None = ...,
        stream_callback: Callable[[bytes], Any] | None = ...,
        keys: None = ...,
    ) -> Any: ...

    @overload
    async def request(
        self,
        urls: list[str],
        *,
        method: str = ...,
        params: dict[str, Any] | None = ...,
        data: Any = ...,
        json: Any = ...,
        headers: dict[str, str] | None = ...,
        timeout: float | None = ...,
        proxy: str | None = ...,
        return_type: ReturnType | str = ...,
        follow_redirects: bool | None = ...,
        verify_ssl: bool | None = ...,
        parse_func: Callable[[Any], T] | None = ...,
        stream_callback: Callable[[bytes], Any] | None = ...,
        keys: list[str] = ...,
    ) -> dict[str, Any]: ...

    @overload
    async def request(
        self,
        urls: list[str],
        *,
        method: str = ...,
        params: dict[str, Any] | None = ...,
        data: Any = ...,
        json: Any = ...,
        headers: dict[str, str] | None = ...,
        timeout: float | None = ...,
        proxy: str | None = ...,
        return_type: ReturnType | str = ...,
        follow_redirects: bool | None = ...,
        verify_ssl: bool | None = ...,
        parse_func: Callable[[Any], T] | None = ...,
        stream_callback: Callable[[bytes], Any] | None = ...,
        keys: None = ...,
    ) -> list[Any]: ...

    @overload
    async def request(
        self,
        urls: str | list[str],
        *,
        method: str = ...,
        params: dict[str, Any] | None = ...,
        data: Any = ...,
        json: Any = ...,
        headers: dict[str, str] | None = ...,
        timeout: float | None = ...,
        proxy: str | None = ...,
        return_type: ReturnType | str = ...,
        follow_redirects: bool | None = ...,
        verify_ssl: bool | None = ...,
        parse_func: Callable[[Any], T] | None = ...,
        stream_callback: Callable[[bytes], Any] | None = ...,
        keys: list[str] | None = ...,
    ) -> Any: ...

    async def request(
        self,
        urls: str | list[str],
        *,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        data: Any = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        proxy: str | None = None,
        return_type: ReturnType | str = ReturnType.JSON,
        follow_redirects: bool | None = None,
        verify_ssl: bool | None = None,
        parse_func: Callable[[Any], Any] | None = None,
        stream_callback: Callable[[bytes], Any] | None = None,
        keys: list[str] | None = None,
    ) -> Any:
        """Make parallel HTTP requests.

        Args:
            urls: Single URL or list of URLs to request.
            method: HTTP method (GET, POST, etc.).
            params: Query parameters.
            data: Request body data.
            json: JSON body (serialized automatically).
            headers: Request headers.
            timeout: Per-request timeout in seconds.
            proxy: Proxy URL (overrides proxy rotation).
            return_type: How to parse the response.
            follow_redirects: Override default follow_redirects setting.
            verify_ssl: Override default verify_ssl setting.
            parse_func: Custom function to parse each response.
            stream_callback: Callback for streaming responses (receives chunks).
            keys: Keys for dict return (must match urls length).

        Returns:
            Single URL → single result
            List of URLs → list of results
            List of URLs with keys → dict mapping keys to results
        """
        if not self._backend:
            raise ConfigurationError("Backend not initialized")

        if isinstance(return_type, str):
            return_type = ReturnType(return_type)

        effective_follow_redirects = (
            follow_redirects if follow_redirects is not None else self.follow_redirects
        )
        effective_verify_ssl = verify_ssl if verify_ssl is not None else self.verify_ssl
        effective_timeout = timeout if timeout is not None else self.timeout

        if isinstance(urls, str):
            single_url = True
            url_list: list[str] = [urls]
        else:
            single_url = False
            url_list = list(urls)

        if keys is not None and len(keys) != len(url_list):
            raise ConfigurationError(
                f"Number of keys ({len(keys)}) must match number of URLs ({len(url_list)})"
            )

        request_options = [
            RequestOptions(
                url=u,
                method=method,
                params=params,
                data=data,
                json=json,
                headers=headers,
                timeout=effective_timeout,
                proxy=proxy,
                return_type=return_type,
                stream_callback=stream_callback,
            )
            for u in url_list
        ]

        tasks = [
            self._execute_request(
                req,
                follow_redirects=effective_follow_redirects,
                verify_ssl=effective_verify_ssl,
            )
            for req in request_options
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        failures: dict[str, FailureDetails] = {}
        processed_results: list[Any] = []

        for idx, result in enumerate(results):
            current_url = url_list[idx]

            if isinstance(result, Exception):
                if self.return_none_on_failure:
                    processed_results.append(None)
                else:
                    failures[current_url] = FailureDetails(url=current_url, error=result)
                    processed_results.append(result)
            else:
                if parse_func is not None:
                    result = parse_func(result)
                processed_results.append(result)

        if failures and not self.return_none_on_failure:
            raise PartialFailureError(
                f"Partial failure: {len(failures)} of {len(url_list)} requests failed",
                failures=failures,
                successes=len([r for r in results if not isinstance(r, Exception)]),
                total=len(url_list),
            )

        if single_url:
            return processed_results[0]
        elif keys is not None:
            return dict(zip(keys, processed_results, strict=True))
        else:
            return processed_results

    async def _execute_request(
        self,
        req: RequestOptions,
        *,
        follow_redirects: bool,
        verify_ssl: bool,
    ) -> Any:
        """Execute a single request with retry, rate limiting, and concurrency.

        Rate token is acquired BEFORE the concurrency slot is occupied,
        so that rate-limit-waiting requests don't block slots that could
        serve other requests.
        """
        if not self._backend:
            raise ConfigurationError("Backend not initialized")

        backend = self._backend

        async def make_request() -> NormalizedResponse:
            # Acquire rate token FIRST (before concurrency slot)
            if self._rate_limiter:
                await self._rate_limiter.acquire()

            # Then acquire concurrency slot
            async with self._concurrency_semaphore:
                # Select proxy: explicit per-request proxy > pool rotation
                selected_proxy = req.proxy
                if selected_proxy is None and self._proxy_pool:
                    selected_proxy = await self._proxy_pool.acquire()
                    if selected_proxy is None and self.random_proxy:
                        selected_proxy = None  # pool exhausted, try direct

                # Build headers with user-agent rotation
                request_headers = self._header_manager.get_headers(
                    {**self._default_headers, **(req.headers or {})}
                )

                try:
                    config = RequestConfig(
                        url=req.url,
                        method=req.method,
                        params=req.params,
                        data=req.data,
                        json=req.json,
                        headers=request_headers,
                        cookies={**self._cookies},
                        timeout=req.timeout,
                        proxy=selected_proxy,
                        http2=self._http2,
                        stream=req.return_type == ReturnType.STREAM,
                        follow_redirects=follow_redirects,
                        verify_ssl=verify_ssl,
                    )
                    response = await backend.request(
                        config,
                        stream_callback=req.stream_callback,
                    )

                    # Check for retryable status codes
                    if response.status_code in DEFAULT_RETRYABLE_STATUSES:
                        retry_after_raw = response.headers.get("retry-after", "")
                        retry_after = _parse_retry_after(retry_after_raw)
                        raise RetryableResponse(
                            f"Retryable status {response.status_code} from {req.url}",
                            status_code=response.status_code,
                            retry_after=retry_after,
                            url=req.url,
                        )

                    # Mark proxy success after a good request
                    if selected_proxy and self._proxy_pool:
                        await self._proxy_pool.mark_success(selected_proxy)

                    return response

                except RetryableResponse:
                    # Mark proxy as failed on retryable response
                    if selected_proxy and self._proxy_pool:
                        await self._proxy_pool.mark_failed(selected_proxy)
                    raise
                except Exception:
                    # Mark proxy as failed on transport error
                    if selected_proxy and self._proxy_pool:
                        await self._proxy_pool.mark_failed(selected_proxy)
                    raise

        response = await self._retry_strategy.execute(make_request)
        return self._parse_response(response, req)

    def _parse_response(self, response: NormalizedResponse, req: RequestOptions) -> Any:
        logger.debug(f"Request completed: {req.url} - Status: {response.status_code}")
        match req.return_type:
            case ReturnType.JSON:
                return response.json_data if response.is_json else None
            case ReturnType.TEXT:
                return response.text
            case ReturnType.CONTENT:
                return response.content
            case ReturnType.RESPONSE:
                return response
            case ReturnType.STREAM:
                # Chunks were already delivered to stream_callback during transport.
                # No additional callback call needed here.
                return None


def fastreq(
    urls: str | list[str],
    *,
    backend: BackendName | str = "auto",
    concurrency: int = 20,
    max_retries: int = 3,
    rate_limit: float | None = None,
    rate_limit_burst: int = 5,
    http2: bool = True,
    impersonate: str | None = None,
    follow_redirects: bool = True,
    verify_ssl: bool = True,
    timeout: float | None = None,
    cookies: dict[str, str] | None = None,
    random_user_agent: bool = True,
    random_proxy: bool = False,
    proxies: list[str] | None = None,
    proxy_selection: ProxySelection | str = ProxySelection.ROUND_ROBIN,
    proxy_cooldown: float = 60.0,
    webshare_file: str | None = None,
    headers: dict[str, str] | None = None,
    debug: bool = False,
    verbose: bool = True,
    return_none_on_failure: bool = False,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    data: Any = None,
    json: Any = None,
    proxy: str | None = None,
    return_type: ReturnType | str = ReturnType.JSON,
    parse_func: Callable[[Any], Any] | None = None,
    stream_callback: Callable[[bytes], Any] | None = None,
    keys: list[str] | None = None,
) -> Any:
    """Synchronous convenience function for parallel requests.

    Uses asyncio.run() internally.

    Args:
        urls: Single URL or list of URLs to request
        backend: Backend to use ("auto", "niquests", "httpx")
        concurrency: Maximum number of concurrent requests
        max_retries: Maximum retry attempts per request
        rate_limit: Requests per second (None for no limit)
        rate_limit_burst: Burst size for rate limiter
        http2: Enable HTTP/2 (if supported by backend)
        follow_redirects: Follow HTTP redirects
        verify_ssl: Verify SSL certificates
        timeout: Default timeout per request (seconds)
        cookies: Initial session cookies
        random_user_agent: Rotate user agents
        random_proxy: Enable proxy rotation
        proxies: List of proxy URLs for rotation
        proxy_selection: Selection strategy ("round_robin" or "random")
        proxy_cooldown: Seconds before retrying a failed proxy
        webshare_file: Path to a Webshare proxy text file
        headers: Default headers applied to all requests
        debug: Enable debug logging
        verbose: Enable verbose output
        return_none_on_failure: Return None instead of raising on failure
        method: HTTP method (GET, POST, etc.)
        params: Query parameters
        data: Request body data
        json: JSON body (serialized automatically)
        proxy: Explicit proxy URL (overrides rotation)
        return_type: How to parse the response
        parse_func: Custom function to parse each response
        stream_callback: Callback for streaming responses
        keys: Keys for dict return (must match urls length)

    Returns:
        Single URL → single result
        List of URLs → list of results
        List of URLs with keys → dict mapping keys to results
    """

    async def _run() -> Any:
        client = FastRequests(
            backend=backend,
            concurrency=concurrency,
            max_retries=max_retries,
            rate_limit=rate_limit,
            rate_limit_burst=rate_limit_burst,
            http2=http2,
            impersonate=impersonate,
            follow_redirects=follow_redirects,
            verify_ssl=verify_ssl,
            timeout=timeout,
            cookies=cookies,
            random_user_agent=random_user_agent,
            random_proxy=random_proxy,
            proxies=proxies,
            proxy_selection=proxy_selection,
            proxy_cooldown=proxy_cooldown,
            webshare_file=webshare_file,
            headers=headers,
            debug=debug,
            verbose=verbose,
            return_none_on_failure=return_none_on_failure,
        )
        async with client:
            return await client.request(
                urls,
                method=method,
                params=params,
                data=data,
                json=json,
                headers=headers,
                timeout=timeout,
                proxy=proxy,
                return_type=return_type,
                parse_func=parse_func,
                stream_callback=stream_callback,
                keys=keys,
            )

    return asyncio.run(_run())


async def fastreq_async(
    urls: str | list[str],
    *,
    backend: BackendName | str = "auto",
    concurrency: int = 20,
    max_retries: int = 3,
    rate_limit: float | None = None,
    rate_limit_burst: int = 5,
    http2: bool = True,
    impersonate: str | None = None,
    follow_redirects: bool = True,
    verify_ssl: bool = True,
    timeout: float | None = None,
    cookies: dict[str, str] | None = None,
    random_user_agent: bool = True,
    random_proxy: bool = False,
    proxies: list[str] | None = None,
    proxy_selection: ProxySelection | str = ProxySelection.ROUND_ROBIN,
    proxy_cooldown: float = 60.0,
    webshare_file: str | None = None,
    headers: dict[str, str] | None = None,
    debug: bool = False,
    verbose: bool = True,
    return_none_on_failure: bool = False,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    data: Any = None,
    json: Any = None,
    proxy: str | None = None,
    return_type: ReturnType | str = ReturnType.JSON,
    parse_func: Callable[[Any], Any] | None = None,
    stream_callback: Callable[[bytes], Any] | None = None,
    keys: list[str] | None = None,
) -> Any:
    """Async convenience function for parallel requests.

    Args:
        urls: Single URL or list of URLs to request
        backend: Backend to use ("auto", "niquests", "httpx")
        concurrency: Maximum number of concurrent requests
        max_retries: Maximum retry attempts per request
        rate_limit: Requests per second (None for no limit)
        rate_limit_burst: Burst size for rate limiter
        http2: Enable HTTP/2 (if supported by backend)
        follow_redirects: Follow HTTP redirects
        verify_ssl: Verify SSL certificates
        timeout: Default timeout per request (seconds)
        cookies: Initial session cookies
        random_user_agent: Rotate user agents
        random_proxy: Enable proxy rotation
        proxies: List of proxy URLs for rotation
        proxy_selection: Selection strategy ("round_robin" or "random")
        proxy_cooldown: Seconds before retrying a failed proxy
        webshare_file: Path to a Webshare proxy text file
        headers: Default headers applied to all requests
        debug: Enable debug logging
        verbose: Enable verbose output
        return_none_on_failure: Return None instead of raising on failure
        method: HTTP method (GET, POST, etc.)
        params: Query parameters
        data: Request body data
        json: JSON body (serialized automatically)
        proxy: Explicit proxy URL (overrides rotation)
        return_type: How to parse the response
        parse_func: Custom function to parse each response
        stream_callback: Callback for streaming responses
        keys: Keys for dict return (must match urls length)

    Returns:
        Single URL → single result
        List of URLs → list of results
        List of URLs with keys → dict mapping keys to results
    """
    client = FastRequests(
        backend=backend,
        concurrency=concurrency,
        max_retries=max_retries,
        rate_limit=rate_limit,
        rate_limit_burst=rate_limit_burst,
        http2=http2,
        impersonate=impersonate,
        follow_redirects=follow_redirects,
        verify_ssl=verify_ssl,
        timeout=timeout,
        cookies=cookies,
        random_user_agent=random_user_agent,
        random_proxy=random_proxy,
        proxies=proxies,
        proxy_selection=proxy_selection,
        proxy_cooldown=proxy_cooldown,
        webshare_file=webshare_file,
        headers=headers,
        debug=debug,
        verbose=verbose,
        return_none_on_failure=return_none_on_failure,
    )
    async with client:
        return await client.request(
            urls,
            method=method,
            params=params,
            data=data,
            json=json,
            headers=headers,
            timeout=timeout,
            proxy=proxy,
            return_type=return_type,
            parse_func=parse_func,
            stream_callback=stream_callback,
            keys=keys,
        )


# Backwards compatibility alias
ParallelRequests = FastRequests

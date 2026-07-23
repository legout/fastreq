from dataclasses import dataclass
from typing import Any


@dataclass
class FailureDetails:
    """Details about a failed request.

    Attributes:
        url: URL that failed
        error: Exception that occurred
        attempt: Retry attempt number (0 = first attempt)
    """

    url: str
    error: Exception
    attempt: int = 0


class FastRequestsError(Exception):
    """Base exception for fastreq library.

    All library exceptions inherit from this base class.
    """

    def __init__(self, message: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(message, *args, **kwargs)


class BackendError(FastRequestsError):
    """Raised when a backend operation fails.

    Indicates a failure in the underlying HTTP client library.

    Attributes:
        backend_name: Name of the backend that failed
    """

    def __init__(
        self, message: str, backend_name: str | None = None, *args: Any, **kwargs: Any
    ) -> None:
        self.backend_name = backend_name
        super().__init__(message, *args, **kwargs)


class ProxyError(FastRequestsError):
    """Raised when a proxy operation fails.

    Indicates a failure with proxy rotation, validation, or connection.

    Attributes:
        proxy_url: Proxy URL that failed (if applicable)
    """

    def __init__(
        self, message: str, proxy_url: str | None = None, *args: Any, **kwargs: Any
    ) -> None:
        self.proxy_url = proxy_url
        super().__init__(message, *args, **kwargs)


class RetryExhaustedError(FastRequestsError):
    """Raised when all retry attempts are exhausted.

    Indicates that a request failed after max_retries attempts.

    Attributes:
        attempts: Number of retry attempts made
        last_error: Last exception that occurred
        url: URL that failed (if applicable)
    """

    def __init__(
        self,
        message: str,
        attempts: int = 0,
        last_error: Exception | None = None,
        url: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.attempts = attempts
        self.last_error = last_error
        self.url = url
        super().__init__(message, *args, **kwargs)


class RateLimitExceededError(FastRequestsError):
    """Raised when rate limit is exceeded.

    Indicates that the rate limiter blocked a request.

    Attributes:
        retry_after: Seconds to wait before retry (if provided)
    """

    def __init__(
        self,
        message: str,
        retry_after: float | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message, *args, **kwargs)


class ValidationError(FastRequestsError):
    """Raised when request validation fails.

    Indicates invalid input parameters or configuration.

    Attributes:
        field_name: Name of the field that failed validation
    """

    def __init__(
        self, message: str, field_name: str | None = None, *args: Any, **kwargs: Any
    ) -> None:
        self.field_name = field_name
        super().__init__(message, *args, **kwargs)


class ConfigurationError(FastRequestsError):
    """Raised when configuration is invalid.

    Indicates missing or invalid configuration parameters.

    Attributes:
        config_key: Name of the configuration key that failed
    """

    def __init__(
        self, message: str, config_key: str | None = None, *args: Any, **kwargs: Any
    ) -> None:
        self.config_key = config_key
        super().__init__(message, *args, **kwargs)


class PartialFailureError(FastRequestsError):
    """Raised when some requests succeed and others fail.

    Occurs when return_none_on_failure=False and some requests fail.

    Attributes:
        failures: Dictionary mapping URLs to FailureDetails
        successes: Number of successful requests
        total: Total number of requests

    Example:
        >>> try:
        ...     results = fastreq(urls=many_urls)
        ... except PartialFailureError as e:
        ...     print(f"Failed: {e.get_failed_urls()}")
        ...     print(f"Success: {e.successes}/{e.total}")
    """

    def __init__(
        self,
        message: str,
        failures: dict[str, FailureDetails] | None = None,
        successes: int = 0,
        total: int = 0,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.failures = failures or {}
        self.successes = successes
        self.total = total
        super().__init__(message, *args, **kwargs)

    def get_failed_urls(self) -> list[str]:
        """Return list of URLs that failed.

        Returns:
            List of URLs that experienced errors
        """
        return list(self.failures.keys())


ParallelRequestsError = FastRequestsError


class RetryableResponse(FastRequestsError):
    """Raised when a response has a retryable status code.

    Carries the status code and optional Retry-After delay so the retry
    strategy can make informed decisions without re-inspecting the response.

    Attributes:
        status_code: HTTP status code that triggered the retry
        retry_after: Seconds to wait before retrying (from Retry-After header)
        url: URL that returned the retryable status
    """

    def __init__(
        self,
        message: str,
        status_code: int,
        retry_after: float | None = None,
        url: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.status_code = status_code
        self.retry_after = retry_after
        self.url = url
        super().__init__(message, *args, **kwargs)

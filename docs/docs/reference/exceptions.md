# Exceptions

All fastreq exceptions inherit from `FastRequestsError`.

## Exception Hierarchy

```
FastRequestsError
├── BackendError
├── ProxyError
├── RetryExhaustedError
├── RateLimitExceededError
├── ValidationError
├── ConfigurationError
└── PartialFailureError
```

---

## Exception Types

### FastRequestsError

Base exception for all fastreq errors.

```python
from fastreq.exceptions import FastRequestsError

try:
    await client.request(url)
except FastRequestsError as e:
    print(f"fastreq error: {e}")
```

---

### BackendError

Raised when a backend operation fails.

```python
from fastreq.exceptions import BackendError

try:
    await client.request(url)
except BackendError as e:
    print(f"Backend {e.backend_name} failed: {e}")
```

**Attributes:**
- `backend_name: str | None` - Name of the backend that failed

**Raised when:**
- Backend cannot be loaded
- Backend encounters an error during request execution

---

### ProxyError

Raised when a proxy operation fails.

```python
from fastreq.exceptions import ProxyError

try:
    await client.request(url, proxy="http://invalid:8080")
except ProxyError as e:
    print(f"Proxy error: {e}")
    print(f"Failed proxy: {e.proxy_url}")
```

**Attributes:**
- `proxy_url: str | None` - Proxy URL that failed

**Raised when:**
- Proxy connection fails
- Proxy validation fails
- Proxy rotation encounters errors

---

### RetryExhaustedError

Raised when all retry attempts are exhausted.

```python
from fastreq.exceptions import RetryExhaustedError

try:
    await client.request(url)
except RetryExhaustedError as e:
    print(f"Retries exhausted after {e.attempts} attempts")
    print(f"Last error: {e.last_error}")
    print(f"Failed URL: {e.url}")
```

**Attributes:**
- `attempts: int` - Number of retry attempts made
- `last_error: Exception | None` - Last exception that occurred
- `url: str | None` - URL that failed

**Raised when:**
- Request fails after `max_retries` attempts
- Retryable error occurs repeatedly

---

### RateLimitExceededError

Raised when rate limit is exceeded.

```python
from fastreq.exceptions import RateLimitExceededError

try:
    await client.request(url)
except RateLimitExceededError as e:
    print(f"Rate limit exceeded")
    print(f"Retry after: {e.retry_after}s")
```

**Attributes:**
- `retry_after: float | None` - Seconds to wait before retry

**Raised when:**
- Rate limiter blocks a request
- Concurrent limit is reached

---

### ValidationError

Raised when request validation fails.

```python
from fastreq.exceptions import ValidationError

try:
    validate_url("invalid-url")
except ValidationError as e:
    print(f"Validation failed for field '{e.field_name}': {e}")
```

**Attributes:**
- `field_name: str | None` - Name of the field that failed validation

**Raised when:**
- URL format is invalid
- Headers are invalid
- Parameters have incorrect types

---

### ConfigurationError

Raised when configuration is invalid.

```python
from fastreq.exceptions import ConfigurationError

try:
    client = FastRequests(backend="invalid")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    print(f"Invalid config key: {e.config_key}")
```

**Attributes:**
- `config_key: str | None` - Name of the configuration key that failed

**Raised when:**
- Backend is not found
- Configuration parameters are invalid
- Backend is not initialized

---

### PartialFailureError

Raised when some requests succeed and others fail.

Only raised when `return_none_on_failure=False` (default).

```python
from fastreq.exceptions import PartialFailureError

try:
    results = await client.request([
        "https://example.com/1",
        "https://example.com/2",
        "https://invalid-url",
    ])
except PartialFailureError as e:
    print(f"Partial failure: {e.successes}/{e.total} succeeded")
    print(f"Failed URLs: {e.get_failed_urls()}")

    # Inspect individual failures
    for url, details in e.failures.items():
        print(f"{url}: {details.error}")
```

**Attributes:**
- `failures: dict[str, FailureDetails]` - Dictionary mapping URLs to `FailureDetails`
- `successes: int` - Number of successful requests
- `total: int` - Total number of requests

**Methods:**
- `get_failed_urls() -> list[str]` - Returns list of URLs that failed

**Raised when:**
- Multiple requests are made and some fail
- `return_none_on_failure=False` (default)

#### FailureDetails

Details about a failed request.

```python
@dataclass
class FailureDetails:
    url: str
    error: Exception
    attempt: int = 0
```

**Attributes:**
- `url: str` - URL that failed
- `error: Exception` - Exception that occurred
- `attempt: int` - Retry attempt number (0 = first attempt)

---

## Handling Failures Gracefully

Use `return_none_on_failure=True` to avoid raising exceptions:

```python
async with FastRequests(return_none_on_failure=True) as client:
    results = await client.request([
        "https://example.com/1",
        "https://invalid-url",
        "https://example.com/2",
    ])

    # Check for None values
    for url, result in zip(urls, results):
        if result is None:
            print(f"Request to {url} failed")
        else:
            print(f"Success: {result}")
```

---

## See Also

- [API Reference: FastRequests](api/fastrequests.md)
- [How-to: Handle Errors](../tutorials/handling-errors.md)
- [How-to: Debug Issues](../how-to-guides/debug-issues.md)

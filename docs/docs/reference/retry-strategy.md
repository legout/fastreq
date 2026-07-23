# Retry Strategy

Automatic retry with exponential backoff and jitter for resilient request handling.

## RetryStrategy

Main retry strategy class.

```python
from fastreq.utils.retry import RetryStrategy, RetryConfig

config = RetryConfig(
    max_retries=3,
    backoff_multiplier=1.0,
    jitter=0.1,
)

strategy = RetryStrategy(config)

result = await strategy.execute(some_async_function)
```

### RetryStrategy Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `execute(func, *args, **kwargs)` | `Any` | Execute function with retry logic |
| `_calculate_delay(attempt)` | `float` | Calculate delay for retry attempt |
| `_should_retry(error)` | `bool` | Determine if error should trigger retry |

---

## RetryConfig

Configuration for retry strategy.

```python
from fastreq.utils.retry import RetryConfig

config = RetryConfig(
    max_retries=3,              # Retry up to 3 times
    backoff_multiplier=1.0,    # Base backoff in seconds
    jitter=0.1,                # 10% jitter
    retry_on=None,             # Retry on all errors (default)
    dont_retry_on=None,        # Don't exclude any errors
)
```

### RetryConfig Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_retries` | `int` | `3` | Maximum retry attempts |
| `backoff_multiplier` | `float` | `1.0` | Base backoff (seconds) |
| `jitter` | `float` | `0.1` | Jitter fraction (0.1 = 10%) |
| `retry_on` | `set[type[Exception]] \| None` | `None` | Exception types to retry |
| `dont_retry_on` | `set[type[Exception]] \| None` | `None` | Exceptions to never retry |

---

## Backoff Formula

Exponential backoff with jitter:

```
delay = backoff_multiplier * (2^attempt) ± (jitter * delay)
```

### Example Calculation

With `backoff_multiplier=1.0` and `jitter=0.1`:

| Attempt | Base Delay | Jitter Range | Actual Delay |
|---------|------------|--------------|--------------|
| 0 | 1.0s | ±0.1s | 0.9s - 1.1s |
| 1 | 2.0s | ±0.2s | 1.8s - 2.2s |
| 2 | 4.0s | ±0.4s | 3.6s - 4.4s |

### Code Implementation

```python
def _calculate_delay(self, attempt: int) -> float:
    base_delay = self.config.backoff_multiplier * (2**attempt)
    jitter_amount = self.config.jitter * base_delay
    jittered_delay = base_delay + random.uniform(-jitter_amount, jitter_amount)
    return float(max(0, jittered_delay))
```

---

## Jitter Calculation

Jitter adds randomness to avoid "thundering herd" problems:

```python
jittered_delay = base_delay + random.uniform(-jitter_amount, jitter_amount)
```

### Why Jitter?

Without jitter, multiple failing requests retry simultaneously:

```
Time 0.0s:  All requests fail
Time 1.0s:  All retry (thundering herd!)
Time 2.0s:  All retry again
```

With jitter, retries are spread out:

```
Time 0.0s:  All requests fail
Time 0.9s:  Request 1 retries
Time 1.1s:  Request 2 retries
Time 1.8s:  Request 3 retries
Time 2.2s:  Request 4 retries
```

---

## Retry Logic

### When to Retry

By default, all exceptions trigger retry:

```python
# Default behavior - retry all errors
config = RetryConfig(max_retries=3)
```

### Retry Specific Errors

```python
# Only retry network errors
import httpx

config = RetryConfig(
    max_retries=3,
    retry_on={httpx.ConnectError, httpx.TimeoutException},
)
```

### Don't Retry Specific Errors

```python
# Retry all errors except 4xx
import httpx

config = RetryConfig(
    max_retries=3,
    dont_retry_on={httpx.HTTPStatusError},
)
```

### Combined Rules

```python
# Retry only network errors, never 4xx
config = RetryConfig(
    max_retries=3,
    retry_on={httpx.ConnectError, httpx.TimeoutException},
    dont_retry_on={httpx.HTTPStatusError},
)
```

---

## Using Retry Strategy

### In FastRequests Client

```python
from fastreq import FastRequests

client = FastRequests(
    max_retries=3,  # Built-in retry
)

async with client:
    results = await client.request(urls)
```

### Standalone Usage

```python
from fastreq.utils.retry import RetryStrategy, RetryConfig
import httpx

config = RetryConfig(max_retries=3, jitter=0.1)
strategy = RetryStrategy(config)

async def fetch(url):
    async with httpx.AsyncClient() as client:
        return await client.get(url)

# Retry automatically
result = await strategy.execute(fetch, "https://example.com")
```

---

## Exhausted Retries

When all retries are exhausted, `RetryExhaustedError` is raised:

```python
from fastreq.exceptions import RetryExhaustedError

try:
    await strategy.execute(func)
except RetryExhaustedError as e:
    print(f"Retries exhausted after {e.attempts} attempts")
    print(f"Last error: {e.last_error}")
```

### RetryExhaustedError Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `attempts` | `int` | Number of retry attempts |
| `last_error` | `Exception \| None` | Last exception |
| `url` | `str \| None` | URL that failed |

---

## Complete Example

```python
from fastreq import FastRequests
from fastreq.exceptions import RetryExhaustedError
import httpx

client = FastRequests(
    max_retries=3,              # Retry up to 3 times
)

async with client:
    try:
        results = await client.request(urls)
    except RetryExhaustedError as e:
        print(f"Failed after {e.attempts} retries")
        print(f"Last error: {e.last_error}")
        # Handle partial failure or abort
```

---

## See Also

- [Reference: Exceptions](exceptions.md)
- [How-to: Handle Errors](../tutorials/handling-errors.md)

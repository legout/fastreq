# Handle Retries

Learn how to configure automatic retries with exponential backoff and selective retry logic.

## Basic Retry Configuration

Use `max_retries` to automatically retry failed requests:

```python
from fastreq import fastreq

# Retry up to 3 times (default)
results = fastreq(
    urls=["https://api.example.com/unstable"],
    max_retries=3,
)

# Disable retries
results = fastreq(
    urls=["https://api.example.com/unstable"],
    max_retries=0,
)

# Increase retries for unreliable services
results = fastreq(
    urls=["https://api.example.com/unstable"],
    max_retries=5,
)
```

## Exponential Backoff with Jitter

The library uses exponential backoff with random jitter:

```python
from fastreq import fastreq

# Retry behavior with max_retries=3
# Attempt 0: immediate
# Attempt 1: wait ~1s (1.0 * 2^1 + jitter)
# Attempt 2: wait ~2s (1.0 * 2^2 + jitter)
# Attempt 3: wait ~4s (1.0 * 2^3 + jitter)
# Failed after 4 total attempts

results = fastreq(
    urls=["https://api.example.com/unstable"],
    max_retries=3,
)
```

**Why Jitter?** Random variation prevents "thundering herd" problems where all retries happen simultaneously.

## Selective Retry with `retry_on`

Only retry on specific HTTP status codes:

```python
from fastreq import fastreq

# Retry only on 5xx server errors
results = fastreq(
    urls=["https://api.example.com/endpoint"],
    max_retries=3,
    retry_on=[500, 502, 503, 504],  # Server errors
)

# Retry on connection errors and server errors
results = fastreq(
    urls=["https://api.example.com/endpoint"],
    max_retries=3,
    retry_on=[500, 502, 503, 504, "timeout", "connection"],
)
```

## Don't Retry with `dont_retry_on`

Never retry on specific status codes:

```python
from fastreq import fastreq

# Don't retry on 4xx client errors
results = fastreq(
    urls=["https://api.example.com/endpoint"],
    max_retries=3,
    dont_retry_on=[400, 401, 403, 404, 429],  # Client errors
)
```

## Example: Retry Only on Server Errors

```python
from fastreq import fastreq

# Retry only when server is having issues
results = fastreq(
    urls=[
        "https://api.example.com/endpoint1",
        "https://api.example.com/endpoint2",
    ],
    max_retries=3,
    retry_on=[500, 502, 503, 504],  # Only server errors
)

# 4xx errors fail immediately without retry
```

## Example: Don't Retry on Validation Errors

```python
from fastreq import fastreq

# Don't retry on validation errors (4xx)
results = fastreq(
    urls=["https://api.example.com/users"],
    method="POST",
    json={"name": "John"},
    max_retries=3,
    dont_retry_on=[400, 401, 403, 404],  # Client errors
)

# Invalid data returns 400 and fails immediately
```

## Combining `retry_on` and `dont_retry_on`

Both parameters can be used together:

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://api.example.com/endpoint"],
    max_retries=3,
    retry_on=[500, 502, 503, 504],           # Retry server errors
    dont_retry_on=[429],                      # Don't retry rate limit
)
```

## Handling Retry Exhaustion

Catch `RetryExhaustedError` when all retries fail:

```python
from fastreq import fastreq, RetryExhaustedError

try:
    results = fastreq(
        urls=["https://api.example.com/unreliable"],
        max_retries=3,
    )
except RetryExhaustedError as e:
    print(f"Retries exhausted after {e.attempts} attempts")
    print(f"Last error: {e.last_error}")
```

## Retry with Custom Error Handling

```python
from fastreq import fastreq, RetryExhaustedError

def fetch_with_fallback(urls):
    try:
        return fastreq(
            urls=urls,
            max_retries=3,
            retry_on=[500, 502, 503, 504],
        )
    except RetryExhaustedError as e:
        print(f"Retries failed: {e.last_error}")
        # Fallback: try again with different parameters
        return fastreq(
            urls=urls,
            max_retries=1,
            timeout=30,  # Longer timeout
        )

results = fetch_with_fallback(
    urls=["https://api.example.com/endpoint"],
)
```

## Retry and Partial Failures

Handle retries with partial failures:

```python
from fastreq import fastreq, PartialFailureError, RetryExhaustedError

urls = [
    "https://api.example.com/endpoint1",
    "https://api.example.com/endpoint2",
    "https://api.example.com/endpoint3",
]

try:
    results = fastreq(
        urls=urls,
        max_retries=3,
    )
except PartialFailureError as e:
    print(f"Partial failure: {e.successes}/{e.total}")
    # Some succeeded, some failed even after retries
```

## Retry Configuration by Backend

Different backends handle retries differently:

```python
from fastreq import fastreq

# niquests: HTTP/2 retries, connection pooling
results = fastreq(
    urls=["https://api.example.com/endpoint"],
    max_retries=3,
    backend="niquests",
)

# httpx: HTTP/2 retries with modern async API
results = fastreq(
    urls=["https://api.example.com/endpoint"],
    max_retries=3,
    backend="httpx",
)
```

## Monitoring Retry Behavior

Enable debug logging to see retry attempts:

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://api.example.com/unstable"],
    max_retries=3,
    debug=True,
)
```

Example output:
```
[DEBUG] Request 1: failed with 500, retry 1/3
[DEBUG] Request 1: failed with 500, retry 2/3
[DEBUG] Request 1: failed with 500, retry 3/3
[DEBUG] Request 1: exhausted retries
```

## Retry Patterns

### Pattern 1: Conservative Retry

For rate-limited APIs:

```python
results = fastreq(
    urls=["https://api.example.com/data"],
    max_retries=2,
    dont_retry_on=[429],  # Don't retry rate limit
)
```

### Pattern 2: Aggressive Retry

For critical operations:

```python
results = fastreq(
    urls=["https://api.example.com/payment"],
    max_retries=5,
    retry_on=[500, 502, 503, 504],
    dont_retry_on=[400, 401],  # Don't retry client errors
)
```

### Pattern 3: Timeout Retry

Retry only on timeouts:

```python
results = fastreq(
    urls=["https://api.example.com/slow"],
    max_retries=3,
    retry_on=["timeout"],
    dont_retry_on=[400, 401, 403, 404, 429, 500],
)
```

## Combining Retries with Other Features

### Retries + Rate Limiting

```python
results = fastreq(
    urls=["https://api.example.com/data"] * 50,
    max_retries=3,
    rate_limit=10,  # 10 req/s
    dont_retry_on=[429],  # Don't retry rate limit
)
```

### Retries + Proxies

```python
results = fastreq(
    urls=["https://api.example.com/data"] * 20,
    max_retries=2,
    proxies=["http://proxy1:8080", "http://proxy2:8080"],
    retry_on=[500, 502, 503, 504],
)
```

### Retries + Timeout

```python
results = fastreq(
    urls=["https://api.example.com/slow"],
    max_retries=3,
    timeout=5,
    retry_on=["timeout"],
)
```

## Best Practices

1. **Set Appropriate Retry Limits**: Don't retry indefinitely
   ```python
   max_retries=3  # Good default
   ```

2. **Don't Retry Client Errors**: 4xx errors indicate client issues
   ```python
   dont_retry_on=[400, 401, 403, 404]
   ```

3. **Use Selective Retries**: Retry only on recoverable errors
   ```python
   retry_on=[500, 502, 503, 504]
   ```

4. **Handle Rate Limits**: Don't retry on 429
   ```python
   dont_retry_on=[429]
   ```

5. **Monitor Retry Exhaustion**: Catch and log retry failures
   ```python
   except RetryExhaustedError as e:
       logger.error(f"Retries failed: {e.last_error}")
   ```

## See Also

- **[Limit Request Rate](limit-request-rate.md)** - Control request frequency
- **[Debug Issues](debug-issues.md)** - Enable debug logging
- **[Handling Errors](../tutorials/handling-errors.md)** - Complete error handling guide
- **[API Reference](../reference/configuration.md)** - Configuration options

# Rate Limiting

Control request rate using the token bucket algorithm with burst capability.

## AsyncRateLimiter

Main rate limiter class that combines token bucket rate limiting with semaphore-based concurrency control.

```python
from fastreq.utils.rate_limiter import AsyncRateLimiter, RateLimitConfig

config = RateLimitConfig(
    requests_per_second=10,
    burst=5,
    max_concurrency=20,
)

limiter = AsyncRateLimiter(config)

async with limiter.acquire():
    # Make request here
    pass
```

### AsyncRateLimiter Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `acquire()` | `AsyncIterator[None]` | Acquire rate limit token and concurrency slot |
| `available()` | `int` | Get available tokens |

---

## RateLimitConfig

Configuration for rate limiting.

```python
from fastreq.utils.rate_limiter import RateLimitConfig

config = RateLimitConfig(
    requests_per_second=10.0,  # 10 requests per second
    burst=5,                    # Allow bursts of up to 5
    max_concurrency=20,         # Max 20 concurrent requests
)
```

### RateLimitConfig Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `requests_per_second` | `float` | Token refill rate (requests/sec) |
| `burst` | `int` | Maximum bucket size (tokens) |
| `max_concurrency` | `int` | Maximum concurrent requests |

---

## TokenBucket

Implements the token bucket algorithm for rate limiting.

```python
from fastreq.utils.rate_limiter import TokenBucket

bucket = TokenBucket(requests_per_second=10, burst=5)

# Get available tokens
tokens = bucket.available()
print(f"Available: {tokens}")

# Acquire token (waits if needed)
await bucket.acquire()
```

### TokenBucket Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `available()` | `int` | Get available tokens |
| `acquire(tokens)` | `None` | Acquire tokens, waiting if necessary |

### TokenBucket Algorithm

The token bucket algorithm works as follows:

1. **Bucket Size**: Maximum number of tokens (`burst`)
2. **Refill Rate**: Tokens added per second (`requests_per_second`)
3. **Token Acquisition**: Wait if insufficient tokens available

```
Time 0s:    5 tokens (full bucket)
Time 0.5s:  Request uses 1 token → 4 tokens remain
            Refill adds 0.5 * 10 = 5 tokens → 5 tokens (capped at burst)
Time 1s:    Request uses 3 tokens → 2 tokens remain
            Refill adds 0.5 * 10 = 5 tokens → 5 tokens (capped at burst)
```

### Refill Formula

```python
elapsed = current_time - last_update
tokens = min(burst, tokens + elapsed * requests_per_second)
```

---

## Using Rate Limiting

### In FastRequests Client

```python
from fastreq import FastRequests

client = FastRequests(
    rate_limit=10.0,      # 10 requests per second
    rate_limit_burst=5,   # Allow bursts of 5
    concurrency=20,
)

async with client:
    results = await client.request(urls)
```

### Standalone Usage

```python
from fastreq.utils.rate_limiter import AsyncRateLimiter, RateLimitConfig

config = RateLimitConfig(requests_per_second=10, burst=5, max_concurrency=20)
limiter = AsyncRateLimiter(config)

async def make_request(url):
    async with limiter.acquire():
        # Request is rate-limited
        response = await fetch(url)
        return response

results = await asyncio.gather(*[make_request(url) for url in urls])
```

---

## Rate Limiting Behavior

### Without Rate Limiting

Requests execute immediately up to concurrency limit:

```
Time 0.0s:  Request 1 starts
Time 0.0s:  Request 2 starts
Time 0.0s:  Request 3 starts
Time 0.1s:  Request 1 completes, Request 4 starts
```

### With Rate Limiting (10 req/s, burst=5)

Requests are throttled:

```
Time 0.0s:  Request 1 starts (tokens: 4)
Time 0.0s:  Request 2 starts (tokens: 3)
Time 0.0s:  Request 3 starts (tokens: 2)
Time 0.0s:  Request 4 starts (tokens: 1)
Time 0.0s:  Request 5 starts (tokens: 0)
Time 0.1s:  Request 6 waits for refill (tokens: 0 → 1)
Time 0.2s:  Request 7 waits for refill (tokens: 0 → 1)
```

### Burst Behavior

Burst allows short bursts above average rate:

```python
config = RateLimitConfig(requests_per_second=2, burst=5)
```

```
Time 0.0s:  5 requests start immediately (burst)
Time 0.5s:  Request 6 waits (0.5s * 2 = 1 token available)
Time 1.0s:  Request 7 waits (0.5s * 2 = 1 token available)
Time 1.5s:  Request 8 waits (0.5s * 2 = 1 token available)
```

---

## Concurrency Control

The `max_concurrency` parameter limits simultaneous requests:

```python
config = RateLimitConfig(
    requests_per_second=10,  # Average 10 req/s
    burst=5,                 # Burst up to 5
    max_concurrency=3,       # Max 3 concurrent
)
```

Behavior:
- Rate limit controls average request rate
- Concurrency limit controls simultaneous requests
- Both limits must be satisfied

---

## Monitoring

### Check Available Tokens

```python
async with limiter.acquire():
    tokens = limiter.available()
    print(f"Tokens before request: {tokens}")
    await make_request()
    tokens_after = limiter.available()
    print(f"Tokens after request: {tokens_after}")
```

---

## See Also

- [How-to: Limit Request Rate](../how-to-guides/limit-request-rate.md)
- [Reference: Retry Strategy](retry-strategy.md)

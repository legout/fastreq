# Parallel Fundamentals

This tutorial explains the core concepts of parallel requests: concurrency, async/await, and backend selection.

**Estimated reading time: 15 minutes**

## What is Concurrency?

Concurrency means performing multiple operations at the same time. In the context of HTTP requests, it means making multiple network calls simultaneously instead of one after another.

### Sequential vs Parallel

```python
import time
import niquests

# Sequential requests (slow)
start = time.time()
for i in range(5):
    niquests.get("https://httpbin.org/delay/1")
print(f"Sequential: {time.time() - start:.1f}s")  # ~5 seconds

# Parallel requests (fast)
from fastreq import fastreq

start = time.time()
fastreq(
    urls=["https://httpbin.org/delay/1"] * 5,
    concurrency=5,
)
print(f"Parallel: {time.time() - start:.1f}s")  # ~1 second
```

In this example, sequential requests take ~5 seconds (1 second per request), while parallel requests take only ~1 second because all 5 requests happen simultaneously.

## Understanding Async/Await

The library uses Python's `async` and `await` syntax for parallel execution.

### Async Basics

```python
import asyncio
from fastreq import fastreq_async

async def fetch_data():
    # This async function can pause while waiting for network I/O
    results = await fastreq_async(
        urls=["https://api.github.com/repos/python/cpython"],
    )
    return results

# Run async code
results = asyncio.run(fetch_data())
```

### How It Works

When you use `await fastreq_async()`, the function:

1. Creates multiple async tasks (one per URL)
2. Executes tasks concurrently using `asyncio.gather()`
3. Pauses while waiting for network responses
4. Returns when all requests complete

This allows Python to efficiently wait for multiple network operations simultaneously.

## Concurrency Limits

The `concurrency` parameter controls how many requests run simultaneously.

```python
from fastreq import fastreq

# Process 100 URLs, 10 at a time
results = fastreq(
    urls=[f"https://api.example.com/page/{i}" for i in range(100)],
    concurrency=10,  # Max 10 concurrent requests
)
```

### Choosing the Right Concurrency

- **Low concurrency (1-5)**: For rate-limited APIs or when preserving order matters
- **Medium concurrency (10-20)**: Good balance for most public APIs
- **High concurrency (50-100)**: For internal services or when speed is critical

Be careful with high concurrency - it may:
- Trigger rate limits
- Overload servers
- Exhaust local resources

## Backend Selection

The library abstracts away different HTTP client libraries.

### Auto-Detection

```python
# Automatically picks the best available backend
results = fastreq(
    urls=["https://httpbin.org/get"],
    backend="auto",  # Default
)
```

### Explicit Backend Selection

```python
# Force specific backend
results = fastreq(
    urls=["https://httpbin.org/get"],
    backend="niquests",  # or "httpx"
)
```

### Backend Comparison

| Feature        | niquests | httpx |
|----------------|----------|-------|
| HTTP/2 Support | ✅ Yes   | ✅ Yes* |
| Streaming     | ✅ Yes   | ✅ Yes |
| Async Native   | ✅ Yes   | ✅ Yes |
| Sync Native    | ✅ Yes   | ❌ No  |
| Ecosystem     | New      | Mature |

*HTTP/2 requires `pip install httpx[http2]` (installs the `h2` extra)

**Recommendation**: Use `niquests` (default) for HTTP/2 support and best performance.

## Rate Limiting

Control request rate to avoid overwhelming servers or hitting rate limits.

```python
from fastreq import fastreq

# Limit to 10 requests per second with burst of 5
results = fastreq(
    urls=["https://api.example.com/endpoint"] * 50,
    rate_limit=10,           # 10 requests per second
    rate_limit_burst=5,      # Allow bursts of 5
)
```

### Why Rate Limit?

- Avoid API rate limits (e.g., 1000 requests/hour)
- Be a good citizen and don't overwhelm servers
- Maintain predictable performance

## Retry Logic

Automatically retry failed requests with exponential backoff.

```python
from fastreq import fastreq

# Retry up to 3 times with backoff
results = fastreq(
    urls=["https://api.example.com/unstable"],
    max_retries=3,
)
```

### How Backoff Works

```python
# Attempt 0: immediate
# Attempt 1: wait 1s (1.0 * 2^1)
# Attempt 2: wait 2s (1.0 * 2^2)
# Attempt 3: wait 4s (1.0 * 2^3)
# Failed after 4 total attempts
```

The library adds **jitter** (random variation) to prevent thundering herd problems.

## Summary

Key concepts:
- **Concurrency**: Make multiple requests simultaneously
- **Async/Await**: Use `asyncio` for efficient parallel execution
- **Concurrency Limit**: Control how many requests run at once
- **Backends**: Choose niquests (default) or httpx
- **Rate Limiting**: Control request rate to avoid rate limits
- **Retry Logic**: Automatically retry failed requests

## Next Steps

- Learn about **[Handling Errors](handling-errors.md)** for robust error handling
- Explore **[How-to Guides](../how-to-guides/index.md)** for practical examples

# Select Backend

Learn how to choose and configure HTTP backends (niquests, httpx).

## Backend Auto-Detection

The library automatically selects the best available backend:

```python
from fastreq import fastreq

# Auto-detection (default)
results = fastreq(
    urls=["https://httpbin.org/get"],
    backend="auto",  # Default behavior
)
```

**Detection Order:**
1. **niquests** - HTTP/2 support, streaming, async native (default)
2. **httpx** - HTTP/2 support (with h2 extra), modern API, async native

Since niquests is a required dependency, auto-detection will always select niquests unless you explicitly request httpx.

## Explicit Backend Selection

Force a specific backend:

```python
from fastreq import fastreq

# Use niquests (default, recommended)
results = fastreq(
    urls=["https://httpbin.org/get"],
    backend="niquests",
)

# Use httpx (modern async API with HTTP/2 support)
results = fastreq(
    urls=["https://httpbin.org/get"],
    backend="httpx",
)
```

## Backend Feature Comparison

| Feature              | niquests | httpx |
|----------------------|----------|-------|
| HTTP/2 Support       | ✅ Yes   | ✅ Yes* |
| Streaming            | ✅ Yes   | ✅ Yes |
| Async Native         | ✅ Yes   | ✅ Yes |
| Sync Native          | ✅ Yes   | ❌ No  |
| Connection Pooling   | ✅ Yes   | ✅ Yes |
| Cookies              | ✅ Yes   | ✅ Yes |
| Proxies              | ✅ Yes   | ✅ Yes |
| Session Reuse        | ✅ Yes   | ✅ Yes |

*HTTP/2 requires `pip install httpx[http2]` (installs the `h2` extra)

## When to Use Each Backend

### Use niquests When:

- You need HTTP/2 support out of the box
- You want the best performance
- You need both sync and async compatibility

```python
from fastreq import fastreq

# Best for modern APIs with HTTP/2
results = fastreq(
    urls=["https://api.example.com/data"] * 100,
    backend="niquests",
    concurrency=50,
)
```

### Use httpx When:

- You prefer httpx's modern API
- You need HTTP/2 with a clean async interface
- You're already using httpx in your project

```python
import asyncio
from fastreq import fastreq_async

async def fetch_with_httpx():
    results = await fastreq_async(
        urls=["https://api.example.com/data"] * 100,
        backend="httpx",
        concurrency=50,
    )
    return results

# HTTP/2 requires httpx[http2] extra
results = asyncio.run(fetch_with_httpx())
```

## HTTP/2 Support Example

niquests and httpx both support HTTP/2 for better performance:

```python
from fastreq import fastreq

# HTTP/2 with niquests (default)
results = fastreq(
    urls=["https://httpbin.org/get"] * 10,
    backend="niquests",
    debug=True,
)

# HTTP/2 with httpx (requires httpx[http2] extra)
results = fastreq(
    urls=["https://httpbin.org/get"] * 10,
    backend="httpx",
)
```

**Benefits of HTTP/2:**
- Multiplexing: Multiple requests over single connection
- Header compression: Reduced bandwidth
- Server push: Optional optimization

## Backend Performance Comparison

Benchmark different backends:

```python
import time
from fastreq import fastreq

urls = ["https://httpbin.org/get"] * 100

for backend in ["niquests", "httpx"]:
    start = time.time()
    results = fastreq(
        urls=urls,
        backend=backend,
        concurrency=20,
    )
    elapsed = time.time() - start
    print(f"{backend}: {elapsed:.2f}s")
```

## Installing Backend-Specific Dependencies

Install with specific backend support:

```bash
# niquests is included by default
pip install fastreq

# Add httpx support (optional)
pip install fastreq[httpx]
```

## Checking Backend Availability

Check which backends are available:

```python
from fastreq.backends import get_available_backends

available = get_available_backends()
print(f"Available backends: {available}")
```

## Backend-Specific Configuration

Some backends support additional configuration:

```python
from fastreq import fastreq

# niquests-specific options
results = fastreq(
    urls=["https://httpbin.org/get"],
    backend="niquests",
    # Backend can expose additional options
)

# httpx-specific options
results = fastreq(
    urls=["https://httpbin.org/get"],
    backend="httpx",
    # Backend can expose additional options
)
```

## Connection Pooling by Backend

All backends support connection pooling:

```python
from fastreq import fastreq

# Connection pooling is automatic
results = fastreq(
    urls=["https://api.example.com/data"] * 100,
    concurrency=20,
    backend="niquests",
)

# Same request reuses connections (if using context manager)
```

## Session Reuse with Context Manager

Reuse sessions across multiple batches:

```python
import asyncio
from fastreq import FastRequests

async def reuse_session():
    async with FastRequests(backend="niquests") as client:
        # First batch
        results1 = await client.request(
            urls=["https://api.github.com/repos/python/cpython"],
        )

        # Second batch (reuses session)
        results2 = await client.request(
            urls=["https://api.github.com/repos/python/pypy"],
        )

        return results1, results2

results1, results2 = asyncio.run(reuse_session())
```

## Error Handling by Backend

Different backends handle errors differently:

```python
from fastreq import fastreq

try:
    results = fastreq(
        urls=["https://invalid-url.com"],
        backend="niquests",
    )
except Exception as e:
    print(f"niquests error: {e}")

try:
    results = fastreq(
        urls=["https://invalid-url.com"],
        backend="httpx",
    )
except Exception as e:
    print(f"httpx error: {e}")
```

## Backend-Specific Timeout Handling

Timeouts work consistently across backends:

```python
from fastreq import fastreq

# Timeout works the same for all backends
results = fastreq(
    urls=["https://httpbin.org/delay/5"],
    timeout=3,  # 3 second timeout
    backend="niquests",  # or "httpx"
)
```

## Backend Selection Strategy

### Production Recommendation

```python
from fastreq import fastreq

# Use auto-detection for production (selects niquests by default)
results = fastreq(
    urls=["https://api.example.com/data"] * 100,
    backend="auto",  # Will pick niquests
    concurrency=20,
)
```

### Development Strategy

```python
# During development, test with both backends
for backend in ["niquests", "httpx"]:
    try:
        results = fastreq(
            urls=test_urls,
            backend=backend,
        )
        print(f"{backend}: OK")
    except Exception as e:
        print(f"{backend}: FAILED - {e}")
```

## Best Practices

1. **Use Auto-Detection**: Let the library choose the best backend
   ```python
   backend="auto"  # Default
   ```

2. **Prefer niquests or httpx**: For HTTP/2 support and modern async API
   ```python
   backend="niquests"  # or "httpx"
   ```

3. **Test Both Backends**: Verify compatibility during development
   ```python
   for backend in ["niquests", "httpx"]:
       # Test code
   ```

4. **Handle Backend Errors**: Catch backend-specific errors
   ```python
   except Exception as e:
       print(f"Backend error: {e}")
   ```

5. **Use Context Managers**: Reuse sessions for better performance
   ```python
   async with FastRequests() as client:
       await client.request(urls=urls)
   ```

## See Also

- **[Make Parallel Requests](make-fastreq.md)** - Request configuration
- **[Stream Large Files](stream-large-files.md)** - Backend streaming differences
- **[API Reference](../reference/backend.md)** - Backend documentation

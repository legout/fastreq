# Debug Issues

Learn how to troubleshoot common problems and enable debug logging.

## Enabling Debug Logging

Use `debug=True` to enable verbose logging:

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://httpbin.org/get"] * 5,
    debug=True,  # Enable debug logging
)
```

Debug output includes:
- Backend selection
- Request start/stop times
- Retry attempts
- Rate limiting info
- Proxy usage
- Error details

## Disabling Progress Bars

Use `verbose=False` to disable progress bars:

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://httpbin.org/get"] * 100,
    verbose=False,  # Quiet mode, no progress bar
)
```

## Checking Backend Availability

Verify which backends are installed:

```python
from fastreq.backends import get_available_backends

available = get_available_backends()
print(f"Available backends: {available}")

# Expected output: ['niquests', 'httpx'] (httpx only if installed)
```

## Testing Backend Connectivity

Test if a backend works:

```python
from fastreq import fastreq

def test_backend(backend_name):
    try:
        results = fastreq(
            urls=["https://httpbin.org/get"],
            backend=backend_name,
            timeout=5,
            debug=True,
        )
        print(f"{backend_name}: OK")
        return True
    except Exception as e:
        print(f"{backend_name}: FAILED - {e}")
        return False

for backend in ["niquests", "httpx"]:
    test_backend(backend)
```

## Debugging Rate Limiting

See rate limiting behavior:

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://api.example.com/data"] * 20,
    rate_limit=5,
    rate_limit_burst=10,
    debug=True,  # Shows rate limiting logs
)
```

Example output:
```
[DEBUG] Rate limit: 5.0 req/s, burst: 10
[DEBUG] Request 1: immediate (bucket: 9/10)
[DEBUG] Request 2: immediate (bucket: 8/10)
...
[DEBUG] Request 11: waiting 0.2s for token
```

## Debugging Retry Attempts

Monitor retry behavior:

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

## Debugging Proxy Issues

See which proxy is being used:

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://httpbin.org/ip"] * 5,
    proxies=[
        "http://proxy1:8080",
        "http://proxy2:8080",
    ],
    debug=True,
)
```

## Common Issues and Solutions

### Issue: Backend Not Available

**Error:** `BackendError: No suitable backend found`

**Solution:** This should not happen since niquests is a required dependency. If it does, reinstall fastreq:

```bash
pip install --force-reinstall fastreq
```

For optional httpx backend:

```bash
pip install fastreq[httpx]
```

### Issue: Requests Timing Out

**Error:** `TimeoutError` or `ReadTimeout`

**Solution:** Increase timeout or check network:

```python
from fastreq import fastreq

# Increase timeout
results = fastreq(
    urls=["https://httpbin.org/delay/10"],
    timeout=15,  # Increase from default
)

# Test network connectivity
import niquests
niquests.get("https://httpbin.org/get", timeout=5)
```

### Issue: Rate Limit Exceeded

**Error:** `RateLimitExceededError` or HTTP 429

**Solution:** Adjust rate limiting:

```python
from fastreq import fastreq

# Lower rate limit
results = fastreq(
    urls=["https://api.example.com/data"] * 100,
    rate_limit=5,           # Reduce from 10
    rate_limit_burst=5,      # Reduce from 10
    dont_retry_on=[429],     # Don't retry rate limit
)
```

### Issue: Proxy Connection Failed

**Error:** `ProxyError` or `ConnectionError`

**Solution:** Test proxy configuration:

```python
import niquests

# Test proxy manually
try:
    response = niquests.get(
        "https://httpbin.org/ip",
        proxies={"http": "http://proxy1:8080"},
        timeout=10,
    )
    print(f"Proxy working: {response.json()['origin']}")
except Exception as e:
    print(f"Proxy failed: {e}")
```

### Issue: HTTP/2 Not Working

**Error:** HTTP/2 not available

**Solution:** Ensure niquests is installed (it's the default):

```bash
# Verify niquests
python -c "import niquests; print('niquests installed')"
```

```python
from fastreq import fastreq

# Force niquests backend
results = fastreq(
    urls=["https://httpbin.org/get"],
    backend="niquests",
    debug=True,
)
```

### Issue: SSL Certificate Errors

**Error:** `SSLError` or certificate validation failed

**Solution:** Verify SSL certificates or disable (not recommended for production):

```python
from fastreq import fastreq

# Note: Disabling SSL verification is not recommended for production
# This is for debugging only
import ssl
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
```

### Issue: Partial Failures

**Error:** `PartialFailureError`

**Solution:** Handle partial failures gracefully:

```python
from fastreq import fastreq, PartialFailureError

urls = [
    "https://api.github.com/repos/python/cpython",
    "https://invalid-url.com",
    "https://api.github.com/repos/python/pypy",
]

try:
    results = fastreq(urls=urls)
except PartialFailureError as e:
    print(f"Partial failure: {e.successes}/{e.total}")
    print(f"Failed URLs: {e.get_failed_urls()}")

    # Optionally retry failed URLs
    failed_urls = list(e.get_failed_urls())
    if failed_urls:
        print(f"Retrying {len(failed_urls)} failed URLs...")
        results = fastreq(urls=failed_urls)
```

### Issue: High Memory Usage

**Error:** Out of memory or slow performance

**Solution:** Use streaming for large files:

```python
from fastreq import fastreq

# Use streaming instead of loading entire response
def stream_handler(response, url):
    with open(f"output_{url.split('/')[-1]}", "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

results = fastreq(
    urls=["https://example.com/large-file.zip"],
    return_type="stream",
    stream_callback=stream_handler,
)
```

## Debugging with Context Manager

Use context manager for better debugging:

```python
import asyncio
from fastreq import FastRequests

async def debug_with_context():
    async with FastRequests(debug=True) as client:
        # First batch
        results1 = await client.request(
            urls=["https://api.github.com/repos/python/cpython"],
        )

        # Second batch (reuses session)
        results2 = await client.request(
            urls=["https://api.github.com/repos/python/pypy"],
        )

        return results1, results2

results1, results2 = asyncio.run(debug_with_context())
```

## Logging Configuration

Use Python logging for custom logging:

```python
import logging
from fastreq import fastreq

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Make requests
results = fastreq(
    urls=["https://httpbin.org/get"] * 5,
    debug=True,
)
```

## Debug Checklist

Use this checklist when debugging:

1. **Backend Available?**
   ```python
   from fastreq.backends import get_available_backends
   print(get_available_backends())
   ```

2. **Network Working?**
   ```python
   import niquests
   niquests.get("https://httpbin.org/get", timeout=5)
   ```

3. **URLs Valid?**
   ```python
   from urllib.parse import urlparse
   for url in urls:
       parsed = urlparse(url)
       print(f"{url}: {parsed.scheme}, {parsed.netloc}")
   ```

4. **Proxy Working?**
   ```python
   import niquests
   niquests.get("https://httpbin.org/ip", proxies={"http": "http://proxy:8080"})
   ```

5. **Rate Limits Correct?**
   ```python
   # Check API documentation for rate limits
   # Use rate_limit below documented limit
   ```

## Best Practices

1. **Enable Debug Logging Early**: Turn on debug when troubleshooting
   ```python
   debug=True
   ```

2. **Test Simple Cases First**: Start with a single URL
   ```python
   fastreq(urls=["https://httpbin.org/get"])
   ```

3. **Check Dependencies**: Verify backends are installed
   ```python
   pip install fastreq  # niquests included by default
   pip install fastreq[httpx]  # optional httpx backend
   ```

4. **Monitor Memory**: Use streaming for large responses
   ```python
   return_type="stream"
   ```

5. **Handle Errors Gracefully**: Use try-except blocks
   ```python
   except Exception as e:
       print(f"Error: {e}")
   ```

## See Also

- **[Handling Errors](../tutorials/handling-errors.md)** - Complete error handling guide
- **[Handle Retries](handle-retries.md)** - Configure retry logic
- **[API Reference](../reference/configuration.md)** - Configuration options

# Use Proxies

Learn how to configure proxy rotation and integrate with proxy providers.

## Proxy Policy

fastreq uses **explicit proxy pools only** — no automatic discovery of free/public proxies.

Proxies are provided through one of three methods:

1. **Explicit proxy list** — pass `proxies=[...]` in code
2. **Environment variable** — set `FASTREQ_PROXIES`
3. **Webshare file** — set `webshare_file` to a file path containing proxy entries

This is a deliberate design choice: free/public proxies are unreliable, slow, and often abused. Production scraping should use a paid proxy service (e.g., Webshare.io, Bright Data) or your own infrastructure.

## Setting Up Proxies

Proxies can be configured via environment variable or code:

### Using Environment Variables

Set the `FASTREQ_PROXIES` environment variable:

```bash
export FASTREQ_PROXIES="http://proxy1:8080,http://proxy2:8080,socks5://proxy3:1080"
```

### Using .env File

Create a `.env` file:

```env
# .env
FASTREQ_PROXIES=http://proxy1:8080,http://proxy2:8080,socks5://proxy3:1080
```

Load with python-dotenv:

```python
from dotenv import load_dotenv
from fastreq import fastreq

load_dotenv()

results = fastreq(
    urls=["https://httpbin.org/ip"] * 5,
)
```

### Using Code Configuration

Pass `proxies` directly:

```python
from fastreq import fastreq

proxies = [
    "http://proxy1.example.com:8080",
    "http://proxy2.example.com:8080",
    "socks5://proxy3.example.com:1080",
]

results = fastreq(
    urls=["https://httpbin.org/ip"] * 10,
    proxies=proxies,
)
```

### Using a Webshare File

Point `webshare_file` to a file containing one proxy per line (`IP:PORT:USER:PASS` format):

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://httpbin.org/ip"] * 10,
    webshare_file="/path/to/proxies.txt",
)
```

## Proxy Rotation

The library automatically rotates through the proxy list:

```python
from fastreq import fastreq

proxies = [
    "http://proxy1:8080",
    "http://proxy2:8080",
    "http://proxy3:8080",
]

results = fastreq(
    urls=["https://httpbin.org/ip"] * 9,
    proxies=proxies,
)

# Requests are distributed across proxies
# proxy1: requests 1, 4, 7
# proxy2: requests 2, 5, 8
# proxy3: requests 3, 6, 9
```

## WebShare.io Integration

Use WebShare.io rotating proxies:

```python
import os
from fastreq import fastreq

# Set WebShare.io proxy (or use environment variable)
webshare_proxy = f"http://{os.getenv('WEBSHARE_USERNAME')}:{os.getenv('WEBSHARE_PASSWORD')}@p.webshare.io:80"

results = fastreq(
    urls=["https://httpbin.org/ip"] * 10,
    proxies=[webshare_proxy],
)
```

### WebShare.io in .env File

```env
# .env
WEBSHARE_USERNAME=your_username
WEBSHARE_PASSWORD=your_password
FASTREQ_PROXIES=http://${WEBSHARE_USERNAME}:${WEBSHARE_PASSWORD}@p.webshare.io:80
```

## Verifying Proxy Usage

Use httpbin.org to verify which proxy was used:

```python
from fastreq import fastreq

proxies = [
    "http://proxy1.example.com:8080",
    "http://proxy2.example.com:8080",
]

results = fastreq(
    urls=["https://httpbin.org/ip"] * 6,
    proxies=proxies,
)

for result in results:
    print(f"IP: {result['origin']}")
```

## Proxy Authentication

Use authenticated proxies:

```python
from fastreq import fastreq

proxies = [
    "http://user:pass@proxy1.example.com:8080",
    "http://user:pass@proxy2.example.com:8080",
]

results = fastreq(
    urls=["https://httpbin.org/ip"] * 5,
    proxies=proxies,
)
```

**Security Note**: Avoid hardcoding credentials. Use environment variables instead:

```python
import os
from fastreq import fastreq

proxies = [
    f"http://{os.getenv('PROXY_USER')}:{os.getenv('PROXY_PASS')}@proxy1:8080",
]

results = fastreq(
    urls=["https://httpbin.org/ip"] * 5,
    proxies=proxies,
)
```

## Different Proxy Types

The library supports HTTP, HTTPS, and SOCKS5 proxies:

```python
from fastreq import fastreq

proxies = [
    "http://proxy.example.com:8080",      # HTTP proxy
    "https://secure-proxy.com:443",        # HTTPS proxy
    "socks5://socks-proxy.com:1080",      # SOCKS5 proxy
]

results = fastreq(
    urls=["https://httpbin.org/ip"] * 6,
    proxies=proxies,
)
```

## Proxy-Specific URLs

Route specific URLs through different proxies:

```python
from fastreq import fastreq

results = fastreq(
    urls=[
        "https://api.github.com/repos/python/cpython",
        "https://api.github.com/repos/python/pypy",
    ],
    proxies=[
        "http://proxy-github:8080",  # First URL
        "http://proxy-github:8080",  # Second URL
    ],
)
```

## No Proxy Configuration

To bypass proxy for specific domains:

```python
import os
os.environ['NO_PROXY'] = 'localhost,127.0.0.1,.local'

from fastreq import fastreq

results = fastreq(
    urls=["https://httpbin.org/ip"],
)
```

## Troubleshooting Proxy Issues

### Test Proxy Connectivity

Test if a proxy works:

```python
import niquests

try:
    response = niquests.get(
        "https://httpbin.org/ip",
        proxies={"http": "http://proxy.example.com:8080"},
        timeout=10,
    )
    print(f"Proxy working: {response.json()['origin']}")
except Exception as e:
    print(f"Proxy failed: {e}")
```

### Enable Debug Logging

See which proxy is being used:

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://httpbin.org/ip"] * 3,
    proxies=["http://proxy1:8080", "http://proxy2:8080"],
    debug=True,
)
```

### Common Proxy Errors

```python
from fastreq import fastreq, ProxyError

try:
    results = fastreq(
        urls=["https://httpbin.org/ip"],
        proxies=["http://invalid-proxy:8080"],
    )
except ProxyError as e:
    print(f"Proxy error: {e}")
    # Check proxy address, port, and authentication
```

## Best Practices

1. **Use Environment Variables**: Store proxy URLs in `.env` files
2. **Monitor Proxy Health**: Check proxy status before large batches
3. **Handle Failures**: Use `return_none_on_failure` for unreliable proxies
4. **Rotate Properly**: Use enough proxies to distribute load
5. **Use Paid Services**: Free/public proxies are unreliable for production — use a paid service like Webshare.io

## Example: Robust Proxy Configuration

```python
import os
from dotenv import load_dotenv
from fastreq import fastreq

load_dotenv()

# Load proxies from environment
proxies_str = os.getenv("FASTREQ_PROXIES", "")
proxies = [p.strip() for p in proxies_str.split(",") if p.strip()]

# Add authenticated proxy if configured
webshare_user = os.getenv("WEBSHARE_USERNAME")
webshare_pass = os.getenv("WEBSHARE_PASSWORD")
if webshare_user and webshare_pass:
    webshare_proxy = f"http://{webshare_user}:{webshare_pass}@p.webshare.io:80"
    proxies.append(webshare_proxy)

# Make requests with fallback
results = fastreq(
    urls=["https://httpbin.org/ip"] * 10,
    proxies=proxies if proxies else None,
    max_retries=2,
    return_none_on_failure=True,
    debug=True,
)

# Filter successful results
successful = [r for r in results if r is not None]
print(f"Successful requests: {len(successful)}/{len(results)}")
```

## See Also

- **[Debug Issues](debug-issues.md)** - Troubleshoot proxy problems
- **[Handle Retries](handle-retries.md)** - Configure retry logic for unreliable proxies
- **[API Reference](../reference/configuration.md)** - Configuration options

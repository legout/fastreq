# Proxy Rotation

Manage, validate, and rotate HTTP proxies with automatic health tracking.

## ProxyPool

Main proxy pool class for proxy rotation and validation.

```python
from fastreq.utils.proxies import ProxyPool, ProxyPoolConfig

config = ProxyPoolConfig(
    proxies=[
        "192.168.1.1:8080",
        "192.168.1.2:8080:user:pass",
    ],
    cooldown=60.0,
)

pool = ProxyPool(config=config)

# Get next available proxy
proxy = await pool.acquire()

# Mark proxy as failed
await pool.mark_failed(proxy)

# Mark proxy as successful
await pool.mark_success(proxy)
```

### ProxyPool Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `acquire()` | `str \| None` | Get next available proxy |
| `mark_failed(proxy)` | `None` | Mark proxy as failed (enters cooldown) |
| `mark_success(proxy)` | `None` | Mark proxy as successful (clears cooldown) |
| `count()` | `int` | Get total proxy count |
| `count_available()` | `int` | Get available proxy count |

---

## ProxyPoolConfig

Configuration for proxy rotation.

```python
from fastreq.utils.proxies import ProxyPoolConfig, ProxySelection

config = ProxyPoolConfig(
    proxies=["192.168.1.1:8080"],                # Proxy list
    selection=ProxySelection.ROUND_ROBIN,         # Selection strategy
    cooldown=60.0,                               # Seconds before retrying failed proxy
)
```

### ProxyPoolConfig Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `proxies` | `list[str] \| None` | `None` | List of proxy URLs |
| `selection` | `ProxySelection` | `ROUND_ROBIN` | Selection strategy (round_robin or random) |
| `cooldown` | `float` | `60.0` | Seconds before retrying failed proxy |

---

## Proxy Formats

### Supported Formats

1. **IP:PORT**
   ```python
   "192.168.1.1:8080"
   ```

2. **IP:PORT:USER:PASS**
   ```python
   "192.168.1.1:8080:admin:password"
   ```

3. **http://USER:PASS@HOST:PORT**
   ```python
   "http://user:pass@proxy.example.com:8080"
   ```

4. **https://USER:PASS@HOST:PORT**
   ```python
   "https://user:pass@proxy.example.com:8080"
   ```

### Proxy Validation

```python
from fastreq.utils.proxies import _is_valid_proxy

# Validate proxy format
is_valid = _is_valid_proxy("192.168.1.1:8080")  # True
is_valid = _is_valid_proxy("invalid-proxy")     # False
```

### IP Validation

IP octets are validated to be in range 0-255:

```python
# Valid
"192.168.1.1:8080"    # True

# Invalid
"256.168.1.1:8080"    # False (256 > 255)
"192.168.1:8080"      # False (missing octet)
```

---

## Loading Proxies

### From Configuration

```python
from fastreq.utils.proxies import ProxyPool, ProxyPoolConfig

config = ProxyPoolConfig(
    proxies=[
        "192.168.1.1:8080",
        "192.168.1.2:8080:user:pass",
    ],
)
pool = ProxyPool(config=config)
```

### From Environment Variable

```bash
# .env or environment
FASTREQ_PROXIES=192.168.1.1:8080,192.168.1.2:8080,http://user:pass@proxy:8080
```

```python
from fastreq.utils.proxies import ProxyPool

pool = ProxyPool.from_env()  # Loads from FASTREQ_PROXIES env var
```

### From Webshare

```python
from fastreq.utils.proxies import ProxyPool

# Load from Webshare plain-text (IP:PORT:USER:PASS per line)
pool = ProxyPool.from_webshare_text(webshare_text)
```

Webshare format: One per line, `IP:PORT:USER:PASS`

---

## Proxy Health Tracking

### Failed Proxies

Failed proxies are temporarily excluded from rotation:

```python
from fastreq.utils.proxies import ProxyPool, ProxyPoolConfig

config = ProxyPoolConfig(
    proxies=["proxy1:8080", "proxy2:8080", "proxy3:8080"],
    cooldown=60.0,  # Retry failed proxies after 60s
)

pool = ProxyPool(config=config)

# Proxy fails
proxy = await pool.acquire()  # e.g., "proxy1:8080"
await pool.mark_failed(proxy)   # Excluded for 60s

# Next request gets different proxy
next_proxy = await pool.acquire()  # "proxy2:8080" (not proxy1)

# After 60s, proxy1 is available again
```

### Successful Proxies

Successful proxies are cleared from failed state:

```python
proxy = await pool.acquire()
# Make request
try:
    result = await make_request(proxy)
    await pool.mark_success(proxy)  # Clear failed status
except Exception:
    await pool.mark_failed(proxy)
```

### Monitoring

```python
# Total proxies
total = pool.count()

# Available proxies (not in cooldown)
available = pool.count_available()

# Failed proxies
failed = total - available
```

---

## Using Proxy Rotation

### In FastRequests Client

```python
from fastreq import FastRequests

# Enable proxy rotation
client = FastRequests(
    random_proxy=True,
    proxy="http://proxy:8080",  # Base proxy
)
```

### Standalone Usage

```python
from fastreq.utils.proxies import ProxyPool, ProxyPoolConfig

config = ProxyPoolConfig(
    proxies=["proxy1:8080", "proxy2:8080"],
)
pool = ProxyPool(config=config)

async def make_request(url):
    proxy = await pool.acquire()
    if not proxy:
        raise Exception("No proxies available")

    try:
        response = await fetch(url, proxy=proxy)
        await pool.mark_success(proxy)
        return response
    except Exception as e:
        await pool.mark_failed(proxy)
        raise e

results = await asyncio.gather(*[make_request(url) for url in urls])
```

---

## Proxy Validation Patterns

Regex patterns for proxy validation:

```python
PROXY_PATTERNS = [
    r"^(\d{1,3}\.){3}\d{1,3}:\d{1,5}$",                    # IP:PORT
    r"^(\d{1,3}\.){3}\d{1,3}:\d{1,5}:[^:]+:[^:]+$",        # IP:PORT:USER:PASS
    r"^http://[^:]+:[^@]+@[^:]+:\d+$",                     # http://user:pass@host:port
    r"^https://[^:]+:[^@]+@[^:]+\d+$",                     # https://user:pass@host:port
]
```

---

## ProxyError

Raised when proxy validation or loading fails:

```python
from fastreq.utils.proxies import ProxyError

try:
    pool = ProxyPool.from_webshare_text("invalid-text")
except ProxyError as e:
    print(f"Proxy validation error: {e}")
```

---

## See Also

- [How-to: Use Proxies](../how-to-guides/use-proxies.md)
- [Reference: Exceptions](exceptions.md)

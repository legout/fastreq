# Validation

Input validation functions for URLs, proxies, headers, and more.

## validate_url()

Validate URL format (must start with http:// or https://).

```python
from fastreq.utils.validators import validate_url

is_valid = validate_url("https://example.com")  # True
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | URL string to validate |

### Returns

`bool` - `True` if valid

### Raises

`ValidationError` - If URL is invalid

### Examples

```python
from fastreq.utils.validators import validate_url, ValidationError

# Valid URLs
validate_url("https://example.com")           # True
validate_url("http://example.com/path")      # True

# Invalid URLs (raises ValidationError)
try:
    validate_url("ftp://example.com")
except ValidationError as e:
    print(f"Invalid URL: {e}")
    # ValidationError: Invalid URL: ftp://example.com. Must start with http:// or https://

try:
    validate_url("not-a-url")
except ValidationError as e:
    print(f"Invalid URL: {e}")
```

### Validation Pattern

```python
pattern = r"^https?://.+"
```

---

## validate_proxy()

Validate proxy URL format.

```python
from fastreq.utils.validators import validate_proxy

is_valid = validate_proxy("192.168.1.1:8080")  # True
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `proxy` | `str` | Proxy URL string to validate |

### Returns

`bool` - `True` if valid format, `False` otherwise

### Valid Formats

1. **IP:PORT**
   ```python
   "192.168.1.1:8080"
   ```

2. **IP:PORT:USER:PASS**
   ```python
   "192.168.1.1:8080:admin:password"
   ```

3. **http://user:pass@host:port**
   ```python
   "http://user:pass@proxy.example.com:8080"
   ```

4. **https://user:pass@host:port**
   ```python
   "https://user:pass@proxy.example.com:8080"
   ```

### Examples

```python
# Valid proxies
validate_proxy("192.168.1.1:8080")                      # True
validate_proxy("192.168.1.1:8080:user:pass")            # True
validate_proxy("http://user:pass@proxy:8080")           # True
validate_proxy("https://user:pass@proxy:8080")          # True

# Invalid proxies
validate_proxy("not-a-proxy")          # False
validate_proxy("192.168.1.1")          # False (missing port)
validate_proxy("")                     # False
validate_proxy(None)                   # False
```

### Validation Patterns

```python
ip_port_simple = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$"
ip_port_with_auth = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+:\w+:\w+$"
http_url = r"^https?://.+"
```

---

## validate_headers()

Validate headers dictionary.

```python
from fastreq.utils.validators import validate_headers

is_valid = validate_headers({
    "Content-Type": "application/json",
    "Authorization": "Bearer token"
})  # True
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `headers` | `dict[str, Any]` | Headers dictionary to validate |

### Returns

`bool` - `True` if valid

### Raises

`ValidationError` - If headers are invalid

### Validation Rules

- `headers` must be a dictionary
- All keys must be strings
- All values must be strings

### Examples

```python
from fastreq.utils.validators import validate_headers, ValidationError

# Valid headers
validate_headers({
    "Content-Type": "application/json",
    "Authorization": "Bearer token",
})  # True

# Invalid headers (raises ValidationError)
try:
    validate_headers("not-a-dict")
except ValidationError as e:
    print(f"Invalid headers: {e}")
    # ValidationError: Headers must be a dictionary

try:
    validate_headers({123: "value"})  # Key not string
except ValidationError as e:
    print(f"Invalid headers: {e}")
    # ValidationError: Header key must be a string, got int

try:
    validate_headers({"key": 123})  # Value not string
except ValidationError as e:
    print(f"Invalid headers: {e}")
    # ValidationError: Header value for key 'key' must be a string, got int
```

---

## normalize_urls()

Normalize URLs to list format.

```python
from fastreq.utils.validators import normalize_urls

# Single URL → list
result = normalize_urls("https://example.com")
# ["https://example.com"]

# List of URLs → list (unchanged)
result = normalize_urls(["https://a.com", "https://b.com"])
# ["https://a.com", "https://b.com"]

# None → None
result = normalize_urls(None)
# None
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `urls` | `str \| list[str] \| None` | Single URL, list of URLs, or None |

### Returns

`list[str] \| None` - List of URLs or None

### Examples

```python
from fastreq.utils.validators import normalize_urls

# Single string
normalize_urls("https://example.com")
# ["https://example.com"]

# List of strings
normalize_urls(["https://a.com", "https://b.com", "https://c.com"])
# ["https://a.com", "https://b.com", "https://c.com"]

# None
normalize_urls(None)
# None

# Empty list
normalize_urls([])
# []
```

---

## Using Validation Functions

### Manual Validation

```python
from fastreq.utils.validators import (
    validate_url,
    validate_proxy,
    validate_headers,
    normalize_urls,
)

# Validate URL
if validate_url("https://example.com"):
    print("URL is valid")

# Validate proxy
if validate_proxy("192.168.1.1:8080"):
    print("Proxy is valid")

# Validate headers
try:
    validate_headers({"Content-Type": "application/json"})
    print("Headers are valid")
except ValidationError as e:
    print(f"Invalid headers: {e}")

# Normalize URLs
urls = normalize_urls("https://example.com")
print(urls)  # ["https://example.com"]
```

### Integration with FastRequests

FastRequests uses these validators internally:

```python
from fastreq import FastRequests

async with FastRequests() as client:
    # URLs are validated internally
    results = await client.request("https://example.com")

    # Headers are validated internally
    results = await client.request(
        "https://example.com",
        headers={"Authorization": "Bearer token"}
    )
```

---

## ValidationError

Base validation error with `field_name` attribute.

```python
from fastreq.exceptions import ValidationError

try:
    validate_url("invalid-url")
except ValidationError as e:
    print(f"Field '{e.field_name}' failed validation")
    # Field 'url' failed validation
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `message` | `str` | Error message |
| `field_name` | `str \| None` | Name of the field that failed |

---

## See Also

- [Reference: Exceptions](exceptions.md)
- [How-to: Debug Issues](../how-to-guides/debug-issues.md)

# Backend Interface

The backend abstraction provides a consistent interface across different HTTP client libraries.

## Backend Base Class

All backends must inherit from `Backend` and implement its abstract methods.

```python
from fastreq.backends.base import Backend

class CustomBackend(Backend):
    @property
    def name(self) -> str:
        return "custom"

    async def request(self, config: RequestConfig) -> NormalizedResponse:
        # Implementation
        pass

    async def close(self) -> None:
        # Cleanup
        pass

    async def __aenter__(self) -> "Backend":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    def supports_http2(self) -> bool:
        return False
```

### Backend Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `name` | `str` | Backend identifier |
| `request()` | `NormalizedResponse` | Execute HTTP request |
| `close()` | `None` | Clean up resources |
| `__aenter__()` | `Backend` | Initialize backend |
| `__aexit__()` | `None` | Cleanup on exit |
| `supports_http2()` | `bool` | HTTP/2 support |

---

## RequestConfig

Configuration for a single HTTP request. Used internally by backends.

```python
from fastreq.backends.base import RequestConfig

config = RequestConfig(
    url="https://example.com",
    method="GET",
    params={"key": "value"},
    data=b"raw data",
    json={"key": "value"},
    headers={"Authorization": "Bearer token"},
    cookies={"session": "abc123"},
    timeout=30.0,
    proxy="http://proxy:8080",
    http2=True,
    stream=False,
    follow_redirects=True,
    verify_ssl=True,
)
```

### RequestConfig Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | required | Request URL |
| `method` | `str` | `"GET"` | HTTP method |
| `params` | `dict[str, Any] \| None` | `None` | Query parameters |
| `data` | `Any` | `None` | Request body data |
| `json` | `Any` | `None` | JSON body |
| `headers` | `dict[str, str] \| None` | `None` | Request headers |
| `cookies` | `dict[str, str] \| None` | `None` | Request cookies |
| `timeout` | `float \| None` | `None` | Timeout in seconds |
| `proxy` | `str \| None` | `None` | Proxy URL |
| `http2` | `bool` | `True` | Enable HTTP/2 |
| `stream` | `bool` | `False` | Enable streaming |
| `follow_redirects` | `bool` | `True` | Follow redirects |
| `verify_ssl` | `bool` | `True` | Verify SSL |

---

## NormalizedResponse

Normalized response from HTTP backends with a consistent interface.

```python
from fastreq.backends.base import NormalizedResponse

response = NormalizedResponse(
    status_code=200,
    headers={"content-type": "application/json"},
    content=b'{"key": "value"}',
    text='{"key": "value"}',
    json_data={"key": "value"},
    url="https://example.com",
    is_json=True,
)
```

### NormalizedResponse Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `status_code` | `int` | HTTP status code |
| `headers` | `dict[str, str]` | Response headers (lowercase keys) |
| `content` | `bytes` | Raw response body |
| `text` | `str` | Decoded response body |
| `json_data` | `Any` | Parsed JSON data |
| `url` | `str` | Final URL (after redirects) |
| `is_json` | `bool` | Whether response is valid JSON |

### NormalizedResponse Methods

#### from_backend()

Create `NormalizedResponse` from backend response.

```python
response = NormalizedResponse.from_backend(
    status_code=200,
    headers={"Content-Type": "application/json"},
    content=b'{"key": "value"}',
    url="https://example.com",
    is_json=True,
)
```

#### _normalize_headers()

Normalize headers by converting all keys to lowercase.

```python
headers = NormalizedResponse._normalize_headers({
    "Content-Type": "application/json",
    "Authorization": "Bearer token"
})
# Returns: {'content-type': '...', 'authorization': '...'}
```

---

## Backend Implementations

### Available Backends

| Backend | HTTP/2 | Description |
|---------|--------|-------------|
| `niquests` | ✅ | Default backend, high performance |
| `httpx` | ✅ | Optional backend, modern async |

### Using Backends

```python
# Auto-select (recommended, selects niquests by default)
client = FastRequests(backend="auto")

# Specific backend
client = FastRequests(backend="niquests")  # or "httpx"
```

### Backend Initialization

Backends are initialized with HTTP/2 configuration:

```python
from fastreq.backends.niquests import NiquestsBackend

backend = NiquestsBackend(http2_enabled=True)

async with backend:
    response = await backend.request(config)
```

---

## Custom Backend Implementation

Create a custom backend:

```python
from fastreq.backends.base import Backend, RequestConfig, NormalizedResponse
import httpx

class HttpxBackend(Backend):
    def __init__(self, http2_enabled: bool = True):
        super().__init__(http2_enabled)
        self._client = None

    @property
    def name(self) -> str:
        return "httpx"

    async def __aenter__(self) -> "Backend":
        self._client = httpx.AsyncClient(http2=self._http2_enabled)
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()

    async def request(self, config: RequestConfig) -> NormalizedResponse:
        if not self._client:
            raise RuntimeError("Backend not initialized")

        response = await self._client.request(
            method=config.method,
            url=config.url,
            params=config.params,
            data=config.data,
            json=config.json,
            headers=config.headers,
            cookies=config.cookies,
            timeout=config.timeout,
            proxy=config.proxy,
            follow_redirects=config.follow_redirects,
            verify=config.verify_ssl,
        )

        return NormalizedResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
            url=str(response.url),
            is_json=response.headers.get("content-type", "").startswith("application/json"),
        )

    def supports_http2(self) -> bool:
        return True
```

---

## See Also

- [How-to: Select a Backend](../how-to-guides/select-backend.md)

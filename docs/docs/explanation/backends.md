# Backends

The fastreq library supports two HTTP backends, each with different capabilities and trade-offs.

## Overview

| Backend | HTTP/2 | Streaming | Async Native | Notes |
|---------|--------|----------|--------------|-------|
| **niquests** | ✓ | ✓ | ✓ | Default, required dependency |
| **httpx** | ✓* | ✓ | ✓ | Optional, modern API |

*HTTP/2 requires httpx[http2] extra (installs h2 package)

## Auto-Detection Order

When `backend="auto"` (default), the library checks backends in this order:

1. **niquests** - HTTP/2 support, streaming, async native (default)
2. **httpx** - HTTP/2 support (with h2 extra), modern async API

The first available backend is used. Since niquests is a required dependency, it will always be selected unless you explicitly request httpx.

## Niquests Backend

### Capabilities

- **HTTP/2 Support**: Native HTTP/2 with multiplexing
- **Streaming**: Full streaming support for large files
- **Async Native**: Built on async I/O from the ground up
- **Connection Reuse**: Efficient connection pooling

### When to Use

- **Default choice** for most use cases
- **HTTP/2 APIs** (e.g., some modern web services)
- **High-throughput scenarios** where connection reuse matters
- **Large file downloads** with streaming

### Implementation Details

```python
class NiquestsBackend(Backend):
    async def __init__(self, http2_enabled: bool = True):
        self._session = niquests.AsyncSession(
            disable_http2=not http2_enabled
        )

    async def request(self, config: RequestConfig) -> NormalizedResponse:
        response = await self._session.request(**kwargs)
        # Handles streaming automatically
        if config.stream:
            content = await response.content
        else:
            content = response.content
```

### Performance Characteristics

- **HTTP/2 Multiplexing**: Multiple requests over single connection
- **Low Overhead**: Async native, minimal thread usage
- **Efficient Streaming**: Memory-efficient for large responses

## Httpx Backend

### Capabilities

- **HTTP/2 Support**: Native HTTP/2 when `h2` extra is installed
- **Streaming**: Full streaming support for large files
- **Async Native**: Built on async I/O with httpx.AsyncClient
- **Modern API**: Clean, well-designed interface
- **Connection Reuse**: Efficient connection pooling

### When to Use

- **Prefer httpx** for new projects or if you already use httpx
- **HTTP/2 APIs** when you want the httpx ecosystem
- **Modern async applications** that value clean APIs
- **Large file downloads** with streaming

### Implementation Details

```python
class HttpxBackend(Backend):
    async def __init__(self, http2_enabled: bool = True):
        self._h2_available = self._check_h2_available()
        http2 = http2_enabled and self._h2_available
        self._client = httpx.AsyncClient(http2=http2)

    async def request(self, config: RequestConfig) -> NormalizedResponse:
        if config.stream:
            async with self._client.stream(**kwargs) as response:
                content = await response.aread()
        else:
            response = await self._client.request(**kwargs)
            content = response.content
```

**Note**: HTTP/2 requires the `h2` package (`pip install httpx[http2]`). Without it, the backend falls back to HTTP/1.1.

### Performance Characteristics

- **HTTP/2 Multiplexing**: When h2 is available
- **Low Overhead**: Modern async implementation
- **Efficient Streaming**: Memory-efficient for large responses
- **Modern Design**: Clean API, well-documented

## Feature Comparison Table

| Feature | niquests | httpx |
|---------|----------|-------|
| **HTTP/2** | ✓ (native) | ✓ (with h2) |
| **HTTP/1.1** | ✓ | ✓ |
| **Streaming** | ✓ | ✓ |
| **Async Native** | ✓ | ✓ |
| **Connection Pooling** | ✓ | ✓ |
| **Session Cookies** | ✓ | ✓ |
| **Thread Safe** | ✓ | ✓ |
| **Maturity** | Medium | High |
| **Installation Size** | ~2MB | ~1MB |

## Performance Considerations

### Throughput

For high-throughput scenarios, performance typically ranks:

1. **niquests** (HTTP/2): Fastest due to multiplexing
2. **httpx** (HTTP/2 with h2): Comparable performance, modern async

### Memory Usage

Both backends have similar memory characteristics for the same workload, with HTTP/2 providing fewer connections → less memory for connections.

### Latency

For single-request latency, differences are minimal. For concurrent requests:

- **HTTP/2 (niquests/httpx)**: Lower latency due to connection reuse and multiplexing
- **HTTP/1.1 (httpx without h2)**: Higher latency under high concurrency

### CPU Usage

Both backends are async native, resulting in lower CPU usage compared to synchronous libraries.

## Backend Selection Guide

### Choose niquests if:
- ✓ You want HTTP/2 support out of the box
- ✓ You need maximum performance
- ✓ You're starting a new project
- ✓ You care about connection efficiency

### Choose httpx if:
- ✓ You prefer httpx's modern API
- ✓ You need HTTP/2 with a clean async interface
- ✓ Your project uses httpx
- ✓ You value clean, well-documented APIs

## Example: Backend-Specific Behavior

### HTTP/2 Multiplexing (niquests/httpx)

With HTTP/2, multiple requests share a single connection:

```python
# With niquests (HTTP/2 enabled by default)
client = FastRequests(backend="niquests", http2=True)
# All 100 requests share 1-2 connections due to multiplexing
results = await client.request(urls=[url] * 100)

# With httpx (HTTP/2 enabled, requires h2)
client = FastRequests(backend="httpx", http2=True)
# All 100 requests share 1-2 connections due to multiplexing
results = await client.request(urls=[url] * 100)
```

The `concurrency` parameter directly limits the number of concurrent connections.

## Installation and Dependencies

### Installing with Specific Backend

```bash
# niquests is included by default
pip install fastreq

# Add httpx support (optional)
pip install fastreq[httpx]
```

### Dependency Sizes

- **niquests**: ~2MB (includes urllib3 dependencies)
- **httpx**: ~1MB (includes httpcore, h2 optional)

## Backend Internals

### Session Management

All backends implement async context managers:

```python
async with FastRequests(backend="niquests") as client:
    # Backend session is initialized here
    results = await client.request(urls=[...])
    # Backend session is closed here automatically
```

### Error Handling

Each backend catches its library-specific exceptions and wraps them in `BackendError`:

```python
# niquests
except niquests.RequestException as e:
    raise BackendError(f"Request failed: {e}", backend_name=self.name)

# httpx
except httpx.HTTPError as e:
    raise BackendError(f"Request failed: {e}", backend_name=self.name)
```

### Response Normalization

All backends return `NormalizedResponse` with consistent structure:

```python
# Regardless of backend, you get the same interface
response = await backend.request(config)
print(response.status_code)    # HTTP status code
print(response.headers)        # Headers (lowercase keys)
print(response.content)        # Raw bytes
print(response.text)           # Decoded string
print(response.json_data)      # Parsed JSON (if applicable)
print(response.url)            # Final URL (after redirects)
```

## Troubleshooting

### HTTP/2 Not Working

**Problem**: You set `http2=True` but requests are still HTTP/1.1

**Solution**: Ensure you're using niquests (default) or httpx with h2 extra:

```python
# niquests (default, HTTP/2 native)
client = FastRequests(backend="niquests", http2=True)

# httpx (requires httpx[http2] extra)
client = FastRequests(backend="httpx", http2=True)
```

### HTTP/2 with httpx

**Problem**: You want HTTP/2 with httpx but it's not working

**Solution**: Install the h2 extra:

```bash
pip install httpx[http2]
# or
pip install fastreq[httpx]
```

The backend will automatically detect if h2 is available and enable HTTP/2.

### Backend Not Found

**Problem**: `ConfigurationError: No suitable backend found`

**Solution**: This should not happen since niquests is a required dependency. If it does, reinstall fastreq:

```bash
pip install --force-reinstall fastreq
```

## Related Documentation

- **[Architecture](architecture.md)** - Design philosophy and component interaction
- **[Rate Limiting](rate-limiting.md)** - How rate limiting works with different backends
- **[Retry Strategy](retry-strategy.md)** - Retry behavior across backends

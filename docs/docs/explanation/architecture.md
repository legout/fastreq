# Architecture

The fastreq library is designed around a few core principles that enable flexible, efficient, and maintainable parallel HTTP requests.

## Design Philosophy

### Strategy Pattern

The library uses the **Strategy pattern** to support multiple HTTP backends through a common interface. This allows you to:

- Swap between niquests and httpx without changing application code
- Add new backends without modifying the client logic
- Test with different backends to find the best fit for your use case

The `Backend` abstract base class defines the contract that all backends must implement:

```python
class Backend(ABC):
    @abstractmethod
    async def request(self, config: RequestConfig) -> NormalizedResponse:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...

    @abstractmethod
    def supports_http2(self) -> bool:
        ...
```

### Async-First Design

Python's `asyncio` is the foundation of the library. All operations are asynchronous internally. The synchronous `fastreq()` function is just a thin wrapper that runs `asyncio.run()` behind the scenes.

**Why async-first?**

- **Performance**: Non-blocking I/O allows thousands of concurrent requests
- **Efficiency**: Minimal overhead with native async backends
- **Modern**: Aligns with modern Python async ecosystem
- **Flexible**: Works seamlessly in async applications and sync contexts

### Separation of Concerns

The library is organized into distinct layers:

```
┌─────────────────────────────────────────────────────────────┐
│                     User API Layer                         │
│  fastreq() / fastreq_async()
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Client Layer                              │
│           FastRequests class                                │
│  (orchestrates requests, retries, rate limiting)            │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────────────┐   ┌─────────────────┐   ┌──────────────────┐
│  Retry Layer  │   │  Rate Limiter   │   │   Utilities      │
│   (backoff)   │   │  (token bucket) │   │  (proxies, etc.) │
└───────────────┘   └─────────────────┘   └──────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Backend Layer                             │
│    NiquestsBackend │ HttpxBackend                           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                 HTTP Libraries                              │
│    niquests │ httpx                                         │
└─────────────────────────────────────────────────────────────┘
```

## Component Overview

### FastRequests (Client)

The main client class that orchestrates everything:

- **Backend selection**: Auto-detects or uses specified backend
- **Request coordination**: Runs parallel requests with concurrency control
- **Configuration**: Centralized settings for all requests
- **Context management**: Handles session lifecycle
- **Cookie management**: Maintains session cookies across requests

Located in: `src/fastreq/client.py`

### Backends

HTTP client adapters that provide a normalized interface:

- **NiquestsBackend**: Default backend, full async, HTTP/2 support, streaming
- **HttpxBackend**: Optional backend, modern async API, HTTP/2 with h2 extra

All backends implement the `Backend` interface and return `NormalizedResponse` objects.

Located in: `src/fastreq/backends/`

### Utilities

Supporting utilities that handle cross-cutting concerns:

- **Retry**: Exponential backoff with jitter for resilient requests
- **Rate Limiter**: Token bucket algorithm for request rate control
- **Proxies**: Proxy rotation and validation
- **Headers**: Header management and random user agent rotation
- **Logging**: Structured logging configuration
- **Validators**: Input validation and error handling

Located in: `src/fastreq/utils/`

## Backend Abstraction Layer

The backend abstraction is crucial for the library's flexibility. Here's how it works:

### Request Normalization

All requests go through a `RequestConfig` dataclass:

```python
@dataclass
class RequestConfig:
    url: str
    method: str = "GET"
    params: dict[str, Any] | None = None
    data: Any = None
    json: Any = None
    headers: dict[str, str] | None = None
    cookies: dict[str, str] | None = None
    timeout: float | None = None
    proxy: str | None = None
    http2: bool = True
    stream: bool = False
    follow_redirects: bool = True
    verify_ssl: bool = True
```

This normalized configuration is passed to each backend, which then translates it to the underlying library's API.

### Response Normalization

All backends return a `NormalizedResponse`:

```python
@dataclass
class NormalizedResponse:
    status_code: int
    headers: dict[str, str]      # All lowercase
    content: bytes
    text: str
    json_data: Any
    url: str
    is_json: bool = False
```

This provides a consistent interface regardless of which backend you use.

### Backend Detection Flow

```
User creates FastRequests(backend="auto")
         │
         ▼
Try importing niquests
    ├── Success → Use NiquestsBackend
    └── ImportError
         │
         ▼
Try importing httpx
    ├── Success → Use HttpxBackend
    └── ImportError
         │
         ▼
Raise ConfigurationError("No suitable backend found")
```

## How Components Interact

### Request Lifecycle

```
1. User calls client.request(urls=[...])
         │
2. Create RequestOptions for each URL
         │
3. Create async tasks for parallel execution
         │
         ┌─────────────────────────────┐
         │                             │
4. Acquire rate limit token     ┌──────────────────┐
         │                    │   Execute         │
         │                    │   Request        │
5. Acquire semaphore slot     │                  │
         │                    └──────────────────┘
         │                             │
6. Backend makes HTTP request      ┌──────────────────┐
         │                         │   Check Retry    │
         │                         │   Should we?     │
7. Get NormalizedResponse        └──────────────────┘
         │                             │
8. Parse response (JSON/text/content) ──► Yes → Wait with backoff → Retry
         │                             │        │
9. Return result                     No       └──────────────────┘
```

### Retry Integration

The retry strategy wraps the entire request execution:

```python
response = await self._retry_strategy.execute(make_request)
```

If `make_request()` fails, the retry strategy:
1. Checks if the error is retryable
2. Calculates exponential backoff delay with jitter
3. Waits the calculated time
4. Retries up to `max_retries`

### Rate Limiting Integration

Rate limiting happens just before the actual HTTP request:

```python
async with rate_limit_ctx:
    return await backend.request(config)
```

If no tokens are available:
1. Wait until tokens are refilled
2. Acquire a token
3. Proceed with request

The semaphore ensures concurrency is never exceeded, regardless of token availability.

## Design Decisions and Trade-offs

### Why Strategy Pattern for Backends?

**Benefits:**
- Easy to add new backends (just implement the interface)
- Backend selection is transparent to user code
- Backends can be swapped at runtime

**Trade-offs:**
- Requires all backends to be async
- Some library-specific features might not be exposed

### Why Token Bucket for Rate Limiting?

**Benefits:**
- Allows bursts up to `burst` size
- Smoother request pattern than fixed window
- Easy to understand and tune

**Trade-offs:**
- Requires tracking state (tokens, last refill time)
- Not as precise as leaky bucket for short timescales

### Why Exponential Backoff with Jitter?

**Benefits:**
- Prevents thundering herd problem
- Reduces load on failing services
- Jitter distributes retry attempts

**Trade-offs:**
- Increases total latency on failures
- Requires tuning for optimal results

### Why Separate Rate Limiting and Concurrency Control?

The library uses both a token bucket (rate limiting) and a semaphore (concurrency):

**Rate Limiting (Token Bucket):**
- Controls request rate (requests per second)
- Allows bursts
- Time-based control

**Concurrency (Semaphore):**
- Limits simultaneous connections
- Prevents resource exhaustion
- Count-based control

**Why both?** They solve different problems:
- Rate limiting protects remote APIs from overload
- Concurrency control protects your application from resource exhaustion

For example, with `rate_limit=10` and `concurrency=20`:
- You'll never exceed 10 requests per second
- You can have up to 20 requests waiting (10 active, 10 queued)

## Performance Characteristics

### Memory Usage

Memory scales with:
- `concurrency`: Number of concurrent requests
- Response size: Larger responses use more memory
- Queue depth: Waiting requests hold their parameters

### CPU Usage

CPU usage is primarily from:
- Async event loop management (low overhead)
- JSON parsing (scales with response size)
- Rate limiting calculations (negligible)

### Network Usage

Network behavior depends on backend:
- **niquests**: HTTP/2 multiplexing, efficient connection reuse
- **httpx**: HTTP/2 multiplexing (with h2 extra), connection pooling

## Future Extensibility

The architecture supports easy extension:

### Adding a New Backend

1. Create a new class inheriting from `Backend`
2. Implement all abstract methods
3. Add to auto-detection list in `_select_backend()`

### Adding a New Retry Algorithm

1. Create a new strategy class
2. Implement the same interface as `RetryStrategy`
3. Make it configurable via `RetryConfig`

### Adding a New Rate Limiting Algorithm

1. Create a new limiter class
2. Implement the same async context manager interface
3. Make it configurable via `RateLimitConfig`

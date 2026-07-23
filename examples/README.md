# fastreq Examples

This directory contains executable Python examples demonstrating the features of the `fastreq` library.

## Prerequisites

### Installation

First, install the library. niquests is included by default:

```bash
# Default install (includes niquests)
pip install fastreq

# Add optional httpx backend
pip install fastreq[httpx]
```

### Environment Variables

Some examples use environment variables for configuration (proxies, API keys). Copy the `.env.example` file to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```bash
# Proxy settings
FASTREQ_PROXIES=http://user:pass@proxy.example.com:8080
WEBSHARE_USERNAME=your_username
WEBSHARE_PASSWORD=your_password

# Optional API keys for specific examples
API_KEY=your_api_key_here
```

## Running Examples

All examples can be run directly:

```bash
# Make examples executable (Linux/Mac)
chmod +x *.py

# Run a specific example
python 01-basic-requests.py
./01-basic-requests.py

# Or using python3 explicitly
python3 01-basic-requests.py
```

## Examples Overview

### Core Features

| # | Example | Description |
|---|---------|-------------|
| 01 | `01-basic-requests.py` | Simple parallel GET requests using httpbin.org |
| 02 | `02-concurrency-tuning.py` | Comparing different concurrency levels |
| 03 | `03-rate-limiting.py` | Rate limiting with burst handling |
| 04 | `04-retry-configuration.py` | Retry logic with exponential backoff |
| 05 | `05-proxy-rotation.py` | Proxy rotation using environment variables |
| 06 | `06-user-agent-rotation.py` | User agent rotation (default and custom) |

### Advanced Features

| # | Example | Description |
|---|---------|-------------|
| 07 | `07-post-json-data.py` | POST requests with JSON payloads |
| 08 | `08-streaming-downloads.py` | Streaming large files with progress tracking |
| 09 | `09-error-handling.py` | Exception handling and graceful failures |
| 10 | `10-backend-selection.py` | Backend selection and feature comparison |
| 11 | `11-http2-usage.py` | HTTP/2 features (niquests backend) |

### Response Handling

| # | Example | Description |
|---|---------|-------------|
| 12 | `12-response-parsing.py` | Different return types and custom parsing |
| 13 | `13-context-manager.py` | Async context manager for session reuse |
| 14 | `14-async-usage.py` | Pure async patterns and integration |
| 15 | `15-cookie-management.py` | Cookie persistence and management |
| 16 | `16-keyed-responses.py` | Named results using keys parameter |
| 17 | `17-graceful-failure.py` | Handling partial successes with `return_none_on_failure` |

## Common Patterns

### Basic Usage

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://httpbin.org/get"] * 5,
    concurrency=3,
)
```

### Async Context Manager

```python
from fastreq import FastRequests

client = FastRequests(concurrency=5)
async with client:
    results = await client.request(urls=my_urls)
```

### Custom Parsing

```python
from fastreq import fastreq, ReturnType

results = fastreq(
    urls=my_urls,
    return_type=ReturnType.RESPONSE,
    parse_func=lambda r: r.status_code,
)
```

## Testing Public APIs

Examples use publicly available APIs for testing:

- **httpbin.org** - HTTP testing service
- **jsonplaceholder.typicode.com** - Mock REST API
- Both services are free and require no authentication

## Troubleshooting

### "No suitable backend found" Error

This should not happen since niquests is a required dependency. If it does, reinstall:

```bash
pip install --force-reinstall fastreq
```

For optional httpx backend:

```bash
pip install fastreq[httpx]
```

### Proxy Errors

- Verify proxy URL format: `http://user:pass@host:port`
- Test proxy connectivity manually first
- Check `.env` file is loaded correctly
- Use `FASTREQ_PROXIES` environment variable

### Import Errors

Ensure you're using Python 3.11+:

```bash
python --version
```

## Additional Resources

- [Official Documentation](https://github.com/legout/fastreq)
- [API Reference](docs/reference/api/)
- [How-to Guides](docs/how-to-guides/)

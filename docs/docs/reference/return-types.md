# Return Types

Control how responses are parsed using the `ReturnType` enum or string values.

## Available Return Types

### JSON

Parses response body as JSON. Returns `dict`, `list`, or `None` if response is not valid JSON.

```python
from fastreq import FastRequests

async with FastRequests() as client:
    # Returns dict/list if JSON
    result = await client.request(
        "https://api.github.com/repos/python/cpython",
        return_type="json"
    )
    print(result['name'])  # 'cpython'
```

**Use when:** Working with APIs that return JSON data

**Returns:** `dict | list | None`

---

### TEXT

Returns response body as decoded UTF-8 string.

```python
from fastreq import FastRequests

async with FastRequests() as client:
    # Returns decoded string
    html = await client.request(
        "https://example.com",
        return_type="text"
    )
    print(html[:100])
```

**Use when:** Working with HTML, plain text, or non-JSON APIs

**Returns:** `str`

---

### CONTENT

Returns response body as raw bytes.

```python
from fastreq import FastRequests

async with FastRequests() as client:
    # Returns raw bytes
    image_data = await client.request(
        "https://example.com/image.png",
        return_type="content"
    )
    with open("image.png", "wb") as f:
        f.write(image_data)
```

**Use when:** Downloading binary files (images, PDFs, archives)

**Returns:** `bytes`

---

### RESPONSE

Returns full `NormalizedResponse` object with all response details.

```python
from fastreq import FastRequests

async with FastRequests() as client:
    # Returns NormalizedResponse
    response = await client.request(
        "https://httpbin.org/get",
        return_type="response"
    )
    print(response.status_code)
    print(response.headers['content-type'])
    print(response.text)
    print(response.json_data)
```

**Use when:** You need status codes, headers, or raw response details

**Returns:** `NormalizedResponse`

**NormalizedResponse attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `status_code` | `int` | HTTP status code |
| `headers` | `dict[str, str]` | Response headers (lowercase keys) |
| `content` | `bytes` | Raw response body |
| `text` | `str` | Decoded response body |
| `json_data` | `Any` | Parsed JSON (if valid) |
| `url` | `str` | Final URL (after redirects) |
| `is_json` | `bool` | Whether response is valid JSON |

---

### STREAM

Streams response content through a callback function.

```python
from fastreq import FastRequests

def stream_callback(chunk: bytes):
    print(f"Received {len(chunk)} bytes")

async with FastRequests() as client:
    await client.request(
        "https://example.com/large-file.zip",
        return_type="stream",
        stream_callback=stream_callback
    )
```

**Use when:** Processing large files without loading into memory

**Returns:** `None` (data processed via callback)

**Note:** Requires `stream_callback` parameter

---

## Using ReturnType Enum

You can use either string values or the `ReturnType` enum:

```python
from fastreq import FastRequests, ReturnType

async with FastRequests() as client:
    # String value
    result1 = await client.request(url, return_type="json")

    # Enum value
    result2 = await client.request(url, return_type=ReturnType.JSON)
```

## Default Return Type

The default return type is `JSON`. If a response is not valid JSON, it returns `None` rather than raising an error.

```python
# Defaults to JSON
result = await client.request("https://example.com")
# Returns None if response is not JSON
```

---

## See Also

- [API Reference: FastRequests.request()](api/fastrequests.md)
- [API Reference: ReturnType](api/returntype.md)
- [How-to: Post JSON Data](../how-to-guides/post-json-data.md)

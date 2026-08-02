# Post JSON Data

Learn how to handle POST, PUT, and PATCH requests with various data formats.

## POST Requests with JSON

Send JSON payloads using the `json` parameter:

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://httpbin.org/post"] * 3,
    method="POST",
    json={
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30,
    },
    headers={"Content-Type": "application/json"},
)

for result in results:
    print(f"Echo: {result['json']}")
```

## POST with Form Data

Send form-encoded data using the `data` parameter:

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://httpbin.org/post"],
    method="POST",
    data={
        "username": "john",
        "password": "secret",
    },
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)

for result in results:
    print(f"Form: {result['form']}")
```

## PUT Requests for Updates

Use `method="PUT"` to update resources:

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://httpbin.org/put"],
    method="PUT",
    json={
        "id": 123,
        "name": "Updated Name",
        "status": "active",
    },
)

for result in results:
    print(f"Updated: {result['json']}")
```

## PATCH Requests for Partial Updates

Use `method="PATCH"` for partial resource updates:

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://httpbin.org/patch"],
    method="PATCH",
    json={
        "status": "completed",  # Only update status
    },
)

for result in results:
    print(f"Patched: {result['json']}")
```

## DELETE Requests

Use `method="DELETE"` to remove resources:

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://httpbin.org/delete"],
    method="DELETE",
)

for result in results:
    print(f"Deleted: {result.get('data')}")
```

## Example: Creating Resources via POST

Create multiple resources in parallel:

```python
from fastreq import fastreq

users = [
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob", "email": "bob@example.com"},
    {"name": "Charlie", "email": "charlie@example.com"},
]

results = fastreq(
    urls=["https://api.example.com/users"] * len(users),
    method="POST",
    json=users,  # Each request gets one user
    headers={
        "Authorization": "Bearer YOUR_TOKEN",
        "Content-Type": "application/json",
    },
)

for i, result in enumerate(results):
    if result.get("id"):
        print(f"Created user {i+1}: ID={result['id']}")
```

## Example: Updating Resources via PUT/PATCH

Update multiple resources:

```python
from fastreq import fastreq

user_ids = [1, 2, 3]
updates = [
    {"status": "active"},
    {"status": "inactive"},
    {"status": "pending"},
]

results = fastreq(
    urls=[f"https://api.example.com/users/{uid}" for uid in user_ids],
    method="PATCH",
    json=updates,
    headers={
        "Authorization": "Bearer YOUR_TOKEN",
    },
)

for i, result in enumerate(results):
    print(f"Updated user {user_ids[i]}: {result.get('status')}")
```

## Different Data per Request

Send different data for each URL using a list:

```python
from fastreq import fastreq

urls = [
    "https://api.example.com/users/1",
    "https://api.example.com/users/2",
    "https://api.example.com/users/3",
]

data_list = [
    {"name": "Alice", "status": "active"},
    {"name": "Bob", "status": "inactive"},
    {"name": "Charlie", "status": "pending"},
]

results = fastreq(
    urls=urls,
    method="PATCH",
    json=data_list,  # List of data dicts
)

for url, result in zip(urls, results):
    print(f"{url}: {result}")
```

## Sending Files as multipart/form-data

Upload files using `files` parameter:

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://httpbin.org/post"],
    method="POST",
    files={
        "file": ("document.txt", b"File content here"),
    },
)

for result in results:
    print(f"Uploaded: {result.get('files')}")
```

## Sending Multiple Files

Upload multiple files:

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://api.example.com/upload"],
    method="POST",
    files={
        "file1": ("doc1.txt", b"Content 1"),
        "file2": ("doc2.txt", b"Content 2"),
        "metadata": ("info.json", b'{"key": "value"}', "application/json"),
    },
)

for result in results:
    print(f"Uploaded files: {result.get('files')}")
```

## Custom Headers for Different Requests

Set headers per request using a list:

```python
from fastreq import fastreq

urls = [
    "https://api.example.com/users",
    "https://api.example.com/posts",
]

headers_list = [
    {"Authorization": "Bearer USER_TOKEN"},
    {"Authorization": "Bearer POST_TOKEN"},
]

results = fastreq(
    urls=urls,
    method="POST",
    json=[{}, {}],
    headers=headers_list,
)
```

## Sending Raw Request Bodies

Send raw request bodies with `data` parameter:

```python
from fastreq import fastreq

# Send raw text
results = fastreq(
    urls=["https://httpbin.org/post"],
    method="POST",
    data="raw text body",
    headers={"Content-Type": "text/plain"},
)

# Send raw bytes
results = fastreq(
    urls=["https://httpbin.org/post"],
    method="POST",
    data=b"binary data",
    headers={"Content-Type": "application/octet-stream"},
)
```

## Query Parameters with POST

Combine query parameters with POST body:

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://httpbin.org/post"],
    method="POST",
    params={"token": "secret"},  # Query params
    json={"key": "value"},      # POST body
)

for result in results:
    print(f"Args: {result['args']}")
    print(f"JSON: {result['json']}")
```

## Authentication with POST

Include authentication in headers:

```python
from fastreq import fastreq

# Bearer token
results = fastreq(
    urls=["https://api.example.com/data"],
    method="POST",
    json={"query": "SELECT *"},
    headers={
        "Authorization": "Bearer YOUR_ACCESS_TOKEN",
    },
)

# API key
results = fastreq(
    urls=["https://api.example.com/data"],
    method="POST",
    json={"query": "SELECT *"},
    headers={
        "X-API-Key": "your-api-key",
    },
)
```

## Handling POST Response Codes

Check response status codes:

```python
from fastreq import fastreq, ReturnType

results = fastreq(
    urls=["https://httpbin.org/status/201"],
    method="POST",
    json={"key": "value"},
    return_type=ReturnType.RESPONSE,
)

for response in results:
    print(f"Status: {response.status_code}")
    print(f"Headers: {response.headers}")
    if response.status_code in [200, 201]:
        print("Success!")
```

## Error Handling for Failed POST Requests

```python
from fastreq import fastreq, PartialFailureError

try:
    results = fastreq(
        urls=[
            "https://api.example.com/users",
            "https://invalid-url.com/users",
        ],
        method="POST",
        json=[{"name": "Alice"}, {"name": "Bob"}],
    )
except PartialFailureError as e:
    print(f"Partial failure: {e.successes}/{e.total}")
    for url, details in e.failures.items():
        print(f"Failed: {url} - {details.error}")
```

## Best Practices

1. **Set Content-Type Headers**: Always specify content type
   ```python
   headers={"Content-Type": "application/json"}
   ```

2. **Use Correct Method**: Choose POST, PUT, or PATCH appropriately
   - POST: Create new resources
   - PUT: Replace entire resource
   - PATCH: Partial update

3. **Handle Errors**: Check status codes or catch exceptions
   ```python
   except PartialFailureError as e:
       print(f"Failed: {e.failures}")
   ```

4. **Authenticate Properly**: Include auth headers
   ```python
   headers={"Authorization": "Bearer YOUR_TOKEN"}
   ```

5. **Validate Responses**: Check response structure
   ```python
   if result.get("id"):
       print(f"Created: {result['id']}")
   ```

## See Also

- **[Make Parallel Requests](make-parallel-requests.md)** - Basic request configuration
- **[Handle Retries](handle-retries.md)** - Configure retry logic for POST requests
- **[Debug Issues](debug-issues.md)** - Troubleshoot request problems
- **[API Reference](../reference/configuration.md)** - Configuration options

# Handle Cookies

Learn how to manage session cookies and authentication.

## Setting Initial Cookies

Use the `cookies` parameter to send cookies with requests:

```python
from fastreq import fastreq

# Send cookies with request
results = fastreq(
    urls=["https://httpbin.org/cookies"],
    cookies={
        "session_id": "abc123",
        "user_token": "xyz789",
    },
)

for result in results:
    print(f"Cookies: {result['cookies']}")
```

## Session Cookies with Context Manager

Use a context manager to maintain cookies across multiple request batches:

```python
import asyncio
from fastreq import FastRequests

async def session_example():
    async with FastRequests() as client:
        # First request - receives session cookie
        results1 = await client.request(
            urls=["https://httpbin.org/cookies/set/session/abc123"],
            return_type="response",
        )

        # Second request - cookie is sent automatically
        results2 = await client.request(
            urls=["https://httpbin.org/cookies"],
        )

        # Third request - cookie persists
        results3 = await client.request(
            urls=["https://httpbin.org/cookies"],
        )

        return results2, results3

results2, results3 = asyncio.run(session_example())
print(f"Session maintained: {results2}")
```

## Adding Cookies with `set_cookies()`

Add cookies to an existing session:

```python
import asyncio
from fastreq import FastRequests

async def add_cookies_example():
    async with FastRequests() as client:
        # Add cookies to session
        client.set_cookies({
            "auth_token": "secret_token_123",
            "user_id": "456",
        })

        # Request includes cookies
        results = await client.request(
            urls=["https://httpbin.org/cookies"],
        )

        return results

results = asyncio.run(add_cookies_example())
print(f"Cookies sent: {results[0]}")
```

## Clearing Cookies with `reset_cookies()`

Clear all cookies from the session:

```python
import asyncio
from fastreq import FastRequests

async def clear_cookies_example():
    async with FastRequests() as client:
        # Set cookies
        client.set_cookies({"session": "abc123"})

        # First request - has cookies
        results1 = await client.request(
            urls=["https://httpbin.org/cookies"],
        )

        # Clear cookies
        client.reset_cookies()

        # Second request - no cookies
        results2 = await client.request(
            urls=["https://httpbin.org/cookies"],
        )

        return results1, results2

results1, results2 = asyncio.run(clear_cookies_example())
print(f"Before reset: {results1[0]}")
print(f"After reset: {results2[0]}")
```

## Authentication with Session Cookies

Authenticate and maintain session across requests:

```python
import asyncio
from fastreq import FastRequests

async def authenticated_session():
    async with FastRequests() as client:
        # Login request - receives session cookie
        login_response = await client.request(
            urls=["https://httpbin.org/cookies/set/session/logged_in"],
            return_type="response",
        )

        # Subsequent authenticated requests
        profile = await client.request(
            urls=["https://httpbin.org/cookies"],
        )

        # Another authenticated request
        dashboard = await client.request(
            urls=["https://httpbin.org/cookies"],
        )

        return profile, dashboard

profile, dashboard = asyncio.run(authenticated_session())
print(f"Authenticated session: {profile[0]}")
```

## Real-World Example: API Authentication

Authenticate with an API and maintain session:

```python
import asyncio
from fastreq import FastRequests

async def api_session():
    async with FastRequests() as client:
        # Login endpoint
        login_data = await client.request(
            urls=["https://api.example.com/login"],
            method="POST",
            json={"username": "user", "password": "pass"},
            headers={"Content-Type": "application/json"},
        )

        # Authenticated requests
        profile = await client.request(
            urls=["https://api.example.com/profile"],
        )

        # More authenticated requests
        posts = await client.request(
            urls=["https://api.example.com/posts"],
        )

        return profile, posts

profile, posts = asyncio.run(api_session())
```

## Cookie Persistence Across Multiple Batches

Use context manager to persist cookies:

```python
import asyncio
from fastreq import FastRequests

async def persistent_session():
    async with FastRequests() as client:
        # Batch 1
        batch1 = await client.request(
            urls=[
                "https://httpbin.org/cookies/set/session/abc123",
                "https://httpbin.org/cookies/set/token/xyz789",
            ],
        )

        # Batch 2 - cookies are sent automatically
        batch2 = await client.request(
            urls=[
                "https://httpbin.org/cookies",
                "https://httpbin.org/cookies",
            ],
        )

        # Batch 3 - cookies still persist
        batch3 = await client.request(
            urls=[
                "https://httpbin.org/cookies",
            ],
        )

        return batch1, batch2, batch3

results = asyncio.run(persistent_session())
```

## Different Cookies for Different Requests

Set cookies per request:

```python
import asyncio
from fastreq import FastRequests

async def different_cookies():
    async with FastRequests() as client:
        # First request with specific cookies
        results1 = await client.request(
            urls=["https://httpbin.org/cookies"],
            cookies={"request_id": "123"},
        )

        # Second request with different cookies
        results2 = await client.request(
            urls=["https://httpbin.org/cookies"],
            cookies={"request_id": "456"},
        )

        return results1, results2

results1, results2 = asyncio.run(different_cookies())
print(f"Request 1: {results1[0]}")
print(f"Request 2: {results2[0]}")
```

## Updating Cookies Incrementally

Add more cookies to existing session:

```python
import asyncio
from fastreq import FastRequests

async def update_cookies():
    async with FastRequests() as client:
        # Initial cookies
        client.set_cookies({"session": "abc123"})

        # Add more cookies
        client.set_cookies({"user_id": "456"})

        # Both cookies are sent
        results = await client.request(
            urls=["https://httpbin.org/cookies"],
        )

        return results

results = asyncio.run(update_cookies())
print(f"All cookies: {results[0]}")
```

## Cookie Expiration and Handling

Check cookie status:

```python
import asyncio
from fastreq import FastRequests

async def cookie_status():
    async with FastRequests() as client:
        # Set cookies
        client.set_cookies({"session": "abc123"})

        # Make request
        results = await client.request(
            urls=["https://httpbin.org/cookies"],
        )

        # Check response cookies
        for result in results:
            if "cookies" in result:
                print(f"Cookies received: {result['cookies']}")

        return results

results = asyncio.run(cookie_status())
```

## Handling Cookie Errors

Handle cookie-related errors:

```python
from fastreq import fastreq

try:
    results = fastreq(
        urls=["https://httpbin.org/cookies"],
        cookies={
            "invalid_cookie": "value",
        },
    )
except Exception as e:
    print(f"Cookie error: {e}")
```

## Combining Cookies with Headers

Send both cookies and headers:

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://httpbin.org/cookies"],
    cookies={"session": "abc123"},
    headers={
        "User-Agent": "MyApp/1.0",
        "Accept": "application/json",
    },
)
```

## Debugging Cookie Issues

Enable debug logging to see cookie handling:

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://httpbin.org/cookies/set/session/test"],
    debug=True,
)

results = fastreq(
    urls=["https://httpbin.org/cookies"],
    debug=True,
)
```

## Best Practices

1. **Use Context Manager**: Maintain cookies across requests
   ```python
   async with FastRequests() as client:
       await client.request(urls=urls)
   ```

2. **Set Cookies Before Requests**: Call `set_cookies()` first
   ```python
   client.set_cookies({"session": "abc"})
   results = await client.request(urls=urls)
   ```

3. **Clear Sensitive Cookies**: Use `reset_cookies()` when done
   ```python
   client.reset_cookies()
   ```

4. **Test Cookie Behavior**: Verify cookies are sent/received
   ```python
   results = await client.request(urls=["https://httpbin.org/cookies"])
   ```

5. **Handle Cookie Expiration**: Check response for new cookies
   ```python
   if 'set-cookie' in response.headers:
       # Update session cookies
   ```

## See Also

- **[Make Parallel Requests](make-parallel-requests.md)** - Request configuration
- **[Post JSON Data](post-json-data.md)** - Authentication examples
- **[API Reference](../reference/api/fastrequests.md)** - Client documentation

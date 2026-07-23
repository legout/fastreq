# Header Management

Manage HTTP headers with automatic user-agent rotation.

## HeaderManager

Main header manager class for automatic user-agent rotation.

```python
from fastreq.utils.headers import HeaderManager

manager = HeaderManager(
    random_user_agent=True,
    user_agents=["Custom UA 1", "Custom UA 2"],
)

# Get headers with random user-agent
headers = manager.get_headers({"Authorization": "Bearer token"})
print(headers["user-agent"])  # Random from list
```

### HeaderManager Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get_headers(custom_headers)` | `Dict[str, str]` | Get headers with user-agent |
| `update_agents_from_remote(url)` | `None` | Update user agents from URL |
| `set_custom_user_agent(ua)` | `None` | Set fixed custom user-agent |
| `get_user_agents()` | `List[str]` | Get current user agent list |

---

## HeaderManager Initialization

```python
from fastreq.utils.headers import HeaderManager

# Default user-agent rotation
manager = HeaderManager(random_user_agent=True)

# Custom user agents
manager = HeaderManager(
    random_user_agent=True,
    user_agents=["Custom UA 1", "Custom UA 2"],
)

# Fixed user-agent (no rotation)
manager = HeaderManager(
    random_user_agent=True,
    custom_user_agent="MyBot/1.0",
)

# Disable user-agent rotation
manager = HeaderManager(random_user_agent=False)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `random_user_agent` | `bool` | `True` | Enable random user-agent selection |
| `user_agents` | `List[str] \| None` | `None` | Custom user agent list |
| `custom_user_agent` | `str \| None` | `None` | Fixed user agent (overrides rotation) |

---

## User Agent Sources

User agents are loaded in priority order:

1. **Custom user agent** (set via `set_custom_user_agent`)
2. **Provided user_agents list** (constructor parameter)
3. **USER_AGENTS environment variable** (comma-separated)
4. **USER_AGENTS_URL environment variable** (fetch from URL)
5. **Default user agents** (built-in list)

### Example Priority

```python
import os

# Set environment
os.environ["USER_AGENTS"] = "Env UA 1,Env UA 2"

# Create manager
manager = HeaderManager(
    user_agents=["Custom UA"],  # Priority 2
    random_user_agent=True,
)

# Gets random from "Custom UA" (priority 2 > priority 3 env)
headers = manager.get_headers()

# Set custom UA (priority 1)
manager.set_custom_user_agent("Fixed UA")

# Now always uses "Fixed UA"
headers = manager.get_headers()
```

---

## Default User Agents

Built-in user agents covering major browsers and platforms:

```python
DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]
```

### Coverage

- **Desktop:** Chrome (Windows, Mac, Linux), Firefox, Edge, Safari
- **Mobile:** iPhone, iPad
- **OS:** Windows 10, macOS 10.15+, Linux

---

## Using Headers

### Get Headers with User-Agent

```python
manager = HeaderManager(random_user_agent=True)

# Get headers with random user-agent
headers = manager.get_headers()
# {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ..."}

# Get headers with custom headers
headers = manager.get_headers({
    "Authorization": "Bearer token",
    "Content-Type": "application/json",
})
# {
#   "user-agent": "Mozilla/5.0 ...",
#   "authorization": "Bearer token",
#   "content-type": "application/json"
# }
```

### Disable User-Agent

```python
manager = HeaderManager(random_user_agent=False)

# No user-agent header
headers = manager.get_headers()
# {}
```

### Fixed User-Agent

```python
manager = HeaderManager(
    random_user_agent=True,
    custom_user_agent="MyBot/1.0",
)

# Always uses fixed user-agent
headers = manager.get_headers()
# {"user-agent": "MyBot/1.0"}
```

---

## Custom User Agents

### Set Custom List

```python
manager = HeaderManager(
    random_user_agent=True,
    user_agents=[
        "MyBot/1.0",
        "MyBot/2.0",
        "MyBot/3.0",
    ],
)

for _ in range(3):
    headers = manager.get_headers()
    print(headers["user-agent"])
# Output: Random from MyBot/1.0, MyBot/2.0, MyBot/3.0
```

### Load from Environment

```bash
# .env
USER_AGENTS=Bot1/1.0,Bot2/1.0,Bot3/1.0
```

```python
import os
from dotenv import load_dotenv

load_dotenv()

manager = HeaderManager(random_user_agent=True)
# Loads from USER_AGENTS env var
```

### Load from Remote URL

```bash
# .env
USER_AGENTS_URL=https://example.com/user-agents.txt
```

```
# user-agents.txt
Bot1/1.0
Bot2/1.0
Bot3/1.0
```

```python
manager = HeaderManager(random_user_agent=True)
# Fetches from USER_AGENTS_URL
```

---

## Updating User Agents

### Update from Remote

```python
manager = HeaderManager(random_user_agent=True)

# Fetch new user agents from URL
manager.update_agents_from_remote("https://example.com/agents.txt")
```

Raises `ValueError` if fetch fails.

---

## Set Custom User-Agent

```python
manager = HeaderManager(random_user_agent=True)

# Set fixed user-agent (disables rotation)
manager.set_custom_user_agent("MyBot/1.0")

headers = manager.get_headers()
print(headers["user-agent"])  # "MyBot/1.0"
```

---

## Get Current User Agents

```python
manager = HeaderManager(
    random_user_agent=True,
    user_agents=["UA1", "UA2", "UA3"],
)

agents = manager.get_user_agents()
print(agents)  # ["UA1", "UA2", "UA3"]
```

Returns a copy of the list.

---

## Using in FastRequests

```python
from fastreq import FastRequests

# Built-in user-agent rotation
client = FastRequests(random_user_agent=True)

async with client:
    # User-agent added automatically
    result = await client.request("https://example.com")
```

---

## See Also

- [How-to: Handle Cookies](../how-to-guides/handle-cookies.md)

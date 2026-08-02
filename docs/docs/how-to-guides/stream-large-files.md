# Stream Large Files

Learn how to download large files efficiently using streaming to save memory.

## Streaming Basics

Use `return_type="stream"` with `stream_callback` to process responses incrementally:

```python
from fastreq import fastreq

def stream_handler(response, url):
    """Handle streaming response."""
    content_length = int(response.headers.get('content-length', 0))
    downloaded = 0

    with open(f"output_{url.split('/')[-1]}", "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                print(f"Downloaded: {downloaded}/{content_length} bytes")

results = fastreq(
    urls=[
        "https://httpbin.org/bytes/10240",
        "https://httpbin.org/bytes/20480",
    ],
    return_type="stream",
    stream_callback=stream_handler,
)
```

## Downloading with Progress Tracking

Track download progress for multiple files:

```python
from fastreq import fastreq
import os

def download_with_progress(response, url):
    filename = os.path.basename(url)
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0

    print(f"Starting: {filename} ({total_size} bytes)")

    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)

                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"{filename}: {percent:.1f}%")

    print(f"Completed: {filename}")

results = fastreq(
    urls=[
        "https://httpbin.org/bytes/10485760",  # 10 MB
        "https://httpbin.org/bytes/20971520",  # 20 MB
    ],
    return_type="stream",
    stream_callback=download_with_progress,
)
```

## Processing Streaming Responses Line by Line

Process large responses line by line (e.g., CSV, JSON lines):

```python
from fastreq import fastreq

def process_jsonl(response, url):
    """Process JSON Lines format."""
    line_count = 0

    for line in response.iter_lines():
        if line:
            import json
            data = json.loads(line)
            line_count += 1
            print(f"Line {line_count}: {data}")

    print(f"Processed {line_count} lines from {url}")

results = fastreq(
    urls=[
        "https://api.example.com/data.jsonl",
    ],
    return_type="stream",
    stream_callback=process_jsonl,
)
```

## Memory Efficiency Comparison

### Non-Streaming (High Memory Usage)

```python
from fastreq import fastreq

# Loads entire response into memory
results = fastreq(
    urls=["https://example.com/large-file.zip"],  # 1 GB file
    return_type="content",
)

# Memory: ~1 GB
```

### Streaming (Low Memory Usage)

```python
from fastreq import fastreq

def save_stream(response, url):
    with open("large-file.zip", "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

# Processes in 8KB chunks
results = fastreq(
    urls=["https://example.com/large-file.zip"],
    return_type="stream",
    stream_callback=save_stream,
)

# Memory: ~8 KB (chunk size)
```

## Parallel File Downloads

Download multiple files simultaneously with progress tracking:

```python
from fastreq import fastreq
from tqdm import tqdm  # pip install tqdm
import os

files = [
    "https://httpbin.org/bytes/10485760",  # 10 MB
    "https://httpbin.org/bytes/20971520",  # 20 MB
    "https://httpbin.org/bytes/52428800",  # 50 MB
]

def download_with_tqdm(response, url):
    filename = f"download_{os.path.basename(url)}"
    total_size = int(response.headers.get('content-length', 0))

    with tqdm(
        total=total_size,
        unit='B',
        unit_scale=True,
        desc=filename,
    ) as pbar, open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))

results = fastreq(
    urls=files,
    concurrency=3,
    return_type="stream",
    stream_callback=download_with_tqdm,
    verbose=False,  # Disable default progress bar
)
```

## Filtering Streaming Content

Filter content while streaming:

```python
from fastreq import fastreq

def filter_lines(response, url):
    """Filter lines containing 'error' keyword."""
    with open(f"filtered_{os.path.basename(url)}", "w") as f:
        for line in response.iter_lines():
            if line:
                text = line.decode('utf-8')
                if 'error' in text.lower():
                    f.write(text + '\n')

results = fastreq(
    urls=["https://api.example.com/logs.txt"],
    return_type="stream",
    stream_callback=filter_lines,
)
```

## Resumable Downloads

Implement resumable downloads with Range headers:

```python
from fastreq import fastreq
import os

def resumable_download(response, url):
    filename = "large-file.bin"
    downloaded_size = 0

    # Check if file exists and get size
    if os.path.exists(filename):
        downloaded_size = os.path.getsize(filename)

    print(f"Resuming from {downloaded_size} bytes")

    mode = 'ab' if downloaded_size > 0 else 'wb'

    with open(filename, mode) as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    print(f"Download complete: {os.path.getsize(filename)} bytes")

# Note: Range headers must be set in request configuration
results = fastreq(
    urls=["https://example.com/large-file.bin"],
    return_type="stream",
    stream_callback=resumable_download,
)
```

## Chunked Upload with Streaming

Stream large files during upload:

```python
from fastreq import fastreq

def stream_large_file(filepath):
    """Generator for streaming file chunks."""
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            yield chunk

# Note: This requires backend-specific implementation
# Check documentation for chunked upload support
```

## Error Handling with Streaming

Handle errors during streaming:

```python
from fastreq import fastreq

def safe_stream(response, url):
    try:
        with open(f"output_{os.path.basename(url)}", "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Downloaded: {url}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        raise

results = fastreq(
    urls=["https://httpbin.org/bytes/10240"],
    return_type="stream",
    stream_callback=safe_stream,
)
```

## Streaming with Different Backends

### niquests (Default, Recommended)

```python
results = fastreq(
    urls=["https://example.com/large-file.zip"],
    backend="niquests",
    return_type="stream",
    stream_callback=lambda r, u: save_stream(r, u),
)
```

### httpx

```python
results = fastreq(
    urls=["https://example.com/large-file.zip"],
    backend="httpx",
    return_type="stream",
    stream_callback=lambda r, u: save_stream(r, u),
)
```

## Best Practices

1. **Use Appropriate Chunk Sizes**: 8KB - 64KB is typical
   ```python
   response.iter_content(chunk_size=8192)  # 8 KB
   ```

2. **Check Content-Length**: Get file size for progress tracking
   ```python
   total_size = int(response.headers.get('content-length', 0))
   ```

3. **Handle Empty Chunks**: Filter out keep-alive chunks
   ```python
   for chunk in response.iter_content():
       if chunk:  # Filter out keep-alive chunks
           f.write(chunk)
   ```

4. **Use Streaming for Large Files**: Only use streaming for files > 1MB
   ```python
   return_type="stream"  # For large files
   return_type="content"  # For small files
   ```

5. **Close Resources**: Always close file handles
   ```python
   with open(filename, "wb") as f:
       for chunk in response.iter_content():
           f.write(chunk)
   ```

## See Also

- **[Make Parallel Requests](make-parallel-requests.md)** - Basic request configuration
- **[Limit Request Rate](limit-request-rate.md)** - Control download rate
- **[API Reference](../reference/configuration.md)** - Configuration options

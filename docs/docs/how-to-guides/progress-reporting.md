# Show Progress Bars

Optional progress reporting for long batch operations. fastreq ships **without** any progress-bar dependency — both `rich` and `tqdm` are pulled in via extras so the core install stays lean.

## Install

```bash
# rich-based progress bars
pip install fastreq[progress-rich]

# tqdm-based progress bars
pip install fastreq[progress-tqdm]
```

You can install both — fastreq picks `rich` if it is importable, otherwise `tqdm`, otherwise none.

## Enable

```python
from fastreq import fastreq

results = fastreq(
    urls=["https://httpbin.org/get"] * 200,
    concurrency=20,
    progress=True,    # opt in
)
```

When `progress=True` and a progress extra is installed, fastreq prints a live progress bar to stderr that updates as requests complete (success, failure, or retry). When no progress extra is installed, `progress=True` is a no-op — no error, no warning.

## Async API

```python
import asyncio
from fastreq import fastreq_async

async def main():
    return await fastreq_async(
        urls=["https://httpbin.org/get"] * 200,
        concurrency=20,
        progress=True,
    )

asyncio.run(main())
```

## Context-manager clients

Same flag on `FastRequests`:

```python
import asyncio
from fastreq import FastRequests

async def main():
    async with FastRequests(concurrency=20, progress=True) as client:
        return await client.request(urls=["https://httpbin.org/get"] * 200)

asyncio.run(main())
```

## Choosing between rich and tqdm

Both render the same information (counts of completed / failed / retried requests). Choose based on your environment:

- **`rich`** — nicer in a TTY; degrades gracefully when stderr is redirected. Renders Unicode blocks and live updates.
- **`tqdm`** — works everywhere, including Jupyter notebooks. Slightly less polished but more battle-tested for non-interactive runs.

If both are installed, fastreq prefers `rich`. To force `tqdm`, uninstall the rich extra.

## No-extras mode

Without `progress-rich` or `progress-tqdm` installed, `progress=True` is silently ignored. This is by design — the same code works in environments where pulling in `rich` or `tqdm` is undesirable (slim containers, server-side batch jobs).

```python
# This is fine to ship — it just does nothing without the extras
results = fastreq(urls=urls, concurrency=10, progress=True)
```

## See also

- [Make Parallel Requests](make-parallel-requests.md) — core request configuration
- [`FastRequests` reference](../reference/api/fastrequests.md) — full `progress=` documentation

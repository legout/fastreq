#!/usr/bin/env python3
"""
HTTP/2 usage example.

This example demonstrates:
- HTTP/2 features with niquests backend
- Checking HTTP/2 protocol
- HTTP/2 benefits for performance

Note: HTTP/2 requires niquests backend (default) or httpx with h2 extra
"""

import asyncio

from fastreq import FastRequests, fastreq


def main():
    print("=== HTTP/2 Usage Example ===\n")

    print("Scenario 1: HTTP/2 with niquests backend")
    print("-" * 50)

    urls = [
        "https://httpbin.org/get",
        "https://httpbin.org/headers",
        "https://httpbin.org/uuid",
    ]

    try:
        results = fastreq(
            urls=urls,
            backend="niquests",
            http2=True,
            verbose=False,
        )

        print(f"✓ Completed {len(results)} requests with HTTP/2")
        print("\nChecking response details:")
        for i, result in enumerate(results):
            if result:
                print(f"  Request {i + 1}: {result.get('url', 'N/A')}")

    except Exception as e:
        print(f"✗ HTTP/2 test failed: {e}")
        print("\nNote: HTTP/2 requires niquests backend (default)")
        print("Install with: pip install fastreq")

    print("\n\nScenario 2: HTTP/2 vs HTTP/1.1 comparison")
    print("-" * 50)

    print("\nHTTP/2 advantages:")
    print("  • Multiplexing: Multiple requests over single TCP connection")
    print("  • Header compression: Smaller request/response sizes")
    print("  • Server push: Server can send resources proactively")
    print("  • Binary protocol: More efficient parsing")

    print("\nWhen to use HTTP/2:")
    print("  • Making many requests to same domain")
    print("  • High-latency networks (benefits from connection reuse)")
    print("  • APIs that support HTTP/2")

    print("\nWhen HTTP/1.1 might be better:")
    print("  • Compatibility with legacy systems")
    print("  • Debugging (HTTP/2 is binary, harder to inspect)")

    print("\n\nScenario 3: Async context manager with HTTP/2")
    print("-" * 50)

    async def test_http2_async():
        client = FastRequests(
            backend="niquests",
            http2=True,
            concurrency=5,
            verbose=False,
        )

        async with client:
            results = await client.request(urls=urls)

        return results

    try:
        results = asyncio.run(test_http2_async())
        print(f"✓ Async HTTP/2: {len(results)} requests completed")
    except Exception as e:
        print(f"✗ Async HTTP/2 failed: {e}")

    print("\n--- HTTP/2 Setup ---")
    print("1. niquests is included by default with fastreq")
    print("2. Use backend='niquests' or backend='auto'")
    print("3. Set http2=True (default is True)")
    print("4. Server must support HTTP/2")
    print("5. For httpx backend: pip install fastreq[httpx]")

    print("\n✓ HTTP/2 can significantly improve performance")


if __name__ == "__main__":
    main()

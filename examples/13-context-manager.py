#!/usr/bin/env python3
"""
Context manager example.

This example demonstrates:
- Using FastRequests as async context manager
- Reusing session across multiple request batches
- Proper resource cleanup
"""

import asyncio

from fastreq import FastRequests


async def main():
    print("=== Context Manager Example ===\n")

    print("Scenario 1: Reusing session across batches")
    print("-" * 50)

    client = FastRequests(
        backend="auto",
        concurrency=5,
        verbose=False,
    )

    async with client:
        print("Session opened")

        batch1_urls = [
            "https://httpbin.org/get?batch=1&req=1",
            "https://httpbin.org/get?batch=1&req=2",
        ]
        results1 = await client.request(urls=batch1_urls)
        print(f"Batch 1: {len(results1)} requests")

        batch2_urls = [
            "https://httpbin.org/get?batch=2&req=1",
            "https://httpbin.org/get?batch=2&req=2",
            "https://httpbin.org/get?batch=2&req=3",
        ]
        results2 = await client.request(urls=batch2_urls)
        print(f"Batch 2: {len(results2)} requests")

        batch3_urls = [
            "https://httpbin.org/get?batch=3&req=1",
        ]
        results3 = await client.request(urls=batch3_urls)
        print(f"Batch 3: {len(results3)} requests")

    print("Session closed (resources cleaned up)")

    print("\n\nScenario 2: Cookie persistence across batches")
    print("-" * 50)

    client = FastRequests(
        backend="auto",
        concurrency=3,
        verbose=False,
    )

    async with client:
        print("Setting initial cookies")
        client.set_cookies({"session_id": "abc123", "user": "test_user"})

        batch_urls = [
            "https://httpbin.org/cookies/set?name=Alice&age=30",
            "https://httpbin.org/cookies",
            "https://httpbin.org/cookies/delete?session_id",
            "https://httpbin.org/cookies",
        ]

        for i, url in enumerate(batch_urls, 1):
            result = await client.request(urls=url)
            if result:
                print(f"  Request {i}: {url}")
                if "cookies" in result:
                    cookies = result.get("cookies", {})
                    if cookies:
                        print(f"    Cookies: {list(cookies.keys())}")

    print("\n\nScenario 3: Manual session management")
    print("-" * 50)

    client = FastRequests(
        backend="auto",
        concurrency=3,
        verbose=False,
    )

    await client.__aenter__()
    print("Session opened manually")

    try:
        urls = ["https://httpbin.org/get"] * 3
        results = await client.request(urls=urls)
        print(f"Requests: {len(results)}")
    finally:
        await client.__aexit__()
        print("Session closed manually")

    print("\n\nScenario 4: Resource cleanup on error")
    print("-" * 50)

    try:
        client = FastRequests(
            backend="auto",
            concurrency=3,
            verbose=False,
        )

        async with client:
            print("Session opened")
            urls = ["https://httpbin.org/get"]
            results = await client.request(urls=urls)
            print(f"Requests: {len(results)}")

            raise ValueError("Simulated error")

    except ValueError:
        print("Error occurred, but session was cleaned up properly")

    print("\n--- Context Manager Benefits ---")
    print("• Automatic resource cleanup (always called)")
    print("• Session reuse across multiple batches")
    print("• Cookie persistence within session")
    print("• Exception-safe cleanup")
    print("• Better performance than creating new sessions")

    print("\n✓ Use context managers for long-running applications")


if __name__ == "__main__":
    asyncio.run(main())

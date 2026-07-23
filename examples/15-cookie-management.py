#!/usr/bin/env python3
"""
Cookie management example.

This example demonstrates:
- Setting cookies with set_cookies()
- Resetting cookies with reset_cookies()
- Cookie persistence across requests
"""

import asyncio

from fastreq import FastRequests


async def main():
    print("=== Cookie Management Example ===\n")

    print("Scenario 1: Setting and using cookies")
    print("-" * 50)

    client = FastRequests(
        backend="auto",
        concurrency=3,
        verbose=False,
    )

    async with client:
        print("Setting initial cookies")
        client.set_cookies(
            {
                "session_id": "abc123",
                "user_id": "user456",
                "theme": "dark",
            }
        )

        print("Making request with cookies")
        result = await client.request(
            urls="https://httpbin.org/cookies",
        )

        if result:
            print("Server received cookies:")
            for name, value in result.get("cookies", {}).items():
                print(f"  {name}: {value}")

    print("\n\nScenario 2: Adding cookies incrementally")
    print("-" * 50)

    async with FastRequests(
        backend="auto",
        verbose=False,
    ) as client:
        print("Setting initial cookie")
        client.set_cookies({"cookie1": "value1"})

        result1 = await client.request(urls="https://httpbin.org/cookies")
        print(f"After cookie1: {list(result1.get('cookies', {}).keys())}")

        print("Adding more cookies")
        client.set_cookies(
            {
                "cookie2": "value2",
                "cookie3": "value3",
            }
        )

        result2 = await client.request(urls="https://httpbin.org/cookies")
        print(f"After adding cookies: {list(result2.get('cookies', {}).keys())}")

    print("\n\nScenario 3: Resetting cookies")
    print("-" * 50)

    async with FastRequests(
        backend="auto",
        verbose=False,
    ) as client:
        print("Setting multiple cookies")
        client.set_cookies(
            {
                "temp1": "val1",
                "temp2": "val2",
                "temp3": "val3",
            }
        )

        result1 = await client.request(urls="https://httpbin.org/cookies")
        print(f"Cookies before reset: {list(result1.get('cookies', {}).keys())}")

        print("Resetting all cookies")
        client.reset_cookies()

        result2 = await client.request(urls="https://httpbin.org/cookies")
        print(f"Cookies after reset: {list(result2.get('cookies', {}).keys())}")

    print("\n\nScenario 4: Cookie persistence across requests")
    print("-" * 50)

    async with FastRequests(
        backend="auto",
        verbose=False,
    ) as client:
        print("Setting session cookie")
        client.set_cookies({"session": "persistent_session"})

        urls = [
            "https://httpbin.org/cookies",
            "https://httpbin.org/cookies/set/test/value",
            "https://httpbin.org/cookies",
            "https://httpbin.org/cookies/delete/session",
            "https://httpbin.org/cookies",
        ]

        for i, url in enumerate(urls, 1):
            result = await client.request(urls=url)
            if result:
                cookies = list(result.get("cookies", {}).keys())
                print(f"  Request {i} ({url.split('/')[-1]}): {cookies if cookies else '(empty)'}")

    print("\n\nScenario 5: Cookies with initial configuration")
    print("-" * 50)

    client = FastRequests(
        backend="auto",
        cookies={
            "initial1": "value1",
            "initial2": "value2",
        },
        verbose=False,
    )

    async with client:
        result = await client.request(urls="https://httpbin.org/cookies")
        if result:
            print(f"Initial cookies: {list(result.get('cookies', {}).keys())}")

    print("\n--- Cookie Management Tips ---")
    print("• set_cookies(): Add/update cookies")
    print("• reset_cookies(): Clear all cookies")
    print("• Cookies persist within session context")
    print("• Use for authentication and session management")
    print("• Server can set cookies (Set-Cookie header)")

    print("\n✓ Cookie management enables stateful HTTP sessions")


if __name__ == "__main__":
    asyncio.run(main())

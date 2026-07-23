#!/usr/bin/env python3
"""
Proxy rotation example.

This example demonstrates:
- Loading proxy from environment variables
- Making requests through proxy
- Handling proxy errors gracefully

Note: This requires valid proxy settings in .env file
"""

import os

from dotenv import load_dotenv

from fastreq import ProxyError, fastreq


def main():
    print("=== Proxy Rotation Example ===\n")

    load_dotenv()

    proxy_url = os.getenv("PROXY_URL")
    if not proxy_url:
        print("⚠ No PROXY_URL found in .env file")
        print("\nTo test proxies:")
        print("1. Copy .env.example to .env")
        print("2. Add PROXY_URL=http://user:pass@host:port")
        print("3. Run this example again")
        print("\nContinuing without proxy...")

    urls = [
        "https://httpbin.org/ip",
        "https://httpbin.org/headers",
        "https://httpbin.org/get",
    ]

    if proxy_url:
        print(f"Using proxy: {proxy_url}")
        print("\nMaking requests through proxy...")
        print("-" * 50)

        try:
            results = fastreq(
                urls=urls,
                proxy=proxy_url,
                concurrency=2,
            )

            print("\nResults:")
            for i, result in enumerate(results):
                print(f"\n--- Request {i + 1} ---")
                if result:
                    if "origin" in result:
                        print(f"IP: {result['origin']}")
                    if "headers" in result:
                        print(f"Headers: {list(result['headers'].keys())}")

            print("\n✓ Requests made successfully through proxy")

        except ProxyError as e:
            print(f"Proxy error: {e}")
            print("Check your proxy URL and credentials")
        except Exception as e:
            print(f"Error: {e}")

    else:
        print("\nMaking direct requests (no proxy)...")
        print("-" * 50)

        results = fastreq(
            urls=urls,
            concurrency=2,
        )

        print(f"\n✓ Completed {len(results)} requests without proxy")

    print("\n--- Proxy Configuration ---")
    print("• Single proxy: Use proxy parameter")
    print("• Multiple proxies: Use the proxies parameter or ProxyPool")
    print("• Format: http://user:pass@host:port")
    print("• Test proxy connectivity before using in production")


if __name__ == "__main__":
    main()

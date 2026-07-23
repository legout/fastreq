#!/usr/bin/env python3
"""
Basic parallel GET requests example.

This example demonstrates:
- Using fastreq() for simple parallel HTTP calls
- Making multiple requests to httpbin.org
- Printing response data
"""

import json

from fastreq import fastreq


def main():
    print("=== Basic Parallel Requests Example ===\n")

    urls = [
        "https://httpbin.org/get",
        "https://httpbin.org/uuid",
        "https://httpbin.org/ip",
        "https://httpbin.org/headers",
        "https://httpbin.org/user-agent",
    ]

    print(f"Making {len(urls)} parallel requests...")
    print("URLs:")
    for url in urls:
        print(f"  - {url}")
    print()

    results = fastreq(
        urls=urls,
        concurrency=3,
    )

    print("\nResults:")
    for i, result in enumerate(results):
        print(f"\n--- Request {i + 1} ---")
        print(json.dumps(result, indent=2))

    print("\n✓ All requests completed successfully")


if __name__ == "__main__":
    main()

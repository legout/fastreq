#!/usr/bin/env python3
"""
POST JSON data example.

This example demonstrates:
- POST requests with JSON payloads
- Sending structured data to APIs
- Verifying response data
"""

import json

from fastreq import ReturnType, fastreq


def main():
    print("=== POST JSON Data Example ===\n")

    urls = [
        "https://httpbin.org/post",
        "https://httpbin.org/post",
        "https://httpbin.org/post",
    ]

    payloads = [
        {"name": "Alice", "age": 30, "city": "New York"},
        {"name": "Bob", "age": 25, "city": "San Francisco"},
        {"name": "Charlie", "age": 35, "city": "Seattle"},
    ]

    print("Making POST requests with JSON payloads...")
    print("-" * 50)

    results = fastreq(
        urls=urls,
        method="POST",
        json=payloads,
        concurrency=3,
        verbose=False,
    )

    print("\nResults:")
    for i, (result, payload) in enumerate(zip(results, payloads, strict=False)):
        print(f"\n--- Request {i + 1} ---")
        print(f"Sent: {payload}")
        if result:
            print(f"Received JSON: {result.get('json')}")
            print(f"Status: {result.get('status_code', 'N/A')}")

    print("\n\nScenario 2: Single POST request")
    print("-" * 50)

    result = fastreq(
        urls="https://httpbin.org/post",
        method="POST",
        json={"message": "Hello, World!", "count": 42},
        return_type=ReturnType.JSON,
        verbose=False,
    )

    print(f"Response: {json.dumps(result, indent=2)}")

    print("\n--- POST Request Tips ---")
    print("• json parameter: Automatically serializes to JSON")
    print("• data parameter: Send raw data (form-encoded, etc.)")
    print("• headers parameter: Add custom headers (Content-Type auto-set)")
    print("• Use json parameter for REST APIs")

    print("\n✓ POST requests are perfect for API interactions")


if __name__ == "__main__":
    main()

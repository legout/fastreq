#!/usr/bin/env python3
"""
Response parsing example.

This example demonstrates:
- Different return types (json, text, content, response)
- Custom parse_func parameter
- Handling various response formats
"""

from fastreq import (
    ReturnType,
    fastreq,
)


def main():
    print("=== Response Parsing Example ===\n")

    urls = [
        "https://httpbin.org/json",
        "https://httpbin.org/html",
        "https://httpbin.org/robots.txt",
        "https://httpbin.org/encoding/utf8",
    ]

    print("Scenario 1: JSON return type (default)")
    print("-" * 50)

    results = fastreq(
        urls=urls,
        return_type=ReturnType.JSON,
        verbose=False,
    )

    print("Results:")
    for i, result in enumerate(results):
        if result:
            print(f"  Request {i + 1}: {type(result).__name__}")
        else:
            print(f"  Request {i + 1}: None (not JSON)")

    print("\n\nScenario 2: TEXT return type")
    print("-" * 50)

    results = fastreq(
        urls=urls,
        return_type=ReturnType.TEXT,
        verbose=False,
    )

    print("Results:")
    for i, result in enumerate(results):
        if result:
            preview = result[:100] if len(result) > 100 else result
            print(f"  Request {i + 1}: {len(result)} chars")
            print(f"    Preview: {preview}...")

    print("\n\nScenario 3: CONTENT return type (bytes)")
    print("-" * 50)

    results = fastreq(
        urls=urls[:2],
        return_type=ReturnType.CONTENT,
        verbose=False,
    )

    print("Results:")
    for i, result in enumerate(results):
        if result:
            print(f"  Request {i + 1}: {len(result)} bytes")

    print("\n\nScenario 4: RESPONSE return type (full object)")
    print("-" * 50)

    results = fastreq(
        urls=urls[:2],
        return_type=ReturnType.RESPONSE,
        verbose=False,
    )

    print("Results:")
    for i, result in enumerate(results):
        if result:
            print(f"  Request {i + 1}:")
            print(f"    Status: {result.status_code}")
            print(f"    Headers: {list(result.headers.keys())[:3]}...")
            print(f"    Content-Length: {len(result.content)}")

    print("\n\nScenario 5: Custom parse_func")
    print("-" * 50)

    def extract_status_code(response):
        """Extract just the status code from response."""
        return response.get("status_code", 0)

    def get_origin_ip(response):
        """Extract origin IP from httpbin response."""
        return response.get("origin", "unknown")

    urls = ["https://httpbin.org/ip", "https://httpbin.org/get"]

    results = fastreq(
        urls=urls,
        return_type=ReturnType.JSON,
        parse_func=lambda r: {
            "origin": r.get("origin", ""),
            "url": r.get("url", ""),
        },
        verbose=False,
    )

    print("Parsed results:")
    for i, result in enumerate(results):
        if result:
            print(f"  Request {i + 1}:")
            print(f"    Origin: {result.get('origin', 'N/A')}")
            print(f"    URL: {result.get('url', 'N/A')}")

    print("\n\nScenario 6: Combining return types")
    print("-" * 50)

    def extract_json_data(response):
        """Parse and extract specific JSON fields."""
        if response and isinstance(response, dict):
            return {
                "data": response.get("data", ""),
                "headers": len(response.get("headers", {})),
            }
        return None

    results = fastreq(
        urls=["https://httpbin.org/post"],
        method="POST",
        json={"test": "data"},
        return_type=ReturnType.JSON,
        parse_func=extract_json_data,
        verbose=False,
    )

    if results:
        print(f"Extracted data: {results[0]}")

    print("\n--- Return Type Summary ---")
    print("ReturnType.JSON:   Parse as JSON (dict/list)")
    print("ReturnType.TEXT:   Return as string")
    print("ReturnType.CONTENT: Return as bytes")
    print("ReturnType.RESPONSE: Full NormalizedResponse object")
    print("ReturnType.STREAM:  Stream with callback")

    print("\n✓ Choose return type based on your needs")


if __name__ == "__main__":
    main()

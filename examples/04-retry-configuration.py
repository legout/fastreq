#!/usr/bin/env python3
"""
Retry configuration example.

This example demonstrates:
- Using max_retries for handling transient failures
- Exponential backoff with jitter
- Testing with an endpoint that sometimes fails
"""

from fastreq import fastreq


def main():
    print("=== Retry Configuration Example ===\n")

    print("Testing retry behavior with potentially unreliable endpoints...\n")

    urls = [
        "https://httpbin.org/status/200",
        "https://httpbin.org/status/500",
        "https://httpbin.org/status/502",
        "https://httpbin.org/status/503",
    ]

    print("Scenario 1: No retries (max_retries=0)")
    print("-" * 50)
    try:
        results = fastreq(
            urls=urls,
            max_retries=0,
            verbose=False,
        )
        print(f"Completed: {len([r for r in results if r])}/{len(urls)}")
    except Exception as e:
        print(f"Failed: {e}")

    print("\nScenario 2: 3 retries (default)")
    print("-" * 50)
    try:
        results = fastreq(
            urls=urls,
            max_retries=3,
            verbose=False,
        )
        print(f"Completed: {len([r for r in results if r])}/{len(urls)}")
    except Exception as e:
        print(f"Failed: {e}")

    print("\nScenario 3: 5 retries with delay simulation")
    print("-" * 50)
    print("Using endpoints that return 200 after delay...")

    delay_urls = [
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/2",
        "https://httpbin.org/delay/1",
    ]

    results = fastreq(
        urls=delay_urls,
        max_retries=3,
        verbose=False,
    )
    print(f"Completed: {len(results)}/{len(delay_urls)} requests")

    print("\n--- Retry Behavior ---")
    print("• Retries use exponential backoff with jitter")
    print("• Only transient errors (5xx, timeouts) are retried")
    print("• Client errors (4xx) are not retried by default")
    print("• Adjust max_retries based on your use case")

    print("\n✓ Retry logic helps handle temporary network issues")


if __name__ == "__main__":
    main()

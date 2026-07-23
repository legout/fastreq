#!/usr/bin/env python3
"""
Rate limiting example.

This example demonstrates:
- Using rate_limit parameter to control request rate
- Handling rate limits with burst capacity
- Token bucket rate limiting in action
"""

import time

from fastreq import fastreq


def main():
    print("=== Rate Limiting Example ===\n")

    urls = [f"https://httpbin.org/delay/{i % 2 + 1}" for i in range(10)]

    print("Scenario 1: No rate limit (concurrency=5)")
    print("-" * 50)
    start = time.time()
    results = fastreq(
        urls=urls,
        concurrency=5,
        rate_limit=None,
        verbose=False,
    )
    elapsed_no_limit = time.time() - start
    print(f"Time: {elapsed_no_limit:.2f}s | Requests: {len(results)}")

    print("\nScenario 2: Rate limit of 5 req/s with burst of 3")
    print("-" * 50)
    start = time.time()
    results = fastreq(
        urls=urls,
        concurrency=5,
        rate_limit=5.0,
        rate_limit_burst=3,
        verbose=False,
    )
    elapsed_with_limit = time.time() - start
    print(f"Time: {elapsed_with_limit:.2f}s | Requests: {len(results)}")

    print("\nScenario 3: Strict rate limit of 2 req/s (burst=2)")
    print("-" * 50)
    start = time.time()
    results = fastreq(
        urls=urls,
        concurrency=5,
        rate_limit=2.0,
        rate_limit_burst=2,
        verbose=False,
    )
    elapsed_strict = time.time() - start
    print(f"Time: {elapsed_strict:.2f}s | Requests: {len(results)}")

    print("\n--- Summary ---")
    print(f"No rate limit:      {elapsed_no_limit:.2f}s")
    print(f"5 req/s (burst=3):  {elapsed_with_limit:.2f}s")
    print(f"2 req/s (burst=2):  {elapsed_strict:.2f}s")

    print("\n✓ Rate limiting controls request throughput")
    print("  Burst allows short-term bursts above the rate limit")
    print("  Use rate limiting to avoid overwhelming servers")


if __name__ == "__main__":
    main()

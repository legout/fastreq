#!/usr/bin/env python3
"""
Concurrency tuning example.

This example demonstrates:
- Comparing different concurrency levels
- Measuring execution time
- Understanding the impact of concurrency
"""

import time

from fastreq import fastreq


def measure_time(concurrency: int, num_requests: int = 20) -> float:
    """Measure time for requests with given concurrency."""
    urls = [f"https://httpbin.org/delay/{i % 3 + 1}" for i in range(num_requests)]

    start = time.time()
    results = fastreq(
        urls=urls,
        concurrency=concurrency,
        verbose=False,
    )
    elapsed = time.time() - start

    return elapsed, len(results)


def main():
    print("=== Concurrency Tuning Example ===\n")
    print("Testing different concurrency levels with 20 requests...\n")

    num_requests = 20
    concurrency_levels = [1, 5, 10, 20]

    results = []
    for concurrency in concurrency_levels:
        elapsed, success_count = measure_time(concurrency, num_requests)
        results.append((concurrency, elapsed, success_count))
        print(
            f"Concurrency: {concurrency:2d} | Time: {elapsed:.2f}s | "
            f"Requests: {success_count}/{num_requests}"
        )

    print("\n--- Analysis ---")
    fastest = min(results, key=lambda x: x[1])
    slowest = max(results, key=lambda x: x[1])
    speedup = slowest[1] / fastest[1]

    print(f"Fastest: concurrency={fastest[0]} (time={fastest[1]:.2f}s)")
    print(f"Slowest: concurrency={slowest[0]} (time={slowest[1]:.2f}s)")
    print(f"Speedup: {speedup:.2f}x")

    print("\n✓ Higher concurrency generally improves performance")
    print("  (Optimal concurrency depends on network and server capacity)")


if __name__ == "__main__":
    main()

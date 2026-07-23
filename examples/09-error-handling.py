#!/usr/bin/env python3
"""
Error handling example.

This example demonstrates:
- Handling PartialFailureError
- Using return_none_on_failure for graceful degradation
- Different error types and handling strategies
"""

from fastreq import (
    BackendError,
    PartialFailureError,
    RetryExhaustedError,
    fastreq,
)


def main():
    print("=== Error Handling Example ===\n")

    print("Scenario 1: Partial failure (default behavior)")
    print("-" * 50)

    urls = [
        "https://httpbin.org/status/200",
        "https://httpbin.org/status/404",
        "https://httpbin.org/status/500",
        "https://httpbin.org/status/503",
    ]

    try:
        results = fastreq(
            urls=urls,
            verbose=False,
        )
    except PartialFailureError as e:
        print("PartialFailureError caught!")
        print(f"  Failed: {len(e.get_failed_urls())}/{e.total} requests")
        print("  Failed URLs:")
        for url in e.get_failed_urls():
            error = e.failures[url].error
            print(f"    - {url}: {error}")

    print("\nScenario 2: Graceful failure (return_none_on_failure)")
    print("-" * 50)

    results = fastreq(
        urls=urls,
        return_none_on_failure=True,
        verbose=False,
    )

    success_count = sum(1 for r in results if r is not None)
    print(f"Results: {success_count} success, {len(results) - success_count} failures")

    for _i, (url, result) in enumerate(zip(urls, results, strict=False)):
        status = "✓ Success" if result is not None else "✗ None (failed)"
        print(f"  {url}: {status}")

    print("\nScenario 3: Handling specific exceptions")
    print("-" * 50)

    test_cases = [
        ("Valid URL", ["https://httpbin.org/get"], False),
        ("Invalid Domain", ["https://thisdomaindoesnotexist12345.com"], True),
    ]

    for name, urls, _expect_error in test_cases:
        print(f"\nTest: {name}")
        try:
            results = fastreq(
                urls=urls,
                max_retries=1,
                verbose=False,
            )
            print(f"  Success: {len(results)} results")
        except BackendError as e:
            print(f"  BackendError: {e}")
        except RetryExhaustedError as e:
            print(f"  RetryExhaustedError: {e}")
        except Exception as e:
            print(f"  Other error ({type(e).__name__}): {e}")

    print("\n--- Error Handling Strategies ---")
    print("• PartialFailureError: Some requests failed")
    print("  - Use return_none_on_failure=True to avoid exceptions")
    print("  - Check failures dict for details")
    print("\n• BackendError: Underlying HTTP client failed")
    print("\n• RetryExhaustedError: All retries exhausted")
    print("\n• ProxyError: Proxy connection/validation failed")

    print("\n✓ Proper error handling makes your code resilient")


if __name__ == "__main__":
    main()

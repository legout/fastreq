#!/usr/bin/env python3
"""
Graceful failure handling example.

This example demonstrates:
- Using return_none_on_failure for partial success
- Handling None results
- Continuing despite failures
"""

from fastreq import (
    PartialFailureError,
    fastreq,
)


def main():
    print("=== Graceful Failure Handling Example ===\n")

    print("Scenario 1: Default behavior (raise on failure)")
    print("-" * 50)

    urls = [
        "https://httpbin.org/status/200",
        "https://httpbin.org/status/404",
        "https://httpbin.org/status/500",
        "https://httpbin.org/get",
    ]

    try:
        results = fastreq(
            urls=urls,
            verbose=False,
        )
    except PartialFailureError as e:
        print("PartialFailureError raised")
        print(f"  Successes: {e.successes}")
        print(f"  Failures: {e.total - e.successes}")
        print("  Failed URLs:")
        for url in e.get_failed_urls():
            error = e.failures[url].error
            print(f"    - {url}: {error}")

    print("\n\nScenario 2: Graceful failure (return None on errors)")
    print("-" * 50)

    results = fastreq(
        urls=urls,
        return_none_on_failure=True,
        verbose=False,
    )

    success_count = sum(1 for r in results if r is not None)
    failure_count = len(results) - success_count

    print(f"Successes: {success_count}")
    print(f"Failures: {failure_count}")
    print("\nDetailed results:")
    for i, (url, result) in enumerate(zip(urls, results, strict=False)):
        status = "✓ Success" if result is not None else "✗ Failed (None)"
        print(f"  Request {i + 1}: {url.split('/')[-1]} - {status}")

    print("\n\nScenario 3: Processing successful results only")
    print("-" * 50)

    print("Extracting data from successful requests:")
    successful_results = [r for r in results if r is not None]

    for i, result in enumerate(successful_results, 1):
        if result:
            print(f"  Result {i}: {result.get('url', 'N/A')}")
            if "origin" in result:
                print(f"    Origin: {result['origin']}")

    print("\n\nScenario 4: Mixed success and failure with POST")
    print("-" * 50)

    post_urls = [
        "https://httpbin.org/post",
        "https://httpbin.org/status/503",
        "https://httpbin.org/post",
        "https://httpbin.org/status/404",
    ]

    post_results = fastreq(
        urls=post_urls,
        method="POST",
        json={"test": "data"},
        return_none_on_failure=True,
        verbose=False,
    )

    print("POST request results:")
    for i, result in enumerate(post_results):
        if result:
            print(f"  Request {i + 1}: ✓ Success")
        else:
            print(f"  Request {i + 1}: ✗ Failed")

    print("\n\nScenario 5: Data aggregation with failures")
    print("-" * 50)

    api_urls = [
        "https://jsonplaceholder.typicode.com/users/1",
        "https://jsonplaceholder.typicode.com/users/invalid",
        "https://jsonplaceholder.typicode.com/users/2",
    ]

    results = fastreq(
        urls=api_urls,
        return_none_on_failure=True,
        verbose=False,
    )

    print("Collecting user data:")
    users = []
    for result in results:
        if result:
            user = {
                "id": result.get("id"),
                "name": result.get("name"),
                "email": result.get("email"),
            }
            users.append(user)
            print(f"  User: {user.get('name', 'Unknown')}")

    print(f"\nSuccessfully fetched {len(users)} users")

    print("\n\nScenario 6: Retry with graceful failure")
    print("-" * 50)

    unreliable_urls = [
        "https://httpbin.org/get?retry=1",
        "https://httpbin.org/status/503",
        "https://httpbin.org/get?retry=2",
        "https://httpbin.org/status/404",
    ]

    results = fastreq(
        urls=unreliable_urls,
        max_retries=3,
        return_none_on_failure=True,
        verbose=False,
    )

    print("Results with retries:")
    for i, result in enumerate(results):
        status = "✓" if result else "✗"
        print(f"  {status} Request {i + 1}")

    print("\n--- Graceful Failure Strategies ---")
    print("• return_none_on_failure=True: Don't raise exceptions")
    print("• Check result is not None before processing")
    print("• Filter: [r for r in results if r is not None]")
    print("• Continue processing successful results")
    print("• Log or track failures separately")

    print("\n✓ Graceful failure handling makes applications more resilient")


if __name__ == "__main__":
    main()

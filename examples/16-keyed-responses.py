#!/usr/bin/env python3
"""
Keyed responses example.

This example demonstrates:
- Using keys parameter for named results
- Getting dict instead of list
- Named result access patterns
"""

from fastreq import fastreq


async def async_example():
    """Async example with keyed responses."""
    print("Async example with keys:")
    print("-" * 50)

    urls = [
        "https://jsonplaceholder.typicode.com/users/1",
        "https://jsonplaceholder.typicode.com/users/2",
        "https://jsonplaceholder.typicode.com/users/3",
    ]

    keys = ["alice", "bob", "charlie"]

    from fastreq import fastreq_async

    results = await fastreq_async(
        urls=urls,
        keys=keys,
        verbose=False,
    )

    print("Results (dict):")
    for key, result in results.items():
        if result:
            print(f"  {key}: {result.get('name', 'N/A')}")


def main():
    print("=== Keyed Responses Example ===\n")

    print("Scenario 1: Using keys parameter")
    print("-" * 50)

    urls = [
        "https://httpbin.org/get?id=alice",
        "https://httpbin.org/get?id=bob",
        "https://httpbin.org/get?id=charlie",
    ]

    keys = ["alice", "bob", "charlie"]

    results = fastreq(
        urls=urls,
        keys=keys,
        verbose=False,
    )

    print("Results (dict):")
    for key, result in results.items():
        if result:
            print(f"  {key}: {result.get('url', 'N/A')}")

    print("\n\nScenario 2: Accessing results by key")
    print("-" * 50)

    print(f"Alice's result URL: {results['alice'].get('url', 'N/A')}")
    print(f"Bob's result URL: {results['bob'].get('url', 'N/A')}")
    print(f"Charlie's result URL: {results['charlie'].get('url', 'N/A')}")

    print("\n\nScenario 3: Keys for API endpoints")
    print("-" * 50)

    urls = [
        "https://jsonplaceholder.typicode.com/users/1",
        "https://jsonplaceholder.typicode.com/posts/1",
        "https://jsonplaceholder.typicode.com/comments/1",
    ]

    keys = ["user", "post", "comment"]

    results = fastreq(
        urls=urls,
        keys=keys,
        verbose=False,
    )

    print("API responses:")
    for key, result in results.items():
        if result:
            if "name" in result:
                print(f"  {key}: {result.get('name', 'N/A')}")
            elif "title" in result:
                print(f"  {key}: {result.get('title', 'N/A')}")

    print("\n\nScenario 4: Error handling with keys")
    print("-" * 50)

    urls = [
        "https://httpbin.org/get?valid=1",
        "https://httpbin.org/status/404",
        "https://httpbin.org/get?valid=2",
    ]

    keys = ["valid1", "error", "valid2"]

    from fastreq import PartialFailureError

    try:
        results = fastreq(
            urls=urls,
            keys=keys,
            verbose=False,
        )
    except PartialFailureError as e:
        print(f"Partial failure: {e.successes}/{e.total}")
        print("Failed URLs:")
        for url in e.get_failed_urls():
            print(f"  - {url}")

    print("\n\nScenario 5: Graceful failure with keys")
    print("-" * 50)

    results = fastreq(
        urls=urls,
        keys=keys,
        return_none_on_failure=True,
        verbose=False,
    )

    print("Results (with return_none_on_failure):")
    for key, result in results.items():
        if result:
            print(f"  {key}: Success")
        else:
            print(f"  {key}: None (failed)")

    print("\n\nScenario 6: Async keyed responses")
    print("-" * 50)

    import asyncio

    asyncio.run(async_example())

    print("\n--- Keyed Responses Benefits ---")
    print("• Named access: results['user'] instead of results[0]")
    print("• Self-documenting: Keys describe what each result is")
    print("• Easier debugging: Clear mapping from request to result")
    print("• More maintainable: Changes to order don't break code")

    print("\n✓ Keys parameter makes results more readable and maintainable")


if __name__ == "__main__":
    main()

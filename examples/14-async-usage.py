#!/usr/bin/env python3
"""
Async usage example.

This example demonstrates:
- Using fastreq_async() function
- Integrating with other async code
- Combining multiple async operations
"""

import asyncio

from fastreq import FastRequests, fastreq_async


async def fetch_data(urls: list[str]) -> list[dict]:
    """Fetch data from multiple URLs asynchronously."""
    print(f"Fetching {len(urls)} URLs...")

    results = await fastreq_async(
        urls=urls,
        concurrency=5,
        verbose=False,
    )

    return results


async def process_data(results: list) -> list:
    """Process results asynchronously."""
    print("Processing results...")

    processed = []
    for i, result in enumerate(results):
        if result:
            processed.append(
                {
                    "index": i,
                    "url": result.get("url", ""),
                    "processed": True,
                }
            )
        await asyncio.sleep(0.01)

    return processed


async def main():
    print("=== Async Usage Example ===\n")

    print("Scenario 1: Using fastreq_async()")
    print("-" * 50)

    urls = [
        "https://httpbin.org/get?id=1",
        "https://httpbin.org/get?id=2",
        "https://httpbin.org/get?id=3",
    ]

    results = await fastreq_async(
        urls=urls,
        concurrency=3,
        verbose=False,
    )

    print(f"Completed {len(results)} requests")
    for result in results:
        if result:
            print(f"  URL: {result.get('url', 'N/A')}")

    print("\n\nScenario 2: Combining with other async operations")
    print("-" * 50)

    async def task_a():
        print("Task A: Starting")
        await asyncio.sleep(1)
        print("Task A: Complete")
        return "Result A"

    async def task_b():
        print("Task B: Starting")
        results = await fastreq_async(
            urls=["https://httpbin.org/delay/1"],
            verbose=False,
        )
        print("Task B: Complete")
        return f"Result B ({len(results)} requests)"

    async def task_c():
        print("Task C: Starting")
        await asyncio.sleep(0.5)
        print("Task C: Complete")
        return "Result C"

    results = await asyncio.gather(task_a(), task_b(), task_c())
    print(f"\nAll tasks complete: {results}")

    print("\n\nScenario 3: Async processing pipeline")
    print("-" * 50)

    urls = [f"https://httpbin.org/get?item={i}" for i in range(5)]

    fetched_data = await fetch_data(urls)
    processed_data = await process_data(fetched_data)

    print("\nPipeline results:")
    print(f"  Fetched: {len(fetched_data)} items")
    print(f"  Processed: {len(processed_data)} items")

    print("\n\nScenario 4: Async with custom client")
    print("-" * 50)

    async def make_requests_with_custom_client():
        client = FastRequests(
            backend="auto",
            concurrency=3,
            verbose=False,
        )

        async with client:
            urls = ["https://httpbin.org/uuid"] * 3
            results = await client.request(urls=urls)
            return results

    results = await make_requests_with_custom_client()
    print(f"Custom client results: {len(results)} requests")

    print("\n\nScenario 5: Sequential async operations")
    print("-" * 50)

    batch1 = await fastreq_async(
        urls=["https://httpbin.org/get?batch=1"],
        verbose=False,
    )

    batch2 = await fastreq_async(
        urls=["https://httpbin.org/get?batch=2"],
        verbose=False,
    )

    print(f"Batch 1: {len(batch1)} requests")
    print(f"Batch 2: {len(batch2)} requests")

    print("\n--- Async Patterns ---")
    print("• fastreq_async(): Quick async function")
    print("• asyncio.gather(): Run multiple async operations")
    print("• Sequential awaits: Run operations in order")
    print("• Custom clients: More control and session reuse")

    print("\n✓ Async patterns enable efficient, non-blocking code")


if __name__ == "__main__":
    asyncio.run(main())

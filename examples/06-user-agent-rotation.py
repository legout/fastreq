#!/usr/bin/env python3
"""
User agent rotation example.

This example demonstrates:
- Default user agent rotation (enabled by default)
- Using custom user agent list
- User agent headers in requests
"""

from fastreq import fastreq


def main():
    print("=== User Agent Rotation Example ===\n")

    urls = [
        "https://httpbin.org/user-agent",
        "https://httpbin.org/user-agent",
        "https://httpbin.org/user-agent",
    ]

    print("Scenario 1: Default user agent rotation")
    print("-" * 50)

    results = fastreq(
        urls=urls,
        random_user_agent=True,
        verbose=False,
    )

    print("\nUser agents used:")
    user_agents = set()
    for i, result in enumerate(results):
        if result and "user-agent" in result:
            ua = result["user-agent"]
            user_agents.add(ua)
            print(f"  Request {i + 1}: {ua[:60]}...")

    print(f"\nUnique user agents: {len(user_agents)}")

    print("\n\nScenario 2: Disable user agent rotation")
    print("-" * 50)

    results = fastreq(
        urls=urls,
        random_user_agent=False,
        verbose=False,
    )

    print("\nUser agents used:")
    user_agents = set()
    for _i, result in enumerate(results):
        if result and "user-agent" in result:
            ua = result["user-agent"]
            user_agents.add(ua)

    print(f"Unique user agents: {len(user_agents)}")

    print("\n\nScenario 3: Custom user agent (single)")
    print("-" * 50)

    custom_ua = "MyCustomApp/1.0 (https://example.com/bot)"

    results = fastreq(
        urls=urls,
        random_user_agent=False,
        headers={"User-Agent": custom_ua},
        verbose=False,
    )

    print("\nUser agents used:")
    for i, result in enumerate(results):
        if result and "user-agent" in result:
            print(f"  Request {i + 1}: {result['user-agent']}")

    print("\n--- User Agent Rotation Benefits ---")
    print("• Avoids detection as a scraper")
    print("• Mimics real browser traffic")
    print("• Useful for web scraping and API access")
    print("• Default enabled: random_user_agent=True")

    print("\n✓ User agent rotation helps prevent blocking")


if __name__ == "__main__":
    main()

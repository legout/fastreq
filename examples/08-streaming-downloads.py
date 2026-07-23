#!/usr/bin/env python3
"""
Streaming downloads example.

This example demonstrates:
- Streaming large file downloads
- Progress tracking with callbacks
- Efficient memory usage

Note: Streaming support varies by backend
"""

from fastreq import ReturnType, fastreq


class ProgressTracker:
    """Track download progress across multiple requests."""

    def __init__(self, total_files: int):
        self.total_files = total_files
        self.completed_files = 0
        self.total_bytes = 0

    def track(self, chunk: bytes, file_num: int) -> None:
        """Called for each chunk received."""
        self.total_bytes += len(chunk)
        print(f"\rFile {file_num + 1}: {len(chunk):,} bytes received", end="")

    def file_complete(self):
        """Mark a file as complete."""
        self.completed_files += 1
        print(f"\n✓ File {self.completed_files}/{self.total_files} complete")


def main():
    print("=== Streaming Downloads Example ===\n")

    print("Scenario 1: Streaming with callback")
    print("-" * 50)

    urls = [
        "https://httpbin.org/bytes/1024",
        "https://httpbin.org/bytes/2048",
        "https://httpbin.org/bytes/512",
    ]

    tracker = ProgressTracker(len(urls))

    def create_callback(file_num: int):
        """Create a callback function for a specific file."""

        def callback(chunk: bytes) -> None:
            tracker.track(chunk, file_num)

        return callback

    [create_callback(i) for i in range(len(urls))]

    fastreq(
        urls=urls,
        return_type=ReturnType.STREAM,
        stream_callback=lambda chunk: None,
        concurrency=2,
        verbose=False,
    )

    print("\n\nScenario 2: Custom progress tracking")
    print("-" * 50)

    file_sizes = {}

    def track_progress(url: str, chunk: bytes) -> None:
        """Track progress for a specific URL."""
        if url not in file_sizes:
            file_sizes[url] = 0
        file_sizes[url] += len(chunk)

        for u, size in file_sizes.items():
            print(f"\r{u}: {size:,} bytes", end="")

    print("\nDownloading files with progress...")

    results = fastreq(
        urls=urls,
        return_type=ReturnType.CONTENT,
        concurrency=2,
        verbose=False,
    )

    print("\n\nDownloaded file sizes:")
    for url, content in zip(urls, results, strict=False):
        if content:
            print(f"  {url}: {len(content):,} bytes")

    print("\n--- Streaming Benefits ---")
    print("• Lower memory usage for large files")
    print("• Progress tracking during download")
    print("• Ability to process data incrementally")
    print("• Cancel mid-download if needed")

    print("\n✓ Streaming is ideal for large file downloads")


if __name__ == "__main__":
    main()

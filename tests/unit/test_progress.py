"""Tests for optional request progress reporting."""

from __future__ import annotations

import asyncio

import pytest

from fastreq.utils.progress import gather_with_progress, progress_reporter


@pytest.mark.asyncio
async def test_gather_with_progress_preserves_input_order_and_reports_completion() -> None:
    completed: list[tuple[int, int]] = []

    async def delayed(value: int, delay: float) -> int:
        await asyncio.sleep(delay)
        return value

    results = await gather_with_progress(
        [delayed(1, 0.02), delayed(2, 0.0), delayed(3, 0.01)],
        callback=lambda current, total: completed.append((current, total)),
    )

    assert results == [1, 2, 3]
    assert completed == [(1, 3), (2, 3), (3, 3)]


@pytest.mark.asyncio
async def test_gather_with_progress_preserves_exceptions() -> None:
    async def fail() -> None:
        raise ValueError("boom")

    results = await gather_with_progress([fail()])

    assert isinstance(results[0], ValueError)
    assert str(results[0]) == "boom"


def test_disabled_progress_does_not_import_optional_ui(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(__import__("sys").modules, "rich", None)
    with progress_reporter(False, total=1, description="test") as advance:
        advance()

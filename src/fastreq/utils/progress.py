"""Optional progress reporting without a mandatory UI dependency."""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Callable, Coroutine, Sequence
from contextlib import contextmanager
from typing import Any, Literal

ProgressMode = Literal["rich", "tqdm"]
ProgressOption = bool | ProgressMode | None
ProgressCallback = Callable[[int, int], Any]


@contextmanager
def progress_reporter(
    mode: ProgressOption,
    *,
    total: int,
    description: str,
):
    """Yield a ``completed`` callback for an optional terminal progress bar.

    ``False``/``None`` disables all UI. ``True`` tries Rich first and then tqdm.
    A named mode requires that optional dependency and raises a useful error when
    it is not installed. Non-interactive stderr suppresses the visual bar while
    retaining the callback semantics for callers that provide one separately.
    """
    if not mode or total == 0:
        yield lambda: None
        return

    selected = "rich" if mode is True else mode
    is_tty = sys.stderr.isatty()

    if selected == "rich":
        try:
            from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn
        except ImportError as exc:
            if mode is True:
                with _tqdm_reporter(total, description, is_tty) as advance:
                    yield advance
                return
            raise RuntimeError(
                "progress='rich' requires the optional dependency; install fastreq[progress-rich]"
            ) from exc

        progress = Progress(
            TextColumn("{task.description}"),
            BarColumn(),
            "{task.completed}/{task.total}",
            TimeRemainingColumn(),
            disable=not is_tty,
        )
        with progress:
            task_id = progress.add_task(description, total=total)

            def advance() -> None:
                progress.advance(task_id)

            yield advance
        return

    if selected == "tqdm":
        try:
            from tqdm.auto import tqdm
        except ImportError as exc:
            raise RuntimeError(
                "progress='tqdm' requires the optional dependency; install fastreq[progress-tqdm]"
            ) from exc

        bar = tqdm(total=total, desc=description, unit="req", disable=not is_tty)

        def advance() -> None:
            bar.update(1)

        try:
            yield advance
        finally:
            bar.close()
        return

    raise ValueError(f"unknown progress mode: {selected!r}; use 'rich' or 'tqdm'")


@contextmanager
def _tqdm_reporter(total: int, description: str, is_tty: bool):
    try:
        from tqdm.auto import tqdm
    except ImportError as tqdm_error:
        raise RuntimeError(
            "progress=True requires either Rich or tqdm; install "
            "fastreq[progress-rich] or fastreq[progress-tqdm]"
        ) from tqdm_error

    bar = tqdm(total=total, desc=description, unit="req", disable=not is_tty)

    def advance() -> None:
        bar.update(1)

    try:
        yield advance
    finally:
        bar.close()


async def gather_with_progress(
    coroutines: Sequence[Coroutine[Any, Any, Any]],
    *,
    mode: ProgressOption = None,
    callback: ProgressCallback | None = None,
    description: str = "Requests",
    return_exceptions: bool = True,
) -> list[Any]:
    """Gather coroutines in input order while reporting completed work."""
    if not coroutines:
        return []
    if mode is None and callback is None:
        return list(await asyncio.gather(*coroutines, return_exceptions=return_exceptions))

    async def run(index: int, coroutine: Coroutine[Any, Any, Any]):
        if not return_exceptions:
            return index, await coroutine, None
        try:
            return index, await coroutine, None
        except Exception as exc:  # preserve gather(return_exceptions=True) behavior
            return index, None, exc

    results: list[Any] = [None] * len(coroutines)
    completed_count = 0
    with progress_reporter(mode, total=len(coroutines), description=description) as advance:
        tasks = [
            asyncio.create_task(run(index, coroutine)) for index, coroutine in enumerate(coroutines)
        ]
        for completed in asyncio.as_completed(tasks):
            try:
                index, result, error = await completed
            except Exception:
                for task in tasks:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                raise
            results[index] = error if error is not None else result
            completed_count += 1
            advance()
            if callback is not None:
                callback(completed_count, len(coroutines))
    return results

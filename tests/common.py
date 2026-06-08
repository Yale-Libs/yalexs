from __future__ import annotations

import asyncio
import time
from asyncio import AbstractEventLoop, TimerHandle
from typing import Any

from aiointercept import aiointercept as _aiointercept

_MONOTONIC_RESOLUTION = time.get_clock_info("monotonic").resolution
ScheduledType = TimerHandle | tuple[float, TimerHandle]


class aiointercept(_aiointercept):  # noqa: N801
    """aiointercept preconfigured to intercept external hosts.

    aioresponses mocked every request by default; aiointercept only
    redirects external hosts when ``mock_external_urls=True``. This shim
    restores the aioresponses-compatible default so the test call sites
    (``@aiointercept()`` / ``async with aiointercept()``) need no changes.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("mock_external_urls", True)
        super().__init__(*args, **kwargs)


def get_scheduled_timer_handles(loop: AbstractEventLoop) -> list[TimerHandle]:
    """Return a list of scheduled TimerHandles."""
    handles: list[ScheduledType] = loop._scheduled  # type: ignore[attr-defined]
    return [
        handle if isinstance(handle, TimerHandle) else handle[1] for handle in handles
    ]


def fire_time_changed() -> None:
    timestamp = time.time()
    loop = asyncio.get_running_loop()
    for task in list(get_scheduled_timer_handles(loop)):
        if not isinstance(task, asyncio.TimerHandle):
            continue
        if task.cancelled():
            continue

        mock_seconds_into_future = timestamp - time.time()
        future_seconds = task.when() - (loop.time() + _MONOTONIC_RESOLUTION)

        if mock_seconds_into_future >= future_seconds:
            task._run()
            task.cancel()

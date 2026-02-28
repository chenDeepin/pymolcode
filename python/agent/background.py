"""Background agent manager for parallel task execution.

Runs multiple agent tasks concurrently, each in its own context,
and collects results.  Inspired by oh-my-opencode's background
agent pattern.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, TypeVar

__all__ = ["AgentHandle", "BackgroundAgentManager"]

LOGGER = logging.getLogger("pymolcode.background")

T = TypeVar("T")


class HandleStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentHandle:
    """Handle to a background agent task."""

    id: str
    description: str
    category: str = "quick"
    status: HandleStatus = HandleStatus.PENDING
    result: Any = None
    error: str | None = None
    _task: asyncio.Task[Any] | None = field(default=None, repr=False)


class BackgroundAgentManager:
    """Manages a pool of background agent tasks.

    Example::

        mgr = BackgroundAgentManager(agent=my_agent, max_parallel=5)
        h1 = await mgr.spawn("Analyze binding site of 3KYS", "analysis")
        h2 = await mgr.spawn("Load and prepare 1UBQ", "structure")
        results = await mgr.gather([h1, h2])
    """

    def __init__(
        self,
        agent: Any | None = None,
        max_parallel: int = 5,
    ) -> None:
        self._agent = agent
        self._max_parallel = max_parallel
        self._semaphore = asyncio.Semaphore(max_parallel)
        self._handles: dict[str, AgentHandle] = {}

    @property
    def active_count(self) -> int:
        return sum(
            1 for h in self._handles.values() if h.status == HandleStatus.RUNNING
        )

    def list_handles(self) -> list[AgentHandle]:
        return list(self._handles.values())

    async def spawn(self, task: str, category: str = "quick") -> AgentHandle:
        """Spawn a background agent task."""
        handle = AgentHandle(
            id=str(uuid.uuid4())[:8],
            description=task,
            category=category,
        )
        self._handles[handle.id] = handle

        async_task = asyncio.create_task(self._run(handle))
        handle._task = async_task

        LOGGER.info("Spawned background agent %s: %s", handle.id, task)
        return handle

    async def gather(self, handles: list[AgentHandle]) -> list[Any]:
        """Wait for all handles to complete and return results."""
        tasks = [h._task for h in handles if h._task is not None]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        return [h.result for h in handles]

    async def cancel(self, handle_id: str) -> bool:
        """Cancel a running background task."""
        handle = self._handles.get(handle_id)
        if handle is None or handle._task is None:
            return False

        if handle.status == HandleStatus.RUNNING:
            handle._task.cancel()
            handle.status = HandleStatus.CANCELLED
            LOGGER.info("Cancelled agent %s", handle_id)
            return True
        return False

    async def map_reduce(
        self,
        tasks: list[str],
        *,
        category: str = "quick",
        reducer: Callable[[list[Any]], Any] | None = None,
    ) -> Any:
        """Spawn multiple tasks and reduce results.

        Args:
            tasks: List of task descriptions.
            category: Agent category for all tasks.
            reducer: Function to combine results. Default concatenates strings.
        """
        handles = [await self.spawn(t, category) for t in tasks]
        results = await self.gather(handles)

        if reducer is not None:
            return reducer(results)

        return "\n---\n".join(str(r) for r in results if r is not None)

    async def _run(self, handle: AgentHandle) -> None:
        """Execute a single background task with semaphore gating."""
        async with self._semaphore:
            handle.status = HandleStatus.RUNNING
            try:
                if self._agent is not None:
                    response = await self._agent.chat(handle.description)
                    handle.result = response.message.content
                else:
                    handle.result = f"[no agent] {handle.description}"

                handle.status = HandleStatus.COMPLETED
                LOGGER.info("Agent %s completed", handle.id)
            except asyncio.CancelledError:
                handle.status = HandleStatus.CANCELLED
            except Exception as exc:
                handle.status = HandleStatus.FAILED
                handle.error = str(exc)
                LOGGER.error("Agent %s failed: %s", handle.id, exc)

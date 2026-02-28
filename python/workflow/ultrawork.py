"""Ultrawork: one-command agentic workflow execution.

Inspired by oh-my-opencode's ``ultrawork`` / ``ulw`` command.
Activates the Hephaestus orchestrator with todo enforcement
and drives the workflow to completion.

Usage:
    pymolcode ultrawork "analyze TEAD1 binding pocket and dock 10 ligands"
"""

from __future__ import annotations

import contextlib
import logging

__all__ = ["run_ultrawork"]

LOGGER = logging.getLogger("pymolcode.ultrawork")


async def run_ultrawork(prompt: str, *, max_iterations: int = 100) -> int:
    """Execute a full agentic workflow from a single prompt.

    Returns 0 on success, 1 on failure.
    """
    from python.agent.agent import Agent
    from python.agent.orchestrator import Hephaestus, TodoStatus

    print("\n  pymolcode ultrawork")
    print(f"  Goal: {prompt}\n")

    agent = Agent()

    with contextlib.suppress(Exception):
        agent._resolve_provider()

    if not agent.config.api_key:
        print("  No LLM provider configured.")
        print("  Run: pymolcode auth login <provider>")
        return 1

    # Use Hephaestus (The Legitimate Craftsman) orchestrator
    hephaestus = Hephaestus(
        agent=agent,
        max_parallel=5,
        max_iterations=max_iterations,
    )

    print("  Hephaestus crafting plan...")
    plan = await hephaestus.plan(prompt)
    print(f"  {len(plan.todos)} steps identified:\n")

    for i, todo in enumerate(plan.todos, 1):
        print(f"    {i}. [{todo.category.value}] {todo.description}")
    print()

    print("  Forging...\n")
    results = await hephaestus.forge(plan)

    completed = sum(1 for t in results if t.status == TodoStatus.COMPLETED)
    failed = sum(1 for t in results if t.status == TodoStatus.FAILED)
    total = len(results)

    print(f"\n  Results: {completed}/{total} completed", end="")
    if failed:
        print(f", {failed} failed", end="")
    print("\n")

    for todo in results:
        icon = "+" if todo.status == TodoStatus.COMPLETED else "x"
        print(f"    [{icon}] {todo.description}")
        if todo.error:
            print(f"        Error: {todo.error}")
        if todo.spec_issues:
            print(f"        Spec issues: {len(todo.spec_issues)}")
        if todo.quality_issues:
            print(f"        Quality issues: {len(todo.quality_issues)}")
    print()

    return 0 if failed == 0 else 1

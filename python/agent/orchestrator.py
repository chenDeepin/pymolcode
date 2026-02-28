"""Hephaestus orchestrator for drug discovery workflows.

Hephaestus: The Legitimate Craftsman - autonomous deep worker for
implementation tasks. Named after the Greek god of craftsmen.

Characteristics (adapted from oh-my-opencode v3.7.1):
- Explores codebase autonomously without hand-holding
- Researches patterns and executes end-to-end
- Deep, focused implementation on complex tasks
- Self-review before completion
- Spec compliance + code quality gates

Model preference: OpenAI models (gpt-4o, gpt-4-turbo) for compatibility.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

__all__ = [
    "AgentCategory",
    "Hephaestus",
    "TaskHandle",
    "TodoItem",
    "TodoStatus",
    "WorkflowPlan",
    "ReviewStage",
]

LOGGER = logging.getLogger("pymolcode.hephaestus")


class AgentCategory(StrEnum):
    """Task categories that map to specialist agents."""

    STRUCTURE = "structure"        # Load/fetch PDB, protein structures
    DOCKING = "docking"            # Molecular docking, ligand binding
    ANALYSIS = "analysis"          # RMSD, energy, interactions
    VISUALIZATION = "visualization"  # Render, color, screenshots
    RESEARCH = "research"          # Database search, literature
    DEEP_WORK = "deep_work"        # Complex multi-step implementation
    QUICK = "quick"                # Simple single-step tasks


class TodoStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReviewStage(StrEnum):
    """Two-stage review process from subagent-driven-development."""

    SELF_REVIEW = "self_review"
    SPEC_COMPLIANCE = "spec_compliance"
    CODE_QUALITY = "code_quality"
    DONE = "done"


@dataclass
class TodoItem:
    """A trackable work item in a workflow."""

    id: str
    description: str
    status: TodoStatus = TodoStatus.PENDING
    category: AgentCategory = AgentCategory.QUICK
    review_stage: ReviewStage = ReviewStage.SELF_REVIEW
    result: Any = None
    error: str | None = None
    spec_issues: list[str] = field(default_factory=list)
    quality_issues: list[str] = field(default_factory=list)

    @property
    def is_done(self) -> bool:
        return self.status in (TodoStatus.COMPLETED, TodoStatus.FAILED)

    @property
    def needs_review(self) -> bool:
        return self.review_stage != ReviewStage.DONE


@dataclass
class TaskHandle:
    """Handle for a running async task."""

    id: str
    category: AgentCategory
    description: str
    task: asyncio.Task[Any] | None = None


@dataclass
class WorkflowPlan:
    """A planned sequence of tasks to execute."""

    goal: str
    todos: list[TodoItem] = field(default_factory=list)
    context: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


# Hephaestus model preferences
HEPHAESTUS_MODEL_PREFERENCES = [
    # Top-tier reasoning models (newest)
    "anthropic/claude-opus-4-6",
    "anthropic/claude-opus-4-5",
    "openai/gpt-5.3-codex",
    "openai/gpt-5.2-codex",
    # Zhipu AI GLM-5
    "zai/glm-5",
    # Kimi K2.5
    "moonshot/kimi-k2.5",
]


class Hephaestus:
    """Hephaestus: The Legitimate Craftsman orchestrator.

    A discipline agent that:
    - Plans goals into concrete implementation steps
    - Delegates to specialist subagents by category
    - Enforces two-stage review (spec + quality)
    - Drives tasks to completion autonomously

    Usage:
        heph = Hephaestus(agent=my_agent)
        plan = await heph.plan("Dock 10 ligands against TEAD1")
        results = await heph.forge(plan)  # "forge" instead of "execute"
    """

    # Hephaestus identity prompt
    IDENTITY = """\
You are Hephaestus, the Legitimate Craftsman.

Your role is autonomous deep work on complex implementation tasks.
You explore codebases, research patterns, and execute end-to-end
without hand-holding.

Core principles:
1. EXPLORE: Understand the codebase before acting
2. RESEARCH: Find existing patterns to follow
3. IMPLEMENT: Build exactly what's needed (no over-engineering)
4. VERIFY: Self-review against spec before completion
5. CRAFT: Produce clean, maintainable code

You prefer OpenAI models for their strong implementation capabilities.
When breaking down tasks, think like a craftsman: precise, methodical,
quality-focused.
"""

    def __init__(
        self,
        agent: Any | None = None,
        max_parallel: int = 5,
        max_iterations: int = 100,
        model: str | None = None,
    ) -> None:
        self._agent = agent
        self._max_parallel = max_parallel
        self._max_iterations = max_iterations
        self._model = model or HEPHAESTUS_MODEL_PREFERENCES[0]
        self._active_handles: dict[str, TaskHandle] = {}

    async def plan(self, goal: str, context: str = "") -> WorkflowPlan:
        """Break a high-level goal into a sequence of todo items.

        Hephaestus plans by understanding the task deeply first,
        then decomposing into concrete implementation steps.

        Args:
            goal: The high-level objective to achieve
            context: Additional context about the work environment
        """
        if self._agent is not None:
            return await self._craft_plan(goal, context)

        return WorkflowPlan(
            goal=goal,
            context=context,
            todos=[
                TodoItem(
                    id=str(uuid.uuid4())[:8],
                    description=goal,
                    category=AgentCategory.QUICK,
                )
            ],
        )

    async def forge(self, plan: WorkflowPlan) -> list[TodoItem]:
        """Execute a workflow plan with craftsman discipline.

        "forge" instead of "execute" - Hephaestus is a craftsman.
        Enforces two-stage review: spec compliance, then code quality.
        """
        LOGGER.info("Hephaestus forging: %s (%d steps)", plan.goal, len(plan.todos))

        iteration = 0
        while iteration < self._max_iterations:
            iteration += 1

            # Find todos that need work
            pending = [t for t in plan.todos if not t.is_done]
            if not pending:
                break

            # Process in batches up to max_parallel
            batch = pending[: self._max_parallel]
            await self._forge_batch(batch, plan.context)

            # Check for failures
            failed = [t for t in batch if t.status == TodoStatus.FAILED]
            if failed:
                LOGGER.warning(
                    "%d tasks failed in iteration %d", len(failed), iteration
                )

        # Final report
        incomplete = [t for t in plan.todos if not t.is_done]
        if incomplete:
            LOGGER.error(
                "%d tasks remain incomplete after %d iterations",
                len(incomplete),
                iteration,
            )
        else:
            LOGGER.info("All %d tasks forged successfully", len(plan.todos))

        return plan.todos

    # Alias for backward compatibility
    async def execute(self, plan: WorkflowPlan) -> list[TodoItem]:
        """Alias for forge() - backward compatibility."""
        return await self.forge(plan)

    async def _forge_batch(self, todos: list[TodoItem], context: str) -> None:
        """Forge a batch of todos with review gates."""
        tasks: list[asyncio.Task[Any]] = []

        for todo in todos:
            todo.status = TodoStatus.IN_PROGRESS
            task = asyncio.create_task(self._forge_single(todo, context))
            handle = TaskHandle(
                id=todo.id,
                category=todo.category,
                description=todo.description,
                task=task,
            )
            self._active_handles[todo.id] = handle
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

        for todo in todos:
            self._active_handles.pop(todo.id, None)

    async def _forge_single(self, todo: TodoItem, context: str) -> None:
        """Forge a single todo item with two-stage review."""
        LOGGER.info("[Hephaestus] Forging: %s", todo.description)

        try:
            # Stage 1: Implementation
            if self._agent is not None:
                impl_prompt = self._build_implementation_prompt(todo, context)
                response = await self._agent.chat(impl_prompt)
                todo.result = response.message.content
            else:
                todo.result = f"Forged: {todo.description}"

            # Stage 2: Self-review
            todo.review_stage = ReviewStage.SELF_REVIEW
            await self._self_review(todo)

            # Stage 3: Spec compliance check
            todo.review_stage = ReviewStage.SPEC_COMPLIANCE
            await self._check_spec_compliance(todo)

            # Stage 4: Code quality check
            todo.review_stage = ReviewStage.CODE_QUALITY
            await self._check_code_quality(todo)

            # Mark complete if all reviews passed
            if not todo.spec_issues and not todo.quality_issues:
                todo.review_stage = ReviewStage.DONE
                todo.status = TodoStatus.COMPLETED
                LOGGER.info("[Hephaestus] Completed: %s", todo.description)
            else:
                # Issues found - mark as failed for retry
                todo.status = TodoStatus.FAILED
                todo.error = "Review issues found"
                LOGGER.warning(
                    "[Hephaestus] Review issues for %s: spec=%d, quality=%d",
                    todo.description,
                    len(todo.spec_issues),
                    len(todo.quality_issues),
                )

        except Exception as exc:
            todo.status = TodoStatus.FAILED
            todo.error = str(exc)
            LOGGER.error("[Hephaestus] Failed: %s -- %s", todo.description, exc)

    async def _self_review(self, todo: TodoItem) -> None:
        """Perform self-review of the implementation."""
        if self._agent is None:
            return

        prompt = f"""\
Review your implementation of: {todo.description}

Self-review checklist:
- Did I fully implement everything specified?
- Are there edge cases I missed?
- Is the code clean and maintainable?
- Did I avoid over-building (YAGNI)?
- Do tests verify actual behavior?

If issues found, list them. Otherwise respond: "Self-review: PASS"
"""
        response = await self._agent.chat(prompt)
        if "PASS" not in response.message.content.upper():
            todo.quality_issues.append("Self-review found issues")

    async def _check_spec_compliance(self, todo: TodoItem) -> None:
        """Check spec compliance (first review gate)."""
        if self._agent is None:
            return

        prompt = f"""\
Spec compliance review for: {todo.description}

Check:
1. Did implementation match the specification exactly?
2. Was anything requested but missing?
3. Was anything added that wasn't requested?

Respond with:
- "SPEC: PASS" if compliant
- "SPEC: ISSUES" followed by list of problems if not
"""
        response = await self._agent.chat(prompt)
        content = response.message.content
        if "ISSUES" in content.upper():
            # Extract issues from response
            todo.spec_issues.append(content)

    async def _check_code_quality(self, todo: TodoItem) -> None:
        """Check code quality (second review gate)."""
        if self._agent is None:
            return

        prompt = f"""\
Code quality review for: {todo.description}

Check:
1. Are names clear and accurate?
2. Is code DRY (no repetition)?
3. Are there magic numbers/strings?
4. Is error handling adequate?
5. Are there potential bugs?

Respond with:
- "QUALITY: PASS" if acceptable
- "QUALITY: ISSUES" followed by list of problems if not
"""
        response = await self._agent.chat(prompt)
        content = response.message.content
        if "ISSUES" in content.upper():
            todo.quality_issues.append(content)

    async def _craft_plan(self, goal: str, context: str) -> WorkflowPlan:
        """Use the LLM to craft a detailed implementation plan."""
        prompt = f"""\
{self.IDENTITY}

Craft an implementation plan for this drug discovery task.
Break it down into concrete, actionable steps.

Context: {context}

Task: {goal}

For each step, consider:
- What needs to be done
- What dependencies exist
- What could go wrong

Format your response as a numbered list of steps.
Each step should be a single actionable task.
"""
        response = await self._agent.chat(prompt)
        text = response.message.content

        todos: list[TodoItem] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            cleaned = line.lstrip("0123456789.-) ").strip()
            if cleaned and len(cleaned) > 3:
                category = self._classify_task(cleaned)
                todos.append(
                    TodoItem(
                        id=str(uuid.uuid4())[:8],
                        description=cleaned,
                        category=category,
                    )
                )

        if not todos:
            todos.append(
                TodoItem(
                    id=str(uuid.uuid4())[:8],
                    description=goal,
                    category=AgentCategory.DEEP_WORK,
                )
            )

        return WorkflowPlan(goal=goal, context=context, todos=todos)

    def _build_implementation_prompt(self, todo: TodoItem, context: str) -> str:
        """Build the implementation prompt for a todo item."""
        return f"""\
{self.IDENTITY}

## Task Description

{todo.description}

## Context

{context}

## Before You Begin

If you have questions about:
- The requirements or acceptance criteria
- The approach or implementation strategy
- Dependencies or assumptions

Ask them now. Raise concerns before starting work.

## Your Job

1. Implement exactly what the task specifies
2. Write tests if applicable
3. Verify implementation works
4. Commit your work (conceptually)
5. Self-review before reporting

## Report Format

When done, report:
- What you implemented
- What you tested
- Files changed
- Any issues or concerns
"""

    def _classify_task(self, description: str) -> AgentCategory:
        """Heuristic classification of a task description."""
        lower = description.lower()

        # Deep work indicators (complex multi-step)
        if any(w in lower for w in ("implement", "refactor", "redesign", "migrate")):
            return AgentCategory.DEEP_WORK

        # Domain-specific categories
        if any(w in lower for w in ("load", "fetch", "pdb", "structure", "protein", "prepare")):
            return AgentCategory.STRUCTURE
        if any(w in lower for w in ("dock", "ligand", "binding", "pocket", "score")):
            return AgentCategory.DOCKING
        if any(w in lower for w in ("analyze", "rmsd", "energy", "interaction", "compare")):
            return AgentCategory.ANALYSIS
        if any(w in lower for w in ("visualize", "render", "color", "screenshot", "display")):
            return AgentCategory.VISUALIZATION
        if any(w in lower for w in ("search", "literature", "database", "pubchem", "query")):
            return AgentCategory.RESEARCH

        return AgentCategory.QUICK


# Backward compatibility alias
Orchestrator = Hephaestus

"""Skill registry for managing available skills."""

from __future__ import annotations

from typing import Any

from python.skill.base import Skill, SkillContext, SkillResult, SkillStatus


class SkillRegistry:
    """Registry of available skills."""

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}
        self._register_builtin_skills()

    def _register_builtin_skills(self) -> None:
        """Register built-in skills."""
        from python.skill.builtin import (
            BindingSiteAnalysisSkill,
            LigandComparisonSkill,
            StructureAnalysisSkill,
            TrajectoryAnalysisSkill,
        )

        self.register(StructureAnalysisSkill())
        self.register(BindingSiteAnalysisSkill())
        self.register(LigandComparisonSkill())
        self.register(TrajectoryAnalysisSkill())

    def register(self, skill: Skill) -> None:
        """Register a skill."""
        self._skills[skill.name] = skill

    def get(self, name: str) -> Skill | None:
        """Get a skill by name."""
        return self._skills.get(name)

    def list_skills(self) -> list[Skill]:
        """List all registered skills."""
        return list(self._skills.values())

    def get_schemas(self) -> list[dict[str, Any]]:
        """Get schemas for all skills."""
        return [skill.get_schema() for skill in self._skills.values()]

    async def execute(
        self,
        name: str,
        params: dict[str, Any],
        context: SkillContext,
    ) -> SkillResult:
        """Execute a skill by name."""
        skill = self.get(name)
        if skill is None:
            return SkillResult(
                skill_name=name,
                status=SkillStatus.FAILED,
                error=f"Unknown skill: {name}",
            )
        return await skill.execute(params, context)

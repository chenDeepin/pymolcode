"""Base classes for the skill system."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SkillStatus(str, Enum):
    """Status of a skill execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SkillResult:
    """Result of a skill execution."""

    skill_name: str
    status: SkillStatus
    output: dict[str, Any] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)
    error: str | None = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.status == SkillStatus.COMPLETED


@dataclass
class SkillContext:
    """Context for skill execution."""

    session_id: str
    working_dir: str
    artifacts_dir: str
    pymol_executor: Any | None = None  # CommandExecutor
    agent: Any | None = None  # Agent
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillParameter:
    """Definition of a skill parameter."""

    name: str
    type: str  # JSON Schema type
    description: str
    required: bool = True
    default: Any | None = None
    enum: list[str] | None = None


class Skill(ABC):
    """Base class for all skills."""

    name: str = "base_skill"
    description: str = "Base skill class"
    version: str = "1.0.0"
    parameters: list[SkillParameter] = []
    tags: list[str] = []

    @abstractmethod
    async def execute(
        self,
        params: dict[str, Any],
        context: SkillContext,
    ) -> SkillResult:
        """Execute the skill with the given parameters."""
        ...

    def get_schema(self) -> dict[str, Any]:
        """Get the JSON schema for this skill."""
        properties = {}
        required = []

        for param in self.parameters:
            prop: dict[str, Any] = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                prop["enum"] = param.enum
            if param.default is not None:
                prop["default"] = param.default
            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
            "tags": self.tags,
        }

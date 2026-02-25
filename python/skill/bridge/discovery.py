"""Multi-source skill discovery engine.

Scans local directories, project skills, and external adapters
to build a unified skill catalog.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

__all__ = ["SkillDiscovery", "SkillMetadata", "SkillSource"]

LOGGER = logging.getLogger("pymolcode.skill.discovery")


class SkillSource(str, Enum):
    """Origin of a discovered skill."""

    BUILTIN = "builtin"
    PROJECT = "project"
    USER = "user"
    OMO = "oh-my-opencode"
    SKILLS_CLI = "skills-cli"


@dataclass
class SkillMetadata:
    """Metadata about a discovered skill."""

    name: str
    description: str
    source: SkillSource
    path: Path | None = None
    version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)
    model_preference: str | None = None
    capabilities: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


class SkillDiscovery:
    """Discovers skills from multiple sources.

    Sources (in priority order):
    1. Built-in skills from ``python/skill/builtin.py``
    2. Project skills from ``./skills/`` in the workspace
    3. User skills from ``~/.pymolcode/skills/``
    4. Oh-My-OpenCode skills via the OmO adapter
    5. External skills via ``npx skills`` CLI
    """

    def __init__(
        self,
        project_dir: Path | None = None,
        user_skills_dir: Path | None = None,
    ) -> None:
        self._project_dir = project_dir or Path.cwd()
        self._user_skills_dir = user_skills_dir or (Path.home() / ".pymolcode" / "skills")
        self._adapters: list[Any] = []
        self._cache: list[SkillMetadata] | None = None

    def register_adapter(self, adapter: Any) -> None:
        """Register an external skill adapter (e.g. OmO)."""
        self._adapters.append(adapter)

    def discover_all(self, *, force_refresh: bool = False) -> list[SkillMetadata]:
        """Scan all sources and return a unified skill catalog."""
        if self._cache is not None and not force_refresh:
            return self._cache

        results: list[SkillMetadata] = []
        results.extend(self._scan_builtin())
        results.extend(self._scan_directory(self._project_dir / "skills", SkillSource.PROJECT))
        results.extend(self._scan_directory(self._user_skills_dir, SkillSource.USER))

        for adapter in self._adapters:
            try:
                results.extend(adapter.discover())
            except Exception as exc:
                LOGGER.warning("Adapter %s failed: %s", type(adapter).__name__, exc)

        self._cache = results
        LOGGER.info("Discovered %d skills from all sources", len(results))
        return results

    def find(self, query: str) -> list[SkillMetadata]:
        """Search for skills matching a query string."""
        catalog = self.discover_all()
        q = query.lower()
        return [
            s
            for s in catalog
            if q in s.name.lower()
            or q in s.description.lower()
            or any(q in t.lower() for t in s.tags)
        ]

    def _scan_builtin(self) -> list[SkillMetadata]:
        """Discover built-in skills from the registry."""
        try:
            from python.skill.registry import SkillRegistry

            registry = SkillRegistry()
            return [
                SkillMetadata(
                    name=skill.name,
                    description=skill.description,
                    source=SkillSource.BUILTIN,
                    version=skill.version,
                    tags=skill.tags,
                )
                for skill in registry.list_skills()
            ]
        except Exception as exc:
            LOGGER.warning("Failed to scan builtins: %s", exc)
            return []

    def _scan_directory(self, base: Path, source: SkillSource) -> list[SkillMetadata]:
        """Scan a directory tree for SKILL.md files."""
        if not base.is_dir():
            return []

        results: list[SkillMetadata] = []
        for skill_file in sorted(base.rglob("SKILL.md")):
            meta = self._parse_skill_md(skill_file, source)
            if meta is not None:
                results.append(meta)

        LOGGER.info("Found %d skills in %s", len(results), base)
        return results

    def _parse_skill_md(self, path: Path, source: SkillSource) -> SkillMetadata | None:
        """Parse a SKILL.md file into metadata."""
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return None

        name = path.parent.name
        description = ""
        tags: list[str] = []
        model_pref: str | None = None
        capabilities: list[str] = []
        raw: dict[str, Any] = {}

        in_frontmatter = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped == "---":
                in_frontmatter = not in_frontmatter
                continue
            if in_frontmatter:
                if stripped.startswith("name:"):
                    name = stripped.split(":", 1)[1].strip()
                elif stripped.startswith("description:"):
                    description = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("# ") and not description:
                description = stripped[2:].strip()

        if not description:
            description = name

        return SkillMetadata(
            name=name,
            description=description,
            source=source,
            path=path.parent,
            tags=tags,
            model_preference=model_pref,
            capabilities=capabilities,
            raw=raw,
        )

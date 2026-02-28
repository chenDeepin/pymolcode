"""Oh-My-OpenCode skill adapter.

Discovers and imports skills from an oh-my-opencode installation
or the bundled reference copy at ``scripts/opencode-dev/``.

OmO skills live under ``.opencode/skills/`` and follow the SKILL.md
convention with frontmatter metadata.
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from python.skill.bridge.discovery import SkillMetadata, SkillSource

__all__ = ["OmOAdapter"]

LOGGER = logging.getLogger("pymolcode.skill.omo")

_OMO_SKILLS_GLOBS = [
    ".opencode/skills/*/SKILL.md",
    "skills/*/SKILL.md",
    "packages/*/skills/*/SKILL.md",
]

_OMO_AGENT_GLOBS = [
    ".opencode/agent/*.md",
]


class OmOAdapter:
    """Adapter for discovering skills from oh-my-opencode.

    Can scan a local directory (e.g. a cloned repo or the bundled
    ``scripts/opencode-dev/`` reference) and optionally invoke
    ``npx skills find`` for the remote registry.
    """

    def __init__(
        self,
        omo_root: Path | None = None,
        enable_remote: bool = False,
    ) -> None:
        self._omo_root = omo_root
        self._enable_remote = enable_remote

    def discover(self) -> list[SkillMetadata]:
        """Return all OmO skills found locally and optionally remotely."""
        results: list[SkillMetadata] = []

        if self._omo_root and self._omo_root.is_dir():
            results.extend(self._scan_local(self._omo_root))

        if self._enable_remote:
            results.extend(self._scan_remote())

        return results

    def _scan_local(self, root: Path) -> list[SkillMetadata]:
        """Scan a local OmO directory for skill definitions."""
        found: list[SkillMetadata] = []

        for pattern in _OMO_SKILLS_GLOBS:
            for skill_file in sorted(root.glob(pattern)):
                meta = self._parse_omo_skill(skill_file)
                if meta is not None:
                    found.append(meta)

        for pattern in _OMO_AGENT_GLOBS:
            for agent_file in sorted(root.glob(pattern)):
                meta = self._parse_omo_agent(agent_file)
                if meta is not None:
                    found.append(meta)

        LOGGER.info("Found %d OmO skills in %s", len(found), root)
        return found

    def _parse_omo_skill(self, path: Path) -> SkillMetadata | None:
        """Parse an OmO SKILL.md into SkillMetadata."""
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return None

        name = path.parent.name
        description = ""
        tags: list[str] = []

        in_fm = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped == "---":
                in_fm = not in_fm
                continue
            if in_fm:
                if stripped.startswith("name:"):
                    name = stripped.split(":", 1)[1].strip()
                elif stripped.startswith("description:"):
                    description = stripped.split(":", 1)[1].strip()
                elif stripped.startswith("tags:"):
                    raw_tags = stripped.split(":", 1)[1].strip()
                    tags = [t.strip().strip("\"'") for t in raw_tags.split(",")]
            elif stripped.startswith("# ") and not description:
                description = stripped[2:].strip()

        return SkillMetadata(
            name=f"omo/{name}",
            description=description or name,
            source=SkillSource.OMO,
            path=path.parent,
            tags=tags,
        )

    def _parse_omo_agent(self, path: Path) -> SkillMetadata | None:
        """Parse an OmO agent markdown file into SkillMetadata."""
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return None

        name = path.stem
        description = ""

        in_fm = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped == "---":
                in_fm = not in_fm
                continue
            if in_fm and stripped.startswith("description:"):
                description = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("# ") and not description:
                description = stripped[2:].strip()

        return SkillMetadata(
            name=f"omo/agent-{name}",
            description=description or name,
            source=SkillSource.OMO,
            path=path.parent,
            tags=["agent"],
        )

    def _scan_remote(self) -> list[SkillMetadata]:
        """Query the skills CLI registry for available skills."""
        try:
            proc = subprocess.run(
                ["npx", "skills", "find", "--json"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if proc.returncode != 0:
                return []

            data = json.loads(proc.stdout)
            return [
                SkillMetadata(
                    name=f"remote/{entry.get('name', 'unknown')}",
                    description=entry.get("description", ""),
                    source=SkillSource.SKILLS_CLI,
                    tags=entry.get("tags", []),
                )
                for entry in data
                if isinstance(entry, dict)
            ]
        except (subprocess.SubprocessError, json.JSONDecodeError, FileNotFoundError):
            LOGGER.debug("npx skills not available")
            return []

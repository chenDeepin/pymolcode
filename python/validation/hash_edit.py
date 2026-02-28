"""Hash-anchored command validation.

Inspired by oh-my-opencode's Hashline pattern: every line the agent
reads is tagged with a content hash.  Edits reference these tags so
stale changes are rejected before corruption.

In pymolcode this is applied to PyMOL command sequences: each
command emitted by the agent carries a hash of the expected state,
and the executor validates it before running.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

__all__ = ["CommandHash", "HashValidator"]


@dataclass(frozen=True)
class CommandHash:
    """A hash-anchored command."""

    line_number: int
    content: str
    hash_id: str

    @staticmethod
    def compute(content: str) -> str:
        """Compute a short hash for content."""
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return digest[:4].upper()


class HashValidator:
    """Validates hash-anchored edits against current state."""

    def __init__(self) -> None:
        self._state: dict[int, CommandHash] = {}

    def snapshot(self, lines: list[str]) -> list[CommandHash]:
        """Take a snapshot of lines and assign hash IDs."""
        result: list[CommandHash] = []
        for i, line in enumerate(lines, 1):
            ch = CommandHash(
                line_number=i,
                content=line,
                hash_id=CommandHash.compute(line),
            )
            self._state[i] = ch
            result.append(ch)
        return result

    def format_with_hashes(self, lines: list[str]) -> str:
        """Format lines with hash anchors (LINE#HASH| content)."""
        snapshot = self.snapshot(lines)
        parts: list[str] = []
        for ch in snapshot:
            parts.append(f"{ch.line_number}#{ch.hash_id}| {ch.content}")
        return "\n".join(parts)

    def validate_edit(
        self,
        line_number: int,
        expected_hash: str,
        _new_content: str = "",
    ) -> bool:
        """Validate that the line hasn't changed since snapshot."""
        current = self._state.get(line_number)
        if current is None:
            return False
        return current.hash_id == expected_hash

    def apply_edit(
        self,
        line_number: int,
        expected_hash: str,
        new_content: str = "",
    ) -> bool:
        """Validate and apply an edit. Returns True on success."""
        if not self.validate_edit(line_number, expected_hash, new_content):
            return False

        self._state[line_number] = CommandHash(
            line_number=line_number,
            content=new_content,
            hash_id=CommandHash.compute(new_content),
        )
        return True

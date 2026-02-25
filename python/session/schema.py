from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class SessionMetadata:
    schema_version: str = SCHEMA_VERSION
    created_at: str = ""
    updated_at: str = ""
    name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionMetadata:
        return cls(
            schema_version=data.get("schema_version", SCHEMA_VERSION),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            name=data.get("name", ""),
        )


@dataclass
class SessionManifest:
    metadata: SessionMetadata = field(default_factory=SessionMetadata)
    chat_file: str = "chat.json"
    scene_file: str = "scene.pse"
    files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "chat_file": self.chat_file,
            "scene_file": self.scene_file,
            "files": self.files,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionManifest:
        metadata_data = data.get("metadata", {})
        return cls(
            metadata=SessionMetadata.from_dict(metadata_data),
            chat_file=data.get("chat_file", "chat.json"),
            scene_file=data.get("scene_file", "scene.pse"),
            files=list(data.get("files", [])),
        )

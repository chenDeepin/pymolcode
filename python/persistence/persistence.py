from __future__ import annotations

import importlib
import json
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Protocol, cast
from uuid import uuid4

from .chat_store import CHAT_SCHEMA_VERSION, ChatStore

if TYPE_CHECKING:
    pass

MANIFEST_SCHEMA_VERSION = "1.0.0"
SCENE_FORMAT_VERSION = "1.0.0"
MEMORY_FORMAT_VERSION = "1.0.0"
Message = dict[str, object]
Manifest = dict[str, object]


class _PyMOLCmd(Protocol):
    def save(self, *args: object, **kwargs: object) -> object: ...

    def load(self, *args: object, **kwargs: object) -> object: ...

    def get_object_list(self, *args: object, **kwargs: object) -> list[object]: ...

    def get_names(self, *args: object, **kwargs: object) -> list[object]: ...


class SessionPersistence:
    def __init__(
        self,
        base_dir: Path | None = None,
        pymol_cmd: _PyMOLCmd | None = None,
        manifest_schema_version: str = MANIFEST_SCHEMA_VERSION,
    ) -> None:
        self._base_dir: Path = (
            Path(base_dir) if base_dir is not None else Path.home() / ".pymolcode" / "sessions"
        )
        self._manifest_schema_version: str = manifest_schema_version
        self._cmd: _PyMOLCmd | None = (
            pymol_cmd if pymol_cmd is not None else self._resolve_pymol_cmd()
        )
        self._chat_store: ChatStore = ChatStore(
            base_dir=self._base_dir, schema_version=CHAT_SCHEMA_VERSION
        )

    def save_session(self, session_id: str, chat_history: list[Message]) -> dict[str, str]:
        safe_session_id = self._safe_session_id(session_id)
        final_dir = self._base_dir / safe_session_id
        staging_container = self._base_dir / ".staging" / f"{safe_session_id}-{uuid4().hex}"
        staging_session_dir = staging_container / safe_session_id
        now_iso = datetime.now(UTC).isoformat()

        staging_session_dir.mkdir(parents=True, exist_ok=False)

        pse_path = staging_session_dir / "scene.pse"
        manifest_path = staging_session_dir / "manifest.json"

        backup_dir: Path | None = None
        created_at = now_iso
        if final_dir.exists():
            previous_manifest = self._read_manifest(final_dir)
            if (
                isinstance(previous_manifest.get("created_at"), str)
                and previous_manifest["created_at"]
            ):
                created_at = str(previous_manifest["created_at"])

        try:
            self._save_pymol_scene(pse_path)

            staged_chat_store = ChatStore(
                base_dir=staging_container, schema_version=CHAT_SCHEMA_VERSION
            )
            _ = staged_chat_store.save_chat(safe_session_id, chat_history)

            staging_memory_dir = staging_session_dir / "memory"
            staging_memory_dir.mkdir(parents=True, exist_ok=True)

            memory_file_count = 0
            if final_dir.exists():
                source_memory_dir = final_dir / "memory"
                if source_memory_dir.exists():
                    for md_file in source_memory_dir.glob("*.md"):
                        shutil.copy(md_file, staging_memory_dir / md_file.name)
                        memory_file_count += 1

            manifest: Manifest = {
                "schema_version": self._manifest_schema_version,
                "session_id": safe_session_id,
                "created_at": created_at,
                "updated_at": now_iso,
                "artifacts": {
                    "scene": {
                        "file": "scene.pse",
                        "format": "pse",
                        "version": SCENE_FORMAT_VERSION,
                    },
                    "chat": {
                        "file": "chat.json",
                        "schema_version": CHAT_SCHEMA_VERSION,
                        "message_count": len(chat_history),
                    },
                    "manifest": {
                        "file": "manifest.json",
                        "schema_version": self._manifest_schema_version,
                    },
                    "memory": {
                        "dir": "memory",
                        "files": ["MEMORY.md", "lessons.md"],
                        "version": "1.0.0",
                    },
                },
                "files": ["scene.pse", "chat.json", "manifest.json", "memory"],
            }
            self._atomic_json_write(manifest_path, manifest)

            if final_dir.exists():
                backup_dir = self._base_dir / f".backup-{safe_session_id}-{uuid4().hex}"
                os.replace(final_dir, backup_dir)

            os.replace(staging_session_dir, final_dir)

            if backup_dir is not None and backup_dir.exists():
                shutil.rmtree(backup_dir)

            if staging_container.exists():
                shutil.rmtree(staging_container)

            return {
                "pse_path": str(final_dir / "scene.pse"),
                "chat_path": str(final_dir / "chat.json"),
                "manifest_path": str(final_dir / "manifest.json"),
            }
        except Exception:
            if backup_dir is not None and backup_dir.exists() and not final_dir.exists():
                os.replace(backup_dir, final_dir)
            if staging_container.exists():
                shutil.rmtree(staging_container, ignore_errors=True)
            raise

    def load_session(self, session_id: str) -> dict[str, object]:
        safe_session_id = self._safe_session_id(session_id)
        session_dir = self._base_dir / safe_session_id
        manifest = self._read_manifest(session_dir)

        artifacts_obj = manifest.get("artifacts")
        if not isinstance(artifacts_obj, dict):
            raise ValueError("manifest.json has invalid artifacts structure")
        artifacts = cast(dict[str, object], artifacts_obj)

        scene_info_obj = artifacts.get("scene")
        if not isinstance(scene_info_obj, dict):
            raise ValueError("manifest.json missing scene artifact")
        scene_info = cast(dict[str, object], scene_info_obj)
        scene_file = str(scene_info.get("file", "scene.pse"))
        scene_path = session_dir / scene_file
        if not scene_path.exists():
            raise FileNotFoundError(f"Missing scene file: {scene_path}")

        cmd = self._require_cmd()
        _ = cmd.load(str(scene_path))

        chat_history = self._chat_store.load_chat(safe_session_id)
        objects = self._list_objects()
        return {
            "chat_history": chat_history,
            "objects": objects,
            "manifest": manifest,
        }

    def list_sessions(self) -> list[dict[str, str]]:
        if not self._base_dir.exists():
            return []

        sessions: list[dict[str, str]] = []
        for path in self._base_dir.iterdir():
            if not path.is_dir() or path.name.startswith("."):
                continue

            manifest_path = path / "manifest.json"
            if not manifest_path.exists():
                continue

            try:
                manifest = self._read_manifest(path)
                metadata: dict[str, str] = {
                    "session_id": str(manifest.get("session_id", path.name)),
                    "schema_version": str(manifest.get("schema_version", "")),
                    "created_at": str(manifest.get("created_at", "")),
                    "updated_at": str(manifest.get("updated_at", "")),
                    "path": str(path),
                }
                sessions.append(metadata)
            except Exception:
                continue

        sessions.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
        return sessions

    def delete_session(self, session_id: str) -> bool:
        safe_session_id = self._safe_session_id(session_id)
        session_dir = self._base_dir / safe_session_id
        if not session_dir.exists():
            return False
        if not session_dir.is_dir():
            return False

        shutil.rmtree(session_dir)
        return True

    @staticmethod
    def _safe_session_id(session_id: str) -> str:
        candidate = session_id.strip()
        if not candidate or any(token in candidate for token in ("/", "\\", "..")):
            raise ValueError("session_id must be a safe non-empty identifier")
        return candidate

    def _save_pymol_scene(self, output_path: Path) -> None:
        cmd = self._require_cmd()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        _ = cmd.save(str(output_path))

    def _list_objects(self) -> list[str]:
        cmd = self._require_cmd()

        if hasattr(cmd, "get_object_list"):
            objects = cmd.get_object_list("all")
            return [str(name) for name in objects]
        if hasattr(cmd, "get_names"):
            objects = cmd.get_names("objects")
            return [str(name) for name in objects]
        return []

    def _read_manifest(self, session_dir: Path) -> Manifest:
        manifest_path = session_dir / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Missing manifest: {manifest_path}")

        data_obj = cast(object, json.loads(manifest_path.read_text(encoding="utf-8")))
        if not isinstance(data_obj, dict):
            raise ValueError("manifest.json is malformed")
        data = cast(dict[str, object], data_obj)
        return self._normalize_manifest(data, session_dir)

    def _normalize_manifest(self, manifest: dict[str, object], session_dir: Path) -> Manifest:
        normalized = dict(manifest)

        metadata_obj = normalized.get("metadata")
        metadata: dict[str, object]
        metadata = cast(dict[str, object], metadata_obj) if isinstance(metadata_obj, dict) else {}

        schema_version = self._read_str(normalized.get("schema_version"))
        if schema_version is None:
            schema_version = self._read_str(metadata.get("schema_version"))

        if schema_version is None:
            raise ValueError("manifest.json missing schema_version")

        session_id = self._read_str(normalized.get("session_id"))
        if session_id is None:
            session_id = self._read_str(metadata.get("name"))
        if session_id is None:
            session_id = session_dir.name

        created_at = self._read_str(normalized.get("created_at"))
        if created_at is None:
            created_at = self._read_str(metadata.get("created_at")) or ""

        updated_at = self._read_str(normalized.get("updated_at"))
        if updated_at is None:
            updated_at = self._read_str(metadata.get("updated_at")) or ""

        scene_file = self._read_str(normalized.get("scene_file")) or "scene.pse"
        chat_file = self._read_str(normalized.get("chat_file")) or "chat.json"

        files_obj = normalized.get("files")
        files: list[object]
        if isinstance(files_obj, list):
            files = list(cast(list[object], files_obj))
        else:
            files = [scene_file, chat_file, "manifest.json"]

        artifacts_obj = normalized.get("artifacts")
        artifacts: dict[str, object]
        if isinstance(artifacts_obj, dict):
            artifacts = cast(dict[str, object], artifacts_obj)
        else:
            artifacts = {
                "scene": {
                    "file": scene_file,
                    "format": "pse",
                    "version": SCENE_FORMAT_VERSION,
                },
                "chat": {
                    "file": chat_file,
                    "schema_version": CHAT_SCHEMA_VERSION,
                    "message_count": 0,
                },
                "manifest": {
                    "file": "manifest.json",
                    "schema_version": self._manifest_schema_version,
                },
            }

        normalized.update(
            {
                "schema_version": self._manifest_schema_version,
                "session_id": session_id,
                "created_at": created_at,
                "updated_at": updated_at,
                "artifacts": artifacts,
                "files": files,
            }
        )
        return normalized

    @staticmethod
    def _read_str(value: object) -> str | None:
        if isinstance(value, str):
            return value
        return None

    @staticmethod
    def _resolve_pymol_cmd() -> _PyMOLCmd | None:
        try:
            module = importlib.import_module("pymol")
            cmd_obj = cast(object, getattr(module, "cmd", None))
            if not hasattr(cmd_obj, "save") or not hasattr(cmd_obj, "load"):
                return None
            return cast(_PyMOLCmd, cmd_obj)
        except Exception:
            return None

    def _require_cmd(self) -> _PyMOLCmd:
        if self._cmd is None:
            raise RuntimeError("PyMOL command API is unavailable")
        return self._cmd

    @staticmethod
    def _atomic_json_write(path: Path, payload: Manifest) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
            tmp_path = Path(handle.name)
        os.replace(tmp_path, path)

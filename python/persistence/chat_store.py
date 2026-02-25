from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import cast


CHAT_SCHEMA_VERSION = "1.0.0"
Message = dict[str, object]


class ChatStore:
    def __init__(
        self,
        base_dir: Path | None = None,
        schema_version: str = CHAT_SCHEMA_VERSION,
    ) -> None:
        self._base_dir: Path = (
            Path(base_dir) if base_dir is not None else Path.home() / ".pymolcode" / "sessions"
        )
        self._schema_version: str = schema_version

    def save_chat(self, session_id: str, messages: list[Message]) -> str:
        session_dir = self._session_dir(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        target = session_dir / "chat.json"

        payload: dict[str, object] = {
            "schema_version": self._schema_version,
            "session_id": session_id,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "messages": self._normalize_messages(messages),
        }

        self._atomic_json_write(target, payload)
        return str(target)

    def load_chat(self, session_id: str) -> list[Message]:
        target = self._session_dir(session_id) / "chat.json"
        if not target.exists():
            return []

        raw_data = cast(object, json.loads(target.read_text(encoding="utf-8")))
        if not isinstance(raw_data, dict):
            return []
        data_obj = cast(dict[str, object], raw_data)

        messages_obj = data_obj.get("messages")
        if not isinstance(messages_obj, list):
            return []

        normalized: list[Message] = []
        typed_messages = cast(list[object], messages_obj)
        for message in typed_messages:
            if isinstance(message, dict):
                typed_message = cast(dict[object, object], message)
                normalized.append({str(key): value for key, value in typed_message.items()})
        return normalized

    def _session_dir(self, session_id: str) -> Path:
        safe_session_id = session_id.strip()
        if not safe_session_id or any(token in safe_session_id for token in ("/", "\\", "..")):
            raise ValueError("session_id must be a safe non-empty identifier")
        return self._base_dir / safe_session_id

    def _normalize_messages(self, messages: list[Message]) -> list[Message]:
        normalized: list[Message] = []
        for message in messages:
            normalized.append({str(key): value for key, value in message.items()})
        return normalized

    @staticmethod
    def _atomic_json_write(path: Path, payload: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
            tmp_path = Path(handle.name)
        os.replace(tmp_path, path)

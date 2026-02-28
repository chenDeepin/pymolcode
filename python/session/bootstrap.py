from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import SessionConfig, load_config
from .schema import SCHEMA_VERSION, SessionMetadata


def get_session_base_dir(config: SessionConfig | None = None) -> Path:
    effective_config = config or load_config()
    return effective_config.session_base_dir


def get_plugins_dir(config: SessionConfig | None = None) -> Path:
    effective_config = config or load_config()
    return effective_config.plugins_dir


def _create_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_schema_version(base_dir: Path) -> None:
    schema_file = base_dir / "schema_version"
    schema_file.write_text(SCHEMA_VERSION, encoding="utf-8")


def _write_initial_config(base_dir: Path) -> None:
    config_file = base_dir / "config.json"
    if config_file.exists():
        return

    initial_config: dict[str, Any] = {
        "session_base_dir": str(base_dir),
        "plugins_dir": str(base_dir / "plugins"),
        "sessions_dir": str(base_dir / "sessions"),
        "log_level": "INFO",
        "pymol_timeout_seconds": 30,
        "max_session_history": 100,
    }

    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(initial_config, f, indent=2)


def _write_sessions_manifest(sessions_dir: Path) -> None:
    manifest_file = sessions_dir / "manifest.json"
    if manifest_file.exists():
        return

    metadata = SessionMetadata(
        created_at=datetime.now(UTC).isoformat(),
        name="sessions-manifest",
    )

    manifest: dict[str, Any] = {
        "metadata": metadata.to_dict(),
        "sessions": [],
    }

    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def bootstrap_directories(
    base_dir: Path | None = None,
    config: SessionConfig | None = None,
) -> dict[str, Path]:
    effective_config = config or load_config()
    effective_base = base_dir or effective_config.session_base_dir

    sessions_dir = effective_base / "sessions"
    plugins_dir = effective_base / "plugins"

    _create_directory(effective_base)
    _create_directory(sessions_dir)
    _create_directory(plugins_dir)

    _write_schema_version(effective_base)
    _write_initial_config(effective_base)
    _write_sessions_manifest(sessions_dir)

    return {
        "base": effective_base,
        "sessions": sessions_dir,
        "plugins": plugins_dir,
    }


def check_migration_needed(base_dir: Path | None = None) -> dict[str, Any]:
    effective_base = base_dir or get_session_base_dir()
    schema_file = effective_base / "schema_version"

    if not schema_file.exists():
        return {
            "needed": True,
            "current_version": None,
            "target_version": SCHEMA_VERSION,
            "reason": "schema_version file missing",
        }

    current_version = schema_file.read_text(encoding="utf-8").strip()

    if current_version == SCHEMA_VERSION:
        return {
            "needed": False,
            "current_version": current_version,
            "target_version": SCHEMA_VERSION,
            "reason": "already at latest version",
        }

    return {
        "needed": True,
        "current_version": current_version,
        "target_version": SCHEMA_VERSION,
        "reason": f"upgrade from {current_version} to {SCHEMA_VERSION}",
    }


def run_migration(base_dir: Path | None = None) -> dict[str, Any]:
    migration_status = check_migration_needed(base_dir)

    if not migration_status["needed"]:
        return {
            "success": True,
            "migrated": False,
            "message": "no migration needed",
            "version": migration_status["current_version"],
        }

    effective_base = base_dir or get_session_base_dir()
    schema_file = effective_base / "schema_version"

    schema_file.write_text(SCHEMA_VERSION, encoding="utf-8")

    return {
        "success": True,
        "migrated": True,
        "message": f"migrated from {migration_status['current_version']} to {SCHEMA_VERSION}",
        "version": SCHEMA_VERSION,
    }

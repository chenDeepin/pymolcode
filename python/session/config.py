from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_SESSION_BASE_DIR = Path.home() / ".pymolcode"
DEFAULT_PLUGINS_DIR = DEFAULT_SESSION_BASE_DIR / "plugins"
DEFAULT_SESSIONS_DIR = DEFAULT_SESSION_BASE_DIR / "sessions"
DEFAULT_ARTIFACTS_DIR = DEFAULT_SESSION_BASE_DIR / "artifacts"
DEFAULT_PDB_DIR = DEFAULT_ARTIFACTS_DIR / "pdb"
DEFAULT_SCRIPTS_DIR = DEFAULT_ARTIFACTS_DIR / "scripts"
DEFAULT_SCREENSHOTS_DIR = DEFAULT_ARTIFACTS_DIR / "screenshots"
DEFAULT_CONFIG_FILE = DEFAULT_SESSION_BASE_DIR / "config.json"


@dataclass
class SessionConfig:
    session_base_dir: Path = field(default_factory=lambda: DEFAULT_SESSION_BASE_DIR)
    plugins_dir: Path = field(default_factory=lambda: DEFAULT_PLUGINS_DIR)
    sessions_dir: Path = field(default_factory=lambda: DEFAULT_SESSIONS_DIR)
    artifacts_dir: Path = field(default_factory=lambda: DEFAULT_ARTIFACTS_DIR)
    pdb_dir: Path = field(default_factory=lambda: DEFAULT_PDB_DIR)
    scripts_dir: Path = field(default_factory=lambda: DEFAULT_SCRIPTS_DIR)
    screenshots_dir: Path = field(default_factory=lambda: DEFAULT_SCREENSHOTS_DIR)
    log_level: str = "INFO"
    pymol_timeout_seconds: int = 30
    max_session_history: int = 100

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_base_dir": str(self.session_base_dir),
            "plugins_dir": str(self.plugins_dir),
            "sessions_dir": str(self.sessions_dir),
            "artifacts_dir": str(self.artifacts_dir),
            "pdb_dir": str(self.pdb_dir),
            "scripts_dir": str(self.scripts_dir),
            "screenshots_dir": str(self.screenshots_dir),
            "log_level": self.log_level,
            "pymol_timeout_seconds": self.pymol_timeout_seconds,
            "max_session_history": self.max_session_history,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionConfig:
        return cls(
            session_base_dir=Path(data.get("session_base_dir", DEFAULT_SESSION_BASE_DIR)),
            plugins_dir=Path(data.get("plugins_dir", DEFAULT_PLUGINS_DIR)),
            sessions_dir=Path(data.get("sessions_dir", DEFAULT_SESSIONS_DIR)),
            artifacts_dir=Path(data.get("artifacts_dir", DEFAULT_ARTIFACTS_DIR)),
            pdb_dir=Path(data.get("pdb_dir", DEFAULT_PDB_DIR)),
            scripts_dir=Path(data.get("scripts_dir", DEFAULT_SCRIPTS_DIR)),
            screenshots_dir=Path(data.get("screenshots_dir", DEFAULT_SCREENSHOTS_DIR)),
            log_level=data.get("log_level", "INFO"),
            pymol_timeout_seconds=data.get("pymol_timeout_seconds", 30),
            max_session_history=data.get("max_session_history", 100),
        )

    def ensure_dirs(self) -> None:
        self.session_base_dir.mkdir(parents=True, exist_ok=True)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.pdb_dir.mkdir(parents=True, exist_ok=True)
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)


def _apply_env_overrides(config: SessionConfig) -> SessionConfig:
    env_mappings = {
        "PYMOLCODE_SESSION_BASE_DIR": "session_base_dir",
        "PYMOLCODE_PLUGINS_DIR": "plugins_dir",
        "PYMOLCODE_SESSIONS_DIR": "sessions_dir",
        "PYMOLCODE_ARTIFACTS_DIR": "artifacts_dir",
        "PYMOLCODE_PDB_DIR": "pdb_dir",
        "PYMOLCODE_SCRIPTS_DIR": "scripts_dir",
        "PYMOLCODE_SCREENSHOTS_DIR": "screenshots_dir",
        "PYMOLCODE_LOG_LEVEL": "log_level",
        "PYMOLCODE_TIMEOUT": "pymol_timeout_seconds",
        "PYMOLCODE_MAX_HISTORY": "max_session_history",
    }

    path_attrs = (
        "session_base_dir",
        "plugins_dir",
        "sessions_dir",
        "artifacts_dir",
        "pdb_dir",
        "scripts_dir",
        "screenshots_dir",
    )
    int_attrs = ("pymol_timeout_seconds", "max_session_history")

    for env_key, attr in env_mappings.items():
        env_value = os.environ.get(env_key)
        if env_value is None:
            continue
        if attr in path_attrs:
            setattr(config, attr, Path(env_value))
        elif attr in int_attrs:
            setattr(config, attr, int(env_value))
        else:
            setattr(config, attr, env_value)

    return config


def load_config(config_path: Path | None = None) -> SessionConfig:
    effective_path = config_path or DEFAULT_CONFIG_FILE

    if effective_path.exists():
        try:
            with open(effective_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            config = SessionConfig.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError):
            config = SessionConfig()
    else:
        config = SessionConfig()

    return _apply_env_overrides(config)

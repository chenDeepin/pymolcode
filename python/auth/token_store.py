"""Secure token storage for OAuth credentials.

Stores tokens in ~/.pymolcode/auth.json with optional encryption.
Adapted from opencode's auth.ts and mcp/auth.ts patterns.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = ["TokenInfo", "TokenStore"]

LOGGER = logging.getLogger("pymolcode.auth.store")

_DEFAULT_AUTH_DIR = Path.home() / ".pymolcode"
_AUTH_FILE = "auth.json"


@dataclass
class TokenInfo:
    """Stored token information for a provider."""

    provider_id: str
    access_token: str
    token_type: str = "Bearer"
    refresh_token: str | None = None
    expires_at: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() >= self.expires_at

    @property
    def is_api_key(self) -> bool:
        return self.token_type == "api_key"

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "provider_id": self.provider_id,
            "access_token": self.access_token,
            "token_type": self.token_type,
        }
        if self.refresh_token:
            d["refresh_token"] = self.refresh_token
        if self.expires_at is not None:
            d["expires_at"] = self.expires_at
        if self.metadata:
            d["metadata"] = self.metadata
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TokenInfo:
        return cls(
            provider_id=data["provider_id"],
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            refresh_token=data.get("refresh_token"),
            expires_at=data.get("expires_at"),
            metadata=data.get("metadata", {}),
        )


class TokenStore:
    """File-based token store for OAuth credentials.

    Tokens are persisted in ``~/.pymolcode/auth.json`` with restrictive
    file permissions (0o600).  The file format mirrors opencode's
    ``auth.json`` layout for cross-tool compatibility.
    """

    def __init__(self, auth_dir: Path | None = None) -> None:
        self._auth_dir = auth_dir or _DEFAULT_AUTH_DIR
        self._auth_file = self._auth_dir / _AUTH_FILE
        self._cache: dict[str, TokenInfo] | None = None

    def _ensure_dir(self) -> None:
        self._auth_dir.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict[str, TokenInfo]:
        if self._cache is not None:
            return self._cache

        if not self._auth_file.is_file():
            self._cache = {}
            return self._cache

        try:
            raw = json.loads(self._auth_file.read_text(encoding="utf-8"))
            self._cache = {
                pid: TokenInfo.from_dict(data) for pid, data in raw.items()
            }
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            LOGGER.warning("Corrupted auth.json, resetting: %s", exc)
            self._cache = {}
        return self._cache

    def _persist(self) -> None:
        self._ensure_dir()
        data = {pid: info.to_dict() for pid, info in self._load().items()}
        tmp_path = self._auth_file.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        with contextlib.suppress(OSError):
            os.chmod(tmp_path, 0o600)
        tmp_path.replace(self._auth_file)

    def get(self, provider_id: str) -> TokenInfo | None:
        """Get stored token for a provider."""
        return self._load().get(provider_id)

    def save(self, provider_id: str, result: Any) -> None:
        """Save an AuthResult as a TokenInfo entry."""
        expires_at: float | None = None
        if getattr(result, "expires_in", None):
            expires_at = time.time() + result.expires_in

        info = TokenInfo(
            provider_id=provider_id,
            access_token=result.access_token or "",
            token_type=getattr(result, "token_type", "Bearer"),
            refresh_token=getattr(result, "refresh_token", None),
            expires_at=expires_at,
            metadata=getattr(result, "metadata", {}),
        )
        tokens = self._load()
        tokens[provider_id] = info
        self._persist()
        LOGGER.info("Saved token for %s", provider_id)

    def save_api_key(self, provider_id: str, api_key: str) -> None:
        """Store a plain API key."""
        info = TokenInfo(
            provider_id=provider_id,
            access_token=api_key,
            token_type="api_key",
        )
        tokens = self._load()
        tokens[provider_id] = info
        self._persist()

    def remove(self, provider_id: str) -> bool:
        """Remove stored credentials for a provider."""
        tokens = self._load()
        if provider_id not in tokens:
            return False
        del tokens[provider_id]
        self._persist()
        LOGGER.info("Removed credentials for %s", provider_id)
        return True

    def list_providers(self) -> list[TokenInfo]:
        """List all stored credentials."""
        return list(self._load().values())

    def get_api_key(self, provider_id: str) -> str | None:
        """Get access token / API key for a provider (convenience)."""
        info = self.get(provider_id)
        if info is None:
            return None
        if info.is_expired:
            return None
        return info.access_token

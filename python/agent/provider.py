"""LLM provider auto-discovery for pymolcode.

Resolution order (first match wins):
1. Explicit PYMOLCODE_MODEL + matching key  (full override)
2. OAuth token store (~/.pymolcode/auth.json)
3. Environment variables for known providers (auto-detect)
4. ~/.pymolcode/config.json  provider settings
5. .env file in project root

LiteLLM model format: ``provider/model-name``
  - openai/gpt-4o
  - anthropic/claude-3-5-sonnet-20241022
  - deepseek/deepseek-chat
  - openai/gpt-4o  with custom api_base  (OpenAI-compatible endpoints)
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

__all__ = ["ProviderInfo", "resolve_provider", "list_available_providers"]

LOGGER = logging.getLogger("pymolcode.provider")

# ---------------------------------------------------------------------------
# Known providers – maps (env_var, litellm_prefix, default_model, api_base?)
# Order = priority when multiple keys are present.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _ProviderDef:
    id: str
    name: str
    env_vars: tuple[str, ...]
    litellm_prefix: str
    default_model: str
    api_base: str | None = None


_KNOWN_PROVIDERS: list[_ProviderDef] = [
    _ProviderDef(
        id="anthropic",
        name="Anthropic",
        env_vars=("ANTHROPIC_API_KEY",),
        litellm_prefix="anthropic",
        default_model="anthropic/claude-sonnet-4-20250514",
    ),
    _ProviderDef(
        id="openai",
        name="OpenAI",
        env_vars=("OPENAI_API_KEY",),
        litellm_prefix="openai",
        default_model="openai/gpt-4o",
    ),
    _ProviderDef(
        id="deepseek",
        name="DeepSeek",
        env_vars=("DEEPSEEK_API_KEY",),
        litellm_prefix="deepseek",
        default_model="deepseek/deepseek-chat",
        api_base="https://api.deepseek.com/v1",
    ),
    _ProviderDef(
        id="zhipu",
        name="Zhipu AI",
        env_vars=("ZAI_API_KEY", "ZAI_API_KEY_pymolcode", "ZHIPUAI_API_KEY"),
        litellm_prefix="zai",  # LiteLLM prefix for zhipu is "zai", not "zhipuai"
        default_model="zai/glm-4.7",
        api_base="https://open.bigmodel.cn/api/coding/paas/v4",
    ),
    _ProviderDef(
        id="openrouter",
        name="OpenRouter",
        env_vars=("OPENROUTER_API_KEY",),
        litellm_prefix="openrouter",
        default_model="openrouter/anthropic/claude-sonnet-4-20250514",
        api_base="https://openrouter.ai/api/v1",
    ),
    _ProviderDef(
        id="google",
        name="Google Gemini",
        env_vars=("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        litellm_prefix="gemini",
        default_model="gemini/gemini-2.5-flash",
    ),
    _ProviderDef(
        id="groq",
        name="Groq",
        env_vars=("GROQ_API_KEY",),
        litellm_prefix="groq",
        default_model="groq/llama-3.3-70b-versatile",
    ),
    _ProviderDef(
        id="mistral",
        name="Mistral",
        env_vars=("MISTRAL_API_KEY",),
        litellm_prefix="mistral",
        default_model="mistral/mistral-large-latest",
    ),
    _ProviderDef(
        id="xai",
        name="xAI",
        env_vars=("XAI_API_KEY",),
        litellm_prefix="xai",
        default_model="xai/grok-3-mini",
    ),
    # Generic OpenAI-compatible: user sets OPENAI_API_BASE + OPENAI_API_KEY
    _ProviderDef(
        id="custom",
        name="Custom (OpenAI-compatible)",
        env_vars=("OPENAI_API_KEY",),
        litellm_prefix="openai",
        default_model="openai/gpt-4o",
    ),
]


@dataclass
class ProviderInfo:
    """Resolved provider ready to pass to LiteLLM."""

    provider_id: str
    provider_name: str
    model: str
    api_key: str
    api_base: str | None = None
    auth_type: str = "api"  # "api" or "oauth"

    def to_litellm_kwargs(self) -> dict[str, Any]:
        """Return kwargs for ``litellm.acompletion(...)``."""
        kw: dict[str, Any] = {
            "model": self.model,
            "api_key": self.api_key,
        }
        if self.api_base:
            kw["api_base"] = self.api_base
        return kw


# ---------------------------------------------------------------------------
# .env loader
# ---------------------------------------------------------------------------


def _load_dotenv(dotenv_path: Path | None = None) -> None:
    """Load a .env file into os.environ (without overwriting existing vars)."""
    candidates = (
        [dotenv_path]
        if dotenv_path
        else [
            Path.cwd() / ".env",
            Path(__file__).resolve().parent.parent.parent / ".env",
        ]
    )
    for p in candidates:
        if p and p.is_file():
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = value
            LOGGER.info("Loaded env from %s", p)
            return


def _load_config_file() -> dict[str, Any]:
    """Load ~/.pymolcode/config.json if it exists."""
    config_path = Path.home() / ".pymolcode" / "config.json"
    if config_path.is_file():
        try:
            with open(config_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


def _find_key(env_vars: tuple[str, ...]) -> str | None:
    for var in env_vars:
        val = os.environ.get(var, "").strip()
        if val and val != "your-api-key-here":
            return val
    return None


def _find_token_store_key(provider_id: str) -> tuple[str | None, str]:
    """Check the OAuth token store for a saved credential.

    Returns (api_key, auth_type) or (None, "api").
    """
    try:
        from python.auth.token_store import TokenStore

        store = TokenStore()
        info = store.get(provider_id)
        if info is not None and not info.is_expired and info.access_token:
            auth_type = "api" if info.is_api_key else "oauth"
            return info.access_token, auth_type
    except Exception:
        pass
    return None, "api"


def resolve_provider(
    *,
    model_override: str | None = None,
    api_key_override: str | None = None,
    api_base_override: str | None = None,
) -> ProviderInfo | None:
    """Auto-detect the best available LLM provider.

    Returns ``None`` only when no API key can be found anywhere.
    """
    _load_dotenv()
    config = _load_config_file()

    # 1. Explicit env override: PYMOLCODE_MODEL
    explicit_model = model_override or os.environ.get("PYMOLCODE_MODEL")
    explicit_key = api_key_override or os.environ.get("PYMOLCODE_API_KEY")
    explicit_base = api_base_override or os.environ.get("PYMOLCODE_API_BASE")

    if explicit_model and explicit_key:
        prefix = explicit_model.split("/")[0] if "/" in explicit_model else "openai"
        provider_name = prefix.title()
        return ProviderInfo(
            provider_id="explicit",
            provider_name=provider_name,
            model=explicit_model,
            api_key=explicit_key,
            api_base=explicit_base,
        )

    # 2. Config file provider preference
    config_provider_id = config.get("llm_provider")
    config_model = config.get("llm_model")
    config_api_key = config.get("llm_api_key")
    config_api_base = config.get("llm_api_base")

    if config_provider_id:
        for pdef in _KNOWN_PROVIDERS:
            if pdef.id == config_provider_id:
                key = config_api_key or _find_key(pdef.env_vars)
                if not key:
                    key, auth_type = _find_token_store_key(pdef.id)
                else:
                    auth_type = "api"
                if key:
                    return ProviderInfo(
                        provider_id=pdef.id,
                        provider_name=pdef.name,
                        model=config_model or pdef.default_model,
                        api_key=key,
                        api_base=config_api_base or pdef.api_base,
                        auth_type=auth_type,
                    )
                break

    # 3. Scan env vars for known providers (priority order)
    for pdef in _KNOWN_PROVIDERS:
        if pdef.id == "custom":
            if not os.environ.get("OPENAI_API_BASE"):
                continue
        key = _find_key(pdef.env_vars)
        auth_type = "api"
        if key:
            api_base = pdef.api_base
            if pdef.id == "custom":
                api_base = os.environ.get("OPENAI_API_BASE")
            LOGGER.info("Auto-detected provider: %s", pdef.name)
            return ProviderInfo(
                provider_id=pdef.id,
                provider_name=pdef.name,
                model=explicit_model or pdef.default_model,
                api_key=key,
                api_base=api_base,
                auth_type=auth_type,
            )

    # 4. Check token store for any saved credentials
    for pdef in _KNOWN_PROVIDERS:
        if pdef.id == "custom":
            continue
        stored_key, auth_type = _find_token_store_key(pdef.id)
        if stored_key:
            LOGGER.info("Using stored credential for provider: %s", pdef.name)
            return ProviderInfo(
                provider_id=pdef.id,
                provider_name=pdef.name,
                model=explicit_model or pdef.default_model,
                api_key=stored_key,
                api_base=pdef.api_base,
                auth_type=auth_type,
            )

    LOGGER.warning(
        "No LLM provider found. Set one of: %s, or run: pymolcode auth login <provider>",
        ", ".join(v for pdef in _KNOWN_PROVIDERS for v in pdef.env_vars if pdef.id != "custom"),
    )
    return None


def list_available_providers() -> list[ProviderInfo]:
    """Return all providers that have a usable API key or stored token."""
    _load_dotenv()
    result: list[ProviderInfo] = []
    seen: set[str] = set()

    for pdef in _KNOWN_PROVIDERS:
        if pdef.id == "custom":
            if not os.environ.get("OPENAI_API_BASE"):
                continue
        key = _find_key(pdef.env_vars)
        auth_type = "api"
        if not key:
            key, auth_type = _find_token_store_key(pdef.id)
        if key and pdef.id not in seen:
            seen.add(pdef.id)
            result.append(
                ProviderInfo(
                    provider_id=pdef.id,
                    provider_name=pdef.name,
                    model=pdef.default_model,
                    api_key=key,
                    api_base=pdef.api_base,
                    auth_type=auth_type,
                )
            )
    return result

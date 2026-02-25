"""Provider-specific OAuth configurations.

Defines the OAuth endpoints, client IDs, and flow types for each
supported LLM provider.  Adapted from opencode's provider/auth.ts
and provider/provider.ts.

IMPORTANT: OAuth client IDs are read from environment variables.
Set these before using OAuth flows:
- OPENAI_CLIENT_ID (optional, has default for ChatGPT Plus/Pro)
- GOOGLE_CLIENT_ID (required for Google OAuth)
- GOOGLE_CLIENT_SECRET (optional)
- GITHUB_COPILOT_CLIENT_ID (optional, has well-known default)

For API key authentication, set the corresponding API key env vars.
"""

from __future__ import annotations

import os
from typing import Any

__all__ = [
    "OAUTH_PROVIDERS",
    "get_provider_auth_config",
    "register_all_providers",
]


def _get_openai_config() -> dict[str, Any]:
    """Get OpenAI OAuth configuration."""
    return {
        "name": "OpenAI",
        "flow": "openai_device_code",
        "client_id": os.environ.get("OPENAI_CLIENT_ID", ""),
        "base_url": "https://auth.openai.com",
        "api_base_url": "https://auth.openai.com/api/accounts",
        "verification_url": "https://auth.openai.com/codex/device",
        "scope": "openid profile email offline_access",
        "env_vars": ("OPENAI_API_KEY",),
        "instructions": "Authorize with your ChatGPT Plus/Pro account (enable device code in chatgpt.com/settings/security) or paste an API key. Set OPENAI_CLIENT_ID env var for OAuth.",
    }


def _get_google_config() -> dict[str, Any]:
    """Get Google OAuth configuration."""
    return {
        "name": "Google Gemini",
        "flow": "google_device_code",
        "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", ""),
        "device_code_url": "https://oauth2.googleapis.com/device/code",
        "token_url": "https://oauth2.googleapis.com/token",
        "scope": "https://www.googleapis.com/auth/generative-language",
        "env_vars": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        "instructions": "Set GOOGLE_CLIENT_ID env var for OAuth, or use API key authentication (recommended). Create OAuth credentials at https://console.cloud.google.com/apis/credentials",
    }


def _get_github_copilot_config() -> dict[str, Any]:
    """Get GitHub Copilot OAuth configuration."""
    return {
        "name": "GitHub Copilot",
        "flow": "device_code",
        "client_id": os.environ.get("GITHUB_COPILOT_CLIENT_ID", ""),
        "device_authorization_url": "https://github.com/login/device/code",
        "token_url": "https://github.com/login/oauth/access_token",
        "scope": "copilot",
        "env_vars": ("GITHUB_TOKEN",),
        "instructions": "Authorize with your GitHub account that has Copilot access. Set GITHUB_COPILOT_CLIENT_ID env var for OAuth.",
    }


def _build_oauth_providers() -> dict[str, dict[str, Any]]:
    """Build OAuth providers configuration dynamically."""
    return {
        "openai": _get_openai_config(),
        "google": _get_google_config(),
        "github-copilot": _get_github_copilot_config(),
        "anthropic": {
            "name": "Anthropic",
            "flow": "api_key",
            "env_vars": ("ANTHROPIC_API_KEY",),
            "instructions": "Paste your Anthropic API key (from console.anthropic.com).",
        },
        "deepseek": {
            "name": "DeepSeek",
            "flow": "api_key",
            "env_vars": ("DEEPSEEK_API_KEY",),
            "instructions": "Paste your DeepSeek API key.",
        },
        "zhipu": {
            "name": "Zhipu AI",
            "flow": "api_key",
            "env_vars": ("ZHIPUAI_API_KEY", "ZAI_API_KEY"),
            "instructions": "Paste your Zhipu AI API key.",
        },
        "openrouter": {
            "name": "OpenRouter",
            "flow": "api_key",
            "env_vars": ("OPENROUTER_API_KEY",),
            "instructions": "Paste your OpenRouter API key (from openrouter.ai/keys).",
        },
        "groq": {
            "name": "Groq",
            "flow": "api_key",
            "env_vars": ("GROQ_API_KEY",),
            "instructions": "Paste your Groq API key.",
        },
        "mistral": {
            "name": "Mistral",
            "flow": "api_key",
            "env_vars": ("MISTRAL_API_KEY",),
            "instructions": "Paste your Mistral API key.",
        },
        "xai": {
            "name": "xAI",
            "flow": "api_key",
            "env_vars": ("XAI_API_KEY",),
            "instructions": "Paste your xAI API key.",
        },
    }


OAUTH_PROVIDERS: dict[str, dict[str, Any]] = _build_oauth_providers()


def get_provider_auth_config(provider_id: str) -> dict[str, Any] | None:
    """Get the OAuth/auth configuration for a provider."""
    return OAUTH_PROVIDERS.get(provider_id)


def register_all_providers(oauth_manager: Any) -> None:
    """Register all known providers with an OAuthManager."""
    for provider_id, config in OAUTH_PROVIDERS.items():
        oauth_manager.register_provider(provider_id, config)

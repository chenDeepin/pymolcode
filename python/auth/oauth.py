"""OAuth 2.0 flow implementation with PKCE support.

Supports device-code and authorization-code flows for LLM provider auth.
Adapted from opencode's provider/auth.ts patterns.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
import os
import secrets
import webbrowser
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import httpx

__all__ = ["AuthResult", "OAuthFlow", "OAuthManager"]

LOGGER = logging.getLogger("pymolcode.auth")


class OAuthFlow(str, Enum):
    """Supported OAuth flow types."""

    DEVICE_CODE = "device_code"
    OPENAI_DEVICE_CODE = "openai_device_code"
    GOOGLE_DEVICE_CODE = "google_device_code"
    AUTHORIZATION_CODE = "authorization_code"
    API_KEY = "api_key"


@dataclass
class AuthResult:
    """Result of an authentication attempt."""

    success: bool
    provider_id: str
    access_token: str | None = None
    refresh_token: str | None = None
    expires_in: int | None = None
    token_type: str = "Bearer"
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PKCEChallenge:
    """PKCE code verifier and challenge pair."""

    verifier: str
    challenge: str
    method: str = "S256"


def generate_pkce() -> PKCEChallenge:
    """Generate a PKCE code verifier and challenge."""
    verifier = secrets.token_urlsafe(64)[:128]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return PKCEChallenge(verifier=verifier, challenge=challenge)


class OAuthManager:
    """Manages OAuth flows for multiple providers.

    Delegates to provider-specific configurations for endpoints and
    flow parameters.
    """

    def __init__(self, token_store: Any | None = None) -> None:
        from python.auth.token_store import TokenStore

        self._token_store = token_store or TokenStore()
        self._providers: dict[str, dict[str, Any]] = {}

    @property
    def token_store(self) -> Any:
        return self._token_store

    def register_provider(self, provider_id: str, config: dict[str, Any]) -> None:
        """Register a provider's OAuth configuration."""
        self._providers[provider_id] = config

    async def authorize(self, provider_id: str) -> AuthResult:
        """Run the appropriate OAuth flow for a provider."""
        config = self._providers.get(provider_id)
        if config is None:
            return AuthResult(
                success=False,
                provider_id=provider_id,
                error=f"Unknown provider: {provider_id}",
            )

        flow = OAuthFlow(config.get("flow", "api_key"))

        if flow == OAuthFlow.DEVICE_CODE:
            return await self._device_code_flow(provider_id, config)
        elif flow == OAuthFlow.OPENAI_DEVICE_CODE:
            return await self._openai_device_code_flow(provider_id, config)
        elif flow == OAuthFlow.GOOGLE_DEVICE_CODE:
            return await self._google_device_code_flow(provider_id, config)
        elif flow == OAuthFlow.AUTHORIZATION_CODE:
            return await self._authorization_code_flow(provider_id, config)
        else:
            return AuthResult(
                success=False,
                provider_id=provider_id,
                error=f"Use 'pymolcode auth login {provider_id}' with an API key",
            )

    async def get_valid_token(self, provider_id: str) -> str | None:
        """Get a valid access token, refreshing if needed."""
        token_info = self._token_store.get(provider_id)
        if token_info is None:
            return None

        if token_info.is_expired:
            refreshed = await self.refresh(provider_id)
            if not refreshed.success:
                LOGGER.warning("Token refresh failed for %s", provider_id)
                return None
            token_info = self._token_store.get(provider_id)
            if token_info is None:
                return None

        return token_info.access_token

    async def refresh(self, provider_id: str) -> AuthResult:
        """Refresh an expired token."""
        token_info = self._token_store.get(provider_id)
        if token_info is None or token_info.refresh_token is None:
            return AuthResult(
                success=False,
                provider_id=provider_id,
                error="No refresh token available",
            )

        config = self._providers.get(provider_id, {})
        token_url = config.get("token_url")
        client_id = config.get("client_id")

        if not token_url or not client_id:
            return AuthResult(
                success=False,
                provider_id=provider_id,
                error="Provider not configured for token refresh",
            )

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    token_url,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": token_info.refresh_token,
                        "client_id": client_id,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
            except (httpx.HTTPError, ValueError) as exc:
                return AuthResult(
                    success=False,
                    provider_id=provider_id,
                    error=f"Refresh failed: {exc}",
                )

        result = AuthResult(
            success=True,
            provider_id=provider_id,
            access_token=data.get("access_token"),
            refresh_token=data.get("refresh_token", token_info.refresh_token),
            expires_in=data.get("expires_in"),
        )
        self._token_store.save(provider_id, result)
        return result

    async def _device_code_flow(self, provider_id: str, config: dict[str, Any]) -> AuthResult:
        """OAuth 2.0 device authorization grant (RFC 8628)."""
        device_url = config["device_authorization_url"]
        token_url = config["token_url"]
        client_id = config["client_id"]
        scope = config.get("scope", "")

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    device_url,
                    data={"client_id": client_id, "scope": scope},
                    headers={"Accept": "application/json"},
                )
                resp.raise_for_status()
                device_data = resp.json()
            except (httpx.HTTPError, ValueError) as exc:
                return AuthResult(
                    success=False,
                    provider_id=provider_id,
                    error=f"Device code request failed: {exc}",
                )

        verification_uri = device_data.get(
            "verification_uri_complete", device_data.get("verification_uri", "")
        )
        user_code = device_data.get("user_code", "")
        device_code = device_data["device_code"]
        interval = device_data.get("interval", 5)
        expires_in = device_data.get("expires_in", 900)

        print(f"\nTo authorize, visit: {verification_uri}")
        if user_code:
            print(f"Enter code: {user_code}")

        try:
            webbrowser.open(verification_uri)
        except Exception:
            pass

        return await self._poll_for_token(
            provider_id, token_url, client_id, device_code, interval, expires_in
        )

    async def _poll_for_token(
        self,
        provider_id: str,
        token_url: str,
        client_id: str,
        device_code: str,
        interval: int,
        expires_in: int,
    ) -> AuthResult:
        """Poll for token after device code authorization."""
        elapsed = 0
        async with httpx.AsyncClient(timeout=30) as client:
            while elapsed < expires_in:
                await asyncio.sleep(interval)
                elapsed += interval

                try:
                    resp = await client.post(
                        token_url,
                        data={
                            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                            "device_code": device_code,
                            "client_id": client_id,
                        },
                        headers={"Accept": "application/json"},
                    )
                    data = resp.json()
                except (httpx.HTTPError, ValueError):
                    continue

                error = data.get("error")
                if error == "authorization_pending":
                    continue
                elif error == "slow_down":
                    interval += 5
                    continue
                elif error:
                    return AuthResult(
                        success=False,
                        provider_id=provider_id,
                        error=data.get("error_description", error),
                    )

                result = AuthResult(
                    success=True,
                    provider_id=provider_id,
                    access_token=data.get("access_token"),
                    refresh_token=data.get("refresh_token"),
                    expires_in=data.get("expires_in"),
                )
                self._token_store.save(provider_id, result)
                LOGGER.info("OAuth token obtained for %s", provider_id)
                return result

        return AuthResult(
            success=False,
            provider_id=provider_id,
            error="Authorization timed out",
        )

    async def _openai_device_code_flow(
        self, provider_id: str, config: dict[str, Any]
    ) -> AuthResult:
        """OpenAI-specific device code flow for ChatGPT Plus/Pro.

        This is different from standard OAuth 2.0 device code (RFC 8628).
        Based on: https://github.com/openai/codex device code implementation.

        Prerequisites:
            User must enable device code auth in ChatGPT settings:
            https://chatgpt.com/codex/settings/general#settings/Security
        """
        api_base_url = config["api_base_url"]
        base_url = config["base_url"]
        client_id = config["client_id"]

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"pymolcode/{provider_id}",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    f"{api_base_url}/deviceauth/usercode",
                    json={"client_id": client_id},
                    headers=headers,
                )
                if resp.status_code == 404:
                    return AuthResult(
                        success=False,
                        provider_id=provider_id,
                        error="Device code login not enabled. Enable it at: https://chatgpt.com/settings/security",
                    )
                resp.raise_for_status()
                user_code_data = resp.json()
            except (httpx.HTTPError, ValueError) as exc:
                return AuthResult(
                    success=False,
                    provider_id=provider_id,
                    error=f"Device code request failed: {exc}",
                )

        device_auth_id = user_code_data.get("device_auth_id")
        user_code = user_code_data.get("user_code") or user_code_data.get("usercode")
        interval = user_code_data.get("interval", 5)
        if isinstance(interval, str):
            interval = int(interval)

        if not device_auth_id or not user_code:
            return AuthResult(
                success=False,
                provider_id=provider_id,
                error="Invalid response from device code endpoint",
            )

        verification_url = f"{base_url}/codex/device"
        print(f"\nTo authorize, visit: {verification_url}")
        print(f"Enter code: {user_code}")
        print("(expires in 15 minutes)")

        try:
            webbrowser.open(verification_url)
        except Exception:
            pass

        return await self._poll_openai_for_code(
            provider_id, config, device_auth_id, user_code, interval
        )

    async def _poll_openai_for_code(
        self,
        provider_id: str,
        config: dict[str, Any],
        device_auth_id: str,
        user_code: str,
        interval: int,
    ) -> AuthResult:
        """Poll OpenAI for authorization code, then exchange for tokens."""
        api_base_url = config["api_base_url"]
        base_url = config["base_url"]
        client_id = config["client_id"]

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"pymolcode/{provider_id}",
        }

        max_wait_sec = 900  # 15 minutes
        elapsed = 0

        async with httpx.AsyncClient(timeout=30) as client:
            while elapsed < max_wait_sec:
                await asyncio.sleep(interval)
                elapsed += interval

                try:
                    resp = await client.post(
                        f"{api_base_url}/deviceauth/token",
                        json={
                            "device_auth_id": device_auth_id,
                            "user_code": user_code,
                        },
                        headers=headers,
                    )

                    if resp.status_code in (403, 404):
                        print(".", end="", flush=True)
                        continue

                    if resp.is_success:
                        code_data = resp.json()
                        auth_code = code_data.get("authorization_code")
                        code_verifier = code_data.get("code_verifier")

                        if not auth_code:
                            return AuthResult(
                                success=False,
                                provider_id=provider_id,
                                error="No authorization code in response",
                            )

                        print("\nAuthorization received! Exchanging for tokens...")
                        return await self._exchange_openai_code(
                            provider_id,
                            base_url,
                            client_id,
                            auth_code,
                            code_verifier,
                        )

                except (httpx.HTTPError, ValueError):
                    print("!", end="", flush=True)
                    continue

        return AuthResult(
            success=False,
            provider_id=provider_id,
            error="Authorization timed out (15 minutes)",
        )

    async def _exchange_openai_code(
        self,
        provider_id: str,
        base_url: str,
        client_id: str,
        auth_code: str,
        code_verifier: str | None,
    ) -> AuthResult:
        """Exchange OpenAI authorization code for tokens."""
        token_url = f"{base_url}/oauth/token"
        redirect_uri = f"{base_url}/deviceauth/callback"

        data = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "code": auth_code,
            "redirect_uri": redirect_uri,
        }
        if code_verifier:
            data["code_verifier"] = code_verifier

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    token_url,
                    data=data,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "application/json",
                    },
                )
                resp.raise_for_status()
                token_data = resp.json()
            except (httpx.HTTPError, ValueError) as exc:
                return AuthResult(
                    success=False,
                    provider_id=provider_id,
                    error=f"Token exchange failed: {exc}",
                )

        result = AuthResult(
            success=True,
            provider_id=provider_id,
            access_token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            expires_in=token_data.get("expires_in"),
        )
        self._token_store.save(provider_id, result)
        LOGGER.info("OAuth token obtained for %s", provider_id)
        return result

    async def _google_device_code_flow(
        self, provider_id: str, config: dict[str, Any]
    ) -> AuthResult:
        """Google OAuth 2.0 device authorization grant (RFC 8628).

        Google's device code flow for limited-input devices.
        Docs: https://developers.google.com/identity/protocols/oauth2/limited-input-device
        """
        device_code_url = config["device_code_url"]
        token_url = config["token_url"]
        client_id = config["client_id"]
        client_secret = config.get("client_secret", "")
        scope = config.get("scope", "")

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    device_code_url,
                    data={
                        "client_id": client_id,
                        "scope": scope,
                    },
                    headers=headers,
                )
                resp.raise_for_status()
                device_data = resp.json()
            except (httpx.HTTPError, ValueError) as exc:
                return AuthResult(
                    success=False,
                    provider_id=provider_id,
                    error=f"Device code request failed: {exc}",
                )

        device_code = device_data.get("device_code")
        user_code = device_data.get("user_code")
        verification_url = device_data.get("verification_url", "https://www.google.com/device")
        interval = device_data.get("interval", 5)
        expires_in = device_data.get("expires_in", 1800)

        if not device_code or not user_code:
            return AuthResult(
                success=False,
                provider_id=provider_id,
                error="Invalid device code response",
            )

        print(f"\nTo authorize, visit: {verification_url}")
        print(f"Enter code: {user_code}")
        print(f"(expires in {expires_in // 60} minutes)")

        try:
            webbrowser.open(verification_url)
        except Exception:
            pass

        return await self._poll_google_for_token(
            provider_id, token_url, client_id, client_secret, device_code, interval, expires_in
        )

    async def _poll_google_for_token(
        self,
        provider_id: str,
        token_url: str,
        client_id: str,
        client_secret: str,
        device_code: str,
        interval: int,
        expires_in: int,
    ) -> AuthResult:
        """Poll Google for token after device code authorization."""
        elapsed = 0

        async with httpx.AsyncClient(timeout=30) as client:
            while elapsed < expires_in:
                await asyncio.sleep(interval)
                elapsed += interval

                data = {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                }

                try:
                    resp = await client.post(
                        token_url,
                        data=data,
                        headers={
                            "Content-Type": "application/x-www-form-urlencoded",
                            "Accept": "application/json",
                        },
                    )
                    result = resp.json()
                except (httpx.HTTPError, ValueError):
                    print(".", end="", flush=True)
                    continue

                error = result.get("error")
                if error == "authorization_pending":
                    print(".", end="", flush=True)
                    continue
                elif error == "slow_down":
                    interval += 5
                    continue
                elif error:
                    return AuthResult(
                        success=False,
                        provider_id=provider_id,
                        error=result.get("error_description", error),
                    )

                auth_result = AuthResult(
                    success=True,
                    provider_id=provider_id,
                    access_token=result.get("access_token"),
                    refresh_token=result.get("refresh_token"),
                    expires_in=result.get("expires_in"),
                )
                self._token_store.save(provider_id, auth_result)
                LOGGER.info("OAuth token obtained for %s", provider_id)
                return auth_result

        return AuthResult(
            success=False,
            provider_id=provider_id,
            error="Authorization timed out",
        )

    async def _authorization_code_flow(
        self, provider_id: str, config: dict[str, Any]
    ) -> AuthResult:
        """OAuth 2.0 authorization code grant with PKCE."""
        auth_url = config["authorization_url"]
        token_url = config["token_url"]
        client_id = config["client_id"]
        redirect_uri = config.get("redirect_uri", "http://localhost:18990/callback")
        scope = config.get("scope", "")

        pkce = generate_pkce()
        state = secrets.token_urlsafe(32)

        params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "code_challenge": pkce.challenge,
            "code_challenge_method": pkce.method,
        }

        url = f"{auth_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        print(f"\nOpen this URL to authorize:\n{url}")

        try:
            webbrowser.open(url)
        except Exception:
            pass

        code = input("\nPaste the authorization code: ").strip()
        if not code:
            return AuthResult(
                success=False,
                provider_id=provider_id,
                error="No authorization code provided",
            )

        return await self._exchange_code(
            provider_id, token_url, client_id, code, redirect_uri, pkce.verifier
        )

    async def _exchange_code(
        self,
        provider_id: str,
        token_url: str,
        client_id: str,
        code: str,
        redirect_uri: str,
        code_verifier: str,
    ) -> AuthResult:
        """Exchange authorization code for tokens."""
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    token_url,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "client_id": client_id,
                        "redirect_uri": redirect_uri,
                        "code_verifier": code_verifier,
                    },
                    headers={"Accept": "application/json"},
                )
                resp.raise_for_status()
                data = resp.json()
            except (httpx.HTTPError, ValueError) as exc:
                return AuthResult(
                    success=False,
                    provider_id=provider_id,
                    error=f"Token exchange failed: {exc}",
                )

        result = AuthResult(
            success=True,
            provider_id=provider_id,
            access_token=data.get("access_token"),
            refresh_token=data.get("refresh_token"),
            expires_in=data.get("expires_in"),
        )
        self._token_store.save(provider_id, result)
        LOGGER.info("OAuth token obtained for %s", provider_id)
        return result

    def set_api_key(self, provider_id: str, api_key: str) -> AuthResult:
        """Store an API key directly (non-OAuth flow)."""
        result = AuthResult(
            success=True,
            provider_id=provider_id,
            access_token=api_key,
            token_type="api_key",
        )
        self._token_store.save(provider_id, result)
        return result

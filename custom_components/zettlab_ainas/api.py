"""Thin async client for the ZettOS device HTTP API.

Transport-only: this module must not import ``homeassistant``. It raises its own
exceptions which the coordinator translates into HA errors.

Verified against Zettlab D4 (ZettOS 1.9.0-beta) and D6 Ultra (1.9.1-beta).
Auth is RSA-PKCS1v15-encrypted password + a JWT sent back in the bare
``Authorization`` header (no ``Bearer`` prefix).
"""

from __future__ import annotations

import asyncio
import base64
from http import HTTPStatus
import logging
from typing import Any

import aiohttp
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15
CODE_OK = 200

# API paths (see CLAUDE.md for the full contract).
_P_PUBLIC_KEY = "/zettos/main/user/v1/public_key"
_P_LOGIN = "/zettos/main/user/v1/login"
_P_BESCAN = "/zettos/main/system-settings/v1/device/beScan"
_P_DEVICE = "/zettos/main/system-settings/v1/device"
_P_STORAGE_POOL = "/zettos/main/system-settings/v1/storage-pool"
_P_MONITOR = "/zettos/monitor/v1/view"
_P_FAN = "/zettos/main/system-settings/v1/fan"
_P_LCD = "/zettos/main/system-settings/v1/lcd"
_P_LIGHT = "/zettos/main/system-settings/v1/light"


class ZettosError(Exception):
    """Base error for the ZettOS client."""


class ZettosConnectionError(ZettosError):
    """Transport/timeout error talking to the device."""


class ZettosAuthError(ZettosError):
    """Authentication failed or the session token is invalid."""


class ZettosApiError(ZettosError):
    """The API returned a non-success ``code``."""

    def __init__(self, code: int, message: str = "") -> None:
        """Store the ZettOS error code."""
        super().__init__(f"ZettOS API error code={code} {message}".strip())
        self.code = code


def _encrypt_password(public_key_pem: str, password: str) -> str:
    """RSA-PKCS1v15-encrypt ``password`` with the device public key, base64-encoded.

    Fast (RSA-2048 public-op); safe to call without an executor.
    """
    public_key = load_pem_public_key(public_key_pem.encode())
    encrypted = public_key.encrypt(password.encode(), padding.PKCS1v15())  # type: ignore[union-attr]
    return base64.b64encode(encrypted).decode()


async def async_probe_device(
    session: aiohttp.ClientSession, host: str, *, verify_ssl: bool = False
) -> dict[str, Any] | None:
    """Return the no-auth ``beScan`` identity for ``host`` or ``None``.

    Used by the config flow to validate a manual host and to identify devices.
    """
    url = f"https://{host}{_P_BESCAN}"
    try:
        async with session.get(
            url,
            ssl=verify_ssl,
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
        ) as resp:
            if resp.status != HTTPStatus.OK:
                return None
            payload = await resp.json(content_type=None)
    except (TimeoutError, aiohttp.ClientError, ValueError):
        return None
    if not isinstance(payload, dict) or payload.get("code") != CODE_OK:
        return None
    data = payload.get("data")
    return data if isinstance(data, dict) else None


class ZettOSClient:
    """Authenticated client for a single ZettOS device."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
        *,
        verify_ssl: bool = False,
    ) -> None:
        """Initialise the client."""
        self._host = host
        self._username = username
        self._password = password
        self._session = session
        self._verify_ssl = verify_ssl
        self._token: str | None = None
        self._lock = asyncio.Lock()

    @property
    def host(self) -> str:
        """Return the device host."""
        return self._host

    def _url(self, path: str) -> str:
        return f"https://{self._host}{path}"

    async def async_login(self) -> None:
        """Perform the RSA-encrypted login and cache the JWT."""
        pem = await self._async_get_public_key()
        encrypted = _encrypt_password(pem, self._password)
        payload = await self._async_raw_request(
            "POST",
            _P_LOGIN,
            json={"username": self._username, "password": encrypted},
            authed=False,
        )
        token = (payload.get("data") or {}).get("token", {}).get("access_token")
        if not token:
            raise ZettosAuthError("login response did not contain an access token")
        self._token = token

    async def _async_get_public_key(self) -> str:
        payload = await self._async_raw_request("GET", _P_PUBLIC_KEY, authed=False)
        pem = (payload.get("data") or {}).get("public_key")
        if not pem:
            raise ZettosAuthError("device did not return a public key")
        return pem

    async def _async_raw_request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        authed: bool = True,
    ) -> dict[str, Any]:
        """Issue one request and return the parsed ``{code,data}`` envelope."""
        headers: dict[str, str] = {}
        if authed:
            if self._token is None:
                raise ZettosAuthError("not logged in")
            # ZettOS expects the bare token (NO "Bearer " prefix).
            headers["Authorization"] = self._token
        try:
            async with self._session.request(
                method,
                self._url(path),
                json=json,
                headers=headers,
                ssl=self._verify_ssl,
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            ) as resp:
                if resp.status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
                    raise ZettosAuthError(f"HTTP {resp.status} for {path}")
                resp.raise_for_status()
                body = await resp.json(content_type=None)
        except ZettosAuthError:
            raise
        except (TimeoutError, aiohttp.ClientError) as err:
            raise ZettosConnectionError(str(err)) from err
        except ValueError as err:
            raise ZettosApiError(-1, f"invalid JSON from {path}: {err}") from err

        if not isinstance(body, dict):
            raise ZettosApiError(-1, f"unexpected response from {path}")
        code = body.get("code")
        if code != CODE_OK:
            raise ZettosApiError(int(code) if isinstance(code, int) else -1, path)
        return body

    async def _async_request(
        self, method: str, path: str, *, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Authenticated request with one transparent re-login on token expiry."""
        async with self._lock:
            if self._token is None:
                await self.async_login()
        try:
            return await self._async_raw_request(method, path, json=json)
        except ZettosAuthError:
            _LOGGER.debug("token rejected for %s, re-logging in", path)
            async with self._lock:
                await self.async_login()
            return await self._async_raw_request(method, path, json=json)

    @staticmethod
    def _data(payload: dict[str, Any]) -> Any:
        return payload.get("data")

    # --- reads -----------------------------------------------------------------

    async def async_get_device(self) -> dict[str, Any]:
        """Device identity (model, sn, version, cpu/gpu/npu, mac, uptime)."""
        return self._data(await self._async_request("GET", _P_DEVICE)) or {}

    async def async_get_storage_pools(self) -> list[dict[str, Any]]:
        """Pools with capacity + per-disk model/temperature/SMART status."""
        data = self._data(await self._async_request("GET", _P_STORAGE_POOL))
        return data if isinstance(data, list) else []

    async def async_get_monitor(self) -> dict[str, Any]:
        """Realtime cpu/npu/gpu/mem and per-disk I/O rates."""
        return self._data(await self._async_request("GET", _P_MONITOR)) or {}

    async def async_get_fan_mode(self) -> int | None:
        """Current fan mode integer."""
        data = self._data(await self._async_request("GET", _P_FAN))
        return data if isinstance(data, int) else None

    async def async_get_lcd(self) -> dict[str, Any]:
        """Screen state, e.g. ``{"status": 1}``."""
        return self._data(await self._async_request("GET", _P_LCD)) or {}

    async def async_get_light(self) -> dict[str, Any]:
        """RGB LED state ``{mode,start_color,end_color,speed,...}``."""
        return self._data(await self._async_request("GET", _P_LIGHT)) or {}

    # --- writes ----------------------------------------------------------------

    async def async_set_fan_mode(self, mode: int) -> None:
        """Set fan mode (mode int is part of the path)."""
        await self._async_request("POST", f"{_P_FAN}/{int(mode)}")

    async def async_set_lcd(self, enable: bool) -> None:
        """Turn the screen on/off."""
        await self._async_request("POST", _P_LCD, json={"enable": enable})

    async def async_set_light(self, payload: dict[str, Any]) -> None:
        """Set the RGB LED ``{mode,start_color,end_color,speed}``."""
        await self._async_request("POST", _P_LIGHT, json=payload)

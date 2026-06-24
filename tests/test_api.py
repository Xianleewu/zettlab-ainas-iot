"""Test the ZettOS API client (auth flow + headers + envelope)."""

from __future__ import annotations

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import pytest
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.zettlab_ainas.api import ZettosApiError, ZettOSClient

HOST = "192.168.1.50"
BASE = f"https://{HOST}"


def _public_key_pem() -> str:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return (
        key.public_key()
        .public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )


async def test_login_and_auth_header(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Login encrypts the password, then sends the bare token (no 'Bearer')."""
    aioclient_mock.get(
        f"{BASE}/zettos/main/user/v1/public_key",
        json={"code": 200, "data": {"public_key": _public_key_pem()}},
    )
    aioclient_mock.post(
        f"{BASE}/zettos/main/user/v1/login",
        json={"code": 200, "data": {"token": {"access_token": "TOK123"}}},
    )
    aioclient_mock.get(
        f"{BASE}/zettos/main/system-settings/v1/device",
        json={"code": 200, "data": {"sn": "X"}},
    )

    client = ZettOSClient(HOST, "admin", "secret", async_get_clientsession(hass))
    device = await client.async_get_device()

    assert device == {"sn": "X"}
    method, url, _data, headers = aioclient_mock.mock_calls[-1]
    assert method == "GET"
    assert url.path.endswith("/device")
    assert headers["Authorization"] == "TOK123"  # no "Bearer " prefix


async def test_non_success_code_raises(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """A non-200 envelope code raises ZettosApiError."""
    aioclient_mock.get(
        f"{BASE}/zettos/main/user/v1/public_key",
        json={"code": 200, "data": {"public_key": _public_key_pem()}},
    )
    aioclient_mock.post(
        f"{BASE}/zettos/main/user/v1/login",
        json={"code": 200, "data": {"token": {"access_token": "TOK"}}},
    )
    aioclient_mock.get(
        f"{BASE}/zettos/main/system-settings/v1/storage-pool",
        json={"code": 14502, "data": {}},
    )

    client = ZettOSClient(HOST, "admin", "secret", async_get_clientsession(hass))
    with pytest.raises(ZettosApiError):
        await client.async_get_storage_pools()

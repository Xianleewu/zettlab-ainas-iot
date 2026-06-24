"""Test the config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest

from custom_components.zettlab_ainas.api import ZettosAuthError, ZettosConnectionError
from custom_components.zettlab_ainas.const import DOMAIN

from .conftest import DEVICE


def _patch_login(client: AsyncMock):
    return patch(
        "custom_components.zettlab_ainas.config_flow.ZettOSClient",
        return_value=client,
    )


def _patch_probe(return_value):
    return patch(
        "custom_components.zettlab_ainas.config_flow.async_probe_device",
        AsyncMock(return_value=return_value),
    )


async def _open_manual(hass: HomeAssistant) -> str:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "manual"}
    )
    assert result["step_id"] == "manual"
    return result["flow_id"]


async def test_manual_flow_success(hass: HomeAssistant) -> None:
    """Manual host → login → entry created with the serial as unique_id."""
    client = AsyncMock()
    client.async_login.return_value = None
    client.async_get_device.return_value = DEVICE

    flow_id = await _open_manual(hass)
    with _patch_probe(DEVICE):
        result = await hass.config_entries.flow.async_configure(
            flow_id, {CONF_HOST: "192.168.1.50"}
        )
    assert result["step_id"] == "login"

    with _patch_login(client):
        result = await hass.config_entries.flow.async_configure(
            flow_id, {CONF_USERNAME: "admin", CONF_PASSWORD: "secret"}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test NAS"
    assert result["result"].unique_id == DEVICE["sn"]
    assert result["data"][CONF_HOST] == "192.168.1.50"


async def test_manual_cannot_connect(hass: HomeAssistant) -> None:
    """Unreachable host shows a connection error."""
    flow_id = await _open_manual(hass)
    with _patch_probe(None):
        result = await hass.config_entries.flow.async_configure(
            flow_id, {CONF_HOST: "10.0.0.9"}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (ZettosAuthError("bad"), "invalid_auth"),
        (ZettosConnectionError("down"), "cannot_connect"),
    ],
)
async def test_login_errors(hass: HomeAssistant, exc: Exception, expected: str) -> None:
    """Login failures surface the right error."""
    flow_id = await _open_manual(hass)
    with _patch_probe(DEVICE):
        await hass.config_entries.flow.async_configure(
            flow_id, {CONF_HOST: "192.168.1.50"}
        )

    client = AsyncMock()
    client.async_login.side_effect = exc
    with _patch_login(client):
        result = await hass.config_entries.flow.async_configure(
            flow_id, {CONF_USERNAME: "admin", CONF_PASSWORD: "bad"}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": expected}

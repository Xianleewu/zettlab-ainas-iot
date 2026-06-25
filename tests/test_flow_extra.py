"""Additional config-flow branches: discovery, remote-id, options, discovery util."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zettlab_ainas.const import CONF_SCAN_INTERVAL, DOMAIN
from custom_components.zettlab_ainas.discovery import async_discover

from .conftest import DEVICE


async def _menu(hass: HomeAssistant, choice: str):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    return await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": choice}
    )


async def test_discover_no_devices_falls_back_to_manual(hass: HomeAssistant) -> None:
    """When nothing is discovered, the flow drops to the manual step."""
    with patch(
        "custom_components.zettlab_ainas.config_flow.async_discover",
        AsyncMock(return_value={}),
    ):
        result = await _menu(hass, "discover")
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"


async def test_discover_with_device(hass: HomeAssistant) -> None:
    """A discovered device can be selected and onboarded."""
    with patch(
        "custom_components.zettlab_ainas.config_flow.async_discover",
        AsyncMock(return_value={"1.2.3.4": DEVICE}),
    ):
        result = await _menu(hass, "discover")
        assert result["step_id"] == "discover"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "1.2.3.4"}
        )
    assert result["step_id"] == "login"

    client = AsyncMock()
    client.async_get_device.return_value = DEVICE
    with patch(
        "custom_components.zettlab_ainas.config_flow.ZettOSClient",
        return_value=client,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_USERNAME: "admin", CONF_PASSWORD: "secret"}
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_HOST] == "1.2.3.4"


async def test_options_flow(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Options flow stores the polling interval."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_INTERVAL: 60}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options[CONF_SCAN_INTERVAL] == 60


async def test_async_discover_returns_empty_without_probe(hass: HomeAssistant) -> None:
    """Discovery is a no-op until the UDP probe payload is decoded."""
    assert await async_discover(hass) == {}

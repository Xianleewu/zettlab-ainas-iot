"""Test control entities (write paths) and diagnostics."""

from __future__ import annotations

from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zettlab_ainas.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def _setup(hass, entry, client) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_light_set_color_and_off(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Setting RGB and turning off post the right payload."""
    await _setup(hass, mock_config_entry, mock_client)

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": "light.test_nas_status_led", "rgb_color": [10, 20, 30]},
        blocking=True,
    )
    payload = mock_client.async_set_light.call_args.args[0]
    assert payload["start_color"] == "#0A141E"
    assert payload["end_color"] == "#0A141E"

    await hass.services.async_call(
        "light", "turn_off", {"entity_id": "light.test_nas_status_led"}, blocking=True
    )
    assert mock_client.async_set_light.call_args.args[0]["start_color"] == "#000000"


async def test_screen_switch(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Screen switch maps to set_lcd(enable)."""
    await _setup(hass, mock_config_entry, mock_client)

    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": "switch.test_nas_screen"}, blocking=True
    )
    mock_client.async_set_lcd.assert_awaited_with(False)

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": "switch.test_nas_screen"}, blocking=True
    )
    mock_client.async_set_lcd.assert_awaited_with(True)


async def test_fan_mode_select(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Selecting a fan mode posts the integer mode."""
    await _setup(hass, mock_config_entry, mock_client)

    assert hass.states.get("select.test_nas_fan_mode").state == "2"
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.test_nas_fan_mode", "option": "1"},
        blocking=True,
    )
    mock_client.async_set_fan_mode.assert_awaited_with(1)


async def test_diagnostics_redacts(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Diagnostics redact secrets and serials."""
    await _setup(hass, mock_config_entry, mock_client)

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)
    assert diag["entry_data"]["password"] == "**REDACTED**"
    assert diag["data"]["device"]["sn"] == "**REDACTED**"

"""Test setup/unload and entity creation."""

from __future__ import annotations

from unittest.mock import AsyncMock

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_setup_and_entities(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Entry loads, entities appear, and a sensor reflects device data."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED

    cpu = hass.states.get("sensor.test_nas_cpu_usage")
    assert cpu is not None
    assert cpu.state == "12.5"

    temp = hass.states.get("sensor.test_nas_cpu_temperature")
    assert temp is not None
    assert temp.state == "43"

    # Per-pool and per-disk dynamic entities exist.
    assert hass.states.get("binary_sensor.test_nas_pool_pool_1_problem").state == "off"
    assert any(
        eid.endswith("temperature") and "disk" in eid
        for eid in hass.states.async_entity_ids("sensor")
    )


async def test_unload(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Entry unloads cleanly."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED

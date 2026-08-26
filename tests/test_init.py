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

    fan = hass.states.get("sensor.test_nas_fan_1_speed")
    assert fan is not None
    assert fan.state == "1066"
    assert fan.attributes["unit_of_measurement"] == "rpm"

    assert hass.states.get("sensor.test_nas_memory_free") is not None
    assert hass.states.get("sensor.test_nas_memory_cache") is not None
    assert hass.states.get("sensor.test_nas_memory_total") is not None

    # Per-pool and per-disk dynamic entities exist.
    assert hass.states.get("binary_sensor.test_nas_pool_pool_1_problem").state == "off"
    assert hass.states.get("sensor.test_nas_pool_pool_1_free") is not None
    assert any(
        eid.endswith("temperature") and "disk" in eid
        for eid in hass.states.async_entity_ids("sensor")
    )


async def test_transfer_rates_from_counter_deltas(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Disk and network rates use byte deltas between monitor snapshots."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    disk = hass.states.get("sensor.test_nas_disk_a_read_rate")
    network = hass.states.get("sensor.test_nas_lan1_download_rate")
    assert disk is not None and disk.state == "unknown"
    assert network is not None and network.state == "unknown"

    monitor = {
        **mock_client.async_get_monitor.return_value,
        "current_time": 1010,
        "disks": {
            "DISK A": {
                "read_bytes": 2000,
                "write_bytes": 4500,
            }
        },
        "nets": {"LAN1": {"bytes_sent": 11000, "bytes_recv": 23000}},
    }
    mock_client.async_get_monitor.return_value = monitor
    await mock_config_entry.runtime_data.async_request_refresh()
    await hass.async_block_till_done()

    assert hass.states.get("sensor.test_nas_disk_a_read_rate").state == "100.0"
    assert hass.states.get("sensor.test_nas_disk_a_write_rate").state == "250.0"
    assert hass.states.get("sensor.test_nas_lan1_upload_rate").state == "100.0"
    assert hass.states.get("sensor.test_nas_lan1_download_rate").state == "300.0"


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

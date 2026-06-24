"""Fixtures for Zettlab AINAS tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zettlab_ainas.const import CONF_VERIFY_SSL, DOMAIN

DEVICE = {
    "device_name": "Test NAS",
    "model_name": "Zettlab D4",
    "sn": "WY000000000TEST",
    "system_version": "1.9.0-beta",
    "cpu": "RK3588",
    "mac_address1": "04:a1:6f:00:00:01",
    "mac_address2": "04:a1:6f:00:00:02",
    "last_start_time": 1781746803,
}

POOLS = [
    {
        "name": "pool_1",
        "status": 0,
        "total_size": 1570389352448,
        "used_size": 35786895360,
        "type": "raid0",
        "disks": [
            {
                "model": "TOSHIBA DT01ACA050",
                "serial_number": "TESTSER1",
                "slot": 0,
                "temperature": 36,
                "type": "HDD",
                "real_path": "/dev/sdc",
                "is_support_smart": True,
                "status": 1,
            }
        ],
    }
]

MONITOR = {
    "cpu": {"usage_rate": 12.5, "thermal": 43},
    "npu": [0, 0, 0],
    "gpu": [0],
    "mem": {"total": 16719732736, "free": 5660459008, "used": 1753964544},
    "disks": {},
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
) -> Generator[None]:
    """Enable loading of the custom integration in every test."""
    yield


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """A configured entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=DEVICE["sn"],
        title=DEVICE["device_name"],
        data={
            CONF_HOST: "192.168.1.50",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "secret",
            CONF_VERIFY_SSL: False,
        },
    )


@pytest.fixture
def mock_client() -> Generator[AsyncMock]:
    """Patch ZettOSClient with canned responses for setup/coordinator."""
    client = AsyncMock()
    client.host = "192.168.1.50"
    client.async_login.return_value = None
    client.async_get_device.return_value = DEVICE
    client.async_get_storage_pools.return_value = POOLS
    client.async_get_monitor.return_value = MONITOR
    client.async_get_fan_mode.return_value = 2
    client.async_get_lcd.return_value = {"status": 1}
    client.async_get_light.return_value = {
        "mode": 6,
        "start_color": "#4B13A3",
        "end_color": "#4B13A3",
        "speed": 1,
    }
    with patch("custom_components.zettlab_ainas.ZettOSClient", return_value=client):
        yield client

"""Diagnostics for Zettlab AINAS."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .const import CONF_PASSWORD
from .coordinator import ZettlabAinasConfigEntry

_REDACT = {CONF_PASSWORD, "sn", "serial_number", "mac_address1", "mac_address2"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ZettlabAinasConfigEntry
) -> dict[str, Any]:
    """Return redacted diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "entry_data": async_redact_data(dict(entry.data), _REDACT),
        "data": async_redact_data(asdict(coordinator.data), _REDACT),
    }

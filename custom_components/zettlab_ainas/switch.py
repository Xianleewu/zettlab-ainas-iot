"""Switch platform for Zettlab AINAS — screen on/off."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ZettlabAinasConfigEntry
from .entity import ZettlabAinasEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZettlabAinasConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the screen switch."""
    async_add_entities([ZettlabScreenSwitch(entry.runtime_data)])


class ZettlabScreenSwitch(ZettlabAinasEntity, SwitchEntity):
    """The device LCD screen power.

    GET ``/lcd`` returns ``{"status": 1}``; set via POST ``/lcd {"enable": bool}``.
    (No brightness setter is exposed by the web API.)
    """

    _attr_translation_key = "screen"

    def __init__(self, coordinator) -> None:
        """Initialise."""
        super().__init__(coordinator, "screen")

    @property
    def is_on(self) -> bool | None:
        """Return whether the screen is on."""
        status = self.coordinator.data.lcd.get("status")
        if not isinstance(status, int):
            return None
        return status == 1

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the screen on."""
        await self.coordinator.client.async_set_lcd(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the screen off."""
        await self.coordinator.client.async_set_lcd(False)
        await self.coordinator.async_request_refresh()

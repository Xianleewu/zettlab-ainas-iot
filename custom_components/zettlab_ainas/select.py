"""Select platform for Zettlab AINAS — fan mode."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ZettlabAinasConfigEntry
from .entity import ZettlabAinasEntity

# The fan-mode integer enum is not yet decoded (observed value: 2). Options are
# the raw modes as strings; relabel in strings.json once the meaning is known.
# Writing is POST /system-settings/v1/fan/{mode}.
FAN_MODE_OPTIONS: tuple[str, ...] = ("0", "1", "2", "3")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZettlabAinasConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the fan-mode select."""
    async_add_entities([ZettlabFanModeSelect(entry.runtime_data)])


class ZettlabFanModeSelect(ZettlabAinasEntity, SelectEntity):
    """Fan operating mode."""

    _attr_translation_key = "fan_mode"
    _attr_options = list(FAN_MODE_OPTIONS)

    def __init__(self, coordinator) -> None:
        """Initialise."""
        super().__init__(coordinator, "fan_mode")

    @property
    def current_option(self) -> str | None:
        """Return the current fan mode as a string."""
        mode = self.coordinator.data.fan_mode
        if mode is None:
            return None
        option = str(mode)
        return option if option in self._attr_options else None

    async def async_select_option(self, option: str) -> None:
        """Set the fan mode."""
        await self.coordinator.client.async_set_fan_mode(int(option))
        await self.coordinator.async_request_refresh()

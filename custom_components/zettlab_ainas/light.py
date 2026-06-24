"""Light platform for Zettlab AINAS — the RGB status LED."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ATTR_RGB_COLOR, ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ZettlabAinasConfigEntry
from .entity import ZettlabAinasEntity

_OFF = "#000000"
_DEFAULT_ON = (255, 255, 255)
_HEX_LEN = 7  # "#RRGGBB"


def _hex_to_rgb(value: Any) -> tuple[int, int, int] | None:
    if not isinstance(value, str) or len(value) != _HEX_LEN or value[0] != "#":
        return None
    try:
        return (int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16))
    except ValueError:
        return None


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZettlabAinasConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the RGB status LED."""
    async_add_entities([ZettlabStatusLight(entry.runtime_data)])


class ZettlabStatusLight(ZettlabAinasEntity, LightEntity):
    """RGB status LED.

    The effect/mode integer enum is not decoded, so this exposes RGB color only
    and preserves the device's current ``mode``/``speed`` on every write. Off is
    represented as black (``#000000``) — visually dark for a status LED.
    """

    _attr_translation_key = "status_led"
    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}

    def __init__(self, coordinator) -> None:
        """Initialise."""
        super().__init__(coordinator, "status_led")

    @property
    def _rgb(self) -> tuple[int, int, int] | None:
        return _hex_to_rgb(self.coordinator.data.light.get("start_color"))

    @property
    def is_on(self) -> bool | None:
        """LED is on when its colour is not black."""
        rgb = self._rgb
        if rgb is None:
            return None
        return rgb != (0, 0, 0)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the current RGB colour."""
        return self._rgb

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the (not-yet-decoded) effect mode and speed."""
        light = self.coordinator.data.light
        return {"mode": light.get("mode"), "speed": light.get("speed")}

    async def _async_write(self, hex_color: str) -> None:
        light = self.coordinator.data.light
        payload = {
            "mode": light.get("mode", 0),
            "start_color": hex_color,
            "end_color": hex_color,
            "speed": light.get("speed", 1),
        }
        await self.coordinator.client.async_set_light(payload)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the LED on / set its colour."""
        rgb = kwargs.get(ATTR_RGB_COLOR)
        if rgb is None:
            current = self._rgb
            rgb = current if current and current != (0, 0, 0) else _DEFAULT_ON
        await self._async_write(_rgb_to_hex(rgb))

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the LED off (set colour to black)."""
        await self._async_write(_OFF)

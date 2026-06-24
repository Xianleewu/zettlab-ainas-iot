"""Binary sensor platform for Zettlab AINAS."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ZettlabAinasConfigEntry
from .entity import ZettlabAinasEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZettlabAinasConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Zettlab AINAS binary sensors."""
    coordinator = entry.runtime_data
    entities = [
        ZettlabPoolProblem(coordinator, name)
        for pool in coordinator.data.pools
        if (name := pool.get("name"))
    ]
    async_add_entities(entities)


class ZettlabPoolProblem(ZettlabAinasEntity, BinarySensorEntity):
    """Problem state of a storage pool (``status`` != 0 → problem)."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator, pool_name: str) -> None:
        """Initialise."""
        super().__init__(coordinator, f"pool_{pool_name}_problem")
        self._pool_name = pool_name
        self._attr_name = f"Pool {pool_name} problem"

    def _pool(self) -> dict[str, Any]:
        for pool in self.coordinator.data.pools:
            if pool.get("name") == self._pool_name:
                return pool
        return {}

    @property
    def is_on(self) -> bool | None:
        """Return True when the pool reports a non-healthy status."""
        status = self._pool().get("status")
        if not isinstance(status, int):
            return None
        return status != 0

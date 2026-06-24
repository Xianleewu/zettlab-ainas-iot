"""Shared base entity for Zettlab AINAS."""

from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import ZettlabAinasCoordinator


class ZettlabAinasEntity(CoordinatorEntity[ZettlabAinasCoordinator]):
    """Base entity: all entities share one device and read from the coordinator."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ZettlabAinasCoordinator, key: str) -> None:
        """Set a stable unique id derived from the device serial."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._device_id}_{key}"

    @property
    def _device_id(self) -> str:
        entry = self.coordinator.config_entry
        return (
            self.coordinator.data.device.get("sn") or entry.unique_id or entry.entry_id
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Group every entity under one HA device, built from ``/device``."""
        device = self.coordinator.data.device
        connections = {
            (CONNECTION_NETWORK_MAC, mac)
            for key in ("mac_address1", "mac_address2")
            if (mac := device.get(key))
        }
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            manufacturer=MANUFACTURER,
            model=device.get("model_name"),
            name=device.get("device_name"),
            sw_version=device.get("system_version"),
            serial_number=device.get("sn"),
            connections=connections,
            configuration_url=f"https://{self.coordinator.client.host}",
        )

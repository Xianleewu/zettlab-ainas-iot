"""Sensor platform for Zettlab AINAS."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    EntityCategory,
    UnitOfDataRate,
    UnitOfInformation,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util

from .coordinator import ZettlabAinasConfigEntry, ZettlabData
from .entity import ZettlabAinasEntity


def _div(num: Any, den: Any) -> float | None:
    """Percentage ``num/den*100`` guarded against bad/zero inputs."""
    try:
        if not den:
            return None
        return round(float(num) / float(den) * 100, 1)
    except (TypeError, ValueError):
        return None


def _num(value: Any) -> StateType:
    return value if isinstance(value, (int, float)) else None


@dataclass(frozen=True, kw_only=True)
class ZettlabSensorDescription(SensorEntityDescription):
    """Sensor description with a value extractor over the snapshot."""

    value_fn: Callable[[ZettlabData], StateType | datetime]


def _uptime(data: ZettlabData) -> datetime | None:
    ts = data.device.get("last_start_time")
    if not isinstance(ts, (int, float)) or ts <= 0:
        return None
    return dt_util.utc_from_timestamp(int(ts))


SENSORS: tuple[ZettlabSensorDescription, ...] = (
    ZettlabSensorDescription(
        key="cpu_usage",
        translation_key="cpu_usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda d: _num(d.monitor.get("cpu", {}).get("usage_rate")),
    ),
    ZettlabSensorDescription(
        key="cpu_temperature",
        translation_key="cpu_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _num(d.monitor.get("cpu", {}).get("thermal")),
    ),
    ZettlabSensorDescription(
        key="memory_usage",
        translation_key="memory_usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda d: _div(
            d.monitor.get("mem", {}).get("used"), d.monitor.get("mem", {}).get("total")
        ),
    ),
    ZettlabSensorDescription(
        key="memory_used",
        translation_key="memory_used",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        suggested_display_precision=2,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _num(d.monitor.get("mem", {}).get("used")),
    ),
    ZettlabSensorDescription(
        key="memory_free",
        translation_key="memory_free",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        suggested_display_precision=2,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _num(d.monitor.get("mem", {}).get("free")),
    ),
    ZettlabSensorDescription(
        key="memory_cache",
        translation_key="memory_cache",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        suggested_display_precision=2,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _num(d.monitor.get("mem", {}).get("cache")),
    ),
    ZettlabSensorDescription(
        key="memory_total",
        translation_key="memory_total",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        suggested_display_precision=2,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _num(d.monitor.get("mem", {}).get("total")),
    ),
    ZettlabSensorDescription(
        key="npu_usage",
        translation_key="npu_usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda d: (
            round(sum(n) / len(n), 1)
            if (
                n := [
                    x for x in d.monitor.get("npu", []) if isinstance(x, (int, float))
                ]
            )
            else None
        ),
    ),
    ZettlabSensorDescription(
        key="gpu_usage",
        translation_key="gpu_usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda d: (
            _num(g[0]) if (g := d.monitor.get("gpu")) and isinstance(g, list) else None
        ),
    ),
    ZettlabSensorDescription(
        key="uptime",
        translation_key="uptime",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_uptime,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZettlabAinasConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Zettlab AINAS sensors."""
    coordinator = entry.runtime_data
    data = coordinator.data

    entities: list[SensorEntity] = [
        ZettlabSensor(coordinator, desc) for desc in SENSORS
    ]
    fan_speeds = data.monitor.get("fan_speed")
    if isinstance(fan_speeds, list):
        entities.extend(
            ZettlabFanSpeedSensor(coordinator, index)
            for index in range(len(fan_speeds))
        )
    disks = data.monitor.get("disks")
    if isinstance(disks, dict):
        for name in disks:
            entities.append(
                ZettlabTransferRateSensor(coordinator, "disk", name, "read")
            )
            entities.append(
                ZettlabTransferRateSensor(coordinator, "disk", name, "write")
            )
    networks = data.monitor.get("nets")
    if isinstance(networks, dict):
        for name in networks:
            entities.append(
                ZettlabTransferRateSensor(coordinator, "network", name, "upload")
            )
            entities.append(
                ZettlabTransferRateSensor(coordinator, "network", name, "download")
            )
    for pool in data.pools:
        name = pool.get("name")
        if not name:
            continue
        entities.append(ZettlabPoolSensor(coordinator, name, "usage"))
        entities.append(ZettlabPoolSensor(coordinator, name, "used"))
        entities.append(ZettlabPoolSensor(coordinator, name, "free"))
        entities.append(ZettlabPoolSensor(coordinator, name, "total"))
        for disk in pool.get("disks", []):
            serial = disk.get("serial_number")
            if serial:
                entities.append(ZettlabDiskTempSensor(coordinator, serial))

    async_add_entities(entities)


class ZettlabSensor(ZettlabAinasEntity, SensorEntity):
    """A device-wide sensor driven by a description value_fn."""

    entity_description: ZettlabSensorDescription

    def __init__(self, coordinator, description: ZettlabSensorDescription) -> None:
        """Initialise."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> StateType | datetime:
        """Return the current value."""
        return self.entity_description.value_fn(self.coordinator.data)


class ZettlabFanSpeedSensor(ZettlabAinasEntity, SensorEntity):
    """Rotational speed of one fan reported by the realtime monitor."""

    _attr_native_unit_of_measurement = REVOLUTIONS_PER_MINUTE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, index: int) -> None:
        """Initialise a dynamically indexed fan sensor."""
        super().__init__(coordinator, f"fan_{index + 1}_speed")
        self._index = index
        self._attr_translation_key = "fan_speed"
        self._attr_translation_placeholders = {"number": str(index + 1)}

    @property
    def native_value(self) -> StateType:
        """Return RPM for this fan, or unknown when it is not reported."""
        speeds = self.coordinator.data.monitor.get("fan_speed")
        if not isinstance(speeds, list) or self._index >= len(speeds):
            return None
        return _num(speeds[self._index])


class ZettlabTransferRateSensor(ZettlabAinasEntity, SensorEntity):
    """Current disk or network byte rate derived from counter deltas."""

    _attr_device_class = SensorDeviceClass.DATA_RATE
    _attr_native_unit_of_measurement = UnitOfDataRate.BYTES_PER_SECOND
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, source: str, name: str, direction: str) -> None:
        """Initialise a transfer-rate sensor."""
        super().__init__(coordinator, f"{source}_{name}_{direction}_rate")
        self._source = source
        self._source_name = name
        self._direction = direction
        self._attr_translation_key = f"{source}_{direction}_rate"
        self._attr_translation_placeholders = {"name": name}

    @property
    def native_value(self) -> StateType:
        """Return the rate calculated by the coordinator."""
        rates = (
            self.coordinator.data.disk_rates
            if self._source == "disk"
            else self.coordinator.data.network_rates
        )
        return _num(rates.get(self._source_name, {}).get(self._direction))


class ZettlabPoolSensor(ZettlabAinasEntity, SensorEntity):
    """A per-storage-pool sensor (usage / used / free / total)."""

    _CONFIG: dict[str, dict[str, Any]] = {
        "usage": {
            "name": "usage",
            "unit": PERCENTAGE,
            "precision": 1,
            "device_class": None,
        },
        "used": {
            "name": "used",
            "unit": UnitOfInformation.BYTES,
            "device_class": SensorDeviceClass.DATA_SIZE,
        },
        "free": {
            "name": "free",
            "unit": UnitOfInformation.BYTES,
            "device_class": SensorDeviceClass.DATA_SIZE,
        },
        "total": {
            "name": "capacity",
            "unit": UnitOfInformation.BYTES,
            "device_class": SensorDeviceClass.DATA_SIZE,
        },
    }

    def __init__(self, coordinator, pool_name: str, metric: str) -> None:
        """Initialise a pool metric sensor."""
        super().__init__(coordinator, f"pool_{pool_name}_{metric}")
        cfg = self._CONFIG[metric]
        self._pool_name = pool_name
        self._metric = metric
        self._attr_name = f"Pool {pool_name} {cfg['name']}"
        self._attr_native_unit_of_measurement = cfg["unit"]
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_class = cfg["device_class"]
        if metric in ("used", "free", "total"):
            self._attr_suggested_unit_of_measurement = UnitOfInformation.GIBIBYTES
            self._attr_suggested_display_precision = 2

    def _pool(self) -> dict[str, Any]:
        for pool in self.coordinator.data.pools:
            if pool.get("name") == self._pool_name:
                return pool
        return {}

    @property
    def native_value(self) -> StateType:
        """Return the pool metric."""
        pool = self._pool()
        if self._metric == "used":
            return _num(pool.get("used_size"))
        if self._metric == "total":
            return _num(pool.get("total_size"))
        if self._metric == "free":
            total = pool.get("total_size")
            used = pool.get("used_size")
            if not isinstance(total, (int, float)) or not isinstance(
                used, (int, float)
            ):
                return None
            return max(total - used, 0)
        return _div(pool.get("used_size"), pool.get("total_size"))


class ZettlabDiskTempSensor(ZettlabAinasEntity, SensorEntity):
    """Temperature of a single disk (matched by serial number)."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, serial: str) -> None:
        """Initialise a disk temperature sensor."""
        super().__init__(coordinator, f"disk_{serial}_temperature")
        self._serial = serial
        self._attr_name = f"Disk {serial} temperature"

    def _disk(self) -> dict[str, Any]:
        for pool in self.coordinator.data.pools:
            for disk in pool.get("disks", []):
                if disk.get("serial_number") == self._serial:
                    return disk
        return {}

    @property
    def native_value(self) -> StateType:
        """Return the disk temperature."""
        return _num(self._disk().get("temperature"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose disk identity for context."""
        disk = self._disk()
        return {
            "model": disk.get("model"),
            "slot": disk.get("slot"),
            "type": disk.get("type"),
            "path": disk.get("real_path"),
        }

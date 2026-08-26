"""DataUpdateCoordinator for Zettlab AINAS — the single poller all entities read."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    ZettosApiError,
    ZettosAuthError,
    ZettOSClient,
    ZettosConnectionError,
    ZettosError,
)
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

type ZettlabAinasConfigEntry = ConfigEntry[ZettlabAinasCoordinator]


@dataclass(slots=True)
class ZettlabData:
    """Snapshot of one poll cycle."""

    device: dict[str, Any] = field(default_factory=dict)
    pools: list[dict[str, Any]] = field(default_factory=list)
    monitor: dict[str, Any] = field(default_factory=dict)
    disk_rates: dict[str, dict[str, float]] = field(default_factory=dict)
    network_rates: dict[str, dict[str, float]] = field(default_factory=dict)
    fan_mode: int | None = None
    lcd: dict[str, Any] = field(default_factory=dict)
    light: dict[str, Any] = field(default_factory=dict)


class ZettlabAinasCoordinator(DataUpdateCoordinator[ZettlabData]):
    """Polls the ZettOS device and exposes a single ``ZettlabData`` snapshot."""

    config_entry: ZettlabAinasConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ZettlabAinasConfigEntry,
        client: ZettOSClient,
    ) -> None:
        """Initialise the coordinator."""
        scan = entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=scan),
        )
        self.client = client
        self._previous_monitor: dict[str, Any] | None = None
        self._previous_monitor_received: float | None = None

    async def _async_update_data(self) -> ZettlabData:
        """Fetch one snapshot from the device."""
        try:
            device = await self.client.async_get_device()
            pools = await self.client.async_get_storage_pools()
            monitor = await self.client.async_get_monitor()
        except ZettosAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except (ZettosConnectionError, ZettosApiError) as err:
            raise UpdateFailed(str(err)) from err

        received = time.monotonic()
        fallback_interval = (
            received - self._previous_monitor_received
            if self._previous_monitor_received is not None
            else None
        )
        disk_rates, network_rates = _transfer_rates(
            monitor, self._previous_monitor, fallback_interval
        )
        self._previous_monitor = monitor
        self._previous_monitor_received = received

        # Control-state reads are best-effort: a single failure must not blank
        # out the sensors.
        return ZettlabData(
            device=device,
            pools=pools,
            monitor=monitor,
            disk_rates=disk_rates,
            network_rates=network_rates,
            fan_mode=await self._safe(self.client.async_get_fan_mode()),
            lcd=await self._safe(self.client.async_get_lcd()) or {},
            light=await self._safe(self.client.async_get_light()) or {},
        )

    async def _safe(self, coro: Any) -> Any:
        """Await ``coro``, returning ``None`` on any device error.

        Core reads (device/pools/monitor) already validated auth; the client
        auto-relogins on token expiry, so a failure here is a transient
        per-endpoint issue that must not blank the whole snapshot.
        """
        try:
            return await coro
        except ZettosError as err:
            _LOGGER.debug("optional read failed: %s", err)
            return None


def _transfer_rates(
    current: dict[str, Any],
    previous: dict[str, Any] | None,
    fallback_interval: float | None = None,
) -> tuple[dict[str, dict[str, float]], dict[str, dict[str, float]]]:
    """Calculate byte rates from two monitor counter snapshots.

    ZettOS exposes cumulative byte counters for disks and network interfaces.
    Its disk ``read_rate``/``write_rate`` values are lifetime averages, so use
    counter deltas to expose useful current rates in Home Assistant instead.
    """
    if previous is None:
        return {}, {}

    current_time = current.get("current_time")
    previous_time = previous.get("current_time")
    if isinstance(current_time, (int, float)) and isinstance(
        previous_time, (int, float)
    ):
        interval = float(current_time) - float(previous_time)
    else:
        interval = fallback_interval or 0
    if interval <= 0:
        return {}, {}

    disk_rates = _group_rates(
        current.get("disks"),
        previous.get("disks"),
        {"read": "read_bytes", "write": "write_bytes"},
        interval,
    )
    network_rates = _group_rates(
        current.get("nets"),
        previous.get("nets"),
        {"upload": "bytes_sent", "download": "bytes_recv"},
        interval,
    )
    return disk_rates, network_rates


def _group_rates(
    current: Any,
    previous: Any,
    counters: dict[str, str],
    interval: float,
) -> dict[str, dict[str, float]]:
    """Return per-item rates for counters that did not reset or disappear."""
    if not isinstance(current, dict) or not isinstance(previous, dict):
        return {}

    rates: dict[str, dict[str, float]] = {}
    for name, values in current.items():
        old_values = previous.get(name)
        if not isinstance(values, dict) or not isinstance(old_values, dict):
            continue
        item_rates: dict[str, float] = {}
        for rate_name, counter_name in counters.items():
            value = values.get(counter_name)
            old_value = old_values.get(counter_name)
            if not isinstance(value, (int, float)) or not isinstance(
                old_value, (int, float)
            ):
                continue
            delta = float(value) - float(old_value)
            if delta >= 0:
                item_rates[rate_name] = delta / interval
        if item_rates:
            rates[str(name)] = item_rates
    return rates

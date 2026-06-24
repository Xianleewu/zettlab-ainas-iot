"""DataUpdateCoordinator for Zettlab AINAS — the single poller all entities read."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
import logging
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

        # Control-state reads are best-effort: a single failure must not blank
        # out the sensors.
        return ZettlabData(
            device=device,
            pools=pools,
            monitor=monitor,
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

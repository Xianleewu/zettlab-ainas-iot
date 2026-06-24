"""LAN discovery for Zettlab AINAS devices (native UDP broadcast).

The device listens on UDP :9527. The exact probe payload used by the official
app is not yet decoded (``DISCOVERY_PROBE`` is a placeholder), so this currently
returns nothing and the config flow falls back to manual / remote-ID entry. Once
the probe is captured, filling ``DISCOVERY_PROBE`` makes discovery work with no
other changes — replies are expected to be the same JSON shape as ``beScan``.
"""

from __future__ import annotations

import json
import logging
import socket

from homeassistant.core import HomeAssistant

from .const import DISCOVERY_PROBE, DISCOVERY_TIMEOUT, DISCOVERY_UDP_PORT

_LOGGER = logging.getLogger(__name__)


def _blocking_discover() -> dict[str, dict]:
    """Broadcast a probe and collect ``{host: identity}`` replies."""
    if not DISCOVERY_PROBE:
        return {}

    found: dict[str, dict] = {}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(DISCOVERY_TIMEOUT)
        sock.sendto(DISCOVERY_PROBE, ("255.255.255.255", DISCOVERY_UDP_PORT))
        while True:
            try:
                data, addr = sock.recvfrom(65535)
            except TimeoutError:
                break
            try:
                payload = json.loads(data.decode())
            except (ValueError, UnicodeDecodeError):
                continue
            info = payload.get("data", payload) if isinstance(payload, dict) else None
            if isinstance(info, dict):
                found[addr[0]] = info
    finally:
        sock.close()
    return found


async def async_discover(hass: HomeAssistant) -> dict[str, dict]:
    """Return discovered devices as ``{host: identity}``."""
    return await hass.async_add_executor_job(_blocking_discover)

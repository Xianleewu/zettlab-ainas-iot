"""Constants for the Zettlab AINAS integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "zettlab_ainas"
MANUFACTURER: Final = "Zettlab"

# Config entry / flow keys.
CONF_HOST: Final = "host"
CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"
CONF_REMOTE_ID: Final = "remote_id"
CONF_VERIFY_SSL: Final = "verify_ssl"
CONF_SCAN_INTERVAL: Final = "scan_interval"

# Defaults. ZettOS gateway serves both :80 and :443 with a self-signed cert,
# so TLS verification is off by default.
DEFAULT_VERIFY_SSL: Final = False
DEFAULT_SCAN_INTERVAL: Final = 30
MIN_SCAN_INTERVAL: Final = 10
DEFAULT_UPDATE_INTERVAL: Final = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

# UDP broadcast discovery (native ZettOS protocol). The device listens on this
# port; the exact probe payload used by the official app is NOT yet decoded, so
# DISCOVERY_PROBE is a placeholder — until it is captured, discovery yields
# nothing and the user falls back to manual host / remote-ID entry.
DISCOVERY_UDP_PORT: Final = 9527
DISCOVERY_PROBE: Final = b""  # TODO: capture the real probe from the Zettlab app
DISCOVERY_TIMEOUT: Final = 3.0

# Cloud relay for remote-ID access.
CLOUD_IOT_URL: Final = "https://iot.zettlab.com"

# Troubleshooting

> [English](troubleshooting.md) · [简体中文](troubleshooting.zh-Hans.md)

## Common issues

### "Failed to connect" (cannot_connect)

- Open `https://<nas-ip>` in a browser from the same network — it must load.
- Confirm Home Assistant and the NAS are on the same LAN / routable subnet.
- Make sure you typed the IP, not a hostname that doesn't resolve in HA.

### "Invalid username or password" (invalid_auth)

- Use the exact credentials from the NAS web UI (default username `admin`).
- If you use two-factor or email login on the device, use the local
  username/password account.

### Re-authentication requested

Your NAS password changed. Click the notification in *Settings → Devices &
Services* and enter the new password.

### Entities show "unavailable"

- The device may be rebooting or off the network — entities recover on the next
  successful poll.
- Check the connection and that the NAS web UI is reachable.

## Enable debug logging

Add to `configuration.yaml`, then restart:

```yaml
logger:
  default: warning
  logs:
    custom_components.zettlab_ainas: debug
```

## Download diagnostics

On the device page, use the three-dot menu → **Download diagnostics**. Secrets
(password, serial, MAC) are redacted automatically. Attach this file when
reporting a bug.

## Known limitations

- **Remote access** isn't supported in-integration — use VPN / reverse proxy /
  Home Assistant Cloud to reach the NAS remotely.
- **Screen brightness** can't be set (device exposes on/off only).
- **Fan-mode** options are raw integers until the labels are decoded.

## Still stuck?

Open an issue: https://github.com/xianleewu/zettlab-ainas-iot/issues — include your
HA version, the device model & firmware, debug logs and diagnostics.

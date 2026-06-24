# Configuration

> [English](configuration.md) · [简体中文](configuration.zh-Hans.md)

## Adding the integration

**Settings → Devices & Services → Add Integration → Zettlab AINAS.** You'll be
offered three ways to add the device:

1. **Discover on the network** — automatically finds Zettlab devices on your LAN.
2. **Enter IP address** — if discovery finds nothing, type the NAS IP (e.g.
   `192.168.1.50`). The address is validated against the device before continuing.
3. **Use remote-access ID** — placeholder; see the README's *Known limitations*.

Then **sign in** with your NAS web username and password (the same account you use
at `https://<nas-ip>`, default username `admin`).

## Credentials & security

- The password is sent to the device **RSA-encrypted** (the device's public key),
  exactly like the web UI; the device returns a short-lived token that is refreshed
  automatically.
- Credentials are stored in the Home Assistant config entry and never sent
  anywhere except your NAS.
- ZettOS uses a self-signed TLS certificate, so certificate verification is off by
  default for the local connection.

## Options

Open the integration's **⚙️ Configure** dialog to set:

- **Polling interval** — how often Home Assistant refreshes data. Default `30`
  seconds, minimum `10`. Lower values are more responsive but add device load.

Changing options reloads the integration automatically.

## Re-authentication

If your NAS password changes, the integration will request **re-authentication** —
a notification appears in *Settings → Devices & Services*. Click it and enter the
new credentials; no need to remove and re-add the device.

## Multiple devices

You can add several NAS units — each becomes its own device, keyed by serial
number, so adding the same NAS twice is prevented automatically.

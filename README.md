<p align="center">
  <img src="assets/logo.png" alt="Zettlab" width="120">
</p>

<h1 align="center">Zettlab AINAS for Home Assistant</h1>

<p align="center">
  <b>English</b> · <a href="README.zh-Hans.md">简体中文</a>
</p>

<p align="center">
  Monitor and control your <a href="https://zettlab.com">Zettlab</a> AI-NAS (ZettOS) from Home Assistant — storage pools, disk health, CPU/NPU/GPU, fans, the RGB status LED and the screen, all over the local network.
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom"></a>
  <a href="https://github.com/xianleewu/zettlab-ainas-iot/actions/workflows/validate.yml"><img src="https://github.com/xianleewu/zettlab-ainas-iot/actions/workflows/validate.yml/badge.svg" alt="Validate"></a>
  <a href="https://github.com/xianleewu/zettlab-ainas-iot/actions/workflows/test.yml"><img src="https://github.com/xianleewu/zettlab-ainas-iot/actions/workflows/test.yml/badge.svg" alt="Tests"></a>
  <a href="https://github.com/xianleewu/zettlab-ainas-iot/releases"><img src="https://img.shields.io/github/v/release/xianleewu/zettlab-ainas-iot?display_name=tag" alt="Release"></a>
  <img src="https://img.shields.io/badge/Home%20Assistant-2024.12%2B-41BDF5?logo=home-assistant&logoColor=white" alt="HA 2024.12+">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/xianleewu/zettlab-ainas-iot" alt="License: MIT"></a>
</p>

---

## ✨ Features

- 📊 **System monitoring** — CPU usage & temperature, NPU/GPU usage, memory usage and used bytes.
- 💾 **Storage** — per-pool capacity / used / usage %, RAID problem state, and per-disk temperature.
- 🌬️ **Fan control** — read and switch the fan mode.
- 💡 **RGB status LED** — full color control as a Home Assistant light.
- 🖥️ **Screen** — turn the device LCD on/off.
- 🔐 **Local & private** — talks only to the NAS over your LAN (RSA-encrypted login, no cloud).
- 🧩 **One device, many entities** — everything grouped under a single HA device, with diagnostics.
- 🌍 **Bilingual** — English and 简体中文 UI translations included.

> Looking for the full list? See the **[entity reference](docs/entities.md)**.

## 📦 Supported devices

| Model | Tested | Notes |
|-------|:------:|-------|
| Zettlab **D4** | ✅ | ZettOS 1.9.0-beta |
| Zettlab **D6 Ultra** | ✅ | ZettOS 1.9.1-beta |
| Other ZettOS models | ⚠️ | Same API — expected to work; please report success/issues |

The integration is **model-agnostic**: it reads the model, serial and firmware from
the device, so new ZettOS models should work without code changes.

## ✅ Requirements

- Home Assistant **2024.12** or newer.
- The NAS reachable on your local network (same LAN / routable IP).
- Your NAS web credentials (the account you use at `https://<nas-ip>`, default username `admin`).

## 🚀 Installation

### HACS (recommended)

1. In HACS, open the three-dot menu → **Custom repositories**.
2. Add `https://github.com/xianleewu/zettlab-ainas-iot` with category **Integration**.
3. Search for **Zettlab AINAS**, install it, and **restart Home Assistant**.

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=xianleewu&repository=zettlab-ainas-iot&category=integration)

### Manual

1. Copy `custom_components/zettlab_ainas` into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## ⚙️ Configuration

Add the integration from the UI — no YAML required:

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=zettlab_ainas)

Or go to **Settings → Devices & Services → Add Integration → Zettlab AINAS**. You
will be guided through three ways to add the device:

1. **Discover on the network** — find devices automatically.
2. **Enter IP address** — if discovery doesn't find it, type the NAS IP.
3. **Use remote-access ID** — *placeholder, see [limitations](#-known-limitations--roadmap)*.

Then sign in with your NAS web username and password. Credentials are stored
encrypted in the config entry and never leave your Home Assistant instance.

**Options** (⚙️ on the integration card): change the **polling interval**
(default 30 s, minimum 10 s).

See the **[configuration guide](docs/configuration.md)** for details.

## 🧩 Entities

A single device is created with, among others:

| Platform | Entity | Source |
|----------|--------|--------|
| `sensor` | CPU usage / temperature, NPU·GPU usage, Memory usage / used | realtime monitor |
| `sensor` | Pool capacity / used / usage %, Disk temperature (per disk) | storage pool |
| `sensor` | Last boot (diagnostic) | device info |
| `binary_sensor` | Pool problem | storage pool |
| `select` | Fan mode | fan |
| `light` | Status LED (RGB) | LED |
| `switch` | Screen on/off | LCD |

Full table with units and notes: **[docs/entities.md](docs/entities.md)**.

## ⚠️ Known limitations & roadmap

- **Remote access (remote ID)** — onboarding step is scaffolded only. Zettlab
  remote access uses a cloud account + P2P tunnel and exposes no reusable local
  API, so reach your NAS remotely with the usual HA options (VPN / reverse proxy
  / Home Assistant Cloud). Tracked for a future release.
- **Screen brightness** — the device exposes on/off but no brightness setter via
  the API; only the on/off `switch` is provided.
- **Fan-mode labels** — the mode values are integers (the human labels aren't yet
  decoded); options are shown as raw modes for now.
- **Reboot / shutdown buttons** — endpoints not yet mapped.

See [CHANGELOG.md](CHANGELOG.md) for release history.

## 🩺 Troubleshooting

- **Can't connect / cannot_connect** — confirm `https://<nas-ip>` opens in a
  browser and the device is on the same network.
- **Invalid auth** — use the same username/password as the NAS web UI.
- **Re-authentication requested** — your password changed; just sign in again.

More in **[docs/troubleshooting.md](docs/troubleshooting.md)**. To file a bug,
download diagnostics from the device page and attach them.

## 🤝 Contributing

Contributions are welcome! Please read **[CONTRIBUTING.md](CONTRIBUTING.md)** for
the dev setup, tests and coding standards.

## 📄 License

Released under the [MIT License](LICENSE).

> Not an official Zettlab product. "Zettlab" and "ZettOS" are trademarks of their
> respective owners. Use at your own risk.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status — READ FIRST

A working **v0.1.0 scaffold is implemented** under `custom_components/zettlab_ainas/`
(as of 2026-06-24): API client, coordinator, 3-step config flow, and
sensor/binary_sensor/select/light/switch platforms — 17 tests passing, ~85%
coverage, ruff-clean. This file is the **design + API contract** behind it: the
device API was reverse-engineered from real hardware (D4 + D6 Ultra) and verified,
so the code is grounded, not guessed. Keep this doc in sync as the code evolves.

- **Scope:** a Home Assistant **custom integration** (Python `custom_components/`,
  HACS-distributable) for **Zettlab AINAS** AI-NAS devices, which run **ZettOS**.
- **Integration domain:** `zettlab_ainas`. `iot_class: local_polling`.
- **Model-agnostic:** one integration covers all ZettOS models (verified on
  **Zettlab D4** @ ZettOS 1.9.0-beta and **Zettlab D6 Ultra** @ 1.9.1-beta —
  identical API surface, different hardware). Never hard-code a model.
- **Independent project.** The shared git root `/home/zettos/workspace/project`
  also holds unrelated embedded-C projects (`clawmate-*`, etc.). Do **not** borrow
  from them. The kernel-C / `high-performance.md` rules do **not** apply — this is
  async Python; follow `~/.claude/rules/python/` + `~/.claude/rules/common/`.
- **Test devices + credentials are not in this repo** (security). They live in
  local agent memory; ask if you need them. Never commit device IPs/passwords.

## What the device is (verified hardware)

ZettOS is a microservice NAS platform on Rockchip RK3588 (aarch64, Debian 12).
A single Go **`zettos-gateway`** binds :80/:443 and reverse-proxies many backend
services (`zettos-system-settings`, `zettos-local-storage`, `zettos-monitor`,
`zettos-ota`, …) on `127.0.0.1`. The integration talks **only** to the gateway's
authenticated HTTP API — never SSH or sysfs.

Hardware exposed (D4): RK3588 8-core + Mali-G610 + 6-TOPS NPU, 16 GB RAM; 7
thermal zones; **2 PWM fans** (RPM + duty); **backlight** 0–255 (LCD); **RGB
status LED**; disks → `mdadm` RAID → `bcache` → `btrfs` pools at `/zettos/pool/N`;
optional UPS (NUT, `_nut._tcp:3493`).

## ZettOS HTTP API contract (verified)

Base URL `https://<host>` (self-signed TLS → the client must allow it, or pin the
device cert). All JSON responses use the envelope `{"code":200,"data":...}`;
**`code != 200` is an error** (e.g. `10020` bad-login, `14502` SMART-not-ready).

**Auth (this is the tricky part):**
1. `GET /zettos/main/user/v1/public_key` (no auth) → `data.public_key` (RSA PEM),
   `data.version`.
2. RSA-**PKCS1 v1.5**-encrypt the password with that key, base64 it.
3. `POST /zettos/main/user/v1/login` with `{"username":"admin","password":"<b64>"}`
   → `data.token.access_token` (JWT ES256), `data.token.expires_at` (~3 h).
4. **Send the token on every request as header `Authorization: <token>` — with NO
   `Bearer ` prefix** (that 401s). `Token: <token>` also works.

Entity-relevant endpoints (all `GET` unless noted; prefix `/zettos/main`):

| Endpoint | Returns (key fields) |
|---|---|
| `…/system-settings/v1/device` | `model_name, device_name, sn, system_version, cpu, gpu, npu, memory, mac_address1/2, ip_address2, power_time, last_start_time` |
| `…/system-settings/v1/device/beScan` *(no auth)* | `model_name, device_name, sn, remote_access_id, ip_address2, system_version, is_init` — used for **discovery** |
| `…/system-settings/v1/storage-pool` | `[{name,status,total_size,used_size,type(raid…),total_devices_number,progress,disks:[{model,serial_number,slot,size,type,status,temperature,is_support_smart,real_path}],hot_spare_disks,ssd_cache_*}]` — **pool + per-disk in one call** |
| `…/system-settings/v1/storage-pool/user_pools` | `[{pool_name,quota}]` |
| `/zettos/monitor/v1/view` *(note: NOT under `/main`)* | realtime: `cpu:{usage_rate,thermal}`, `npu:[…]`, `gpu:[…]`, `mem:{total,free,used,cache,…}`, `disks:{"DISK A":{read_rate,write_rate,read_bytes,write_bytes},…}` |
| `…/system-settings/v1/fan` | GET → `data` = fan-mode int (e.g. `2`). **Set:** `POST …/v1/fan/{mode}` (mode in the URL path, no body) |
| `…/system-settings/v1/lcd` | GET → `{status:1}` (screen on/off). **Set:** `POST …/v1/lcd` `{enable:<bool>}` — **on/off only; no brightness setter exists in the web API** |
| `…/system-settings/v1/light` | GET → `{mode,last_mode,start_color:"#RRGGBB",end_color:"#RRGGBB",speed}`. **Set:** `POST …/v1/light` with that same object — **RGB LED** |
| `…/system-settings/v1/device/smart/{start(POST),status,statusAsync,info,stop}` | async SMART; `info` is `14502` until a scan has run |
| `…/system-settings/v1/ups/status/` *(no auth)* | UPS status (when a UPS is attached) |
| `…/system-settings/v1/system/configs` | `{ai_threshold,default_personal_pool,firmware_id,…}` |
| `…/local-storage/v1/storage/list` | team/share folders per pool |
| `…/local-storage/v1/disks`, `…/disks/size`, `…/disks/usb` | disk inventory |

**Write contracts** (extracted from the `mfFiles` JS bundle —
`api.setFanMode/setLcd/setLight`): fan = `POST …/v1/fan/{mode}`; lcd =
`POST …/v1/lcd {enable}`; light = `POST …/v1/light {mode,start_color,end_color,
speed}`. The on-device config mirrors live state in
`/zettos/emmc/config/{fan_mode,fan1_speed,fan2_speed,lcd_brightness,light_mode}`.
Fan-mode integer enum is not yet decoded (current value `2`); screen **brightness**
(`lcd_brightness=255`) has **no HTTP setter** — likely device-local only.

## Proposed HA entity model (← map each to the API above)

- **sensor:** CPU usage-% + temperature, NPU/GPU usage, memory used/free/%
  (← `monitor/v1/view`); per-disk read/write throughput (← `monitor/v1/view`);
  per-pool total/used/free/usage-%; per-disk temperature (×N) + status; pool RAID
  status + rebuild progress; device uptime (`last_start_time`); UPS load/charge
  (if present); `system_version` (diagnostic).
- **binary_sensor:** pool healthy; disk healthy / SMART-ok; UPS online; device
  reachable.
- **select:** `fan_mode` ← `POST …/v1/fan/{mode}` (decode the int enum first).
- **light:** RGB status LED — `rgb_color` ← start/end color, `effect` ← `mode`,
  via `POST …/v1/light`.
- **switch:** screen on/off ← `POST …/v1/lcd {enable}`. (No brightness `number`
  entity — no HTTP setter; revisit if one is found.)
- **button:** SMART scan (`device/smart/start`); reboot/shutdown (endpoints not in
  the web bundles — capture via Playwright interception of the quick-panel).
- **update:** firmware via `zettos-ota` (`firmware_id` in `system/configs`).
- **DeviceInfo:** `identifiers={sn}`, `manufacturer="Zettlab"`,
  `model=model_name`, `name=device_name`, `sw_version=system_version`,
  `connections=mac_address*`.

## Discovery (config_flow)

The device's native discovery is **UDP broadcast on port 9527** (handled by
`zettos-system-settings`) **+ HTTP LAN scan** — match the user's two mechanisms:
- **LAN scan (reliable, implement first):** probe `https://<ip>/zettos/main/
  system-settings/v1/device/beScan` (no auth) across the subnet; a ZettOS reply
  identifies model/sn/version. Drives both manual setup and a "scan" step.
- **UDP 9527 broadcast:** native fast discovery; packet format not yet captured
  (sniff the official app or `zettos-system-settings` to replicate).
- mDNS/zeroconf is **not** reliable here (device only advertises generic
  `_smb._tcp` / TimeMachine / `_nut._tcp`), so don't rely on it as primary.

### Remote access (the "remote ID" step) — investigated, deferred

Verified architecture: remote access is **cloud-account + P2P-tunnel**, not a
reusable HTTPS proxy:
- The "my devices" portals `us-my.zettlab.com` / `cn-my.zettlab.com` require an
  OIDC **Zettlab cloud account** sign-in (`us-iam.zettlab.com`, email/Google/
  Apple) and the device must be **bound** to it (test devices show
  `cloud_account:""` = unbound).
- Those portals talk to their **own** cloud backend (`/api/v1/...`) — they do
  **not** pass through the device `/zettos/` API, so there is no stable cloud URL
  HA could reuse.
- The device reaches the cloud via a P2P tunnel client `/zettos/emmc/bin/p2p/
  pgTunnelStatic` (tunnel id `ZETTLAB0622E8786A…`; the short `remote_access_id`
  e.g. `29c3` is the pairing code). `GET …/v1/service/remote/p2p` → `false`
  (disabled by default).

Implication: full remote-ID support needs a cloud account, device binding, and
the P2P tunnel protocol — heavy and cloud-dependent. The `async_step_remote_id`
stays a clean placeholder; recommend users reach the NAS remotely via the normal
HA patterns (VPN / reverse proxy / Nabu Casa) and keep this integration on the
**local** API. Revisit only with a cloud account + bound device to capture the
flow.

## Target repository layout (HACS-compatible)

```
custom_components/zettlab_ainas/
  __init__.py        # setup/unload, entry.runtime_data = coordinator
  manifest.json      # domain, version, requirements, iot_class=local_polling
  const.py
  api/               # ZettOS client: aiohttp, RSA-login, NO homeassistant imports
  coordinator.py     # DataUpdateCoordinator — single poller
  config_flow.py     # manual host + beScan validation/scan + reauth + options
  entity.py          # shared CoordinatorEntity base + DeviceInfo (from /device)
  sensor.py binary_sensor.py number.py select.py light.py switch.py button.py update.py
  diagnostics.py strings.json translations/en.json
tests/   hacs.json   pyproject.toml   README.md
```

## Commands

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements_test.txt        # homeassistant, pytest-homeassistant-custom-component, ruff
ruff format . && ruff check . --fix
pytest                                       # full suite + coverage
pytest tests/test_config_flow.py::test_user_flow -v   # single test
pytest --cov=custom_components/zettlab_ainas --cov-report=term-missing
# CI: home-assistant/actions/hassfest@master  +  hacs/action (category: integration)
```

## Conventions

- **Async-only**; never block the loop. `aiohttp` via
  `homeassistant.helpers.aiohttp_client.async_get_clientsession`; offload any
  blocking crypto with `hass.async_add_executor_job`.
- Modern HA pattern: typed `ConfigEntry`, `entry.runtime_data` (no
  `hass.data[DOMAIN]`); coordinator wrapped errors (`UpdateFailed`,
  `ConfigEntryAuthFailed` on token/login failure → triggers reauth).
- API client is transport-only and **must not import `homeassistant`**; it raises
  its own exceptions which the coordinator translates.
- Full type hints, `from __future__ import annotations`, small focused files
  (one platform per file), validate every API response before building state.
- TDD, ≥80% coverage; mock the ZettOS transport — never hit a real device in CI.
- No secrets in code, fixtures, or this repo.
- **Docs are bilingual** (English + `*.zh-Hans.md`): `README`, `docs/{entities,
  configuration,troubleshooting}`. Update both languages plus `CHANGELOG.md` on
  any user-facing change. Brand assets (official Zettlab "Z" icon) live in
  `assets/`; for the icon to show in the HA/HACS UI, submit `icon.png`/`logo.png`
  to the `home-assistant/brands` repo.

## Open items to capture before/while implementing

1. **Fan-mode integer enum** (current `2`) — try each `POST …/v1/fan/{n}` and
   read back, or decode from firmware, to label the `select` options.
2. **reboot / shutdown / scrub** endpoints — not in the web bundles; capture via
   Playwright route-interception when clicking the desktop quick-panel
   重启/关机 (stub the response so the device doesn't actually reboot).
3. **UDP 9527** discovery packet format (only if implementing native broadcast;
   the HTTP `beScan` LAN scan is sufficient for v1).
4. Whether screen **brightness** is settable at all via any service.

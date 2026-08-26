# Entity reference

> [English](entities.md) · [简体中文](entities.zh-Hans.md)

All entities belong to a single Home Assistant device (identified by the NAS
serial number). Entity IDs are prefixed with your device name, e.g.
`sensor.<device>_cpu_usage`.

## Sensors

| Entity | Unit | Device class | Default | Source |
|--------|------|--------------|:------:|--------|
| CPU usage | % | — | on | `monitor/v1/view` → `cpu.usage_rate` |
| CPU temperature | °C | temperature | on | `monitor/v1/view` → `cpu.thermal` |
| Memory usage | % | — | on | `monitor/v1/view` → `mem.used / mem.total` |
| Memory used | GiB | data size | on | `monitor/v1/view` → `mem.used` |
| Memory free | GiB | data size | on | `monitor/v1/view` → `mem.free` |
| Memory cache | GiB | data size | on | `monitor/v1/view` → `mem.cache` |
| Memory total | GiB | data size | on | `monitor/v1/view` → `mem.total` |
| NPU usage | % | — | **off** | `monitor/v1/view` → `npu[]` (averaged) |
| GPU usage | % | — | **off** | `monitor/v1/view` → `gpu[]` |
| Fan _N_ speed | rpm | — | on | `monitor/v1/view` → `fan_speed[]` |
| Disk _N_ read/write rate | B/s | data rate | on | delta of `disks[].read_bytes/write_bytes` |
| Network _N_ upload/download rate | B/s | data rate | on | delta of `nets[].bytes_sent/bytes_recv` |
| Last boot | timestamp | timestamp | on (diagnostic) | `device` → `last_start_time` |
| Pool _N_ usage | % | — | on | `storage-pool` → `used_size / total_size` |
| Pool _N_ used | GiB | data size | on | `storage-pool` → `used_size` |
| Pool _N_ free | GiB | data size | on | `storage-pool` → `total_size - used_size` |
| Pool _N_ capacity | GiB | data size | on | `storage-pool` → `total_size` |
| Disk _SERIAL_ temperature | °C | temperature | on | `storage-pool` → `disks[].temperature` |

Disk temperature sensors expose extra attributes: `model`, `slot`, `type`, `path`.

NPU and GPU sensors are **disabled by default** (often idle at 0); enable them on
the entity page if you want them.

Fan, disk-I/O and network entities are created according to the arrays/maps the
device returns, so models with two or three fans work without model-specific
configuration. Transfer-rate sensors are `unknown` for the first poll because
two counter samples are required; subsequent values are current bytes per second.

## Binary sensors

| Entity | Device class | On when | Source |
|--------|--------------|---------|--------|
| Pool _N_ problem | problem | pool `status` ≠ 0 | `storage-pool` |

## Controls

| Entity | Platform | Behaviour | Source |
|--------|----------|-----------|--------|
| Fan mode | `select` | Choose the fan mode (raw integer values until labels are decoded) | `POST fan/{mode}` |
| Status LED | `light` | RGB color; "off" sets the LED to black. The device effect mode & speed are preserved and shown as attributes | `POST light` |
| Screen | `switch` | Turn the device LCD on/off | `POST lcd {enable}` |

## Notes

- Dynamic entities (fans, pools, disks and network interfaces) are created from
  the device state at setup time. If the hardware changes later, reload the
  integration to pick it up.
- There is no brightness control: the device exposes screen on/off only.

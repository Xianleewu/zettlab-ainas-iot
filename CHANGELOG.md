# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-24

Initial release.

### Added

- Local-polling integration for Zettlab AINAS (ZettOS) devices, verified on
  **Zettlab D4** and **D6 Ultra**; model-agnostic.
- ZettOS API client with RSA-encrypted login and JSON envelope handling.
- Config flow with three onboarding paths: network discovery, manual IP, and a
  remote-access-ID placeholder; plus re-authentication and an options flow
  (polling interval).
- Entities:
  - `sensor`: CPU usage & temperature, NPU/GPU usage, memory usage & used,
    per-pool capacity/used/usage, per-disk temperature, last boot.
  - `binary_sensor`: storage-pool problem.
  - `select`: fan mode.
  - `light`: RGB status LED.
  - `switch`: screen on/off.
- Diagnostics with secret redaction.
- English and Simplified Chinese translations.

### Known limitations

- Remote access via remote ID is scaffolded only (cloud + P2P, not implemented).
- No screen-brightness control (device exposes on/off only via the API).
- Fan-mode options are shown as raw integers (labels not yet decoded).

[Unreleased]: https://github.com/xianleewu/zettlab-ainas-iot/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/xianleewu/zettlab-ainas-iot/releases/tag/v0.1.0

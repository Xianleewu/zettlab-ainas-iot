#!/usr/bin/env python3
"""Live end-to-end check against a real Zettlab AINAS device.

Exercises the integration's actual API client (no Home Assistant required) and
prints the values the entities would expose. Useful for verifying a new model or
firmware before/after changing the integration.

Usage:
    python scripts/live_check.py <host> [username]
    # password is read from the ZETTLAB_PASS environment variable

Example:
    ZETTLAB_PASS=secret python scripts/live_check.py 192.168.1.50
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import aiohttp

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent / "custom_components" / "zettlab_ainas"),
)

from api import ZettOSClient


async def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    host = sys.argv[1]
    user = sys.argv[2] if len(sys.argv) > 2 else "admin"
    password = os.environ.get("ZETTLAB_PASS")
    if not password:
        print("error: set the ZETTLAB_PASS environment variable", file=sys.stderr)
        return 2

    async with aiohttp.ClientSession() as session:
        client = ZettOSClient(host, user, password, session, verify_ssl=False)
        await client.async_login()
        device = await client.async_get_device()
        pools = await client.async_get_storage_pools()
        monitor = await client.async_get_monitor()
        fan = await client.async_get_fan_mode()
        lcd = await client.async_get_lcd()
        light = await client.async_get_light()

    cpu = monitor.get("cpu", {})
    mem = monitor.get("mem", {})
    mem_pct = round(mem.get("used", 0) / mem.get("total", 1) * 100, 1)
    print(f"== {host} ==")
    print(
        f"device : {device.get('model_name')} | sn={device.get('sn')} | fw={device.get('system_version')}"
    )
    print(
        f"monitor: cpu={cpu.get('usage_rate')}% temp={cpu.get('thermal')}C mem={mem_pct}%"
    )
    for pool in pools:
        used = round(pool.get("used_size", 0) / pool.get("total_size", 1) * 100, 1)
        disks = [d for d in pool.get("disks", []) if d.get("serial_number")]
        print(
            f"pool   : {pool.get('name')} {used}% used  type={pool.get('type')} disks={len(disks)}"
        )
        for disk in disks:
            print(
                f"  disk : slot{disk.get('slot')} {disk.get('model')} {disk.get('temperature')}C"
            )
    print(f"fan    : mode={fan}")
    print(f"lcd    : {lcd}")
    print(f"light  : mode={light.get('mode')} color={light.get('start_color')}")
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

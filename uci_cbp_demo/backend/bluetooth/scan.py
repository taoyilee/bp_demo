#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
import logging
from typing import List

from bleak.backends.device import BLEDevice

logger = logging.getLogger("bp_demo")


def check_adaptor() -> bool:
    import asyncio
    from bleak import discover
    mac_addresses = []

    async def run():
        devices = await discover()
        mac_addresses.extend(devices)

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run())
    except Exception as e:
        if str(e) == "Bluetooth adapter not found":
            return False
        raise e
    return True


def scan() -> List[BLEDevice]:
    import asyncio
    from bleak import discover
    mac_addresses = []

    async def run():
        devices = await discover()
        mac_addresses.extend(devices)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    return mac_addresses

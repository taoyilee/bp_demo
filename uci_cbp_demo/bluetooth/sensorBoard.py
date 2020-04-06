#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
import asyncio
import logging

import txdbus.error
from bleak import BleakClient

from uci_cbp_demo.bluetooth.callbacks import CapCallback
from uci_cbp_demo.bluetooth.constants import CAP1_CHAR_UUID, CAP2_CHAR_UUID

logger = logging.getLogger("bp_demo")


class SensorBoard:
    _cap1_callback = CapCallback()
    _cap2_callback = CapCallback()

    def __init__(self, addr, pipe):
        self.addr = addr
        self.pipe = pipe

    async def stop_cap1_notify(self, client):
        try:
            while True:
                await client.stop_notify(CAP1_CHAR_UUID)
                await asyncio.sleep(1)
        except txdbus.error.RemoteError:
            pass

    async def stop_cap2_notify(self, client):
        try:
            while True:
                await client.stop_notify(CAP2_CHAR_UUID)
                await asyncio.sleep(1)
        except txdbus.error.RemoteError:
            pass

    async def while_loop(self, keyboard_interrupt=True):
        while True:
            if keyboard_interrupt and self.pipe.poll():
                break
            await asyncio.sleep(1)

    async def notify_cap1(self, loop, keyboard_interrupt=True):
        logger.info(f"Notify characteristics of device {self.addr}")
        async with BleakClient(self.addr, loop=loop) as client:
            x = await client.is_connected()
            logger.info(f"Connected: {x}")
            self.pipe.send("connected")
            await client.start_notify(CAP1_CHAR_UUID, self.cap1_callback)
            await self.while_loop(keyboard_interrupt)
            logger.info("Stopping notification...")
            await client.stop_notify(CAP1_CHAR_UUID)

    async def notify_cap2(self, loop, keyboard_interrupt=True):
        logger.info(f"Notify characteristics of device {self.addr}")
        async with BleakClient(self.addr, loop=loop) as client:
            x = await client.is_connected()
            logger.info(f"Connected: {x}")
            self.pipe.send("connected")
            await client.start_notify(CAP2_CHAR_UUID, self.cap2_callback)
            await self.while_loop(keyboard_interrupt)
            logger.info("Stopping notification...")
            await client.stop_notify(CAP2_CHAR_UUID)

    async def notify_both(self, loop, keyboard_interrupt=True):
        logger.info(f"Notify characteristics of device {self.addr}")
        client = BleakClient(self.addr, loop=loop)
        await client.connect()
        logger.info(f"Connected to {self.addr}")
        self.pipe.send("connected")
        await client.start_notify(CAP1_CHAR_UUID, self.cap1_callback)
        await client.start_notify(CAP2_CHAR_UUID, self.cap2_callback)
        await self.while_loop(keyboard_interrupt)
        logger.info("Stopping notification...")
        # await self.stop_cap1_notify(client)
        # await self.stop_cap2_notify(client)
        await client.disconnect()

    def start_cap1_notification(self, keyboard_interrupt=True):
        loop = asyncio.get_event_loop()
        # https://github.com/hbldh/bleak/issues/93; new_event_loop is not going to work.
        loop.run_until_complete(self.notify_cap1(loop, keyboard_interrupt))

    def start_cap_notification(self, keyboard_interrupt=True):
        loop = asyncio.get_event_loop()
        # https://github.com/hbldh/bleak/issues/93; new_event_loop is not going to work.
        loop.run_until_complete(self.notify_both(loop, keyboard_interrupt))

    def start_cap2_notification(self, keyboard_interrupt=True):
        loop = asyncio.get_event_loop()
        # https://github.com/hbldh/bleak/issues/93; new_event_loop is not going to work.
        loop.run_until_complete(self.notify_cap2(loop, keyboard_interrupt))

    @property
    def cap1_callback(self):
        return self._cap1_callback

    @property
    def cap2_callback(self):
        return self._cap2_callback

    @cap1_callback.setter
    def cap1_callback(self, value):
        self._cap1_callback = value

    @cap2_callback.setter
    def cap2_callback(self, value):
        self._cap2_callback = value

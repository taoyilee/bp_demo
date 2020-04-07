#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
import asyncio
import logging

import txdbus.error
from bleak import BleakClient

from uci_cbp_demo.bluetooth.callbacks import CapCallback
from uci_cbp_demo.bluetooth.constants import CAP1_CHAR_UUID, CAP2_CHAR_UUID

logger = logging.getLogger("bp_demo")


async def while_loop(pipe, wait_time=None):
    if wait_time is not None:
        await asyncio.sleep(wait_time)
    else:
        while True:
            if pipe.poll():
                break
            await asyncio.sleep(1)


async def _stop_notify_uuid(client, uuid):
    try:
        while True:
            await client.stop_notify(uuid)
            await asyncio.sleep(1)
    except txdbus.error.RemoteError:
        pass


async def _start_notify_uuid(addr, loop, pipe, uuids, callbacks, wait_time=None):
    logger.info(f"Connecting to {addr}")
    client = BleakClient(addr, loop=loop)
    await client.connect()
    logger.info(f"Connected to {client.address}")
    pipe.send("connected")
    assert len(set(uuids)) == len(uuids), "Characteristic UUIDs must be unique"
    for u, c in zip(uuids, callbacks):
        logger.info(f"Notifying {u}")
        await client.start_notify(u, c)

    await while_loop(pipe, wait_time)
    logger.info("Stopping notification...")
    for u in uuids:
        await _stop_notify_uuid(client, u)
    await client.disconnect()


def run_until_complete(f, wait_time=None):
    loop = asyncio.get_event_loop()
    # https://github.com/hbldh/bleak/issues/93; new_event_loop is not going to work.
    loop.run_until_complete(f(loop, wait_time))


class SensorBoard:
    _cap1_callback_internal = CapCallback()
    _cap2_callback_internal = CapCallback()
    _cap1_callback = None
    _cap2_callback = None

    def __init__(self, addr, pipe):
        self.addr = addr
        self.pipe = pipe

    async def notify_cap1(self, loop, wait_time=None):
        await _start_notify_uuid(self.addr, loop, self.pipe, [CAP1_CHAR_UUID], [self.cap1_callback], wait_time)

    async def notify_cap2(self, loop, wait_time=None):
        await _start_notify_uuid(self.addr, loop, self.pipe, [CAP2_CHAR_UUID], [self.cap2_callback], wait_time)

    async def notify_both(self, loop, wait_time=None):
        await _start_notify_uuid(self.addr, loop, self.pipe, [CAP1_CHAR_UUID, CAP2_CHAR_UUID],
                                 [self.cap1_callback, self.cap2_callback], wait_time)

    def start_cap1_notification(self, wait_time=None):
        run_until_complete(self.notify_cap1, wait_time)

    def start_cap_notification(self, wait_time=None):
        run_until_complete(self.notify_both, wait_time)

    def start_cap2_notification(self, wait_time=None):
        run_until_complete(self.notify_cap2, wait_time)

    @property
    def cap1_callback(self):
        if self._cap1_callback is not None:
            return lambda sender, data: self._cap1_callback(*self._cap1_callback_internal(sender, data))
        return self._cap1_callback_internal

    @property
    def cap2_callback(self):
        if self._cap2_callback is not None:
            return lambda sender, data: self._cap2_callback(*self._cap2_callback_internal(sender, data))
        return self._cap2_callback_internal

    @cap1_callback.setter
    def cap1_callback(self, value):
        assert callable(value), "callback must be callable"
        self._cap1_callback = value

    @cap2_callback.setter
    def cap2_callback(self, value):
        assert callable(value), "callback must be callable"
        self._cap2_callback = value

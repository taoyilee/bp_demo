#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
import asyncio
from multiprocessing import Pipe

from bleak import BleakClient

from uci_cbp_demo.logging import logger
from .constants import UUID


class SensorState:

    def __init__(self):
        self._session_connected = False
        self._ch1_active = False
        self._ch2_active = False
        self._ch1_enabled = False
        self._ch2_enabled = False

    def connected(self):
        self._session_connected = True

    def ch_start(self, ch):
        if getattr(self, f"_ch{ch}_enabled"):
            setattr(self, f"_ch{ch}_active", True)

    def ch_stop(self, ch):
        setattr(self, f"_ch{ch}_active", False)

    def ch_state(self, ch, state):
        setattr(self, f"_ch{ch}_active", state)

    def ch_enabled(self, ch, enabled):
        setattr(self, f"_ch{ch}_enabled", enabled)

    def stop(self):
        self.ch_stop(1)
        self.ch_stop(2)
        return True

    def resume(self):
        for c in self.caps_enabled:
            self.ch_start(c)
        return True

    @property
    def ACTIVE(self):
        return self.CH1_ACTIVE or self.CH2_ACTIVE

    @property
    def CH1_ACTIVE(self):
        return self._ch1_active

    @property
    def CH2_ACTIVE(self):
        return self._ch2_active

    @property
    def CONNECTED(self):
        return self._session_connected

    @property
    def PAUSED(self):
        return self.CONNECTED and not self.ACTIVE

    @property
    def caps_active(self):
        _caps = []
        if self._ch1_active:
            _caps.append(1)
        if self._ch2_active:
            _caps.append(2)
        return _caps

    @property
    def caps_enabled(self):
        _caps = []
        if self._ch1_enabled:
            _caps.append(1)
        if self._ch2_enabled:
            _caps.append(2)
        return _caps

    def __repr__(self):
        return f"state: {self._session_connected} {self._ch1_active} {self._ch2_active}"


async def while_loop(pipe, state, wait_time=None, client=None, callback=None):
    if wait_time is not None:
        await asyncio.sleep(wait_time)
    else:
        while True:
            if pipe.poll():
                message = pipe.recv()
                logger.info(f"Message: {message} received, {state}")
                if state.ACTIVE and message[0] in ["STOP", "PAUSE"]:
                    for c in state.caps_active:
                        logger.info(f"stopping notification of {UUID[f'cap{c}']}")
                        await client.stop_notify(UUID[f'cap{c}'])
                    state.stop()

                elif state.PAUSED and message[0] == "START":
                    for c in state.caps_enabled:
                        logger.info(f"Resuming notification of {UUID[f'cap{c}']}")
                        await client.start_notify(UUID[f'cap{c}'], callback)
                    state.resume()

                if message[0] == "CH1":
                    if message[1] != state.CH1_ACTIVE:
                        if message[1]:
                            logger.info(f"starting notification of {UUID[f'cap1']}")
                            await client.start_notify(UUID['cap1'], callback)
                        else:
                            logger.info(f"stopping notification of {UUID[f'cap1']}")
                            await client.stop_notify(UUID['cap1'])
                    state.ch_state(1, message[1])
                if message[0] == "CH2":
                    if message[1] != state.CH2_ACTIVE:
                        if message[1]:
                            logger.info(f"starting notification of {UUID[f'cap2']}")
                            await client.start_notify(UUID['cap2'], callback)
                        else:
                            logger.info(f"stopping notification of {UUID[f'cap2']}")
                            await client.stop_notify(UUID['cap2'])
                    state.ch_state(2, message[1])
                if message[0] == "STOP":
                    break
            await asyncio.sleep(1)


def invalid_message(c):
    logger.warning(f"Invalid message: {c}")


async def start_notify_uuid(addr, loop, pipe: "Pipe", callback, wait_time=None):
    state = SensorState()
    uuids = set()
    while True:
        logger.info(f"Waiting for commands")
        pipe.poll(None)
        c = pipe.recv()
        logger.info(f"{c} received")
        if c[0] == "MAC":
            logger.info(f"Address set to {c[1]}")
            addr = c[1]
        elif c[0] == "CH1" and c[1]:
            state.ch_enabled(1, c[1])
            uuids.add(UUID["cap1"])
        elif c[0] == "CH2" and c[1]:
            state.ch_enabled(2, c[1])
            uuids.add(UUID["cap2"])
        if c[0] == "CONNECT":
            break

    logger.info(f"Connecting to {addr}")
    async with BleakClient(addr, loop=loop) as client:
        logger.info(f"Connected to {client.address}")
        pipe.send(("CONNECTED", None))
        state.connected()
        await while_loop(pipe, state, wait_time, client, callback)


def run_until_complete(f, callbacks, wait_time=None):
    loop = asyncio.get_event_loop()
    # https://github.com/hbldh/bleak/issues/93; new_event_loop is not going to work.
    loop.run_until_complete(f(loop, callbacks, wait_time))

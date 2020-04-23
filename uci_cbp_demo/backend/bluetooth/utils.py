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
        self._dac1 = 0
        self._dac2 = 0

    @property
    def dac1(self):
        return [self._dac1]

    @property
    def dac2(self):
        return [self._dac2]

    @dac1.setter
    def dac1(self, value):
        self._dac1 = int(value)

    @dac2.setter
    def dac2(self, value):
        self._dac2 = int(value)

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
                command, value = pipe.recv()
                logger.info(f"Message: {command} received")
                if state.ACTIVE and command in ["STOP", "PAUSE"]:
                    for c in state.caps_active:
                        logger.info(f"stopping notification of {UUID[f'cap{c}']}")
                        await client.stop_notify(UUID[f'cap{c}'])
                    state.stop()

                elif state.PAUSED and command == "START":
                    await client.write_gatt_char(UUID[f'dac1'], getattr(state, f"dac1"))
                    await client.write_gatt_char(UUID[f'dac2'], getattr(state, f"dac2"))
                    for c in state.caps_enabled:
                        logger.info(f"Resuming notification of {UUID[f'cap{c}']}")
                        await client.start_notify(UUID[f'cap{c}'], callback)
                    state.resume()

                if command[:2] == "CH":
                    ch = command[2]
                    if value != state.CH1_ACTIVE:
                        if value:
                            logger.info(f"starting notification of {UUID[f'cap{ch}']}")
                            await client.start_notify(UUID[f'cap{ch}'], callback)
                        else:
                            logger.info(f"stopping notification of {UUID[f'cap{ch}']}")
                            await client.stop_notify(UUID[f'cap{ch}'])
                    state.ch_state(ch, value)
                if command[:3] == "DAC":
                    ch = command[3]
                    setattr(state, f"dac{ch}", value)
                    await client.write_gatt_char(UUID[f'dac{ch}'], getattr(state, f"dac{ch}"))

                if command == "STOP":
                    break
            await asyncio.sleep(1)


async def start_notify_uuid(addr, loop, pipe: "Pipe", callback, wait_time=None):
    state = SensorState()
    uuids = set()
    while True:
        logger.info(f"Waiting for commands")
        pipe.poll(None)
        command, value = pipe.recv()
        logger.info(f"{command}, {value} received")
        if command == "CONNECT":
            break

        if command == "MAC":
            logger.info(f"Address set to {value}")
            addr = value
        if command[:2] == "CH":
            ch = command[2]
            state.ch_enabled(ch, value)
            uuids.add(UUID[f"cap{ch}"])
        if command[:3] == "DAC":
            ch = command[3]
            logger.info(f"dac{ch} value set to {value}")
            setattr(state, f"dac{ch}", value)

    logger.info(f"Connecting to {addr}")
    async with BleakClient(addr, loop=loop) as client:
        logger.info(f"Connected to {client.address}")
        pipe.send(("CONNECTED", None))
        await client.write_gatt_char(UUID[f'dac1'], state.dac1)
        await client.write_gatt_char(UUID[f'dac2'], state.dac2)
        state.connected()
        await while_loop(pipe, state, wait_time, client, callback)


def run_until_complete(f, callbacks, wait_time=None):
    loop = asyncio.get_event_loop()
    # https://github.com/hbldh/bleak/issues/93; new_event_loop is not going to work.
    loop.run_until_complete(f(loop, callbacks, wait_time))

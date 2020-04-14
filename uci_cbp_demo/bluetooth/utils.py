#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
import asyncio
import logging
from multiprocessing import Pipe

from bleak import BleakClient

logger = logging.getLogger("bp_demo")


async def while_loop(pipe, wait_time=None, client=None, uuids=None, callback=None):
    state = "RUNNING"
    if wait_time is not None:
        await asyncio.sleep(wait_time)
    else:
        while True:
            if pipe.poll():
                message = pipe.recv()
                if state == "RUNNING" and message[0] == "STOP":
                    break
                elif state == "PAUSED" and message[0] == "STOP":
                    logger.info("Resuming notification")
                    for u in uuids:
                        logger.info(f"Resuming notification of {u}")
                        await client.start_notify(u, callback)
                    break
                elif state == "RUNNING" and message[0] == "PAUSE":
                    logger.info("Pausing notification")
                    state = "PAUSED"
                    for u in uuids:
                        await client.stop_notify(u)
                elif state == "PAUSED" and message[0] == "CONNECT":
                    state = "RUNNING"
                    logger.info("Resuming notification")
                    for u in uuids:
                        logger.info(f"Resuming notification of {u}")
                        await client.start_notify(u, callback)
            await asyncio.sleep(1)


def invalid_message(c):
    logger.warning(f"Invalid message: {c}")


async def _start_notify_uuid(addr, loop, pipe: "Pipe", uuids, callback, wait_time=None):
    connected = False
    while not connected:
        logger.info(f"Waiting for commands")
        pipe.poll(None)
        c = pipe.recv()
        logger.info(f"{c} received")
        if c[0] == "MAC":
            logger.info(f"Address set to {c[1]}")
            addr = c[1]
            pipe.poll(None)
            c = pipe.recv()
            if c[0] == "CONNECT":
                connected = True
            else:
                invalid_message(c)
        elif c[0] == "CONNECT":
            connected = True
        else:
            invalid_message(c)

    logger.info(f"Connecting to {addr}")
    async with BleakClient(addr, loop=loop) as client:
        logger.info(f"Connected to {client.address}")
        pipe.send("connected")
        assert len(set(uuids)) == len(uuids), "Characteristic UUIDs must be unique"

        for u  in  uuids:
            logger.info(f"Notifying {u}")
            await client.start_notify(u, callback)

        await while_loop(pipe, wait_time, client, uuids, callback)
        logger.info("Stopping notification...")
        try:
            for u in uuids:
                await client.stop_notify(u)
        except Exception as e:
            logger.warning(f"Notification has been stopped already ?? {str(e)}")


def run_until_complete(f, callbacks, wait_time=None):
    loop = asyncio.get_event_loop()
    # https://github.com/hbldh/bleak/issues/93; new_event_loop is not going to work.
    loop.run_until_complete(f(loop, callbacks, wait_time))

#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
import logging

from .bluetooth.callbacks import CapCallback
from .bluetooth.utils import start_notify_uuid, run_until_complete

logger = logging.getLogger("bp_demo")


class SensorBoard:

    def __init__(self, addr, pipe):
        self.addr = addr
        self.pipe = pipe

    async def _notify(self, loop, callbacks, wait_time=None):
        await start_notify_uuid(self.addr, loop, self.pipe, callbacks, wait_time)

    def start_session(self, queues=None, wait_time=None):
        logger.info("Setting Up Bluetooth")
        callback = CapCallback(queue=queues)
        run_until_complete(self._notify, callback, wait_time)

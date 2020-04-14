#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
import logging

from uci_cbp_demo.bluetooth.callbacks import CapCallback
from uci_cbp_demo.bluetooth.constants import CAP1_CHAR_UUID, CAP2_CHAR_UUID
from .utils import _start_notify_uuid, run_until_complete

logger = logging.getLogger("bp_demo")


class SensorBoard:
    _cap1_callback = None
    _cap2_callback = None

    def __init__(self, addr, pipe):
        self.addr = addr
        self.pipe = pipe

    async def notify_cap1(self, loop, callbacks, wait_time=None):
        await _start_notify_uuid(self.addr, loop, self.pipe,
                                 [CAP1_CHAR_UUID], callbacks, wait_time)

    async def notify_cap2(self, loop, callbacks, wait_time=None):
        await _start_notify_uuid(self.addr, loop, self.pipe,
                                 [CAP2_CHAR_UUID], callbacks, wait_time)

    async def notify_both(self, loop, callbacks, wait_time=None):
        await _start_notify_uuid(self.addr, loop, self.pipe,
                                 [CAP1_CHAR_UUID, CAP2_CHAR_UUID],
                                 callbacks, wait_time)

    def start_cap1_notification(self, queues=None, wait_time=None):
        callback = CapCallback(queue=queues)
        run_until_complete(self.notify_cap1, callback, wait_time)

    def start_cap2_notification(self, queues=None, wait_time=None):
        callback = CapCallback(queue=queues)
        run_until_complete(self.notify_cap2, callback, wait_time)

    def start_cap_notification(self, queues=None, wait_time=None):
        callback = CapCallback(queue=queues)
        run_until_complete(self.notify_both, callback, wait_time)

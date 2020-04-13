#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
import logging

from uci_cbp_demo.bluetooth.callbacks import CapCallback, IMUCallback, AccData, MagData, GyroData
from uci_cbp_demo.bluetooth.constants import CAP1_CHAR_UUID, CAP2_CHAR_UUID, ACC_CHAR_UUID, GYRO_CHAR_UUID, \
    MAG_CHAR_UUID
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
                                 [CAP1_CHAR_UUID, ACC_CHAR_UUID, GYRO_CHAR_UUID, MAG_CHAR_UUID], callbacks, wait_time)

    async def notify_cap2(self, loop, callbacks, wait_time=None):
        await _start_notify_uuid(self.addr, loop, self.pipe,
                                 [CAP2_CHAR_UUID, ACC_CHAR_UUID, GYRO_CHAR_UUID, MAG_CHAR_UUID], callbacks, wait_time)

    async def notify_both(self, loop, callbacks, wait_time=None):
        await _start_notify_uuid(self.addr, loop, self.pipe,
                                 [CAP1_CHAR_UUID, CAP2_CHAR_UUID, ACC_CHAR_UUID, GYRO_CHAR_UUID, MAG_CHAR_UUID],
                                 callbacks, wait_time)

    async def notify_acc(self, loop, callbacks, wait_time=None):
        await _start_notify_uuid(self.addr, loop, self.pipe, [ACC_CHAR_UUID], callbacks, wait_time)

    async def notify_gyro(self, loop, callbacks, wait_time=None):
        await _start_notify_uuid(self.addr, loop, self.pipe, [GYRO_CHAR_UUID], callbacks, wait_time)

    async def notify_mag(self, loop, callbacks, wait_time=None):
        await _start_notify_uuid(self.addr, loop, self.pipe, [MAG_CHAR_UUID], callbacks, wait_time)

    def start_acc_notification(self, queues=None, wait_time=None):
        callbacks = [IMUCallback(AccData, queues['acc'])] if queues is not None else [IMUCallback(AccData)]
        run_until_complete(self.notify_acc, callbacks, wait_time)

    def start_gyro_notification(self, queues=None, wait_time=None):
        callbacks = [IMUCallback(GyroData, queues['gyro'])] if queues is not None else [IMUCallback(GyroData)]
        run_until_complete(self.notify_gyro, callbacks, wait_time)

    def start_mag_notification(self, queues=None, wait_time=None):
        callbacks = [IMUCallback(MagData, queues['mag'])] if queues is not None else [IMUCallback(MagData)]
        run_until_complete(self.notify_mag, callbacks, wait_time)

    def start_cap1_notification(self, queues=None, wait_time=None):
        callbacks = [CapCallback(v) for k, v in queues.items()] if queues is not None else [CapCallback()]
        run_until_complete(self.notify_cap1, callbacks, wait_time)

    def start_cap2_notification(self, queues=None, wait_time=None):
        callbacks = [CapCallback(v) for k, v in queues.items()] if queues is not None else [CapCallback()]
        run_until_complete(self.notify_cap2, callbacks, wait_time)

    def start_cap_notification(self, queues=None, wait_time=None):
        if queues is not None:
            callbacks = [CapCallback(queues['cap1']),
                         CapCallback(queues['cap2']),
                         # IMUCallback(AccData, queues['acc']),
                         # IMUCallback(GyroData, queues['gyro']),
                         # IMUCallback(MagData, queues['mag'])
                         ]
        else:
            callbacks = [CapCallback(), CapCallback(),
                         # IMUCallback(AccData), IMUCallback(GyroData), IMUCallback(MagData)
                         ]
        run_until_complete(self.notify_both, callbacks, wait_time)

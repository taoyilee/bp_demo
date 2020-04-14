# MIT License
# Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)

import logging
import multiprocessing
import select
import struct
import sys

import numpy as np

from uci_cbp_demo.bluetooth.constants import CAP1_CHAR_UUID
from uci_cbp_demo.bluetooth.constants import CLK_PERIOD
from uci_cbp_demo.datastructures import IterableQueue

logger = logging.getLogger("bp_demo")


class IMUData:

    def __init__(self, time, x, y, z):
        self.time = time
        self.x = x
        self.y = y
        self.z = z


class CapData:
    time = None
    cap = None
    channel = None
    acc_full_scale = 4
    gyro_full_scale = 7.6e-3
    mag_full_scale = 1 / 16

    def __init__(self, time, cap, channel, acc: "IMUData", gyro: "IMUData", mag: "IMUData"):
        self.time = time
        self.cap = cap
        self.channel = channel
        self.acc = acc
        self.gyro = gyro
        self.mag = mag

    @classmethod
    def from_bytes(cls, sender, bytes_array):
        try:
            unpacked = struct.unpack("HIhhhhhhhhh", bytes_array)
        except struct.error as e:
            logger.error(f"Length of bytes_array is {len(bytes_array)}")
            raise e
        time_stamp = unpacked[0] * CLK_PERIOD
        cap_readings = 8 * np.array(unpacked[1]) / (2 ** 24 - 1)

        acc = IMUData(time_stamp, cls.acc_full_scale * unpacked[2] / (2.0 ** 15),
                      cls.acc_full_scale * unpacked[3] / (2.0 ** 15),
                      cls.acc_full_scale * unpacked[4] / (2.0 ** 15))

        gyro = IMUData(time_stamp, cls.gyro_full_scale * unpacked[5] / (2.0 ** 15),
                       cls.gyro_full_scale * unpacked[6] / (2.0 ** 15),
                       cls.gyro_full_scale * unpacked[7] / (2.0 ** 15))
        mag = IMUData(time_stamp, cls.mag_full_scale * unpacked[8],
                      cls.mag_full_scale * unpacked[9],
                      cls.mag_full_scale * unpacked[10])
        logger.debug(f"mag: {mag.x:.2f} {mag.y:.2f} {mag.z:.2f}")
        channel = 1 if sender == CAP1_CHAR_UUID else 2
        return cls(time_stamp, cap_readings, channel, acc, gyro, mag)

    def __repr__(self):
        return f"CH{self.channel} {self.cap:.3f} pF @ {1000 * self.time:.2f} ms"


def is_data():
    s = select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])
    return s


class CapCallback:
    def __init__(self, queue: dict = None, start_time=0):
        self.start_time = 0
        self.history = IterableQueue(100)
        if queue is not None:
            for k, v in queue.items():
                assert isinstance(v, multiprocessing.queues.Queue), \
                    "must assign a dictionary of multiprocessor.Queue to this attribute"
        self.queue = queue
        self.prev_time = None
        self.max_time = None

    def __call__(self, sender, bytes_array):
        data = CapData.from_bytes(sender, bytes_array)
        if self.max_time is None:
            self.max_time = data.time
            self.prev_time = data.time
            logger.debug(data)
            return data, sender

        if data.time > self.prev_time:
            delta = data.time - self.prev_time
            self.prev_time = data.time
            self.history.put(delta)
            self.max_time += delta
        else:
            self.prev_time = data.time
            try:
                assert len(self.history) != 0, "history shouldn't be empty"
                self.max_time += np.mean(self.history)
            except AssertionError:
                pass
        old_time = data.time
        data.time = self.max_time
        data.mag.time = self.max_time
        data.gyro.time = self.max_time
        data.acc.time = self.max_time
        logger.info(f"{data.channel} {old_time:.3f} {self.max_time:.3f}")
        if len(self.history) > 2:
            logger.debug(f"{data} fs = {1 / np.mean(self.history):.2f}")
        else:
            logger.debug(f"{data}")
        if self.queue is not None:
            self.queue[f"cap{data.channel}"].put(data)
        return data, sender

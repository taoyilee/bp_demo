# MIT License
# Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)

import logging
import multiprocessing
import select
import struct
import sys
import time
from multiprocessing import Queue

import numpy as np

from uci_cbp_demo.bluetooth.constants import CAP1_CHAR_UUID
from uci_cbp_demo.bluetooth.constants import CLK_PERIOD
from uci_cbp_demo.datastructures import IterableQueue

logger = logging.getLogger("bp_demo")


class IMUData:
    time = None
    name = ""
    x = None
    y = None
    z = None

    def __init__(self, time, x, y, z):
        self.time = time
        self.x = x
        self.y = y
        self.z = z

    @classmethod
    def from_bytes(cls, sender, bytes_array):
        unpacked = struct.unpack("Hhhh", bytes_array)
        reading_x = np.array(unpacked[1]) / (2 ** 15)
        reading_y = np.array(unpacked[2]) / (2 ** 15)
        reading_z = np.array(unpacked[3]) / (2 ** 15)
        time_stamp = unpacked[0] * CLK_PERIOD
        return cls(time_stamp, reading_x, reading_y, reading_z)

    def __repr__(self):
        return f"{self.name} {self.x:.2e} {self.y:.2e} {self.z:.2e}"


class AccData(IMUData):
    name = "acc"
    full_scale = 4

    @classmethod
    def from_bytes(cls, sender, bytes_array):
        unpacked = struct.unpack("Hhhh", bytes_array)
        time_stamp = unpacked[0] * CLK_PERIOD
        reading_x = cls.full_scale * unpacked[1] / 2 ** 15
        reading_y = cls.full_scale * unpacked[2] / 2 ** 15
        reading_z = cls.full_scale * unpacked[3] / 2 ** 15
        return cls(time_stamp, reading_x, reading_y, reading_z)


class GyroData(IMUData):
    name = "gyro"
    full_scale = 7.6e-3

    @classmethod
    def from_bytes(cls, sender, bytes_array):
        unpacked = struct.unpack("Hhhh", bytes_array)
        time_stamp = unpacked[0] * CLK_PERIOD
        reading_x = cls.full_scale * unpacked[1] / 2.0 ** 15
        reading_y = cls.full_scale * unpacked[2] / 2.0 ** 15
        reading_z = cls.full_scale * unpacked[3] / 2.0 ** 15
        return cls(time_stamp, reading_x, reading_y, reading_z)


class MagData(IMUData):
    name = "mag"
    full_scale = 1.0

    @classmethod
    def from_bytes(cls, sender, bytes_array):
        unpacked = struct.unpack("Hhhh", bytes_array)
        reading_x = cls.full_scale * unpacked[1] / (2.0 ** 15)
        reading_y = cls.full_scale * unpacked[2] / (2.0 ** 15)
        reading_z = cls.full_scale * unpacked[3] / (2.0 ** 15)
        time_stamp = unpacked[0] * CLK_PERIOD
        return cls(time_stamp, reading_x, reading_y, reading_z)


class CapData:
    time = None
    cap = None
    channel = None

    def __init__(self, time, cap, channel):
        self.time = time
        self.cap = cap
        self.channel = channel

    @classmethod
    def from_bytes(cls, sender, bytes_array):
        unpacked = struct.unpack("HI", bytes_array)
        cap_readings = 8 * np.array(unpacked[1]) / (2 ** 24 - 1)
        time_stamp = unpacked[0] * CLK_PERIOD
        channel = 1 if sender == CAP1_CHAR_UUID else 2
        return cls(time_stamp, cap_readings, channel)

    def __repr__(self):
        return f"CH{self.channel} {self.cap:.3f} pF @ {1000 * self.time:.2f} ms"


def is_data():
    s = select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])
    return s


def unpack_data(data, output_prob=False, offset=-0.0042):
    if output_prob:
        timestamp, voltage, prob = struct.unpack("HIf", data)
        return timestamp, 1.17 * (2 * voltage / (2 ** 24 - 1) - 1) + offset, prob
    else:
        timestamp, voltage = struct.unpack("HI", data)
        return timestamp, 1.17 * (2 * voltage / (2 ** 24 - 1) - 1) + offset


def notification_handler(sender, data, output_queue: "Queue", output_prob=False):
    try:
        mcu_time, voltage, prob = unpack_data(data, output_prob=output_prob)
    except struct.error:
        logger.error(f"struct unpack raised an error, data size is {len(data)} bytes")
        raise
    logger.debug(f"Voltage: {voltage:.4f} Volt")
    if output_prob:
        output_queue.put((mcu_time, time.time(), voltage, prob))
    else:
        output_queue.put((mcu_time, time.time(), voltage))


class CapCallback:
    def __init__(self, queue=None):
        self.history = IterableQueue(100)
        if queue is not None:
            assert isinstance(queue, multiprocessing.queues.Queue), \
                "must assign a multiprocessor.Queue to this attribute"
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
        data.time = self.max_time
        if len(self.history) > 2:
            logger.debug(f"{data} fs = {1 / np.mean(self.history):.2f}")
        else:
            logger.debug(f"{data}")
        if self.queue is not None:
            self.queue.put(data)
        return data, sender


class IMUCallback:
    def __init__(self, dataclass, queue=None):
        self.history = IterableQueue(100)
        if queue is not None:
            assert isinstance(queue, multiprocessing.queues.Queue), \
                "must assign a multiprocessor.Queue to this attribute"
        self.queue = queue
        self.prev_time = None
        self.max_time = None
        self.dataclass = dataclass

    def __call__(self, sender, bytes_array):
        # logger.info(f"{self.dataclass.name}: {bytes_array}")
        data = self.dataclass.from_bytes(sender, bytes_array)
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
        data.time = self.max_time
        if len(self.history) > 2:
            logger.debug(f"{data.time:.1f} {data} fs = {1 / np.mean(self.history):.2f}")
        else:
            logger.debug(f"{data}")
        if self.queue is not None:
            self.queue.put(data)
        return data, sender

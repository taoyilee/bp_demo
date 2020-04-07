# MIT License
# Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)

import logging
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


def unpack_characteristic_data(bytes_array):
    unpacked = struct.unpack("IHHHIIIIhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhBBBB", bytes_array)
    cap_readings = 8 * np.array(unpacked[4:8]) / 2 ** 24
    imu = np.array(unpacked[8:44])  # / 2 ** 16
    acc = 4 * (imu[0:12] / 2 ** 15)
    gyro = 3.8e-3 * (imu[12:24] / 2 ** 15)
    mask = np.array([True if u != 0 else False for u in unpacked[0:4]])
    time_stamps = np.array(unpacked[0:4], dtype=float)
    time_stamps[1:] += time_stamps[0]
    time_stamps = time_stamps * CLK_PERIOD
    time_stamps = time_stamps[mask]
    channel = np.array(unpacked[44:48])
    return {"time": time_stamps,
            "cap": cap_readings[mask],
            "acc": {"x": acc[0:4][mask], "y": acc[4:8][mask], "z": acc[8:12][mask]},
            "gyro": {"x": gyro[0:4][mask], "y": gyro[4:8][mask], "z": gyro[8:12][mask]},
            "mag": {"x": imu[24:28][mask], "y": imu[28:32][mask], "z": imu[32:36][mask]},
            "channel": channel[mask]
            }


class CapCallback:
    def __init__(self):
        self.history = IterableQueue(100)
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
        return data, sender

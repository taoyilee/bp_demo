# MIT License
# Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
import struct

import numpy as np

CLK_FREQ = 32768.0  # 32.768kHz
CLK_PERIOD = 1 / CLK_FREQ


def unpack_cap(bytes_array):
    unpacked = struct.unpack("HI", bytes_array)
    cap_readings = 8 * np.array(unpacked[1]) / (2 ** 24 - 1)
    time_stamp = unpacked[0] * CLK_PERIOD
    return {"time": time_stamp, "cap": cap_readings}


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

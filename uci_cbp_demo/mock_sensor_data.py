N_READINGS = 4

CLK = 32.768 * 1e3  # Hz
PERIOD = 10  # ms
import numpy as np


def sine_wave(t):
    return np.sin(2 * np.pi * 1 * t / CLK)


def cap():
    import struct
    time = 0
    while True:
        if time == 2 ** 31 - 1:
            time = 0
        starting_timestamp = time
        time += int(CLK * PERIOD / 1000)
        if time >= (0x7fff * 2 + 1):
            time = 0
        cap = int(((1 + sine_wave(time) / 2) / 50) * (2 ** 24 - 1))
        yield struct.pack("HI", *[starting_timestamp, cap])


def sensor():
    import random
    import struct
    time = 0
    while True:
        if time == 2 ** 31 - 1:
            time = 0
        starting_timestamp = time
        time += int(CLK * PERIOD / 1000)
        delta_timestamps = [random.randint(0, 100) for _ in range(N_READINGS - 1)]
        delta_timestamps.sort()

        # cap = [random.randint(0, 2 ** 24 - 1) for _ in range(N_READINGS)]
        cap = [int(((1 + sine_wave(time) / 2) / 50) * (2 ** 24 - 1)) for _ in range(N_READINGS)]
        acc = [random.randint(-2 ** 15, 2 ** 15 - 1) for _ in range(3 * N_READINGS)]
        gyro = [random.randint(-2 ** 15, 2 ** 15 - 1) for _ in range(3 * N_READINGS)]
        mag = [random.randint(-2 ** 15, 2 ** 15 - 1) for _ in range(3 * N_READINGS)]
        channel = [0, 1, 0, 1]
        data = [starting_timestamp] + delta_timestamps + cap + acc + gyro + mag + channel
        yield struct.pack("IHHHIIIIhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhBBBB", *data)

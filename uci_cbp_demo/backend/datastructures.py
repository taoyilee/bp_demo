#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
import numpy as np


class RotationalDataQueue(list):
    def head_updated_callback(self):
        pass

    def __init__(self, window_size=10):
        self._i = 0
        self.window_size = window_size
        super(RotationalDataQueue, self).__init__()

    @property
    def non_empty(self):
        return sum([1 if d is not None else 0 for d in self])

    def sort_time(self):
        self.sort(key=lambda x: x.time)

    @property
    def time(self):
        return np.array([d.time for d in self])

    @property
    def duration(self):
        return np.max(self.time) - np.min(self.time)

    def put(self, value):
        self.append(value)
        self.sort_time()
        while self.duration > self.window_size:
            self.pop(0)

    def __repr__(self):
        return ",".join([str(d) for d in self[:5]])


class IterableQueue(list):
    def __init__(self, size):
        self._i = 0
        self.size = size
        super(IterableQueue, self).__init__()

    def put(self, value):
        self.append(value)
        if len(self) > self.size:
            self.pop(0)


class CapIterableQueue(IterableQueue):
    def __init__(self, size):
        super(CapIterableQueue, self).__init__(size)

    @property
    def cap(self):
        return np.array([d.cap for d in self if d is not None])


class CapDisplayDataQueue(RotationalDataQueue):
    def __init__(self, window_size):
        super(CapDisplayDataQueue, self).__init__(window_size)

    @property
    def cap(self):
        return np.array([d.cap for d in self if d is not None])

    @property
    def acc(self):
        return np.array([d.acc for d in self if d is not None])

    @property
    def gyro(self):
        return np.array([d.gyro for d in self if d is not None])

    @property
    def mag(self):
        return np.array([d.mag for d in self if d is not None])


class IMUDisplayDataQueue(RotationalDataQueue):
    def __init__(self, window_size):
        super(IMUDisplayDataQueue, self).__init__(window_size)
        self._min_time = 0
        self._prev_min_time = 0

    @property
    def x(self):
        return np.array([d.x for d in self if d is not None])

    @property
    def y(self):
        return np.array([d.y for d in self if d is not None])

    @property
    def z(self):
        return np.array([d.z for d in self if d is not None])

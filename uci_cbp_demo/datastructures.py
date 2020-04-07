#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
import numpy as np


class RotationalDataQueue(list):
    def head_updated_callback(self):
        pass

    def __init__(self, size):
        self._i = 0
        super(RotationalDataQueue, self).__init__()
        for _ in range(size):
            self.append(None)

    @property
    def non_empty(self):
        return sum([1 if d is not None else 0 for d in self])

    def put(self, value):
        self[self._i] = value
        if self._i == 0:
            self.head_updated_callback()

        self._i += 1
        if self._i == len(self):
            self._i = 0

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
    def time(self):
        _time = np.array([d.time for d in self if d is not None])
        return _time

    @property
    def cap(self):
        return np.array([d.cap for d in self if d is not None])


class CapDisplayDataQueue(RotationalDataQueue):
    def __init__(self, size):
        super(CapDisplayDataQueue, self).__init__(size)
        self._min_time = 0
        self._prev_min_time = 0

    def head_updated_callback(self):
        self._prev_min_time = self._min_time
        self._min_time = self[0].time

    @property
    def time(self):
        _time = np.array([d.time for d in self if d is not None])
        return _time

    @property
    def time_plot(self):
        _time = np.array([d.time for d in self if d is not None])
        _time -= self._min_time
        _time[self._i:] += self._min_time - self._prev_min_time
        return _time

    @property
    def cap(self):
        return np.array([d.cap for d in self if d is not None])

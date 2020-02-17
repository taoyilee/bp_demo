# MIT License
# Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
WINDOW = 5
TARGET_FS = 200
CUTOFF = 20
STOP_ATTEN = 20
FS = 100 / 2
TS = 1 / FS
WINDOW_FFT = 20
MAX_DATA_QUEUE = 1.5 * (WINDOW_FFT / TS)

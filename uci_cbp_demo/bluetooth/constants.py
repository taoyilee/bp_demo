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
CLK_FREQ = 32768.0  # 32.768kHz
CLK_PERIOD = 1 / CLK_FREQ
CAP1_CHAR_UUID = "71ee1401-1232-11ea-8d71-362b9e155667"
CAP2_CHAR_UUID = "71ee1402-1232-11ea-8d71-362b9e155667"
ACC_CHAR_UUID = "71ee1403-1232-11ea-8d71-362b9e155667"
GYRO_CHAR_UUID = "71ee1404-1232-11ea-8d71-362b9e155667"
MAG_CHAR_UUID = "71ee1405-1232-11ea-8d71-362b9e155667"

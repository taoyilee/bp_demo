# MIT License
# Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)import sys
import logging
from multiprocessing import Pipe, Queue, Process

logger = logging.getLogger("bp_demo")


def gui_noargs():
    gui(a=1, b=0, ch1=True, ch2=True, addr="FA:21:46:BA:84:0F")


def gui(a=1, b=0, ch1=True, ch2=True, addr=None):
    from uci_cbp_demo.ui.gui_cap import GUI
    from uci_cbp_demo.bluetooth import SensorBoard
    pipe_1, pipe_2 = Pipe()
    inter_process_queue = {"cap1": Queue(), "cap2": Queue(), "acc": Queue(), "gyro": Queue(), "mag": Queue()}

    sensor = SensorBoard(addr=addr, pipe=pipe_2)

    if ch1 and ch2:
        p = Process(target=sensor.start_cap_notification, args=(inter_process_queue,))
    elif ch1:
        p = Process(target=sensor.start_cap1_notification, args=(inter_process_queue,))
    elif ch2:
        p = Process(target=sensor.start_cap2_notification, args=(inter_process_queue,))
    else:
        raise ValueError("Either CH1 or CH2 must be enabled")
    logger.info("Setting Up Bluetooth")
    p.start()
    logger.info("Starting GUI")
    GUI(sensor, inter_process_queue, a, b, ch1, ch2).start_gui(pipe_1)
    p.terminate()

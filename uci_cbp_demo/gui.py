# MIT License
# Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)import sys
import logging
from multiprocessing import Pipe, Queue, Process

logger = logging.getLogger("bp_demo")


def gui_noargs():
    gui(a=1, b=0, ch1=True, ch2=True, addr="DC:4E:6D:9F:E3:BA")


def gui(a=1, b=0, ch1=True, ch2=True, addr="DC:4E:6D:9F:E3:BA"):
    from uci_cbp_demo.ui.gui_cap import GUIController, GUIModel
    from uci_cbp_demo.bluetooth import SensorBoard
    pipe_1, pipe_2 = Pipe()
    q = {"cap1": Queue(), "cap2": Queue(), "acc": Queue(), "gyro": Queue(), "mag": Queue()}
    sensor = SensorBoard(addr=addr, pipe=pipe_2)
    _gui = GUIController(GUIModel(q, pipe_1, a=a, b=b, ch1=ch1, ch2=ch2, addr=addr))
    p = Process(target=sensor.start_cap_notification, args=(q,))
    p.start()
    _gui.start_gui()
    p.terminate()

#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
from multiprocessing import Process, Pipe

from uci_cbp_demo.logging import logger


def tui_main(addr=None, ch1=True, ch2=True):
    from uci_cbp_demo.ui.terminal import TerminalManager

    from uci_cbp_demo.backend import SensorBoard
    pipe_1, pipe_2 = Pipe()
    tm = TerminalManager(pipe_1)

    sensor = SensorBoard(addr=addr, pipe=pipe_2)

    if ch1 and ch2:
        logger.info("Notifying CH1/CH2")
        process = Process(target=sensor.start_cap_notification)
    elif ch1:
        logger.info("Notifying CH1")
        process = Process(target=sensor.start_cap1_notification)
    elif ch2:
        logger.info("Notifying CH2")
        process = Process(target=sensor.start_cap2_notification)
    else:
        raise ValueError("Either CH1 or CH2 must be enabled")
    process.start()
    tm.handle_session()

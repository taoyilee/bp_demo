#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
from multiprocessing import Process, Pipe


def tui_main(addr=None, ch1=True, ch2=True):
    from uci_cbp_demo.ui.terminal import TerminalManager

    from uci_cbp_demo.backend import SensorBoard
    pipe_1, pipe_2 = Pipe()
    tm = TerminalManager(pipe_1)

    sensor = SensorBoard(addr=addr, pipe=pipe_2)
    process = Process(target=sensor.start_session)
    process.start()
    if ch1:
        pipe_1.send(("CH1", None))
    if ch2:
        pipe_1.send(("CH2", None))
    tm.handle_session()

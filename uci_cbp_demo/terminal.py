#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)

# MIT License
# Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)import sys
import logging
import platform
import sys
import time

from uci_cbp_demo.bluetooth.callbacks import is_data

logger = logging.getLogger("bp_demo")
if platform.system() == "Linux":
    import termios
    import tty


class TerminalManager:
    def __init__(self, pipe):
        if platform.system() == "Linux":
            self.term_settings = termios.tcgetattr(sys.stdin)
        self.pipe = pipe

    def wait_for_connection(self):
        while not self.pipe.poll():
            time.sleep(1)  # wait for connection

    def handle_session(self):
        self.wait_for_connection()
        if platform.system() == "Linux":
            tty.setcbreak(sys.stdin.fileno())
            while not is_data():
                pass
        else:
            time.sleep(20)
        self.pipe.send(("STOP", None))
        logger.info("Restoring tty...")
        if platform.system() == "Linux":
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.term_settings)

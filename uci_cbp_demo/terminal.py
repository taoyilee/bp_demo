#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)

# MIT License
# Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)import sys
import logging
import sys
import termios
import time
import tty

from uci_cbp_demo.bluetooth.callbacks import is_data

logger = logging.getLogger("bp_demo")


class TerminalManager:
    def __init__(self, pipe):
        self.term_settings = termios.tcgetattr(sys.stdin)
        self.pipe = pipe

    def wait_for_connection(self):
        while not self.pipe.poll():
            time.sleep(1)  # wait for connection

    def handle_session(self):
        self.wait_for_connection()
        tty.setcbreak(sys.stdin.fileno())
        while not is_data():
            pass
        self.pipe.send("stop")
        logger.info("Restoring tty...")
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.term_settings)

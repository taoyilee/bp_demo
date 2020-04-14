# MIT License
# Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)import sys
import logging
import sys
from multiprocessing import Process, Pipe

import click

import uci_cbp_demo

logger = logging.getLogger("bp_demo")
console_handler = logging.StreamHandler()
logger.setLevel(logging.INFO)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

DEBUG = False
MOCK = False


@click.group()
@click.version_option(version=uci_cbp_demo.__version__)
@click.option('--debug/--no-debug', help="Enable DEBUG mode", default=False)
def cli(debug=False, mock=False):
    global DEBUG
    DEBUG = debug
    global MOCK
    MOCK = mock
    if DEBUG:
        logger.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.DEBUG)
    logger.debug('Debug mode is %s' % ('on' if debug else 'off'))


@cli.command()
@click.option('--addr', default=None)
@click.option('--ch1/--no-ch1', default=True)
@click.option('--ch2/--no-ch2', default=True)
def tui(addr=None, ch1=True, ch2=True):
    from uci_cbp_demo.terminal import TerminalManager

    from uci_cbp_demo.bluetooth import SensorBoard
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


@cli.command()
@click.option('-a', default=1, help='Scaling coefficient')
@click.option('-b', default=0, help='Shifting in Y')
@click.option('--ch1/--no-ch1', default=True)
@click.option('--ch2/--no-ch2', default=True)
@click.option('--addr', help="Address (MAC: Windows/Linux; UUID: MacOSX)", default=None)
def gui(a=1, b=0, ch1=True, ch2=True, addr=None):
    from uci_cbp_demo.gui import gui
    gui(a, b, ch1, ch2, addr)


@cli.command()
def scan():
    from uci_cbp_demo.bluetooth import scan, check_adaptor
    if check_adaptor():
        for mac in scan():
            logger.info(f"{mac.name}: {mac.address}")
    else:
        logger.warning(f"Please check Bluetooth adaptor (powered off?)")


@cli.command()
@click.option('--addr', default=None)
def list_char(addr):
    from uci_cbp_demo.bluetooth import list_char
    services = list_char(addr)
    for s in services:
        logger.info(s)


if __name__ == "__main__":
    sys.exit(cli())

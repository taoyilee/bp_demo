# MIT License
# Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)import sys
import logging
import sys

import click

import uci_cbp_demo
from uci_cbp_demo.logging import logger, console_handler

DEBUG = False


@click.group()
@click.version_option(version=uci_cbp_demo.__version__)
@click.option('--debug/--no-debug', help="Enable DEBUG mode", default=False)
def cli(debug=False):
    global DEBUG
    DEBUG = debug
    if DEBUG:
        logger.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.DEBUG)
    logger.debug('Debug mode is %s' % ('on' if debug else 'off'))


@cli.command()
@click.option('--addr', default=None)
@click.option('--ch1/--no-ch1', default=True)
@click.option('--ch2/--no-ch2', default=True)
def tui(addr=None, ch1=True, ch2=True):
    from uci_cbp_demo.ui import tui_main
    tui_main(addr, ch1, ch2)


@cli.command()
def scan():
    from uci_cbp_demo.backend.bluetooth import scan, check_adaptor
    if check_adaptor():
        for mac in scan():
            logger.info(f"{mac.name}: {mac.address}")
    else:
        logger.warning(f"Please check Bluetooth adaptor (powered off?)")


@cli.command()
@click.option('--addr', default=None)
def list_char(addr):
    from uci_cbp_demo.backend.bluetooth import list_char
    services = list_char(addr)
    for s in services:
        logger.info(s)


@cli.command()
def gui():
    from uci_cbp_demo.ui import main
    main()


if __name__ == "__main__":
    sys.exit(cli())

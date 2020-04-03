# MIT License
# Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)import sys
import logging
import sys
import termios
import time
import tty
from multiprocessing import Process, Pipe

import click

from uci_cbp_demo.bluetooth.callbacks import is_data

logger = logging.getLogger("bp_demo")
console_handler = logging.StreamHandler()
logger.setLevel(logging.INFO)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

DEBUG = False


@click.group()
@click.option('--debug/--no-debug', default=False)
def cli(debug):
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
    from uci_cbp_demo.bluetooth.sensorBoard import SensorBoard

    old_settings = termios.tcgetattr(sys.stdin)

    pipe_1, pipe2 = Pipe()
    sensor = SensorBoard(addr=addr, pipe=pipe2)
    keyboard_interrupt = True
    if ch1 and ch2:
        logger.info("Notifying CH1/CH2")
        process = Process(target=sensor.start_cap_notification, args=(keyboard_interrupt,))
    elif ch1:
        logger.info("Notifying CH1")
        process = Process(target=sensor.start_cap1_notification, args=(keyboard_interrupt,))
    elif ch2:
        logger.info("Notifying CH2")
        process = Process(target=sensor.start_cap2_notification, args=(keyboard_interrupt,))
    else:
        raise ValueError("Either CH1 or CH2 must be enabled")
    process.start()

    while not pipe_1.poll():
        time.sleep(1)  # wait for connection
    tty.setcbreak(sys.stdin.fileno())
    while not is_data():
        pass
    pipe_1.send("stop")
    logger.info("Restoring tty...")
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


@cli.command()  # @cli, not @click!
@click.option('-a', default=1, help='Scaling coefficient')
@click.option('-b', default=0, help='Shifting in Y')
@click.option('--mock/--no-mock', default=False)
@click.option('--mac', default=None)
@click.option('--uuid', default=None)
def gui(a=1, b=0, mock=False, mac=None, uuid=None):
    from uci_cbp_demo.gui_cap import start_gui
    start_gui(a, b, mock=mock, mac=mac, uuid=uuid)


@cli.command()  # @cli, not @click!
def scan():
    import asyncio
    from bleak import discover

    async def run():
        devices = await discover()
        for d in devices:
            logger.info(d)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())


@cli.command()  # @cli, not @click!
@click.option('--addr', default=None)
def list_char(addr):
    import asyncio
    from bleak import BleakClient

    async def run(address, loop):
        async with BleakClient(address, loop=loop) as client:
            x = await client.is_connected()
            logger.info("Connected: {0}".format(x))

            for service in client.services:
                logger.info("[Service] {0}: {1}".format(service.uuid, service.description))
                for char in service.characteristics:
                    if "read" in char.properties:
                        try:
                            value = bytes(await client.read_gatt_char(char.uuid))
                        except Exception as e:
                            value = str(e).encode()
                    else:
                        value = None
                    logger.info(
                        "\t[Characteristic] {0}: ({1}) | Name: {2}, Value: {3} ".format(
                            char.uuid, ",".join(char.properties), char.description, value
                        )
                    )
                    for descriptor in char.descriptors:
                        value = await client.read_gatt_descriptor(descriptor.handle)
                        logger.info(
                            "\t\t[Descriptor] {0}: (Handle: {1}) | Value: {2} ".format(
                                descriptor.uuid, descriptor.handle, bytes(value)
                            )
                        )

    loop = asyncio.get_event_loop()
    logger.info(f"Connecting to {addr}")
    loop.run_until_complete(run(addr, loop))


if __name__ == "__main__":
    sys.exit(cli())

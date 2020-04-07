# MIT License
# Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)import sys
import logging
import sys
from multiprocessing import Process, Pipe

import click

from uci_cbp_demo.terminal import TerminalManager

logger = logging.getLogger("bp_demo")
console_handler = logging.StreamHandler()
logger.setLevel(logging.INFO)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

DEBUG = False
MOCK = False  # use mock data source


@click.group()
@click.option('--debug/--no-debug', help="Enable DEBUG mode", default=False)
@click.option('--mock/--no-mock', help="Use mock data source instead of reading from Bluetooth", default=False)
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
    from uci_cbp_demo.bluetooth.sensorBoard import SensorBoard
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


@cli.command()  # @cli, not @click!
@click.option('-a', default=1, help='Scaling coefficient')
@click.option('-b', default=0, help='Shifting in Y')
@click.option('--ch1/--no-ch1', default=True)
@click.option('--ch2/--no-ch2', default=True)
@click.option('--addr', help="Address (MAC: Windows/Linux; UUID: MacOSX)", default=None)
def gui(a=1, b=0, ch1=True, ch2=True, addr=None):
    from uci_cbp_demo.gui_cap import GUI
    from uci_cbp_demo.bluetooth.sensorBoard import SensorBoard
    pipe_1, pipe_2 = Pipe()
    sensor = SensorBoard(addr=addr, pipe=pipe_2)
    if not ch1 and not ch2:
        raise ValueError("Either CH1 or CH2 must be enabled")
    GUI(sensor, a, b, ch1, ch2).start_gui(pipe_1)


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

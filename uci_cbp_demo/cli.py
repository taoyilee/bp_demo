# MIT License
# Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)import sys
import sys

import click

DEBUG = False


@click.group()
@click.option('--debug/--no-debug', default=False)
def cli(debug):
    global DEBUG
    DEBUG = debug
    click.echo('Debug mode is %s' % ('on' if debug else 'off'))


@cli.command()  # @cli, not @click!
@click.option('-a', default=1, help='Scaling coefficient')
@click.option('-b', default=0, help='Shifting in Y')
@click.option('--mock/--no-mock', default=False)
@click.option('--mac', default=None)
@click.option('--uuid', default=None)
def gui(a=1, b=0, mock=False, mac=None, uuid=None):
    from uci_cbp_demo.gui_cap import start_gui
    start_gui(a, b, mock=mock,mac=mac, uuid=uuid)


@cli.command()  # @cli, not @click!
def scan():
    import asyncio
    from bleak import discover

    async def run():
        devices = await discover()
        for d in devices:
            print(d)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())


if __name__ == "__main__":
    sys.exit(cli())

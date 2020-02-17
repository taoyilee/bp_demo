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
def gui(a=1, b=0):
    from uci_cbp_demo.gui_cap import start_gui
    start_gui(a, b)


if __name__ == "__main__":
    sys.exit(cli())

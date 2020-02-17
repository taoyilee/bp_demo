"""Console script for uci_cbp_demo."""
import sys
import click


@click.command()
def main(args=None):
    """Console script for uci_cbp_demo."""
    click.echo("Replace this message by putting your code into "
               "uci_cbp_demo.cli.main")
    click.echo("See click documentation at https://click.palletsprojects.com/")
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover

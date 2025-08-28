import click

from src.download import download
from src.read import read


@click.group()
@click.help_option("-h", "--help")
@click.version_option("0.1.1", "-v", "--version", message="%(prog)s %(version)s", prog_name="n2epub")
def cli() -> None:
    """A cli to download light/web novels as epub files."""
    pass

cli.add_command(download)
cli.add_command(read)

if __name__ == "__main__":
    cli()
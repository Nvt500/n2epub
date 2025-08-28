import click

from src.download import download


@click.group()
@click.help_option("-h", "--help")
@click.version_option("0.1.0", "-v", "--version", message="%(prog)s %(version)s", prog_name="n2epub")
def cli() -> None:
    """A cli to download light/web novels as epub files."""
    pass

cli.add_command(download)

if __name__ == "__main__":
    cli()
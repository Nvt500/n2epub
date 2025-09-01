import importlib
import click

from src import constants
from src.providers.novel_bin import NovelBinDownloader


@click.command()
@click.help_option("-h", "--help")
@click.argument("url")
@click.option("-p", "--provider", "provider", is_flag=False, flag_value="", type=click.STRING, default=None, help="Name of the provider (website) of the novel.", metavar="PROVIDER")
@click.option("-s", "--sync", "sync", is_flag=True, default=True, help="Download synchronously.")
@click.option("-w", "--wait", "wait_time", default=3, type=click.IntRange(0, clamp=True), show_default=True, help="Time between each chapter.", metavar="TIME")
@click.option("-v", "--verbose", "verbose", is_flag=True, default=False, help="Output extra information.")
@click.option("-m", "--max-workers", "max_workers", default=10, type=click.IntRange(1, clamp=True), show_default=True, help="Chapter group size to be downloaded at once in async.", metavar="WORKERS")
def download(url: str, provider: str | None, sync: bool, wait_time: int, verbose: bool, max_workers: int) -> None:
    """Downloads a novel from a url as an epub file

        URL: the url to the homepage of the series to download.

        If the --provider flag is not given, the provider will be automatically detected,
        ie if url starts with https://novelbin the NovelBinDownloader will be used.

        Use --provider as a flag to pick from a list of available providers.

        Only in sync wait_time is the number of seconds to wait between downloading each chapter.

        Only in async max_workers is the size of the group of chapters to be downloaded at once.
    """

    try:
        if provider is None:
            if url.startswith("https://novelbin"):
                NovelBinDownloader(url).download(sync, wait_time, verbose, max_workers)
            else:
                raise Exception(f"{url} does not match any known provider (use --provider to explicitly specify a provider).")
            return
        if provider == "":
            provider = get_provider()

        provider_dict = importlib.import_module("src.providers." + provider).__dict__
        downloader = list(provider_dict.values())[-1]
        downloader(url).download(sync, wait_time, verbose, max_workers)
    except constants.ProgError as e:
        raise Exception(e)
    except ModuleNotFoundError:
        click.echo(f"{provider} is not a valid provider.", err=True)
    except Exception as e:
        click.echo(f"Error occurred while downloading:\n\t{e}", err=True)


def get_provider() -> str:
    """Gets user selected provider from list of available providers"""

    click.clear()
    file_num = 1
    providers = []
    for file_name in [key for key in importlib.import_module("src.providers").__dict__.keys() if not key.startswith("__")]:
        provider_dict = importlib.import_module("src.providers." + file_name).__dict__
        downloader_class = list(provider_dict.values())[-1]
        click.echo(f"{file_num}. {downloader_class.__doc__ or downloader_class.__name__} ({file_name})")
        providers.append(file_name)

        file_num += 1

    click.echo("Enter the name of the provider (the name in the last set of parentheses):")
    while True:
        provider = click.get_text_stream("stdin").readline().strip()
        for prov in providers:
            if provider == prov:
                click.clear()
                return provider

        click.echo("\nEnter a valid provider:")

# n2epub

A cli to download light/web novels as epub files.

The same as [man2cbz](https://github.com/Nvt500/man2cbz) but with novels.

# Installation

Either download the executable from the releases or build it yourself with something like `pyinstaller`.

# Usage

## Download

```text
Usage: n2epub download [OPTIONS] URL

  Downloads a novel from a url as an epub file

  URL: the url to the homepage of the series to download.

  If the --provider flag is not given, the provider will be automatically
  detected, ie if url starts with https://novelbin the NovelBinDownloader will
  be used.

  Use --provider as a flag to pick from a list of available providers.

  Sync:
      wait_time: number of seconds to wait between downloading each chapter,
          cloudflare can time out if it goes too fast and I find 3 seconds to work fine
      retries is ignored
  Async:
      wait_time: number of seconds to wait between each try of downloading a chapter
      retries: number of times to retry downloading a chapter

Options:
  -h, --help               Show this message and exit.
  -p, --provider PROVIDER  Name of the provider (website) of the novel.
  -s, --sync               Download synchronously.
  -w, --wait TIME          Time between each chapter or try.  [default: 3;
                           x>=0]
  -r, --retries RETRIES    Number of times to retry downloading each chapter.
                           [default: 5; x>=0]
```

If the provider is using something like cloudflare, it can time out so waiting between each chapter 
download can keep prevent that. In async, it retries if failed after waiting some time as other
requests are going at the same time so timing out is inevitable.

### Providers

Providers are websites where the novels are stored like https://novelbin.com/. Providers are 
listed in the providers folder in their own python file. To add one create a class and extend 
the Downloader superclass in `downloader.py`.

Requirements of subclass:

- `__init__(self, homepage_url: str)`: MUST be called with super().__init__ and should pass the
  url of the homepage.
- `get_all_chapter_urls(self, response: requests.Response) -> list[str]`: MUST be implemented in order to get
  each chapter's url.
- `get_chapter_text(self, response: requests.Response) -> str`: MUST be implemented in order to get 
  each chapter's text.
- `get_novel_title(self, response: requests.Response) -> str`: MUST be implemented in order to get the
  novel's title.
- The other three (`get_chapter_title`, `get_cover_image_url`, `get_novel_author`) are not required, but you probably should implement them.
- This is optional, but if there is a doc string for the class, it will be shown when listing available providers and can give the user additional information like mentioned above
- THE CLASS EXTENDING `Downloader` MUST BE THE LAST THING IT THE FILE

After following these requirements, simply call the `download()` method of the superclass.

List of implemented providers:

- Novel Bin: https://novelbin.com/

## Read

```text
Usage: n2epub read [OPTIONS] FILENAME

  Read a novel in the command line from an epub file

Options:
  -h, --help  Show this message and exit.
```

Allows for reading novels without external tools.

Controls:
- Reading
  - Vertical arrow keys: scroll up and down to view the chapter
  - Horizontal arrow keys: switch between chapters
  - tab: go to toc
  - q: quit
- Table of Contents
  - Vertical arrow keys: scroll up and down to choose a chapter
  - enter: select the highlighted chapter
  - q: quit to reading without selecting anything

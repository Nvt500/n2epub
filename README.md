
# n2epub

A cli to download light/web novels as epub files.

The same as [man2cbz](https://github.com/Nvt500/man2cbz) but with novels.

# Installation

Either download the executable from the releases or build it yourself with something like `pyinstaller`.

The .exe is for windows, the no extension is the linux binary.

```text
python -m venv venv
venv\Scripts\activate | source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
pyinstaller src/n2epub.spec --distpath dist --workpath build
deactivate
```

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

  Only in sync wait_time is the number of seconds to wait between downloading
  each chapter.

  Only in async max_workers is the size of the group of chapters to be
  downloaded at once.

Options:
  -h, --help                 Show this message and exit.
  -p, --provider PROVIDER    Name of the provider (website) of the novel.
  -s, --sync                 Download synchronously.
  -w, --wait TIME            Time between each chapter.  [default: 3; x>=0]
  -v, --verbose              Output extra information.
  -m, --max-workers WORKERS  Chapter group size to be downloaded at once in
                             async.  [default: 10; x>=1]
```

If the provider is using something like cloudflare, it can time out so waiting between each chapter 
download can keep prevent that.

### Testing: Looked on "Latest Release" for newer novels with fewer chapters

- https://novelbin.com/b/fff-class-trashero
    #### Sync:
        442 chapters * 3 seconds each = 1326 seconds
    #### Async (max_workers=10):
        Using time.time() before and after = 719 seconds
- https://novelbin.com/b/my-unrestrained-lives
    #### Sync:
        63 chapters * 3 seconds each = 189 seconds
        Using time.time() before and after = 198 seconds
    #### Async (max_workers=10):
        Using time.time() before and after = 61 seconds
- https://novelbin.com/b/bestowing-falna-on-the-kunoichi
    #### Sync:
        60 chapters * 3 seconds each = 180 seconds
    #### Async (max_workers=10):
        Using time.time() before and after = 78 seconds
    #### Async (max_workers=15)
        Using time.time() before and after = 116 seconds

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
  -h, --help    Show this message and exit.
  -s, --select  Choose a novel from the directory of the executable.
```

Allows for reading novels without external tools. When using `--select` just type anything for 
`FILENAME`.

Controls:
- Reading
  - Vertical arrow keys, w and s: scroll up and down to view the chapter
  - Horizontal arrow keys, a and d: switch between chapters
  - tab: go to toc
  - q: quit
- Table of Contents
  - Vertical arrow keys, w and s: scroll up and down to choose a chapter
  - enter or space: select the highlighted chapter
  - q: quit to reading without selecting anything

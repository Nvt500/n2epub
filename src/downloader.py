import concurrent.futures
import os
import pathlib
import time
import click
import cloudscraper
import requests
from ebooklib import epub

from src import constants


class Downloader:
    """Downloader Template

        In a derived Downloader class:
            __init__(self, homepage_url: str): MUST be called with super().__init__ and should pass the url of the homepage.
            get_all_chapter_urls(self, response: requests.Response) -> list[str]: MUST be implemented in order to get each chapter's url.
            get_chapter_text(self, response: requests.Response) -> str: MUST be implemented in order to get each chapter's text.
            get_novel_title(self, response: requests.Response) -> str: MUST be implemented in order to get the novel's title.
            The other three (get_chapter_title, get_cover_image_url, get_novel_author) are not required, but you probably should implement them.

        After these conditions are fulfilled simply call the download method.
    """


    def __init__(self, homepage_url: str) -> None:
        """Constructor

            homepage_url: the url to the homepage of the novel
        """

        self.homepage_url = homepage_url
        self.scraper = cloudscraper.create_scraper()


    def download(self, threaded: bool, wait_time: int, verbose: bool, max_workers: int) -> None:
        """Download all chapters as an epub file

            threaded: get chapters asynchronously if true

            Sync:
                wait_time: number of seconds to wait between downloading each chapter, cloudflare can time out if it goes too fast and I find 3 seconds to work fine
                verbose: ignored
                max_workers: ignored
            Async:
                wait_time: ignored
                verbose: output extra information
                max_workers: max number of concurrent downloads
        """

        home_page_response = self.scraper.get(self.homepage_url)

        urls = self.get_all_chapter_urls(home_page_response)
        novel_title = self.get_novel_title(home_page_response)
        novel_author = self.get_novel_author(home_page_response)
        cover_image_url = self.get_cover_image_url(home_page_response)

        if os.path.exists(os.path.join(constants.get_root_dir(), novel_title + ".epub")):
            raise Exception(f"{os.path.join(constants.get_root_dir(), novel_title + ".epub")} already exists.")

        book = epub.EpubBook()
        book.set_identifier(f"{novel_title} {len(urls)}")
        book.set_title(novel_title)
        book.set_language("en")
        if novel_author:
            book.add_author(novel_author)

        if cover_image_url:
            cover_image_response = self.scraper.get(cover_image_url)
            book.set_cover("cover" + pathlib.Path(cover_image_url).suffix, cover_image_response.content)
            cover = epub.EpubHtml(title="Cover", file_name="cover_page.xhtml")
            cover.content = "<img src=\"cover.jpg\" width=\"100%\" height=\"100%\">"
            book.add_item(cover)
            book.toc.append(cover)

            book.spine = ["cover", cover, "nav"]
        else:
            book.spine = ["nav"]

        time1 = time.time()

        if not threaded:
            chapters = self.download_chapters(urls, wait_time)
        else:
            chapters = self.download_chapters_threaded(urls, verbose, max_workers)

        time2 = time.time()
        click.echo(f"Downloaded {len(urls)} chapters in {time2 - time1} seconds.")

        if chapters is None:
            return
        for chapter in chapters:
            book.add_item(chapter)
            book.toc.append(chapter)
            book.spine.append(chapter)

        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        epub.write_epub(novel_title + ".epub", book)
        click.echo(f"\nDownloaded {os.path.join(constants.get_root_dir(), novel_title + ".epub")}.")


    def download_chapters(self, urls: list[str], wait_time: int) -> list[epub.EpubHtml]:
        """Download all chapters synchronously as epub.Html

            urls: list of urls to download
            wait_time: number of seconds to wait between downloading each chapter
        """

        chapters = []
        for i, url in enumerate(urls):
            chapter_response = self.scraper.get(url, timeout=15)
            chapter_title = self.get_chapter_title(chapter_response) or f"Chapter {i+1}"
            chapter_text = self.get_chapter_text(chapter_response)
            chapter = epub.EpubHtml(title=chapter_title, file_name=f"{i+1}_{"_".join(chapter_title.split(" "))}.xhtml")
            chapter.content = """<html>
                <h1>{chapter_title}</h1>
                {chapter_text}
            </html>""".format(chapter_title=chapter_title, chapter_text="\n".join([f"<p>{line}</p>" for line in chapter_text.splitlines()]))
            chapters.append(chapter)
            click.echo(f"Got {chapter_title} at {url} ({i + 1}/{len(urls)}).")
            time.sleep(wait_time)
        return chapters


    def download_chapters_threaded(self, urls: list[str], verbose: bool, max_workers: int) -> list[epub.EpubHtml] | None:
        """Download all chapters asynchronously as epub.Html

            urls: list of urls to download
            verbose: output extra information
            max_workers: max number of concurrent downloads
        """

        chapters = [None for _ in range(len(urls))]
        chapters_done = [False for _ in  range(max_workers)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.get_chapter_page, url, i + 1, chapters_done, len(urls), verbose): (url, i) for i, url in enumerate(urls)}
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                url = futures[future][0]
                index = futures[future][1]
                if future.result()[0] is None:
                    click.echo(f"Download failed at {url} for {self.homepage_url}.")
                    executor.shutdown(cancel_futures=True)
                    return None
                chapter, chapter_title = future.result()
                chapters[index] = chapter
                click.echo(f"Got {chapter_title} at {url} ({i + 1}/{len(urls)}).")
        return chapters


    def get_chapter_page(self, chapter_url: str, chapter_number: int, chapters_done: list[bool], num_chapters: int, verbose: bool) -> (epub.EpubHtml | None, str):
        """Get the page in the epub for the chapter

            chapter_url: the url to the chapter
            chapter_number: the chapter number
            chapters_done: a list of booleans to check that each chapter of a group is done before moving on
            num_chapters: the number of total chapters to download not the group's total
            verbose: output extra information

            returns the chapter page and the chapter_title
        """

        times = [3, 15, 30, 60, 0]

        if verbose:
            click.echo(f"\tDownloading {chapter_url} ({chapter_number}/{num_chapters}).")

        chapter = None
        chapter_title = ""
        for retry in range(5):
            chapter_response = self.scraper.get(chapter_url, timeout=15)
            if chapter_response.status_code != 200:
                if verbose:
                    click.echo(f"\t\tRetrying download of {chapter_url} after {times[retry]} seconds because {chapter_response.status_code} {chapter_response.reason}.")
                time.sleep(times[retry])
                continue

            chapter_title = self.get_chapter_title(chapter_response) or f"Chapter {chapter_number}"
            chapter_text = self.get_chapter_text(chapter_response)
            chapter = epub.EpubHtml(title=chapter_title, file_name=f"{chapter_number}_{"_".join(chapter_title.split(" "))}.xhtml")
            chapter.content = """<html>
    <h1>{chapter_title}</h1>
    {chapter_text}
</html>""".format(chapter_title=chapter_title, chapter_text="\n".join([f"<p>{line}</p>" for line in chapter_text.splitlines()]))
            break

        chapters_done[(chapter_number-1) % len(chapters_done)] = True
        if chapter_number == num_chapters:
            for i in range((len(chapters_done)-1)-((chapter_number-1) % len(chapters_done))):
                chapters_done.pop()

        if verbose:
            click.echo(f"\t{chapter_title or "Failed Chapter"} is waiting ({chapters_done.count(True)}/{len(chapters_done)})... ")
        while not chapters_done.count(True) == len(chapters_done):
            pass

        time.sleep(2)
        chapters_done[(chapter_number-1) % len(chapters_done)] = False
        return (chapter, chapter_title)


    def get_all_chapter_urls(self, response: requests.Response) -> list[str]:
        """Get all chapter urls"""

        raise constants.ProgError("To be implemented.")


    def get_chapter_title(self, response: requests.Response) -> str | None:
        """Get the chapter's title"""

        raise constants.ProgError("To be implemented.")


    def get_chapter_text(self, response: requests.Response) -> str:
        """Get the chapter's text"""

        raise constants.ProgError("To be implemented.")


    def get_cover_image_url(self, response: requests.Response) -> str | None:
        """Get the novel's cover image's url"""

        raise constants.ProgError("To be implemented.")


    def get_novel_title(self, response: requests.Response) -> str:
        """Get the novel's title"""

        raise constants.ProgError("To be implemented.")


    def get_novel_author(self, response: requests.Response) -> str | None:
        """Get the novel's author"""

        raise constants.ProgError("To be implemented.")
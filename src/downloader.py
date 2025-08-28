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


    def download(self, threaded: bool, wait_time: int = 3, retries: int = 5) -> None:
        """Download all chapters as an epub file

            Sync:
                wait_time: number of seconds to wait between downloading each chapter, cloudflare can time out if it goes too fast and I find 3 seconds to work fine
                retries is ignored
            Async:
                wait_time: number of seconds to wait between each try of downloading a chapter
                retries: number of times to retry downloading a chapter
        """

        home_page_response = self.scraper.get(self.homepage_url)

        urls = self.get_all_chapter_urls(home_page_response)
        novel_title = self.get_novel_title(home_page_response)
        novel_author = self.get_novel_author(home_page_response)
        cover_image_url = self.get_cover_image_url(home_page_response)

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

        if not threaded:
            chapters = self.download_chapters(urls, wait_time)
        else:
            chapters = self.download_chapters_threaded(urls, wait_time, retries)
        for chapter in chapters:
            book.add_item(chapter)
            book.toc.append(chapter)
            book.spine.append(chapter)

        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        epub.write_epub(novel_title + ".epub", book)
        click.echo(f"Downloaded {os.path.join(constants.get_root_dir(), novel_title)}.")


    def download_chapters(self, urls: list[str], wait_time: int) -> list[epub.EpubHtml]:
        """Download all chapters synchronously as epub.Html

            urls: list of urls to download
            wait_time: number of seconds to wait between downloading each chapter
        """

        chapters = []
        for i, url in enumerate(urls):
            chapter, chapter_title = self.get_chapter_page(url, i + 1, wait_time, 0)
            chapters.append(chapter)
            click.echo(f"Got {chapter_title} at {url} ({i + 1}/{len(urls)}).")
            time.sleep(wait_time)
        return chapters


    def download_chapters_threaded(self, urls: list[str], wait_time: int, retries: int) -> list[epub.EpubHtml]:
        """Download all chapters asynchronously as epub.Html

            urls: list of urls to download
            wait_time: number of seconds to wait between each try of downloading a chapter
            retries: number of times to retry downloading a chapter
        """

        chapters = [None for _ in range(len(urls))]
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.get_chapter_page, url, i + 1, wait_time, retries): (url, i) for i, url in
                       enumerate(urls)}
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                url = futures[future][0]
                index = futures[future][1]
                chapter, chapter_title = future.result()
                chapters[index] = chapter
                click.echo(f"Got {chapter_title} at {url} ({i + 1}/{len(urls)}).")
        return chapters


    def get_chapter_page(self, chapter_url: str, chapter_number: int, wait_time: int, retries: int) -> (epub.EpubHtml, str):
        """Get the page in the epub for the chapter

            chapter_url: the url to the chapter
            chapter_number: the chapter number
            wait_time: number of seconds to wait between each try of downloading a chapter
            retries: number of times to retry downloading a chapter

            returns the chapter page and the chapter_title
        """

        exc = None
        for retry in range(retries+1):
            try:
                chapter_response = self.scraper.get(chapter_url)
                chapter_title = self.get_chapter_title(chapter_response) or f"Chapter {chapter_number + 1}"
                chapter_text = self.get_chapter_text(chapter_response)
            except Exception as e:
                exc = e
                time.sleep(wait_time)
                continue
            else:
                chapter = epub.EpubHtml(title=chapter_title,
                                        file_name=f"{chapter_number + 1}_{"_".join(chapter_title.split(" "))}.xhtml")
                chapter.content = """<html>
            <h1>{chapter_title}</h1>
            {chapter_text}
            </html>""".format(chapter_title=chapter_title,
                              chapter_text="\n".join([f"<p>{line}</p>" for line in chapter_text.splitlines()]))
                return chapter, chapter_title

        raise Exception(f"Failed to get {chapter_url} after {retries} tries and waiting {wait_time} seconds because: \n\t{exc}.")


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
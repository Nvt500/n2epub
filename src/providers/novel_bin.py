import re
import requests

from src.downloader import Downloader


class NovelBinDownloader(Downloader):
    """Novel Bin"""


    def __init__(self, homepage_url: str) -> None:
        """Constructor"""

        super().__init__(homepage_url)


    def get_all_chapter_urls(self, _response: requests.Response) -> list[str]:
        """Get all chapter urls"""
        url = _response.url.rstrip("/")
        novel_id = url.rsplit("/", maxsplit=1)[1]
        response = self.scraper.get("https://novelbin.me/ajax/chapter-archive?novelId="+novel_id)
        return re.findall(r'<a\n.*href=["\']([^"\']*)["\']', response.text)


    def get_chapter_title(self, response: requests.Response) -> str | None:
        """Get the chapter's title"""

        try:
            return re.search(r'title: "([^"]*)"', response.text).group(1)
        except AttributeError:
            raise Exception(f"Cannot find the chapter's title at {response.url}")


    def get_chapter_text(self, response: requests.Response) -> str:
        """Get the chapter's text"""

        all_text = re.findall(r'<p>((?=.*</p>).*?)</p>', response.text, re.DOTALL)[:-3]
        return "\n".join(line.strip() for line in all_text)


    def get_cover_image_url(self, response: requests.Response) -> str | None:
        """Get the novel's cover image's url"""

        try:
            return re.search(f'<meta property="og:image" content="([^"]*)"', response.text).group(1)
        except AttributeError:
            raise Exception(f"Cannot find the novel's cover image at {response.url}.")


    def get_novel_title(self, response: requests.Response) -> str:
        """Get the novel's title"""

        try:
            return re.search(f'<meta property="og:novel:novel_name" content="([^"]*)"', response.text).group(1)
        except AttributeError:
            raise Exception(f"Cannot find the novel's title at {response.url}.")


    def get_novel_author(self, response: requests.Response) -> str | None:
        """Get the novel's author"""

        try:
            return re.search(f'<meta property="og:novel:author" content="([^"]*)"', response.text).group(1)
        except AttributeError:
            raise Exception(f"Cannot find the novel's author at {response.url}.")
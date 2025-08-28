import curses
import os
import re
import click
import ebooklib
from ebooklib import epub


@click.command()
@click.help_option("-h", "--help")
@click.argument("filename")
def read(filename: str) -> None:
    """Read a novel in the command line from an epub file"""

    try:
        if not os.path.exists(filename) or not filename.endswith(".epub"):
            raise Exception(f"File {filename} either does not exist or is not an epub file.")

        curses.wrapper(main_window, filename)
    except Exception as e:
        click.echo(f"Error occurred while reading:\n\t{e}", err=True)


def get_content(filename: str) -> list[tuple[str, list[str]]]:
    """Get the content of an epub file

        [
            (chapter_title, [
                lines_of_text_with_max_len_curses.COLS,
            ]),
        ]
    """

    book = epub.read_epub(filename)

    content = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        if isinstance(item, epub.EpubHtml) and item.file_name[0].isdigit():
            text = item.get_content().decode()
            title = re.search('<h1>((?=.*</h1>).*?)</h1>', text).group(1)
            lines = re.findall(r'<p>((?=.*</p>).*?)</p>', text)
            lines = text_to_lines("\n ".join(lines))
            content.append((title, lines))
    return content


def text_to_lines(text: str) -> list[str]:
    """Formats text to lines with max length of curses.COLS"""

    words = re.split(r' ', text)
    lines = []
    line = ""
    for word in words:
        if len(line) + len(word) >= curses.COLS:
            lines.append(line.strip())
            line = ""
            continue
        line += word + " "
        if word[-1] == "\n":
            lines.append(line.strip())
            line = ""
    if line.strip() != "":
        lines.append(line.strip())
    return lines


def main_window(window: curses.window, filename: str) -> None:
    """Manages the curses window"""

    window.keypad(True)
    window.scrollok(True)
    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)

    content = get_content(filename)
    start_line_index = 0 # The line to start rendering text from
    chapter_index = 0 # The index of the chapter to render

    render_chapter(window, content, start_line_index, chapter_index)
    while (key := window.getkey()) != "q":
        if key == "KEY_UP" and start_line_index > 0:
            start_line_index -= 1
        elif key == "KEY_DOWN" and start_line_index < len(content[chapter_index][1]) - curses.LINES + 1: # +1 for chapter title
            start_line_index += 1
        elif key == "KEY_LEFT" and chapter_index > 0:
            chapter_index -= 1
            start_line_index = 0
        elif key == "KEY_RIGHT" and chapter_index < len(content) - 1:
            chapter_index += 1
            start_line_index = 0
        elif key == "\t":
            if (new_index := manage_toc(window, content, chapter_index)) is not None:
                chapter_index = new_index
                start_line_index = 0

        window.clear()
        render_chapter(window, content, start_line_index, chapter_index)

    curses.nocbreak()
    window.keypad(False)
    curses.echo()
    curses.endwin()


def render_chapter(window: curses.window, content: list[tuple[str, list[str]]], start_line_index: int, chapter_index: int) -> None:
    """Renders the chapter's lines starting at start_line_index and ending when reaching curses.LINES and renders the chapter's title"""

    title = content[chapter_index][0]
    chapter_tracker = f" ({chapter_index+1}/{len(content)})"
    if len(title) + len(chapter_tracker) >= curses.COLS:
        title = title[:curses.COLS-len(chapter_tracker)-3] + "..."
    window.addstr(0, 0, title + chapter_tracker)
    y = 1
    for line in content[chapter_index][1][start_line_index: start_line_index + curses.LINES - 1]:
        window.addstr(y, 0, line)
        y += 1


def manage_toc(window: curses.window, content: list[tuple[str, list[str]]], chapter_index: int) -> int | None:
    """Manages choosing a chapter in the table of contents"""

    new_chapter_index = chapter_index
    y_position = 0 if chapter_index < curses.LINES else chapter_index - curses.LINES + 1
    while True:
        window.clear()
        render_toc(window, content, new_chapter_index, y_position)
        key = window.getkey()
        if key == "q":
            return None
        if key == "KEY_UP" and new_chapter_index > 0:
            new_chapter_index -= 1
            if new_chapter_index > curses.LINES - 2:
                y_position -= 1
        elif key == "KEY_DOWN" and new_chapter_index < len(content) - 1:
            new_chapter_index += 1
            if new_chapter_index >= curses.LINES:
                y_position += 1
        elif key == "\n":
            return new_chapter_index


def render_toc(window: curses.window, content: list[tuple[str, list[str]]], chapter_index: int, y_position: int) -> None:
    """Renders the table of contents and returns the chosen chapter's index"""

    y = 0
    for title, _ in content[y_position:y_position + curses.LINES]:
        if y_position + y == chapter_index:
            window.addstr(y, 0, title, curses.A_BOLD)
        else:
            window.addstr(y, 0, title)
        y += 1

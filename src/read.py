import curses
import os
import re
import click
import ebooklib
from ebooklib import epub

from src import constants


@click.command()
@click.help_option("-h", "--help")
@click.argument("filename")
@click.option("-s", "--select", "select", is_flag=True, default=False, help="Choose a novel from the directory of the executable.") # If I replace choose with select pycharm gets mad (bruh)
def read(filename: str, select: bool) -> None:
    """Read a novel in the command line from an epub file"""

    try:
        if select:
            filename = choose_novel()

        if not os.path.exists(filename) or not filename.endswith(".epub"):
            raise Exception(f"File {filename} either does not exist or is not an epub file.")

        curses.wrapper(main_window, filename)
    except Exception as e:
        click.echo(f"Error occurred while reading:\n\t{e}", err=True)


def choose_novel() -> str:
    """Choose a novel from the directory of the executable"""

    click.clear()
    dir = constants.get_root_dir()
    files = [path for path in os.listdir(dir) if path.endswith(".epub")]
    if not files:
        raise Exception(f"No epub files found in {dir}.")

    click.echo("Choose a novel by entering the number:")
    for i, file in enumerate(files):
        click.echo(f"{i+1}. {file}")

    while True:
        try:
            chosen_novel = click.get_text_stream("stdin").readline().strip()
            chosen_novel = int(chosen_novel)
            if chosen_novel < 1 or chosen_novel > len(files):
                raise Exception
        except Exception as e:
            click.echo(f"Choose a number between 1 and {len(files)}.\n", err=True)
            continue
        else:
            click.clear()
            return files[chosen_novel-1]


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
        if (key == "KEY_UP" or key == "w") and start_line_index > 0:
            start_line_index -= 1
        elif (key == "KEY_DOWN" or key == "s") and start_line_index < len(content[chapter_index][1]) - curses.LINES + 1: # +1 for chapter title
            start_line_index += 1
        elif (key == "KEY_LEFT" or key == "a") and chapter_index > 0:
            chapter_index -= 1
            start_line_index = 0
        elif (key == "KEY_RIGHT" or key == "d") and chapter_index < len(content) - 1:
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
        if (key == "KEY_UP" or key == "w") and new_chapter_index > 0:
            new_chapter_index -= 1
            if new_chapter_index > curses.LINES - 2:
                y_position -= 1
        elif (key == "KEY_DOWN" or key == "s") and new_chapter_index < len(content) - 1:
            new_chapter_index += 1
            if new_chapter_index >= curses.LINES:
                y_position += 1
        elif key == "\n" or key == " ":
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

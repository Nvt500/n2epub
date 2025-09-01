# n2epub changelog

## 0.1.2 - 9-1-2025 - Linux Support, Better Async, & Quality of Life Changes

- Linux binary built with workflows automatically and added to release
- Async doesn't immediately die if downloading more than 50 chapters
  - Downloads in groups which can be specified with `--max-workers`
  - It waits an increasing amount of time between each fail
    - First try is 3 seconds, second is 15, third is 30, and fourth is 60
  - Cuts down a lot of time although in order to not implode, it still takes time
    - 22 minutes to 12 minutes for 442 chapters
    - 3 minutes to 1 or 1.5 minutes for 60 chapters
- Added `--select` option to `read` command in order to easily choose a novel to read

## 0.1.1 - 8-28-2025 - Bugfix and New Command

- Added the `read` command in order to read any novels downloaded in the command line using `curses`
  (`windows-curses` for windows)
- Fixed naming of chapter files when creating an epub
  - The naming of chapters would start at 2 instead of 1 ie `2_Chapter_2` instead of `1_Chapter_1`

## 0.1.0 - 8-28-2025 - n2epub Created

- n2epub was created
- Providers implemented:
  - Novel Bin: https://novelbin.com/
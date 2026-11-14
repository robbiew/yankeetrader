# Notices

## Yankee Trader: Resurrection

The Go source, scripts, tests, documentation and research write-ups that make
up the reconstruction are Copyright (c) 2026 Robbie W. and released under the
[MIT License](LICENSE). The game builds against
[GoDoors](https://github.com/robbiew/godoors), which is also MIT-licensed.

## Original Yankee Trader 3.6 material

Yankee Trader was written by Alan Davenport (Copyright (c) 1989–1994 Alan
Davenport) and distributed as shareware. The MIT License does **not** cover
his work, and no rights in it are granted or claimed here. That includes:

- the original DOS distribution in [`archive/dos-original/`](archive/dos-original/)
  (executables, `.DOC`/`.TXT` files, `YTOPEN.ANS`/`YTOPEN.ASC` artwork);
- original artwork and text the Go game embeds or reproduces, such as
  [`internal/door/assets/`](internal/door/assets/) (title screen, opening
  artwork, instructions and help screens), which therefore also ship inside
  `yt` binaries;
- original game text, screens and binary excerpts quoted in
  [`research/`](research/), [`evidence/`](evidence/) and
  [`archive/`](archive/) for reconstruction and compatibility research.

The original distribution also contains third-party files under their own
authors' terms, such as `BRUN30.EXE` (the Microsoft QuickBASIC runtime) and
the `MARK.COM`/`RELEASE.COM` memory utilities. The player reference
spreadsheet [`archive/references/ytcalc.xls`](archive/references/) is a
third-party file kept under its author's terms.

This material is kept for preservation, interoperability research and faithful
reconstruction. If you are a rights holder and have concerns, please open an
issue.

## Other third-party material

- `research/yt-maint/clock-neutral-host/` contains excerpts of
  [DOSBox Staging](https://www.dosbox-staging.org/) source, Copyright the
  DOSBox Team and the DOSBox Staging Team, under GPL-2.0-or-later as marked in
  each file's SPDX header. They are kept as research evidence and are not
  compiled into Yankee Trader.
- Release archives bundle the licence texts of Go and the Go modules they are
  built from under `licenses/`.

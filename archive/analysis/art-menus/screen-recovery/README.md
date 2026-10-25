# Recovered DOS layouts and colors

`index.html` contains ten 80-by-25 screen references. Each has a text transcription, SVG, and PNG. The original cell bytes are retained in each run directory's `SCREENS.BIN`.

## Evidence

The original YT.EXE and YTCONFIG.EXE run in DOSBox Staging with copied test fixtures. A small resident capture utility copies the active B800 color text page: 2,000 character/attribute pairs per frame. This preserves screen placement, foreground/background attribute values, and the status bar. It avoids inferring columns or colors from redirected logs. The keyboard script waits between commands and captures only at explicit markers.

Recovered screens: startup, ship information, sector display, main command help, computer prompt and help, team menu, planet display and help, and sysop configuration. These capture one fixture player's state. Team membership changes visible choices; other game states and menus are not exhaustively captured.

The gallery maps attributes through the standard DOS palette. It uses modern monospace fonts, not recovered VGA glyph bitmaps; PNGs use Menlo. Blink is displayed steadily, and the hardware cursor is omitted. The raw buffer preserves attribute bytes and cursor metadata. These are local console screens; remote ANSI output has not been compared. Thus these are faithful character-cell references, not pixel-identical DOS screenshots.

Each frame is 4,016 bytes: 16 bytes of metadata followed by 4,000 screen bytes. Metadata words contain BIOS video mode/column byte, columns, active page offset, page-zero cursor position, then four zero words. The captured runs use video mode 3, 80 columns, page zero. `frames.json` records hashes and attributes; `provenance.json` and each run's provenance record fixture source and executable hashes. Existing `GAME.LOG` files record the same sessions without screen attributes.

## Reproduction

From the project root:

```
nasm -f bin analysis/art-menus/screen-recovery/capture.asm -o analysis/art-menus/screen-recovery/CAPTURE.COM
nasm -f bin analysis/art-menus/screen-recovery/dump.asm -o analysis/art-menus/screen-recovery/DUMP.COM
python3 analysis/art-menus/screen-recovery/run.py main
python3 analysis/art-menus/screen-recovery/run.py computer
python3 analysis/art-menus/screen-recovery/run.py config
python3 analysis/art-menus/screen-recovery/render.py
```

`png.py` additionally needs Pillow and the macOS Menlo font. The run script uses the local Homebrew DOSBox Staging executable. Runs overwrite only their own copied fixtures. The game may pause for its unregistered-copy notice before returning to DOS. The capture utility installs interrupt vectors only inside its isolated DOSBox process; it does not patch the game binaries.

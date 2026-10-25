# DOS planet menu and prompt comparison

Eleven isolated DOSBox Staging sessions captured **37 original 80×25 character/attribute screens** directly from B800 video memory. The source `YT.EXE` SHA-256 is `c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`. Each fixture is copied from its archived experiment's `before.dat` into a disposable directory. No archived binary or save is mounted or modified.

Reproduce with `python3 scripts/recover_planet_screens.py /absolute/new/directory`. DOSBox Staging runs with the DOS date October 24, 2026, midnight initial time, 200,000 CPU cycles, dummy video/audio, and the preserved `CAPTURE.COM`/`DUMP.COM` utilities. `@` captures cells without a key; `~` waits 36 BIOS ticks. All captures stay below the utility's 12-frame limit. Each 4,016-byte frame retains 16 bytes of BIOS metadata followed by 4,000 interleaved character/attribute bytes.

| Session | Captured stages |
| --- | --- |
| menu | Landing/display, `?` help, `D` redisplay |
| transfer | `T` submenu, fighter quantity, successful fighter transfer |
| cargo | Completed cargo deposit and refreshed display |
| bank | Desired final balance prompt and completed deposit |
| invest | Expenditure prompt, productivity receipt, refreshed production |
| garrison | Target garrison prompt and completed force transfer |
| takeall | `A` receipt and refreshed inventories |
| create | Purchase, name, confirmation and successful creation |
| foreign | Landing denial, force-landing prompt and declined assault |
| take-cargo | Ore, organics and equipment quantity prompts and completed takes |
| take-weapons | Fighters, missiles, mines and plasma quantity prompts and completed takes |

Directories contain raw `SCREENS.BIN`, exact DOS key streams, compressed original game/emulator logs, and provenance. `verify_planet_screens.py` verifies executable/fixture/input/tool hashes, keystrokes, screen/transcript hashes, frame counts, BIOS geometry/cursor bounds, scenario prompts and return to the original DOS launcher.

## Rendering recovered from the cells

Landing and creation start with the green `<Land/Create planet>` label. Existing-planet reports, help, submenus, prompts and receipts use DOS cyan (foreground 3) on black. Typed responses are gray (7). Permission `DENIED!` is bright yellow with blink (attribute `8e`); the garrison receipt is bright cyan with blink (`8b`); the fighter transfer receipt uses cyan with blink (`83`). The sector's planet/forces line is bright yellow.

The report has nine rows, in this order: ore, organics, equipment, fighters, missiles, mines, credits, ground forces and plasma bolts. Labels are 13 characters, dotted as captured. Production ends at column 26, planetary amount at 37 and carried amount at 49. Blank lines separate the report, free-holds message and `Planet command (?=help) [A]?` prompt. Help and transfer menus preserve the original keys. Captured odd closing parentheses in `<Take Organics)` and the equivalent equipment/weapon titles are retained.

The report derives all fields from the current world. Its displayed 1% production estimates use the original single-precision constant, matching DOS's displayed 99 daily credits for a 10,000-credit bank and zero daily forces for a garrison of 100. This display rounding does not change the backend's exact integer bank balances or interest, or restore the DOS money-rounding exploit. Other rates use the existing production/interest model.

## Native implementation and validation

`smoke_planet_parity.py` drives the actual native game through real PTYs and compares **all 37 captured stages** within their planet-body regions: exact characters/positions, visible foregrounds, and all backgrounds. Only time-left digits are dynamic in those regions. Blank cells' invisible foreground attributes are ignored, as in the port comparison; their backgrounds remain checked. Status/caller labels and preceding startup/sector history remain live and outside the body comparison. Snapshots omit cursor glyphs, fonts and blink animation. Native ANSI blink sequences for the three captured messages are checked separately; PNGs show their steady phase.

Native fixtures read the preserved DOS fixture fields, map the two human IDs into the Go world, and use the current clock for lazy production. Tests check saved credits, inventories, production investment, garrisons and landing tokens. A real Enter tests the default take-all action against the original explicit-`A` receipt. Every scenario also runs with `--ascii`, checking that no ANSI or non-ASCII bytes appear. `--render` optionally regenerates paired DOS/Go PNGs using Pillow/Menlo; CI needs neither image dependency.

The interface uses the existing rules for all committed actions. It rechecks landing tokens, current permission, balances, stock and capacity under the store lock. Creation commits only after confirmation and rejects a sector change while naming. A replacement landing retains its own token when an old session leaves. Unit tests cover default/zero quantities, invalid input, denied/changed access, insufficient funds, cancellation, disconnects before/after a commit, and session replacement.

`N` renaming is now implemented and separately verified in [the rename recovery](../yt-planet-rename/RECOVERY.md). `!` (thrusters) and forced landing remain unavailable because those Go game actions are not implemented. Their historical menu/prompt is retained and selecting them reports the limitation without changing the world. Invalid numeric input uses the existing safe integer rules; large-number formatting, timing, complete game parity and real BBS deployment are not asserted. `-compact` keeps the existing explicit commands.

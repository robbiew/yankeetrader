# DOS-style startup and first menus

Recovered 2026-10-25 from the preserved Yankee Trader 3.6 DOS executables and
original artwork. The Go frontend now defaults to this sequence; `-compact`
retains the previous command frontend. This is a startup/presentation milestone,
not a claim of full DOS game parity.

## Original evidence

The archive already preserved 80×25 B800 character/attribute captures of the
startup, ship information and menus. Two additional isolated DOSBox sessions
capture the new-player and returning-player paths in this folder:

- `new/`: seven frames, with original key stream, transcript and provenance.
  LOCAL NEWTRADER opens the game, selects Pilot, confirms it, declines
  instructions, pauses at ship information, enters the main prompt and displays
  help. The DOS ship starts with one missile, 100 shields and full cloak; those
  are observed DOS values, not current Go-world values.
- `returning/`: four frames from LOCAL TESTER using the copied existing world.
  A snapshot after typing `?` **before Enter** still shows the sector prompt;
  after Enter it shows help. Main commands therefore retain line entry rather
  than being implemented as immediate hotkeys.

Both use `archive/analysis/yt-combat/experiments/team-transfer-current/before.dat`
as the initial world. Originals were never mounted or modified. The resident
capture utility records 16 metadata bytes followed by 2,000 character/attribute
pairs per frame. Captures use DOS date/time 2026-10-24 00:00:00, advancing while
keys are fed. These are local-console observations; they do not establish remote
DOS ANSI parity.

The target YT.EXE SHA-256 remains
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
REA 6.8.0/Ghidra 12.1.4 returned alias-prompt string evidence
`ev_8bb694bd3ea038873f51975c596cb8140efc5449822a8b341ffee27ad60bdd63`
and exact startup bytes at `0x1b721`, evidence
`ev_45dfd36b3ee695b1aa11a33905b8721a19be89bd30acea80b064527e14b220cc`.
The [exported bundle](rea-evidence.json) retains both. The runtime-aware main
listing at `1000:b721..b9d8` supplies alias prompts, reserved names, duplicate
checking and confirmation; the sub2 listing at `2e79:1035` supplies ship info.
Static runtime selectors are interpreted alongside the DOS captures, not accepted
as decompiler-proven gameplay rules.

## Implemented sequence

1. Resurrection title adapted from the original positions/colors; press any key.
2. YTOPEN ANSI art or ASCII welcome with Resurrection branding and a repository
   link replacing old contact details, with its own key pause before
   Initializing and caller lookup.
3. For new players, enter and confirm an in-game alias. Enter selects the real
   name from Door32, or the local caller name. Reserved/duplicate aliases are
   rejected. A player is created only after confirmation, with alias uniqueness
   rechecked inside the store transaction.
4. New players choose whether to page through the preserved original manual.
5. Ship information is rendered from current player, port-ownership and world
   state using the recovered table skin. Press any key to continue.
6. Sector/port/planet/warp display, then the timed main command prompt.
7. Enter redisplays the sector; `?` draws the original main help; `C` exposes the
   original computer menu. Options 3, 7 and 10 connect to autopilot, avoid edits
   and path finding. `M;sector` and quit confirmation consume stacked input.

ANSI output reserves the bottom status row while the upper 24 rows scroll.
While waiting for a main/computer command, the remaining session time refreshes
without discarding typed input. Local ANSI output maps CP437 to UTF-8; remote
ANSI output keeps the original bytes. Plain text emits neither ANSI controls nor
CP437 box bytes. The embedded title, info skin and main-help templates are copied
from the original 4,000-byte character/attribute pages. Opening art/manual bytes
are copied through the DOS Ctrl-Z EOF marker; `assets.json` records hashes.

The live title, opening page and optional manual pages say “Original game by
Alan Davenport” and “Based on Yankee Trader Version 3.6.” The title and opening
also show project version 0.1.0 and the GitHub link. Old compilation date,
registration notices and BBS contact details are replaced. Embedded source
assets and archived captures remain unchanged.

## State and compatibility

A chosen alias persists across both classic and compact reconnects even if the
BBS display handle changes. Stable identity still comes from BBS namespace and
record number. Unconfirmed or escaped onboarding does not create a player;
EOF/disconnect ends the session. Confirmed actions retain the existing
transactional save guarantees.

`LastLogin` is an optional UTC date, written on DOS-style login, to avoid falsely
claiming an unknown previous visit happened today. Older saves omit it and load
normally. Previous strict-decoder binaries reject this new field even though
world Version remains 2. Back up the world before upgrading; a backup restore
loses subsequent progress. Alias input remains bounded to the existing printable
1–41-character game name constraints.

## Fidelity boundaries

- The Go world has no radio inbox, scanner or cloak state. The frontend marks
  those unavailable instead of copying fixture readings. It does not invent
  Orion membership, a captain role, credits, port counts or equipment.
- DOS's new-player inactivity/death deletion notice is omitted because that
  lifecycle is not implemented. Existing Go starting inventory and UTC
  maintenance are preserved; UI work does not silently add DOS equipment.
- Original menus/manual include unimplemented combat, team, ownership and
  other functions. Selecting them reports unavailable. Planet/port/trade submenus
  retain their current Go workflows; this milestone does not recreate every DOS
  submenu. Classic `L` lands;
  `LOOK` preserves access to sector display, and compact `L` is unchanged.
- The opening file is emitted promptly and paused explicitly so fast terminals
  can read it before the ship-information screen clears it. This readability
  pause does not assert original DOS timing. Runtime output translates the
  asset's CSI save/restore controls to VT100 equivalents; embedded source bytes
  remain unchanged. DOS's evaluation delay, sound effects
  and transfer-speed pacing are not emulated. The separate LOCAL.EXE launcher
  banner is not reproduced as if it were part of the Go game.
- The terminal remains byte/ASCII-oriented for typed names/commands. The default
  80×25 layout is not a responsive terminal UI; use plain or compact output for
  unsuitable terminals. Modern-font PNGs preserve cells/colors, not VGA pixels.

## Validation and reproduction

`python3 scripts/verify_startup_evidence.py` verifies 11 original frames,
transcript/keystroke provenance and embedded asset identity. The real PTY smoke
compares all 2,000 title cells/attributes against the DOS template plus explicit
branding overlays, and the first 23 main-help rows against DOS, while checking live stats, alias persistence, key pauses, computer menu,
Escape cancellation and ASCII fallback. It holds both opening and info screens
without sending a key and checks their cells stay unchanged; new, returning,
ASCII and CRLF-title-input paths are covered.

```sh
python3 scripts/recover_startup.py /tmp/yt-startup-new
python3 scripts/verify_startup_evidence.py
go test -race ./...
go vet ./...
go build -o bin/yt ./cmd/yt
python3 scripts/smoke_startup.py
python3 scripts/smoke_navigation.py
python3 scripts/smoke.py
```

The recovery runner finds DOSBox Staging through PATH or `--dosbox`, uses a new
disposable directory and preserves original files. Startup smoke uses only
stdlib Python and disposable Go worlds. Optional `--render` adds PNGs with
Pillow and the macOS Menlo font; CI verifies cells without those dependencies.

Rendered PTY captures: [opening artwork](../../evidence/startup/opening.png), [title](../../evidence/startup/title.png),
[ship information](../../evidence/startup/info.png),
[main help](../../evidence/startup/help.png), and
[computer menu](../../evidence/startup/computer-help.png).

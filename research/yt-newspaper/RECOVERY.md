# Galactic newspaper and news history — research

Thirteen isolated original DOS processes (eleven YT.EXE sessions and two
YTMAINT.EXE runs) establish computer option 8, Today/Yesterday selection,
public login/team-creation events, persistence and maintenance rotation.
This research does not implement Go newspaper gameplay. It is based on the
unchanged original binaries, controlled copied inputs and completed runtime
paths, rather than the manual's broad claim that nearly everything is logged.

## Findings

| Probe | Observed result |
| --- | --- |
| `today` | `C;8;T` prints today's seeded lines in order and the public login entry |
| `yesterday` | `C;8;Y` prints yesterday's lines; today's lines/login remain absent |
| `invalid-choice` | `X` repeats the selection prompt; subsequent `T` reads today |
| `lowercase` | Lowercase `t` is accepted |
| `empty-today` | An initially empty today file contains a login entry before the query |
| `empty-yesterday` | An existing empty yesterday file produces no entries or missing-file error |
| `missing-yesterday` | A missing file prints `*** GAME FILE [YTYNEWS.DAT] NOT FOUND! ***` and appends that error to today's news |
| `dos-eof` | Login append removes bytes at/after today's DOS Ctrl-Z, then writes the login entry and a final Ctrl-Z |
| `yesterday-eof` | Reader stops at Ctrl-Z, omitting the hidden suffix while preserving the entire yesterday file on disk |
| `team-created` | A real team creation appends `Q  Created Team 1 -=- News Team`; no invitation password enters public news |
| `team-reconnect` | Reopening the exact post-creation world and news files retains the event and adds one more login entry |
| `rotate-next-day` | Next-day maintenance copies today's lines into yesterday, replacing the previous yesterday history; new today begins with maintenance output |
| `rotate-same-day` | Maintenance prints `Maintenance not needed!` yet still rotates and executes its maintenance path |

All eleven game sessions preserve the caller's 500 turns, sector 1, credits,
cargo, fighters, shields, cloak and other ship resources. Team creation changes
team metadata as intended; normal logout publishes score caches. These are
resource-neutral queries, not byte-identical whole-world runs. The two maintenance
runs intentionally mutate the world and are not resource-conservation controls.

The file snapshots distinguish activity before selection from the read itself.
An empty today file is **not** evidence of an empty reader: login populates it.
Similarly, today's Ctrl-Z probe alone cannot establish reader EOF handling:
login has already truncated the suffix. The separate empty/EOF yesterday controls
avoid both confounders. Yesterday remains byte-for-byte unchanged during every
game query, including its hidden EOF suffix in the dedicated control.

## Static evidence and provenance

`rea.json` retains complete Ghidra 12.1.4 byte Evidence against YT.EXE SHA256
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`:

- `1000:8ca5..8d2e`: option 8 dispatch, validated `T`/`Y` choice, filenames
  `ytnews.dat` / `YTYNEWS.DAT`, and call to the shared text-file reader.
- `1000:a57c..a6b4`: sequential reader, EOF/stop checks and text-prefix color
  selection. Prefixes `  - `, ` ***`, ` +++` and `-=*` select display classes.
  Plain transcripts establish characters/order; they do not validate exact
  runtime screen attributes or pagination/interrupt behavior.
- `1f42:1a9b..1ad5`: shared newspaper append routine targeting `ytnews.DAT`.
- `1000:58b3..58ed`: team-created event formatting and append call.

`maintenance-rea.json` retains the rotation block `1000:68db..691e` against
YTMAINT.EXE SHA256
`8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6`.
The independent verifier reconstructs each MZ image and relocation fixups before
comparing every byte. Coordinates are loaded linear addresses using segment
0x1000. Control-flow interpretations also use the preserved QuickBASIC annotated
listings; byte reads are not a claim that Ghidra decompiled BASIC.

The seeded TODAY/YESTERDAY marker lines are explicitly synthetic file contents
for reader/rotation tests. Login and team creation are **real gameplay-produced**
public events. The team case uses normal `T;2` prompts and password ABCD in a
throwaway fixture. The reconnect case consumes its exact saved world/news files,
not a reconstructed approximation. All full before/after worlds, before/after
news files (including empty/missing distinctions and Ctrl-Z), keystrokes,
transcripts, emulator logs and hashes are retained under `dos/`.

## Reproduction and verification

With DOSBox Staging installed:

```
python3 scripts/recover_newspaper.py /private/tmp/yt-newspaper-new
python3 scripts/verify_newspaper.py /private/tmp/yt-newspaper-new
python3 scripts/verify_archive.py
```

The runner makes new disposable directories from the archived
`fixture-team-create` source and mounts only those copies. It patches player 2's
sector to Earth and team membership to zero, leaving login/account metadata and
all other fields intact. Game time starts at 00:00:00 on 10/24/2026; next-day
maintenance uses 10/25/2026. Four independent DOS workers are used, followed by
the linked reconnect. Neither original EXE nor archive data is modified.

`expected.json` fixes intended commands, selected report text, absent cross-day
text and selection-prompt counts. `verify_newspaper.py` checks scenario coverage,
full-world input reconstruction, exact reconnect chaining, every retained file's
hash, resource conservation, actual event suffixes, password absence, normalized
rotation plus raw Ctrl-Z bytes, same-day maintenance fallthrough and REA bytes.
A rehashed wrong-day rotation and rehashed false report transcript are rejected
by independent semantic controls, rather than accepted merely because hashes
were updated. CI verifies the preserved evidence without requiring DOSBox.

## Implementation contract and remaining boundaries

The next implementation can expose computer 8 plus `NEWS [TODAY|YESTERDAY]`,
using server UTC dates with clear day labels and a friendly empty-history message.
Keep public events distinct from private radio and session spy intelligence.
Append a typed event in the same authoritative transaction as its successful
action; rejected/cancelled operations must produce no success event. Record
public aliases/team names at event time, never identities, docking/session tokens,
invitation secrets or private planet/account balances. Render bounded safe text
with pagination and reject stale/dead sessions before disclosing a page.

Use the existing once-per-UTC-day maintenance guard. Do **not** reproduce the
DOS same-day history loss or log a player-visible missing-file diagnostic as a
world event. The original two-file history retains only today and yesterday;
a bounded dated journal is a deliberate modern storage adaptation and needs an
explicit retention, missing-day and migration policy. Do not silently backfill
unrecorded historical events from current ownership or scores.

The first proven event producers are login and team creation. The static caller
inventory also contains registration/replacement, planet creation, acquisition
and combat paths, but those event formats and trigger boundaries need targeted
validation before they are advertised as recovered. Exact DOS colors, long-file
paging, Ctrl-X interruption, missing-today startup, corrupt/binary input,
concurrent DOS writers, every event category, timezone behavior and crash-safe
DOS rotation remain unverified. Research does not establish a generic promise
that every action belongs in public news.

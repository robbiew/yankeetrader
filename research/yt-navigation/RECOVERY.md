# Navigation and sensors: first playable slice

Recovered and validated 2026-10-25 against the preserved Yankee Trader 3.6
`YT.EXE`, SHA-256
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
REA 6.8.0 and Ghidra 12.1.4 supplied static evidence; DOSBox Staging executed
isolated copies. No original executable, archived Ghidra project, or live save
was modified. There was no existing GitHub issue in this repository at inspection.

## Findings and evidence

| Question | Confirmed result | DOS cases |
|---|---|---|
| What does `S` scan? | Six outgoing adjacent sectors in stored warp order, excluding the current sector. Shows port name/selling type, planet name/ground forces, other uncloaked ships/fighters/shields, and each sector's outgoing warps. | sensors, sensors-zero |
| Does scanning require turns? | No turn charge, and scanning works with zero turns. | sensors, sensors-zero |
| What does normal movement cost? | One turn per outgoing adjacent hop. One remaining turn permits a hop, leaving zero. Nonadjacent movement and movement at zero turns are rejected without moving or charging a turn. | move, move-last, move-invalid, move-zero |
| Does path finding move or charge? | No. Computer option 10 reports an explicit start-to-destination route and its hop count. | path, path-reverse |
| How are routes selected? | Shortest directed path. Equal-length alternatives follow stored warp order in the tested graph; reverse travel can take a different route. | path, path-reverse |
| How does autopilot work? | Computer option 3 plots from the current sector, asks for confirmation, then executes ordinary `M` commands one at a time. Four hops cost four turns. | autopilot |
| What if cancelled or underfunded? | `N` leaves position/turns unchanged. A course costing four turns is rejected with only three available. | autopilot-cancel, autopilot-short |
| Same or unreachable destination? | Same-sector path is rejected. An unreachable destination reports no acceptable path; neither case moves or spends turns. | path-same, path-unreachable |

These are **13 completed DOS sessions**, with 26 compressed full before/after
saves, raw keystrokes, emulator logs, readable transcripts and a
[manifest](dos/results.json). `scripts/verify_navigation_evidence.py` checks
hashes, snapshot fields, transcript completion, scan contents, routes, and the
matching Go fixture. The two shortest-path examples are
`100 -> 101 -> 107 -> 109 -> 110` and
`101 -> 107 -> 109 -> 110 -> 100`. This demonstrates why a reverse-link assumption
would be wrong. The first graph also has an equal-length alternative through
102/108, which DOS does not select.

Whole saves may change during login, quitting and sensor cartography updates;
the no-turn/no-movement claims compare player position/turn fields, not whole-save
identity. The Go scanner is read-only: DOS's port last-seen bookkeeping is not
modeled by this slice.

## Static investigation using REA

The [REA evidence bundle](rea/evidence.json) retains five observations:

- Load-image verification `ev_03514cdc41e9c75482e17cee3453202b476020e2c67335ece260857148a762e9`
  returned `verified`, with DOS real-mode language and load segment `0x1000`.
- String searches `ev_ed204934008f805f8f7d2477d4ede99a8d079b9cb6dd6c7b33f887696e5f5647`
  and `ev_0d62f6dc6ebfa33bd94f168bca08d474f5107746bdeb34d1d4a971cf9c73ecd8`
  found danger-scanner/runtime text but not the ordinary sensors heading. This
  is a bounded negative result over Ghidra-defined strings, not proof of absence.
- Exact byte reads `ev_2fb42887d18214446939bf3489da975dd9aafd516394bf13924a192d90b19055`
  at `0x116bc` and
  `ev_19e24bd9a38fafdc966311c0957eac325e07517f390eb3b4ac344b7010cb6566`
  at `0x24ddc` match the existing runtime-aware dispatch/listing.

The archived annotated listings establish the following interpretation anchors:

- Main `1000:16bc..16d8`: dispatch `S`, enable sensor flag, invoke display.
- Main `1000:162f..1656`: call display at normalized `1f42:59bc`.
- Sub `1f42:59bc..6320`: adjacent-sector iteration, sensors header, port/planet/
  ship/defense output, outgoing warps, pagination.
- Sub `1f42:1016..13c7`: breadth-first traversal over the six stored outgoing
  links and a predecessor/queue structure; supports a separate avoid list.
- Main `1000:8f0c..92cc`: path start/destination, route display, turn budget,
  confirmation and generation of stacked ordinary movement commands.
- Main `1000:a848..a8c1`: turn deduction and exhausted-turn handling.

QuickBASIC's inline runtime calls still require the annotated decoder and DOS
experiments. REA's verified import does not establish correct decompiler control
flow, complete function discovery, or runtime behavior.

## Go behavior and deliberate safeguards

- `S` (`SCAN`/`SENSORS`) displays current public observations of outgoing adjacent
  sectors. Ship output contains alias, team, fighters and shields; it does not
  expose identity keys, credits, cargo, bank balances or session tokens.
- `PATH <start> <destination>` is free. `AUTO <destination>` displays the course
  and requires `Y`; an empty response cancels. These direct commands fit the
  existing Go command interface; the DOS computer menu is not recreated here.
- `M` remains unchanged, and `L` retains the existing Go look command.
- Every autopilot hop reloads authoritative state under the store lock and
  commits before output. Position changes, insufficient remaining turns,
  expired session time, Ctrl-X, or a failed terminal write stop the course.
  Completed hops stay spent; stale courses never teleport or restore old state.
- Ctrl-X is checked between hops. Other received keys are retained for the next
  prompt. The entire route is not an atomic transaction: disconnecting after
  one successful hop preserves that hop.
- Tests exercise actual DOS route/accounting fixtures, zero-turn scanning,
  rejected hops, confirmation, interruption, disconnect, and competing state
  changes. The PTY smoke script exercises real GoDoors I/O and persistence.

## Avoid-list follow-up — 2026-10-25

Ten additional original DOS sessions establish the 30-slot editor and its
routing effects. See [the manifest](avoid-dos/results.json), compressed saves,
keystrokes and transcripts. `scripts/verify_avoid_evidence.py` verifies 20 more
save snapshots plus matching Go fixture provenance. Combined with the first
slice, the evidence covers **23 completed DOS sessions and 46 save snapshots**.

- `avoid-reroute`: slot 1 blocks 101; the route switches to
  `100 -> 102 -> 108 -> 109 -> 110` without spending turns.
- `avoid-block`: blocking both 101 and 102 prevents any route to 110.
- `avoid-start` / `avoid-destination`: an avoided endpoint rejects the path.
- `avoid-clear`: setting slot 1 back to zero restores the original route.
- `avoid-slot30`: the last of the 30 slots is effective.
- `avoid-slot31` / `avoid-invalid-sector`: invalid slot/sector input does not
  alter the route or spend turns.
- `avoid-manual`: ordinary movement into avoided sector 101 still succeeds,
  costing exactly one turn.
- `avoid-reconnect`: reopens the completed `avoid-reroute` world's saved output;
  all 30 slots are zero and the original route returns. The before snapshot
  exactly matches that source session's after snapshot. The DOS list is
  session-only in this tested login path.

REA's [avoid-editor byte evidence](rea/avoid-evidence.json),
`ev_63f4fe624f599b24fa55b2b1307bb65c01d522d9e910a8bba44e4f4ef7417243`,
reads 44 bytes at linear `0x18b89`. This matches the annotated menu code's slot
lookup and assignment into the 30-entry array at logical DS `18b8`.
Main `1000:8959..8c4b` contains the editor, slot/sector bounds and zero-to-clear
operation; sub `1f42:107f..1100` applies the avoid entries before traversal and
handles avoided endpoints. These static leads were checked against the sessions
above, rather than treated as proof on their own.

Go now exposes `AVOID` and `AVOID <slot 1-30> <sector>` (zero clears a slot).
Edits are validated and saved under the world lock with no turn charge. The list
is private to each player and controls both `PATH` and `AUTO`; manual movement
and scanning ignore it. Numbered slots permit repeated sector entries.

**Deliberate departure:** Go persists the list across reconnects. DOS resets it
in the tested path. This avoids silently dropping a player's routing preferences
when a connection ends. Existing version-2 saves with no `AvoidSectors` field
load with an empty list; invalid sectors or more than 30 stored entries are
rejected. Each autopilot hop revalidates the entire remaining route against live
preferences, position, links and turn budget. A newly avoided future sector stops
the course immediately, preserving previously committed hops.

Save compatibility is forward-only after a successful avoid edit: `AvoidSectors`
is written even when all 30 slots are subsequently cleared, and the version
stays at 2. Older strict decoders reject this field. Preserve a pre-edit backup
before returning to an older binary; restoring it loses subsequent progress.

Session tests cover changed preferences during confirmation and after a committed
hop. The real PTY smoke covers rerouting, reconnect persistence, clearing, Ctrl-X
and preservation of the queued quit key. Hazard and emergency-warp behavior is
still not implemented.

## Remaining boundaries

This is not complete navigation or scanning parity. Sector mines/fighter forces,
cloaked-ship detection and danger-scanner failure probabilities, emergency warps,
NPC encounters and utility/computer
reports remain separate work. Current Go sectors have no hazards or cloak
state; scans report the real fields that exist instead of inventing hazard
readings. Landing remains governed by the existing planet permissions.

The DOS tests here use empty sector defenses and an uncloaked human ship. They
do not demonstrate safe travel through hostile sectors. Introduce encounter and
death/session invariants before enabling combat hazards in Go.

## Reproduction

```sh
python3 scripts/recover_navigation.py /tmp/yt-navigation-new
python3 scripts/verify_navigation_evidence.py
python3 scripts/verify_avoid_evidence.py
go test -race ./...
go vet ./...
go build -o bin/yt ./cmd/yt
python3 scripts/smoke_navigation.py
```

The DOS runner requires DOSBox Staging on `PATH` (or an explicit `--dosbox` path);
the destination must not exist. It mounts disposable fixtures, never the archive.
Each case fixes DOS date/time to 2026-10-24 00:00:00 to match the source login
fixture; actual simulated seconds advance while the key feeder runs. The
packaged evidence can be checked without DOSBox or running any DOS executable.

To reproduce the avoid-list suite in separate disposable directories:

```sh
python3 scripts/recover_navigation.py /tmp/yt-avoid-new --only \
  avoid-reroute avoid-block avoid-destination avoid-start avoid-manual \
  avoid-clear avoid-slot30 avoid-slot31 avoid-invalid-sector
python3 scripts/recover_navigation.py /tmp/yt-avoid-login \
  --source /tmp/yt-avoid-new/avoid-reroute --only avoid-reconnect
```

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

## Remaining boundaries

This is not complete navigation or scanning parity. Sector mines/fighter forces,
cloaked-ship detection and danger-scanner failure probabilities, emergency warps,
autopilot avoid-list editing/persistence, NPC encounters and utility/computer
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
go test -race ./...
go vet ./...
go build -o bin/yt ./cmd/yt
python3 scripts/smoke_navigation.py
```

The DOS runner requires DOSBox Staging at `/opt/homebrew/bin/dosbox-staging`;
the destination must not exist. It mounts disposable fixtures, never the archive.
Each case fixes DOS date/time to 2026-10-24 00:00:00 to match the source login
fixture; actual simulated seconds advance while the key feeder runs. The
packaged evidence can be checked without DOSBox or running any DOS executable.

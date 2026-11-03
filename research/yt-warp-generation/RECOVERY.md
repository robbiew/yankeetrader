# DOS warp-generation rules

Checked 2026-11-02 against the archived Yankee Trader 3.6 initializer. Ordinary
warps, long warps, isolation repair and Earth shortcuts are now implemented as
an independently opt-in new-world profile. This is rule parity with documented
modern safeguards, not exact QuickBASIC seed-to-map replay.

## What was already recovered

The earlier [initializer report](../yt-init/RECOVERY.md) identified six warp
columns, sector-record offsets and the broad initialization phases. The retained
DOS validation and port-generation worlds already supplied complete final maps.
They did not establish all edge-selection rules, repair traversal, shortcut
stepping or fractional index rounding. The established Go generator used a
bidirectional ring plus four additional distinct exits per sector.

This milestone reuses that archive, recovers the missing algorithm, retains
native observations, isolates phases with declared copied-executable controls,
and implements the verified rules. Original archival binaries remain unchanged.

## Available in the Go game

```sh
./bin/yt -data dos-map -init -dos-warps -seed 36
./bin/yt -data dos-map -local Player

# Both recovered generation profiles, in a separate new world:
./bin/yt -data dos-universe -init -dos-warps -dos-ports -seed 36
```

`-dos-warps` and `-dos-ports` are independent and initialization-only. Omit either
flag to retain that subsystem's established generator. Explicitly supplying either
flag, even as `=false`, outside initialization is rejected. Existing worlds are
never overwritten by initialization or regenerated on upgrade/login/maintenance.

Save 34 adds `WarpGeneration: "dos"`. Supported older worlds upgrade without
changing their complete map or selecting the new profile. Existing save 33 port
profiles retain their economy. Genesis and administrative reset preserve both
settings independently, bind map settings to the Genesis quote and create fresh
maps from the new seed. Full-world export/restoration includes both settings and
the actual saved sectors. Older binaries cannot read save 34; restore a matching
stopped backup when rolling back. DOS `.DAT` import/export remains unsupported.

The generation table retains all six slots internally, including holes. Publishing
filters zero slots while preserving relative order and removes only Earth's
redundant self-warp. Every published sector has 1–6 valid distinct external exits;
Earth's ordered exits are 2,3,4,5,6. Both forward and reverse Earth connectivity
are checked before a candidate is returned. No live save receives a partial map.

## Recovered algorithm and native evidence

Target: `archive/dos-original/YT-INIT.EXE`, SHA256
`601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2`.
Runtime: `BRUN30.EXE`, SHA256
`3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8`.

The six int16-like columns use DS 185a, with stride 3001; sector 0 is reserved.
Sector record `51+s` stores the six destinations at offsets 41,45,49,53,57,61.
Ghidra loaded addresses use base 0x10000. Code offset `o` maps to file `o+0x200`;
constants below use actual file offsets. `rea.json` retains eight complete byte
observations, independently checked against the relocated MZ image. Two extra
uninterpreted memory windows are retained but are not grounds for algorithm claims.

| Phase | Recovered rule | Initializer main offsets |
| --- | --- | --- |
| Earth seed | For column0..5, place reciprocal links `Earth↔column+1` in that column; includes Earth1→1 | `0e0b–0e6f` |
| Local links | Visit sectors ascending, columns0..5. First draw≤MBF0.4 and column<5 attempts an offset1..10. Reverse the offset strictly when sector>`N−10`. Both matching slots must be free, and no pair may already exist in either direction in any column | `0eca–1067` |
| Long links | Column5 only, if empty: separate draw≥MBF0.985; sample destination1..N, require nonself and its sixth slot empty, then write a reciprocal pair. Self-target returns to the chance gate | `106b–113a` |
| Empty rows | Repeat the same sector if it has no exit after all six attempts | `1160–1209` |
| Isolation repair | Ascending targets2..N, persistent reached set, fresh BFS from Earth when needed; inspect all six slots in order. If unreachable, select an earlier sector with free sixth slot and connect its sixth slot to the target, replacing the target's sixth slot | `1283–130f`, `13d3–1636` |
| Earth shortcuts | `x=8+400*RND`; while `x<N`, convert x to an integer, write a directed sixth-slot return to Earth only if empty, then `x=x+400*RND` | `1369–13cd` |

The helper at `004f–006c` implements `INT(RND*bound)+1`. The MBF constants at
file0x2f44/0x2f4c/0x2ff6 are 0.4/0.985/400. Native Evidence IDs for the main
construction, repair and constant reads include
`ev_4ce820ec659fc447067e45ad6d7d706bf0dc8dc0e1544299d6cd2d678649b9ae`,
`ev_5a07cdb74ec1888cb70450606002dc0f97b72638e1c6ff5f85e7e54e60a66a66`,
`ev_3d2086b9f39fe17d897d63c581fad5a1388af2f17987312fa62febdc6a089072`
and `ev_618d74ed7356bb2a1cb9522959e7ca9212d23f4acac339fb3e6accce96201120`.
These are static observations, not execution traces.

BFS maintains predecessor/queue arrays per search and a reached array across
searches. It scans all six neighbors of a popped sector before testing for target
completion. All earlier sectors are Earth-reachable by induction; repair selects
only an earlier source. DOS repeatedly samples until that source's sixth slot is
free. Logged repair pairs read **target then source**, not source then target.
The original visits the reserved zero row harmlessly; the modern BFS skips it.

## Controlled DOS phase captures

`python3 scripts/recover_warp_generation.py /tmp/new-warp-captures` runs copies
in a new disposable directory under DOSBox Staging. Date 11/02/2026 and midnight
are fixed. The original initializer is unpatched in the original case; the other
cases declare exact byte replacements in disposable copies:

| Case | Patch | Purpose |
| --- | --- | --- |
| original | none | Complete initializer graph |
| no-repair | file0x1420: `bf50a6→e91404`, main1220→1637 | Save graph before isolation repair and shortcuts |
| repair-only | file0x1557: `cd3fbc→e9dd02`, main1357→1637 | Save after repair, before shortcuts |
| local-only | no-repair jump plus file0x2f4c: `f6287c80→00000081` | Suppress random wormhole acceptance by changing its chance threshold to 1 |

Every case declares the disposable five-byte maintenance-child exit stub
`b8004ccd21`; this avoids altering the graph after initialization. The execution
chain is not represented as wholly untouched. Both raw program-normal-termination
output and an independent shell-return marker are required. Original/runtime,
patched-copy and retained-file hashes are checked; copied executables are removed
from retained results. The writer and verifier have independent patch contracts.

| Observed graph | Edges including Earth self-link | Weak components | Earth reaches / can return |
| --- | --- | --- | --- |
| no-repair |7771|20|2953 / 2953|
| repair-only |7809|1|3000 / 3000|
| original |7824|1|3000 / 3000|
| local-only |7689|28|322 / 322|

Nineteen logged repairs change 38 sixth-slot endpoints; replay reproduces the
entire repair-only table. The final phase adds 15 directed sixth-slot Earth
shortcuts. All first-five columns are identical across no-repair, repair-only and
original. Every first-five edge is reciprocal in the same column and within ten
sector numbers. Sparse holes are common and slot order matters.

Suppressing random wormholes changes later RNG consumption: first-five slots
change in 2610 sectors versus the no-repair control. The local-only case is not a
pure deletion of the sixth column. The existing Earth↔6 seed remains. Reciprocal
sixth-slot links may also be geographically short, so distance alone cannot
identify a wormhole versus another sixth-slot edge.

`internal/game/testdata/dos_warps.json.gz` packages all three complete 3001×6 tables,
source world/copied-executable identities and the ordered repair pairs. Its entire
contents are compared with retained DOS worlds by the independent verifier. Go
tests reproduce the repair-only and final tables with scripted modern choices,
checking traversal and write semantics without claiming the same QB random seed.

## Shortcut index rounding

Static code converts the cumulative single-precision position without an INT
operation. Five declared one-write controls establish positive rounding:

| Synthetic shortcut position | Changed sector |
| --- | --- |
|100.00|100|
|100.25|100|
|100.50|101|
|100.75|101|
|101.50|102|

It is nearest integer with positive halves upward; neither floor nor ties-even
matches the observations. No conclusion about negative conversion is needed.

`recover_warp_rounding.py` changes copied initializer main13b3→1637 after the
first shortcut write, replaces the 400 scale by 0 and the 8 offset by the synthetic
position. The offset constant is also used by a month comparison; raw calendar
capture confirms November so that branch does not change. Raw clock capture
confirms midnight. Each normally returned world differs from the repair-only
baseline in **exactly one of all 18,000 warp cells**. The independent verifier
pins the baseline, patches, executable hashes, calendar, clock and normal return.

## Deliberate modern differences and remaining gaps

- Go uses its seeded random stream, independently from the port/graph legacy
  stream; it does not emulate QB seeding or draw-for-draw MBF calculations.
- Six-column construction and order are preserved, but the final saved slice
  removes zero placeholders and Earth's redundant self-link. General self-link
  validation remains strict.
- DOS long-link code lacks a cross-column duplicate check. The modern generator
  rejects duplicate exits in both directions.
- Empty-row and long-self retries are capped at 128. An empty row then tries a
  deterministic nearby reciprocal link; failure rejects the unpublished world.
- Repair samples uniformly from the finite eligible earlier sixth-slot pool.
  If no source exists, generation fails rather than looping forever or silently
  overwriting a reachable source slot. The target-side overwrite follows DOS.
- Shortcut generation models single-precision cumulative positions and the
  observed positive-half-up index conversion, with a 32×table-length draw budget.
  A pathological zero-step stream fails finitely. This is not full MBF emulation.
- Reduced 8–3000-sector worlds remain supported. Out-of-range local candidates in
  tiny worlds are skipped instead of reproducing DOS's fixed 3000-sector assumptions.
- Final forward/reverse Earth connectivity is verified. Existing worlds retain
  their original maps, including the established ring; selecting the new profile
  requires a new world. Native BBS/balance acceptance is separate from local tests.

Initializer raw seeding and selected exact graph replay were subsequently
verified in the [RNG follow-up](../yt-rng-seeding/RECOVERY.md). Full port-stream
replay, remaining MBF boundary arithmetic and DOS save conversion remain open.
The active profile still uses its documented Go stream and safeguards. Recovered
local/long links, repair and shortcut phases are implemented.

## Verification

```sh
python3 scripts/verify_warp_generation.py
python3 scripts/test_verify_warp_generation.py
python3 scripts/verify_warp_rounding.py
python3 scripts/test_verify_warp_rounding.py
python3 scripts/smoke_warp_generation.py
go test -race -count=1 ./...
go vet ./...
```

Independent verifiers reject rehashed graph/phase/patch/normal-return mutations,
false floor/ties-even results, altered golden tables and missing/truncated native
reads. Go tests cover chance thresholds, RNG draw order, matching columns,
boundaries, duplicates, finite fallback/failure, full native phase replay, rounding,
connectivity, deterministic seeds, save round trips, migration, independent port
selection, quote invalidation and both season resets. CLI/PTY checks cover both
interfaces, navigation, archive/reset settings, initialization admission and legacy
map preservation. CI runs all verifiers and tests without requiring DOSBox.

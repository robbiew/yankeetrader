# Complete pre-maintenance initializer record replay

This research milestone extends the merged [graph/port replay](../yt-port-replay/RECOVERY.md)
to every byte of the complete pre-maintenance `YTDATA.DAT`. It adds no production
initialization mode, DOS save import/export, schema change or gameplay behavior.

## Verified result

All ten retained controls match **4,151 records × 137 bytes = 568,687 bytes**
each, or **5,686,870 bytes** total. [Replay results](replay-results.json) preserve
whole-world and per-block observed/replayed hashes, measured seed provenance,
RNG draw counts and first-difference diagnostics. Synthesis takes a measured raw
seed, date and scoreboard path; it reads original DATA and recovered writer
rules, never an observed world or copied record template.

| Block | Records | Recovered writer behavior |
| --- | --- | --- |
| Configuration | 1 | Defaults, scoreboard path/length, year/day bookkeeping, first-draw HQ sector and raw unused fields |
| Inactive players | 50 | 41 spaces followed by 96 zero bytes |
| Sectors | 3,000 | Complete graph, raw zero FAC residues, port links, final HQ defense and Earth bookkeeping pointer |
| Ports | 1,000 | Existing exact placement/name/economy replay and full raw records |
| Inactive planets | 100 | Configuration FIELD-buffer inheritance, clearing only offset 85 |

The six earlier fixed-clock controls remain unchanged: midnight/repeat, +1/+2
seconds, 12:34 and next date. Four fresh unmodified-initializer controls add a
repeat baseline, `SCORES.TXT`, January 1, 2027 and February 29, 2028. Each has a
separate copied-executable raw seed probe. All four measured midnight seeds are
`c805`, retaining TIMER's raw zero residue rather than assuming numeric zero.

Only disposable copies run under DOSBox. The initializer and runtime copies
match their archived original hashes; the maintenance child is an explicit
five-byte exit stub (`b8004ccd21`) to expose state before maintenance. No actual
maintenance result is attributed to this milestone. The runner preloads a
known radio sentinel and observes its removal. Earlier six controls discarded
auxiliary files; their absence is not retroactively presented as evidence.

## Raw record findings

**Sector zero residues:** before the first warp conversion, converting the
sector index to an integer overwrites the low FAC word while retaining the
upper word from `sector + 51`. Converting integer zero clears only the exponent.
Following zero slots retain the previous serialized FAC mantissa. Thus numeric
zero normalization would silently change the original world bytes. Complete
sector synthesis follows this bounded native conversion sequence.

**Planet FIELD inheritance:** the planet phase reads configuration into the
shared random-access record buffer, clears only offset 85, and writes every
inactive slot. These records are neither blank planets nor copies of the last
port. Their otherwise unused bytes retain the configuration's path, dates,
HQ sector and settings. No new semantic meaning is assigned to inactive fields.

**January 1 cancellation:** `day - 1` is numerically zero, but the original
single-add cancellation path clears only the FAC exponent. The calendar's
preceding `INT((year % 100) / 4)` leaves the mantissa of 6 in the 2027 control,
producing `00004000`. The same raw bytes propagate into all 100 inactive planet
records. The model explicitly preserves this bounded arithmetic residue.
It does not introduce a general MBF arithmetic emulator.

**Final HQ writes:** after ordinary record generation, the initializer changes
only HQ-sector defense strength to 10,000, its owner to -1, and Earth-sector
offset 105 to the selected HQ sector. The earlier HQ random draw is reused;
there are no additional modeled random draws after the port phase.

## Native and runtime evidence

[Native contracts](native-contracts.json) retain 23 bounded original-byte ranges
for the calendar, configuration/FIELD map, player/sector/planet writes, HQ
patches, auxiliary routines, constants and relevant BRUN30 conversions/addition.
The independent verifier pins binary/listing identities, range coordinates,
full lengths and bytes. These are archived original bytes and annotated listing
analysis, corroborated by local disassembly; **they are not fresh REA provider
observations**. The current Ghidra provider lacks its configured JDK, so no new
successful REA session is claimed. Existing native evidence remains reusable.

Fresh runtime artifacts live in `controls/world-dos` and `controls/seed-dos`.
Independent checks bind exact command/input recipes, clock/date/return logs,
executable patch contracts for raw seed probes and pinned complete outputs.
Newspaper initialization has seven native PRINT lines with the observed
`00:00:01` execution timestamp in these four controls, and alias initialization
writes `Dummy,Dummy,Dummy,Dummy` plus DOS line ending/EOF. The original deletes
`YTRMSG.DAT`; it does not leave an empty file. These auxiliary outcomes are
verified separately. The seeded replay synthesizes `YTDATA.DAT`, not elapsed
execution time or a general timestamped auxiliary-file stream.

## Portable validation

```sh
python3 scripts/verify_initializer_native.py
python3 scripts/test_verify_initializer_native.py
python3 scripts/verify_initializer_controls.py
python3 scripts/test_verify_initializer_controls.py
python3 scripts/verify_initializer_targets.py
python3 scripts/test_verify_initializer_targets.py
python3 scripts/replay_qb_initializer.py --check
python3 scripts/test_replay_qb_initializer.py
```

The report changes only with explicit `--output`. Tests reject rehashed corrupt
worlds, raw zero residues, altered native ranges, false seeds/clocks/returns,
scoreboard input, malformed auxiliary contents and a recreated radio file.
Replay tests also forbid reading target worlds during synthesis.
Reproduction requires DOSBox Staging; portable verification needs only Python
and retained repository artifacts, without Java, REA or a DOS emulator.

## Scope and next work

Bounded inputs are the original default 3,000 sectors/1,000 ports/50 player
slots/100 planet slots, selected 2026–2028 dates and ASCII scoreboard paths up
to 41 bytes. Ten controls establish selected complete-record replay, not every
possible date, input, platform, MBF operation or initial-maintenance outcome.
Original duplicate-location and self-warp behavior remains research evidence.

The next integration step is a separately reviewed compatibility contract:
define seed/date inputs, whether original defects are represented or corrected,
safety bounds and immutable existing-save behavior before adding a production
profile. General MBF/RND variants, exact initial maintenance and DOS save
interoperability remain separate. Current playable `-seed`, `-dos-ports`,
`-dos-warps`, prices, save **34**, exports/restores and safeguards are unchanged.

# Bounded maintenance record replay — historical guest-clock profile

**2026-11-05 update:** the separate [clock-neutral host profile](CLOCK_NEUTRAL.md)
closes the four-byte gap for this bounded recipe and exactly replays all six
untouched files. This report, its old profile and comparison pins remain unchanged
as historical evidence; statements below about the remaining gap describe that
guest-instrumented profile.

This is a research-only before-to-after model of the all-inactive-player initial
fixture. It follows [the measured RNG phase ledger](PHASE_CHRONOLOGY.md) from
PR #88. It changes no Go gameplay, dependency, original archive, `qb36-v1`
recipe or save format 35.

**Untouched byte-exact replay is not yet established.** The model reconstructs
all six files and matches instrumented main-body-end outputs exactly. Against
four untouched runs it differs in exactly four bytes: port 606's timestamp. That
measured clock-observation limitation remains visible in the report and tests;
no target-derived correction, timestamp mask or CPU tuning hides it.

## Independent model and explicit inputs

[`replay_maintenance_records.py`](../../scripts/replay_maintenance_records.py)
composes three pure components and the final configuration/ranking writers:

- [Port writer](../../scripts/replay_maintenance_ports.py): ten-day production,
  strict first-maximum stock/class selection, coefficient sign normalization and
  raw observed TIMER/60 values. The model preserves names, production rates and
  all unassigned bytes from the pre-maintenance record.
- [NPC writer](../../scripts/replay_maintenance_npcs.py): missing Wanderer,
  Xannoron and Mercenary Base; nineteen shrinking-bound allocations; original
  directed, column-ordered BFS and route writes; eager player-scan RNG consumption;
  desertion/lottery draws and raw FIELD/zero residues.
- [Auxiliary writer](../../scripts/replay_maintenance_aux.py): news rotation,
  bootstrap event lines, empty message archive and no-active-human/team scoreboard.
  Literal strings and the PRINT USING mask are read from the immutable original
  executable, not copied from a target file or transcript.
- Final configuration day at offset 81 and inactive score-cache offset 109 writes. Fresh
  native evidence establishes that the inactive value is MBF **double −1**;
  its first four bytes alone misleadingly resemble a single-precision zero.

Core synthesis takes **only** the three pre-maintenance files, explicit calendar
and text clocks, startup state and measured clock inputs. It accepts no target
world, target hash or per-record output patch table. Tests deny every file read
inside core synthesis except the immutable original executable used for constants.
Completed targets are opened only by a separate comparison layer.

The startup state is independently derived from raw TIMER `00004800`, its
negation `0000c800` and the retained old low byte 5. The 41+19 helper TIMER samples
are authenticated by the prior sequence checker; the model derives each reseed
and subsequent stream state itself. It does not take post-draw state arrays as
synthesis inputs. A fresh first-hit sample at `218e` supplies Xannoron TIMER
`cdcc4c7c` (approximately 0.05 seconds) before division/truncation.

Clock inputs are declared external measurements, **not** a prediction from a
printed `00:00:00` string. The admitted model is the default 4,151-record geometry,
50 empty players, initially inactive planets, no owned ports or mine hazards,
and the recovered clean ten-day port state. Unsupported branches fail rather
than silently use a target template. General MBF, live players, battles,
nonempty commerce/message state and arbitrary worlds/clocks are not recovered.

## Whole-file result, without masking

[The complete generated comparison report](record-replay-report.json) includes
all six files, full hashes, per-block mismatch counts and every remaining byte.
Each comparison covers **570,059 bytes**:568,687 world bytes and 1,372 auxiliary
bytes.

| World block | Bytes | Untouched mismatches |
| --- | ---: | ---: |
| Configuration, 1 record | 137 | 0 |
| Players, 50 records | 6,850 | 0 |
| Sectors, 3,000 records | 411,000 | 0 |
| Ports, 1,000 records | 137,000 | **4** |
| Planets, 100 records | 13,700 | 0 |

| Auxiliary file | Bytes | Untouched mismatches |
| --- | ---: | ---: |
| YTNAME.DAT | 26 | 0 |
| YTNEWS.DAT | 434 | 0 |
| YTYNEWS.DAT | 309 | 0 |
| YTRMSG.DAT | 0 | 0 |
| YTSCORE.ASC | 603 | 0 |

All four untouched targets (fresh entry/repeat, default-port oracle and read-only
oracle) retain the same four-byte difference. The two separate instrumented
main-body-end targets match **every one of the 570,059 bytes** exactly. Their
executable cleanup footer is bypassed by diagnostics: equality here is not an
untouched-normal-completion claim.

The NPC model independently computes all nineteen routes, 496 edges, 41 single-draw
helper calls, 19 four-draw helper calls and 25,891 RND executions. It reaches the
measured lottery endpoint `4307ee`. These counts are results of its before-world
route and RNG calculations, not a hardcoded route-length table. Every sector and
planet byte agrees, including inherited unused fields and noncanonical zeros.

## The port-clock edge and why it remains open

The original writes the raw single-precision result of TIMER/60 at port offset 101.
Two clock epochs appear in this fixture:

| Epoch value | Raw FAC | Interpretation |
| --- | --- | --- |
| Before the first tick | `00004800` | Numeric zero with retained mantissa |
| After the first tick | `0e745a76` | Approximately 0.00083333335 minutes |

Independent nth-hit probes bracket the instrumented transition: port 605 is the
first value and port 606 is the second. Expanding that measured epoch schedule
synthesizes every instrumented port byte. In the untouched output, port 606 still
has `00004800`; its transition is at 607. Therefore record 3657, offsets 101–104,
contains the only four differing bytes. The untouched bytes are `00 00 48 00`;
the model's independently observed diagnostic profile gives `0e 74 5a 76`.

The default CS-counter diagnostic is timing-intrusive at this edge. A separate
read-only 386DWORD comparison of the current port index preserves flags and the
complete displaced instruction, performs no per-visit counter writes, preserves
file length/MZ header and uses the same CPU/clock settings. It still produces the
same four-byte difference. Its paired selected partial outputs and completed
main-body outputs agree with the default profile. No settings were calibrated to
make a target hash pass. An unretained flags-removal experiment is excluded from
acceptance and is not needed to reproduce the retained finding.

The model **does not** move the epoch start to607 using target output as input.
Doing that would hide the unobserved clock boundary rather than recover it.
A clock-neutral observation method or an independently justified timing model is
needed before claiming exact untouched replay. All other output bytes remain in
the comparison; none are dropped because they are unused or numerically zero.

## FIELD and numeric details closed in this slice

The Wanderer restoration writer does **not** clear offset 81. The initial slot's
inherited value 305 survives. The earlier [native note](../yt-wanderer/rea/NATIVE.md)
now corrects that claim. A mutation test changes an unassigned input byte and
requires exactly that one output byte to change, detecting target-template use.

Explicit source zero constants are retained as raw four-byte values rather than
canonicalized. In this historical sub-minute profile, Xannoron's TIMER/60
followed by INT clears the exponent but keeps
the fraction's mantissa, yielding `0e745a00` at offset 89. The port's raw numeric
zero likewise remains `00004800`. Integer equality alone would miss these facts.

The admitted port class counts are 346/336/318. The strict maximum test preserves
the first cargo on a tie; selected coefficients become positive and the others
negative. Empty stocks advance by exactly ten times each bounded integer rate.
The modern production economy is not replaced by these research-only rules.

## Retained evidence and portable verification

The new immutable [input controls](record-input-controls/) contain 28 returned runs:

- Four entry controls: two untouched runs, startup TIMER and Xannoron TIMER. The
  entry capture command now emits all four directly, including site `007d`,
  hit 1, source `001a`; no separate manual startup capture is needed.
- Seventeen default port controls: untouched oracle, 1,000-visit body-end counter
  and fifteen terminating clock samples selected by a bounded search.
- Seven separately labeled read-only 386diagnostic controls: untouched oracle,
  complete miss and five selected port-index samples.

The checker reconstructs both disposable diagnostic variants independently,
validates exact metadata/raw pins, launch/clock/zero-status/return witnesses and
original input identities, then checks the complete paired-file comparisons and
605/606 transition. The startup stop is before the maintenance banner and preserves
all three input files exactly. [The retained read-only assembly](record-replay-native/ports/readonly-probe.asm)
reproduces both selected-port and never-hit patches exactly. The read-only guard emits original CS header bytes,
not a counter marker; it is never mistaken for ordinary program completion.

Fourteen fresh REA/Ghidra byte reads, all independently matched against relocated
original MZ bytes, are retained in three packets:

- [Ports](record-replay-native/ports/rea.json), one 1,928-byte writer read:
  `ev_cf13e47dc2ef79bc24eb65c68bb2f6a56df735e83d4b3ba9b90c6187f46a141b`.
- [NPCs](record-replay-native/npc/rea.json), three complete writer ranges including
  the Wanderer assignment list:
  `ev_72238fc8070c6b162c4287f1f769228fd14978ef5b6242b90236532d69bcb631`.
- [Auxiliary/rankings](record-replay-native/auxiliary/rea.json), ten reads covering writers,
  rotation, literals, masks and the double-precision −1 constant:
  `ev_7780b9339a4ab4e61784c452aea32e9b6301c9daf8b4798e1539d7494e5a9f57`.

The adjacent FINDINGS files retain all addresses, lengths, identities, evidence
IDs, source mappings and limitations. Static reads alone do not establish runtime
execution; the paired raw controls and synthesis comparisons provide that part.

```sh
python3 scripts/verify_maintenance_record_inputs.py
python3 scripts/test_verify_maintenance_record_inputs.py
python3 scripts/test_replay_maintenance_ports.py
python3 scripts/test_replay_maintenance_records.py
python3 scripts/replay_maintenance_records.py --output /tmp/maintenance-replay.json
```

The input suite has 49 corruption/provenance tests; the port suite has 10 property
tests and the composed model has 21 whole-file/guard tests. CI retains these checks
and every earlier validation command. They verify a bounded research result with
an explicit known gap; they do not declare exact untouched replay achieved.
To enforce that stronger requirement, this command currently **fails**:

```sh
python3 scripts/replay_maintenance_records.py --require-untouched-exact
```

New captures require DOSBox Staging, absent output directories and declared
research CPU support for the read-only 386comparison:

```sh
python3 scripts/recover_maintenance_record_inputs.py /tmp/yt-record-inputs-new
python3 scripts/recover_maintenance_port_clock.py /tmp/yt-port-clock-new
python3 scripts/recover_maintenance_port_clock_readonly.py /tmp/yt-port-readonly-new
```

Expected pins are not automatically refreshed. Python standard library suffices
for portable checks; DOSBox/REA/NASM/Java remain research tools. No Go/terminal
playtest, native Windows durability or live BBS acceptance is newly claimed.
Next close the clock-observation gap, then require complete equality against
untouched runs and add independently measured dates/clocks before considering a
production compatibility contract.


[Independent calendar controls](CALENDAR_CONTROLS.md) subsequently verify positive
integer-minute storage and the unnamed lottery-candidate branch in a noon case.
The historical baseline counts/report above remain unchanged; production Go and
save 35 are unaffected.

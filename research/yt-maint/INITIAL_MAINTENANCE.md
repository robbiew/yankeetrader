# Original initializer → initial maintenance: bounded native controls

Captured 2026-11-04 from copied original distribution binaries. This is research;
Go gameplay, `qb36-v1`, save schema 35 and source fingerprints are unchanged.
The playable projection still uses independently seeded modern NPC bootstrap and
UTC watermarks. It does not reproduce this raw DOS transition.

## What was already recovered

[Daily maintenance recovery](RECOVERY.md) establishes bounded economics and NPC
rules, supplemented by the later faction, lottery and event research. The
[complete initializer replay](../yt-initializer-replay/RECOVERY.md) deliberately
replaces the maintenance child with a declared five-byte exit stub. Its source
worlds are **before** the transition measured here. Those established features
and the modern full-world acceptance campaign are not missing implementation.

## Capture method

Eight disposable DOSBox Staging mounts use copied, hash-checked YT-INIT, BRUN30
and YTMAINT originals; no archived file or executable is changed. All mounts use
200,000 CPU cycles and dummy audio/video. Initialization starts at DOS midnight
with `Y` confirmation and an empty scoreboard path. Raw logs, return markers,
clock witnesses, answers, exact commands, compressed worlds and every generated
DAT/ASC side file are retained under [initial-controls](initial-controls).

- `baseline` and `repeat`: November 2, 2026, independent exact repeats.
- `new-year`: January 1, 2027, a second date boundary.
- Each has an **integrated** control: untouched initializer and actual original
  maintenance child in the same launch. Both completion messages and the
  subsequent shell return are mandatory.
- Each also has a **split** control: declared exit-stub child, retained full
  before-world/name/news files, then original maintenance in a fresh emulator
  launch with clock reset to midnight. This distinguishes the pre-maintenance
  boundary from an inferred snapshot inside the integrated run.
- `second-one-split` and `second-two-split` initialize identically, then request
  maintenance clocks 00:00:01 and 00:00:02. Actual DOS witnesses read **0.98** and
  **1.97** seconds because of DOS clock granularity; they are not described as
  exact integer TIMER samples.

The integrated initializer returns at 7.36 emulated seconds. Stub initialization
returns at 6.81 seconds. Separate midnight maintenance returns at 0.49 seconds.
These are measured witnesses for this environment, not real-world speed claims.
The independently checked binary identities are in the capture recipe and
verifier; original maintenance SHA-256 is
`8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6`.

## Observed record and auxiliary changes

In each split control, 1,095 of 4,151 records change: one configuration,
50 inactive player, 41 sector, 1,000 port and three planet records. The
configuration and port maintenance day advance from the initializer watermark
(day-of-year minus one, port production day minus ten) to current day-of-year.
Every unused player slot changes only offset 109, numerically zero to -1.
All 3,000 six-slot warp arrays and all 1,000 port names remain byte-identical.
The complete raw changes, including MBF residual bytes, are hash-pinned.

The baseline split port changes include class (offset 41), day (45), all three
stocks (49/53/57), coefficient signs (73/77/81), and time (101). For example,
Earth changes class 3→2, day 296→306 and stocks 0→186160/308710/105780;
its rates 18616/30871/10578 stay unchanged. This is one native observation,
not a general production formula inferred from one example.

Planet slots 1, 99 and 100 become The Wanderer, Mercenary Base and Xannoron.
Twenty sector records contain positive Xannor mobile forces after maintenance.
The final auxiliary set is YTNAME.DAT, YTNEWS.DAT, YTYNEWS.DAT, empty YTRMSG.DAT,
and YTSCORE.ASC. The newspaper records maintenance/NPC creation; the scoreboard
is produced with the captured date/time. Both before/after auxiliary bytes are
retained where a split boundary exists.

## Clock sensitivity and remaining RNG work

Both November direct launches repeat byte-for-byte, as do both midnight split
runs. Integrated and midnight-split outputs differ. Three split starting worlds
(midnight, requested second one and requested second two) are byte-identical,
but their final worlds differ. This removes initializer-world variation as an
explanation for the bounded clock-sensitive maintenance result.

| Control | Wanderer sector | Mercenary Base sector | Xannoron sector |
| --- | ---: | ---: | ---: |
| Integrated baseline | 1349 | 2925 | 849 |
| Midnight split | 1095 | 2598 | 849 |
| Requested second one (observed 0.98s) | 1497 | 78 | 849 |
| Requested second two (observed 1.97s) | 2982 | 359 | 849 |

The complete port rate/coefficient slices match across these four runs, as do
class counts (346/336/318). Planet placement and mobile effects differ. These
observations establish clock sensitivity of the transition, **not** the exact
maintenance RANDOMIZE input, runtime RNG state, draw counts or operation order.
These untouched controls contain no maintenance RNG instrumentation, and no
new decompilation is claimed for them. The
integrated run has no internal before snapshot; its comparison uses the
separately reproduced initializer boundary.

[Subsequent runtime tracing](RNG_TRACE.md) now captures startup seed and complete
instrumented event streams with transcript phase boundaries and explicit timing
perturbation measurements. Application call-site ordering and timer-controlled
comparisons remain next against these untouched native oracles. Exact post-maintenance Go replay, arbitrary clocks and
general MBF arithmetic remain unimplemented. Preserve the modern fixes for
same-day reruns and clock rollback rather than importing DOS defects.

## Portable verification and reproduction

CI needs only Python standard library; it does not execute DOS binaries.

```sh
python3 scripts/verify_initial_maintenance.py
python3 scripts/test_verify_initial_maintenance.py
```

The verifier independently pins every decompressed world/side file, validates
exact control/file inventories, binary identities, commands, clocks, completion
and shell-return witnesses, NPC slots, graph/name preservation and repeat/clock
relationships. Launch provenance is parsed independently: each phase must record the exact
recipe invocation, isolated control mount, fixed 200,000 applied CPU cycles and
expected emulator/video/sound settings. Four test methods exercise 20 rejection
controls (17 rehashed content alterations, two missing controls/witnesses and a
forged binary hash), including empty and contradictory launch logs for both phases.
Rehashing altered observations in their manifest does not make them pass.

For new native observations, use an absent destination with DOSBox Staging:

```sh
python3 scripts/recover_initial_maintenance.py /tmp/yt-initial-maintenance-new
python3 scripts/verify_initial_maintenance.py /tmp/yt-initial-maintenance-new
```

Exact pins describe this emulator/clock recipe. A different environment that
fails them needs investigation and separately reviewed observations, not an
automatic refresh of the expected hashes.

## Follow-up: seed and first-hit boundaries

The [subsequent precision slice](RNG_FIRST_HITS.md) measures entry/helper seeds
and selected first-hit RND pairs with terminating copies and fresh untouched
oracles. It supersedes the seed-site deferral only for those bounded observations;
complete dynamic draw ordering and exact post-maintenance replay remain open.
The earlier raw worlds and auxiliary bytes above remain unchanged.

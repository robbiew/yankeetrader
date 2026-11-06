# Clock/date controls for evolved maintenance handoffs

Four explicit two-child profiles now retain **48 complete original-DOS runs**.
Every first child starts from its corresponding mode's verified converged
November 2 parent; every second child takes all six first-child output files
unchanged. All **288 input-file links** match, and all six output files agree
across the six capture modes at each of the eight stages (**288 output files**).
No output is masked or repaired to obtain this equality.

This extends the [three-day midnight replay](EVOLVED_CHAIN_REPLAY.md) with new
controlled observations. It does not broaden that published profile; a
[separate replay](EVOLVED_CLOCK_REPLAY.md) now synthesizes these new cases.
Go gameplay, dependencies, generation
fingerprints and save **35** are unchanged. PR #97 remains a separate review scope;
this follow-up research is kept on its own local branch.

## Declared schedules and exact inheritance

| Profile | First child | Second child |
|---|---|---|
| `second-two` | November 3, 2026, requested 00:00:02 | November 4, midnight |
| `noon` | November 3, 2026, requested noon | November 4, midnight |
| `catchup-eleven` | November 13, 2026, midnight | November 14, midnight |
| `new-year` | January 1, 2027, midnight | January 2, midnight |

The parent is the actual first day's complete output from the
[convergence corpus](CONVERGENCE_CHAIN.md), with eighteen mobile pointers sharing
one physical deployment. Its immutable manifest is checked before copying each
mode's six files. No world, name, public/yesterday/private journal or scoreboard
is reset between parent and child. All actual before files are retained.

Each stage has two unobserved runs, one attach-only and three observed runs.
Original YTMAINT and BRUN30 bytes are unchanged. Fresh disposable mounts, pinned
200000 cycles, complete lifecycle/controller records and actual DOS source frames
are preserved. All 48 processes returned naturally; no failed capture or retry
is counted in this accepted corpus.

## Observed clock and calendar effects

Requested time is not a substitute for source time. The two-second shell request
actually reports **1.97 seconds** and the noon request **43199.92 seconds** under
the pinned BIOS clock. The observer retains separate per-writer DATE/TIMER/TIME
returns, including raw port timestamps and independently bound text clocks.

The original saved base year remains 2026 across New Year. January 1 and 2, 2027
write serial days **366 and 367**, not Gregorian day-of-year 1 and 2.

The first long gaps are eleven and sixty days from the parent update. Both use
the original ten-day economy cap. That does not make their NPC streams identical:
the first placement helper has the same old RNG witness `c181c500`, but its raw
TIMER is `cdcc4c7c` in catch-up and `cdcc4c7d` at New Year (nominally 0.05 and
0.1 seconds). Source calendar work affects the timing of later calls. These are
witness-assisted observations, not newly computed full RNG traces.

The ordinary friendly planet shows the interval effect: noon/next-midnight gives
ground **505000 → 512575 → 515137**, while the midnight chain gives
505000 → 510050 → 515150. Catch-up gives 505000 → 555500 → 561055.
The long-gap first child's largest port rate is **65528**, beyond the earlier
profile's deliberately bounded 40000 admission. These are measured extensions
of known economy rules, not evidence that those rules are newly missing.

## Newly selected, already recovered combat paths

| Profile | First-child Xannor | Second-child Xannor | Helper 1/2 inventories |
|---|---:|---:|---|
| Second two | 10000 | 9994 | 41/17 → 41/0 |
| Noon | 8300 | 8300 | 40/17 → 40/14 |
| Eleven-day catch-up | 10000 | 10000 | 41/17 → 42/0 |
| New Year | 10000 | 9638 | 41/17 → 42/0 |

- The two-second profile's second child hits mine sector **980**. Its source
  helper witness derives roll **223**; the six-fighter group loses only its six
  fighters. Public hit/death lines reconcile with the actual six-fighter physical
  loss, and the saved mine count falls from one to zero. Mine 1169 remains, and
  group 20 deposits a new mine at 439.
- Noon selects **fourteen Wanderer attack/death pairs**, totaling **1700** Xannor.
  Earlier ordinary economy supplies 250 ground; nineteen ground units are spent,
  leaving 231. Positive ground never exhausts, so this does not select production
  damage or deletion.
- New Year's second child selects **four Mercenary Base attack/death pairs**,
  with announced forces 23 + 216 + 53 + 70 = **362**. Five defending ground units
  are spent: post-economy 194650 becomes 194645. The Base survives with its title.

The independent verifier parses the literal public fatal outcomes and reconciles
their sum with actual before/after physical ownership and scoreboard values.
Claimed mine expenditure must also appear in the saved records. Unknown battle
lines fail explicitly. Ground formulas are not inferred from public force-loss
summaries alone. Names/yesterday news retain exact source bytes; private mail
remains empty in these all-inactive-player contexts.

## Explicit boundaries of the published replay

Running the unchanged published three-day API with its real original prefix and
these source clocks produces bounded rejection, not a numerical mismatch:

| Profile | Existing boundary reached |
|---|---|
| Second two | First child is admitted; the second selects an excluded mine encounter |
| Noon | Measured midnight source-port-clock guard |
| Eleven-day catch-up | Consecutive November 2/3/4 recipe admission |
| New Year | Consecutive November 2/3/4 recipe admission |

The published profile remains unchanged. A [separate before-only extension](EVOLVED_CLOCK_REPLAY.md)
now admits these measured fractional/long/year intervals and bounded larger rates,
and composes the recovered mine death and positive-ground Wanderer/Base paths
with exact RNG, casualties and receipts.
A guard rejection is distinct from a model that calculated incorrect output.

## Provenance and reproduction

[The frozen corpus](evolved-clock-controls/) contains **1318 files**, including
four executed acquisition sources. Manifest SHA-256:
`c6fc45c0d1adf29bf2104574d1e341791f9f9fa15d2059c52a04ecd917beb826`.
Parent corpus manifest:
`164cc9d62bef6b213226ca8e125e39d282e6b851a9b6ffaf048e933a290d1f8c`.
Original YTMAINT is
`8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6`;
BRUN30 is `3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8`.
All source callbacks authenticate with the existing complete context definitions;
no new caller, provider installation or byte query was needed. Relevant original
[mine/route](../yt-xannor-mobile/RECOVERY.md) and
[planetary defense](../yt-xannor-planets/RECOVERY.md) evidence is reused.

All **47 independent provenance/semantic tests** pass, covering actual launch and
CPU/date/time evidence, source attribution, exact per-mode inheritance, raw clocks
and text headers, physical scores/public deaths, mine expenditure, artifact pins,
rebound metadata and explicit unknown-outcome rejection. The output classifier
reports six-mode differences if present rather than masking them. All eight
retained stages currently classify as equal.

```sh
python3 scripts/verify_maintenance_evolved_clocks.py
python3 scripts/test_verify_maintenance_evolved_clocks.py
# Actual acquisition requires the pinned installed DOSBox and Frida17.23.2:
python3 scripts/recover_maintenance_evolved_clocks.py /tmp/new-evolved-clocks \
  --scratch /private/tmp/new-evolved-clock-mounts \
  --frida-module /absolute/path/to/frida.js
```

Acquisition requires fresh destinations and stops on failed lifecycle checks.
Portable verification launches no emulator, Frida, Go application or network.
The prior midnight replay, capture corpora and admission boundaries remain intact.
README, plan and portable CI checks are updated. General MBF, active-player
maintenance, arbitrary worlds, live BBS and native Windows acceptance remain
separate from these controlled observations.

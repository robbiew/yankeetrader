# Maintenance clock/date matrix: seven exact profiles and one encounter gap

This research extends [the pinned midnight experiment](CLOCK_NEUTRAL.md) without
changing that corpus or silently generalizing its clock schedule. Eight declared
recipes use the same original three-file, all-inactive initial world. **All48
native controls match all six outputs within their recipe.** The before-only
model matches seven recipes completely; the late-night seed reaches a newly
exposed planet-interaction path that remains explicitly unsupported.

There is no Go gameplay, dependency, original archive, `qb36-v1` fingerprint or
save35 change. This remains evidence-driven maintenance research, not a general
DOS save importer or predictor from an arbitrary clock string.

## Retained matrix and complete comparisons

Each row contains two ordinary unobserved runs, one Frida attach-only control
and three host-observed runs. Every guest executable is unchanged before/after;
every DOSBox process exits naturally with status0. The independent verifier
requires all six outputs, original inputs, actual launch/CPU logs, exact observer
source, original code/frame attribution, tool identities and complete lifecycle
records. No forced stop, dropped event, unknown caller or missing output passes.

All rows use **saved base-year26** and the same original before-world. These are
additional maintenance dates, not freshly initialized replacement worlds.
Requested time is a DOS shell command; the actual returned time is retained and
need not equal that string because DOSBox quantizes it to BIOS ticks.

| Recipe | Requested date/time | Fixed cycles | Observed news | Observed scoreboard | Before-only model |
| --- | --- | ---: | --- | --- | --- |
| `shift-two` | 11/02/2026 00:00:02 | 200000 | Nov2 00:00:02 | Nov2 00:00:02 | Exact |
| `noon` | 11/02/2026 12:00:00 | 200000 | Nov2 12:00:00 | Nov2 12:00:00 | Exact |
| `late` | 11/02/2026 23:59:59 | 200000 | Nov2 23:59:59 | Nov2 23:59:59 | Explicit Wanderer encounter gap |
| `near-midnight-100k` | 11/02/2026 23:59:59 | 100000 | Nov2 23:59:59 | Nov2 **24:00:00** | Exact |
| `rollover` | 11/02/2026 23:59:59 | 10000 | Nov2 23:59:59 | **Nov3 00:00:08** | Exact |
| `next-day` | 11/03/2026 00:00:00 | 200000 | Nov3 00:00:00 | Nov3 00:00:00 | Exact |
| `eleven-days` | 11/13/2026 00:00:00 | 200000 | Nov13 00:00:00 | Nov13 00:00:00 | Exact |
| `next-year` | 01/01/2027 00:00:00 | 200000 | Jan1 00:00:00 | Jan1 00:00:00 | Exact |

The100000/10000cycle recipes deliberately test the text-rounding and calendar
boundaries under explicit different schedules. They are compared with their own
unobserved controls; no CPU setting was adjusted to make an output agree with
the previous midnight target. Host instrumentation is not passive, and these
complete byte comparisons establish neutrality only for the declared recipes.

Each successful trace drives all six native targets for its own recipe: seven
recipes × three independent traces × six targets = **126 complete comparisons**,
570,059bytes each, with zero differences. The three `late` traces remain in the
[generated report](clock-matrix-replay-report.json) as unsupported entries, rather
than disappearing from the denominator. Native output equality for that recipe
is established; model byte equality is not.

## Recovered date and clock behavior

**TIMER and TIME$ are different operations.** The observer records DOSAH2c at the
original handler return, before BRUN restores the caller's CX/DX. TIMER retains
fractional seconds and its measured raw zero residue. TIME$ rounds the second up
when hundredths are at least50, carries seconds/minutes, and does not wrap hour24
before formatting. The100k profile actually writes24:00:00 with the preceding
calendar date. The model preserves that string; it does not normalize it to
00:00:00 or increment a separately sampled date to make it look conventional.

**Calendar samples belong to particular writers.** News reads TIME$ then DATE$;
the scoreboard reads DATE$ then TIME$. The calendar helper is called at startup,
once for each of1000ports, separately for Wanderer/Xannoron/MercenaryBase
creation and once for the final configuration watermark. In the actual rollover
trace,668port date samples are Nov2 and332are Nov3. Per-port date and TIMER samples
remain separate even if an individual pair straddles midnight. NPC creation days,
final watermark, news and scoreboard dates are explicit inputs to their writers.

**The calendar count is relative to the saved base year.** With this unchanged
2026world, Jan1,2027 writes legacy day366, not day-of-year1. A newly initialized
2027world would be a different input and would not test that branch. The new
model admits only observed2026/2027 source dates and preserves the base year.
Multi-year, leap-year and century behavior is not inferred from Python's calendar. The separate [fresh-world calendar controls](CALENDAR_CONTROLS.md) include an independently initialized leap day; they do not establish the same saved-base-year world's multi-year transition.

**The old helper-call count was clock-specific.** The shift-two, noon and actual
rollover seeds take the lottery gate and make a42nd single-range helper call.
It chooses an inactive player and ends without an award. The other recipes use41;
all retain19shrinking helper calls. The new parser records and qualifies every
call rather than requiring the old1066-event inventory or discarding the extra
call. The branch consumes real RNG state and is included in synthesis.

The port writer is restricted to this fixture's saturated ten-day production
cap. Saved port day296 is unchanged: Nov3 is11days later and Nov13 is21days
later; the `eleven-days` recipe name means11days after the original Nov2
experiment, not11days after the saved port timestamp. Noon Xannoron creation also needs the actual nonzero integer TIMER/60 value,
not the earlier sub-minute-only zero result. Separate opt-in matrix entrypoints
extend the pure port/NPC/auxiliary writers while the original strict profile and
its regression results remain reproducible.

## Explicit remaining encounter gap

The before-only `late` model prefix sends mobile Xannor group2, strength382, into
sector658. That sector links to slot1, **The Wanderer**, owned by0. This reaches
the old model's excluded planet-interaction path at RNGstate `ea7184`, after four
single-range and one shrinking helper calls. These facts are derived from the
simulated prefix, not copied from an after-file to repair the result.

The model stops before that interaction. It does not assume the encounter is
harmless, assert an unmeasured battle outcome, copy target bytes, or skip the
sector. The next concrete research slice is the original maintenance behavior
when a mobile Xannor group reaches the Wanderer, including RNG consumption and
record/side-file aftermath. General encounters remain separate work.

## Attribution, scheduling and retained native evidence

The new [observer](../../scripts/observe_maintenance_clock_matrix.js) records both
DOSAH2a calendar calls andAH2c time calls. It buffers raw entry/return registers,
64-byte interrupt stacks, BP frames, original runtime/application/nested call
bytes, physical segment caches, PIC ticks and complete CPU-cycle budgets. The10000-cycle recipe produces no separate CPU-setting
log line; its exact launch arguments and recorded fixed budget are verified,
while100000/200000 also require their explicit log lines. No
guest register, RAM or executable is written by the observer.

Original runtime return sites are `c07f` DATE$, `c0f7` TIME$ and `c137` TIMER.
Raw frames and original far-call bytes bind each returned date/time to its
application writer and nested helper caller. Four shell DOS calls remain in the
trace but are excluded from application inputs. All1000port DATE and TIMER calls
are independently indexed; missing, duplicated or relabelled calls fail closed.

The installed DOSBox0.83.0ARM64 binary and Frida17.23.2 identities are unchanged
from the earlier research. Source and native facts are retained in
[the new native evidence packet](clock-matrix-native/FINDINGS.md), including two
focused original-binary reads and one pinned official BIOS source file. The
[original host source packet](clock-neutral-host/FINDINGS.md) remains unchanged.

Slow schedules expose interpreter-slice refills inside the DOS handler, so a
positive CPU_Cycles delta is not automatically an observer failure. The verifier
checks the fixed maximum/auto-adjust flag and normalizes the full
Cycles+CycleLeft budget against elapsed PIC ticks. The five-dispatch BIOS path
and failed postdecrement test explain the measured five/six-count deltas; native
notes preserve the limited scheduler predicates rather than claiming a universal
formula based only on entry cycles. AH2c's DOS overhead changes IP by2; AH2a
leaves it unchanged. That IP operation is not itself a five-cycle subtraction.

## Portable verification and fresh acquisition

```sh
python3 scripts/verify_maintenance_clock_matrix.py
python3 scripts/test_verify_maintenance_clock_matrix.py
python3 scripts/test_replay_maintenance_clock_matrix.py
python3 scripts/replay_maintenance_clock_matrix.py --output /tmp/clock-matrix-replay.json
```

The independent verifier authenticates the retained controls; the replay command
reports the known unsupported `late` observations. To demand every profile be
exact, use `--require-all-exact`; it intentionally fails while that gap remains.

Fresh acquisition requires the declared installed host and an existing compatible
Frida module. Use new output/scratch directories; this does not refresh pins:

```sh
python3 scripts/recover_maintenance_clock_matrix.py /tmp/clock-matrix-new \
  --scratch /tmp/clock-matrix-disposable \
  --frida-module /absolute/path/to/frida/build/src/frida.js
```

`--profiles` and `--modes` permit explicit smaller diagnostic selections; the
retained accepted corpus is the complete eight-by-six default matrix. Acquiring
inputs never reads an expected after-world. Portable verification uses Python
standard library only. Production gameplay, other worlds/encounters, uncapped
production, multi-year/century parity, other emulator/CPU implementations, native
Windows durability and live BBS acceptance remain outside this milestone.

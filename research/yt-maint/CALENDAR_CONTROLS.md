# Independent maintenance dates and clocks

Captured 2026-11-05 using copied original guest binaries and the pinned host-side
observer from [clock-neutral research](CLOCK_NEUTRAL.md). Twelve completed runs
cover four fresh initial worlds: November 3, 2026; January 1, 2027; February 29,
2028; and November 2, 2026 with maintenance requested at 12:34:00.

This is a research model extension. Production Go maintenance, save 35,
`qb36-v1` source fingerprints, archived originals and releases are unchanged.
These are independent **initial maintenance** cases, not a multi-day evolved
world campaign. The existing modern multi-day acceptance remains separate.

## Acquisition and complete comparison

Each case runs the original initializer at midnight in a new mount with the
explicitly declared maintenance exit stub. Three before-files and all initializer
completion/return/clock/launch witnesses are retained. Every complete 568,687-byte
before-world also matches the independent recovered initializer model at state
`c805` and the declared source date. No target output is used to build an input.

The same before-files then feed three fresh maintenance mounts: one unobserved
run and two independently host-observed runs. The guests YTMAINT/BRUN30 are
unmodified and hash-checked before and after. Only host-side DOS GetSystemTime
observation is installed. All twelve programs terminate normally. Outputs are
retained with launch arguments, commands, natural-exit/controller/clock witnesses,
loaded observer source and complete raw paired time observations.

Both observed outputs equal the unobserved output byte-for-byte in every case.
Each of the eight traces independently drives before-only synthesis, which is
compared with all three paired outputs: **24 complete six-file comparisons,
13,681,416 compared bytes, zero mismatches**. Each comparison includes YTDATA.DAT,
YTNAME.DAT, YTNEWS.DAT, YTYNEWS.DAT, YTRMSG.DAT and YTSCORE.ASC. No record, auxiliary
file, timestamp, unused field, raw zero residue or offset is masked or patched
from an after-target.

| Case | Requested maintenance date/time | Helper 1 / 2 samples | Model RND draws | Model lottery candidate |
| --- | --- | ---: | ---: | --- |
| Next day | 11/03/2026 00:00:00 | 41 / 19 | 25,891 | Gate declines |
| New Year | 01/01/2027 00:00:00 | 41 / 19 | 25,891 | Gate declines |
| Leap day | 02/29/2028 00:00:00 | 41 / 19 | 25,491 | Gate declines |
| Noon | 11/02/2026 12:34:00 | 42 / 19 | 25,192 | Unnamed player record 43 |

Helper TIMER inventories are direct paired host observations. RND totals,
selected player and endpoints are **model-derived**, not a new native full-RND
trace. The noon DOS starting witness is 12:33:59.91 due to native time-setting
granularity; its original news/scoreboard text reads 12:34:00. This explicit text
clock is an input of this selected profile, not a general TIME$ formatter model.

## Noon branches recovered and admitted

The former NPC model intentionally required a sub-minute creation clock and a
lottery gate below 0.5. This control exposes two bounded branches:

- Xannoron's TIMER/60 followed by INT stores a positive integer minute. It is
  **753**, raw MBF `00403c8a`, rather than a numeric-zero residual. The model now
  encodes the floor for positive results while preserving the original FAC
  mantissa/exponent-zero behavior when the integer result is zero. Static
  evidence is original main `2186..21a3` (TIMER, division by 60, INT, field store).
- The lottery's gate passes, calls helper 1 once more and selects an unnamed
  player slot, then exits without creating a planet. Original main
  `537e..53ed` shows the 0.5 gate, helper call at `53af`, and name-length test.
  All initial player slots are unnamed; active-player awards remain outside
  this model. Exactly the observed helper inventory must be consumed. The old
  gate-declines profile still requires its original 41 samples.

These are supported by complete raw output equality. They do not enable new
modern gameplay or claim arbitrary NPC/combat branches.

## Zero-cycle host refill witnesses

The old baseline verifier requires five fewer CPU cycles at each returned time
call. Fresh New Year and noon runs each expose one zero-budget entry where the
nested BIOS call refills the CPU budget:

| Profile | Event ordinal | Before cycles | After cycles | PIC unchanged |
| --- | ---: | ---: | ---: | --- |
| New Year | 581 | 0 | 6349 | Yes |
| Noon | 324 | 0 | 6350 | Yes |

The original host source already retained in `clock-neutral-host` explains the
nested execution: `src--dos--dos.cpp`, GetSystemTime case 0x2c, calls
`CALLBACK_RunRealInt(0x1a)`; `src--cpu--callback.cpp` invokes `DOSBOX_RunMachine`
for that BIOS call, and the CPU core/scheduler handles exhausted slices. These
are raw counter observations, not clock inputs or output corrections.

The two profiles explicitly require these exact ordinal/zero-entry/return-value
witnesses. Every other event still requires the original five-cycle delta;
all register, stack, original-call signature and source-attribution checks stay
active. The actual exceptional inventory must equal the declared one. The old
profile supplies no refill allowance and rejects any changed delta. Paired
untouched equality establishes neutrality for these specific capture recipes.
No generic arbitrary-cycle allowance, rewritten raw trace or masked register
was introduced.

## Integrity and tests

`calendar-pins.json` independently authenticates every retained file, including
metadata and reference outputs. The verifier pins that manifest, original guest
identities and the parent host-source/observation corpus. Actual acquisition
sources are frozen under `calendar-acquisition/` with a separately pinned source
manifest; evolving tools do not retroactively redefine acquisition provenance.
No retained observation has been modified to satisfy the model.

```sh
python3 scripts/verify_maintenance_calendar.py
python3 scripts/test_maintenance_calendar.py
python3 scripts/verify_maintenance_clock_neutral.py
python3 scripts/test_verify_maintenance_clock_neutral.py
python3 scripts/test_replay_maintenance_records.py
python3 scripts/test_replay_maintenance_clock_neutral.py
python3 scripts/verify_archive.py
```

Five new test methods exercise the twelve-run corpus, all four before-only
profiles with forbidden after-target reads, eight refill/caller/port corruptions,
four unsupported-input/inventory conditions and four retained-artifact mutations.
Existing 63 observation, 21 composed-model and eight clock-neutral replay tests
still pass. CI verification needs only Python standard library; native capture
additionally needs the already documented host and operator-supplied Frida/Node.

Fresh acquisition requires absent output/scratch paths:

```sh
python3 scripts/recover_maintenance_calendar.py /tmp/calendar-new \
  --scratch /tmp/calendar-disposable \
  --frida-module /absolute/path/to/frida/build/src/frida.js
python3 scripts/verify_maintenance_calendar.py /tmp/calendar-new
```

ASLR, PIDs, host timestamps and mount paths legitimately change, so a fresh corpus
requires independent semantic review and pinning; the verifier does not approve
new hashes automatically. The immutable retained corpus stays unchanged.

## Remaining work

The selected next-day, New Year, leap-day and non-midnight initial-world controls
are now complete, not missing research. These four cases are not arbitrary-date,
arbitrary-clock or arbitrary-world prediction. Next expand bounded state coverage:
occupied NPC placement/rejection, faction collision/merging and populated-player
or evolved maintenance. Retain explicit rejection for unrecovered paths and pair
new host profiles with untouched runs. General MBF and broader TIME$ formatting,
clock rollovers during execution, exact DOS save interoperability and production
compatibility remain separate. Modern exploit safeguards remain intentional.

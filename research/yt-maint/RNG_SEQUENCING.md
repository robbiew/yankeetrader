# Maintenance reseeds, executed-site counts and one occupied-candidate retry

This follows [first-hit recovery](RNG_FIRST_HITS.md). It measures the original
YTMAINT.EXE against one inactive-player initial-world fixture, with a repeated
launch, shifted clock and explicitly synthetic occupancy gate. It adds no Go
behavior, dependency or save-35 change. Full post-maintenance replay is still a
separate milestone.

## Evidence and questions answered

The retained [controls](sequence-controls/) contain **463 returned runs**:

- Four untouched executable runs: baseline, independent repeat, requested second
  two, and the occupied-candidate fixture.
- 78 main-body-end counters: every one of the 43 literal RND instructions plus
  both helper reseeds in baseline; eleven selected sites in each other fixture.
- 381 terminating nth-hit reads: every baseline helper's old state, sampled
  TIMER, seeded state and draw output; eight selected raw RND FACs; four initial
  occupied-fixture helper calls; and all 60 baseline helper return addresses.

Every captured input and output is retained or reconstructed from immutable
source pins. The independent verifier checks decoded DAT/ASC bytes, executable
patch reconstruction, launch options, clocks, DOS exit witnesses and arithmetic
relationships. These are separate runs stopping at individual boundaries, not
one simultaneous trace of every operation.

### Observed literal-site counts

The baseline counters execute all the way to the return from the maintenance
main body. The 43-site inventory has nine nonzero counts; the other 34 are zero.

| Main offset | Executions | Phase context |
| --- | ---: | --- |
| `2237` | 1 | Wanderer post-selection draw |
| `226c` | 1 | Wanderer post-selection draw |
| `2363` | 1 | Wanderer post-selection draw |
| `3348` | 950 | Eager player-cloak candidate scan |
| `3c0e` | 24,800 | Eager ordinary interception player-cloak scan |
| `46af` | 20 | Desertion chance, before the ownership condition excludes NPC forces |
| `537e` | 1 | Super-planet lottery gate |
| `7908` | 41 | Single-draw reseeding helper |
| `7989` | 76 | Repeated shrinking-bound helper |
| **Total** | **25,891** | Literal RND encodings in this fixture only |

An apparent ineligible player or nonhuman owner does not necessarily suppress a
random draw: the original evaluates several combined conditions eagerly. The
950 count fits 19 complete 50-player candidate scans. The 24,800 count is 496
complete 50-player scans; it is **not** established as 496 route hops. Native
context identifies the loop, while the counter measures the executions. Arbitrary
worlds, active-player branches and indirect runtime paths are not covered by this
literal inventory.

### Repeated helper seeding and call order

All **41** single-draw helper reseeds and **19** shrinking-bound helper reseeds
match the raw sampled TIMER transform:

```text
newState = (oldState & 255)
         | ((FAC[0] XOR FAC[2]) << 8)
         | ((FAC[1] XOR FAC[3]) << 16)
nextRND  = (214013 * state + 1744579) mod 2^24
```

The old state's low byte is retained at each invocation; helpers do not restart
from a universal constant. All 41 single-draw outputs and all 76 shrinking-bound
outputs match exact LCG steps. The latter form nineteen four-draw sequences,
each beginning at that invocation's newly measured seed. Eight independently
captured raw FAC outputs also equal `state / 2^24` exactly.

Stack return-IP/CS observations identify each baseline helper caller. Every
observed frame has the same main code segment, `01a3`, in these launches:

| Helper | Ordered return IPs | Meaning of selected caller |
| --- | --- | --- |
| `78f3` | `1f88`, `26a8`, then (`320a`, `3284`) nineteen times, then `437a` | Wanderer selection; Xannor fallback preparation; group fallback/candidate placement; Mercenary Base restoration |
| `7939` | `31a3` nineteen times | Mobile allocation's shrinking-bound helper; no mine-damage caller in this fixture |

The component count is therefore `1 + 1 + 19 + 19 + 1 = 41`. The native literal
caller inventory contains other paths, but those are not observed helper callers
in this baseline. Per-helper ordering and the native call flow do not constitute
a complete global ordering of all 25,891 draws.

### Candidate rejection is a different loop

The single-draw helper `78f3` contains no internal retry. Its Wanderer caller
reads the selected sector's planet link (record offset 93) and calls the helper
again when that field is positive. The helper `7939` instead reseeds once and
takes repeated shrinking-bound draws; its four iterations are not four rejected
destinations.

The occupancy fixture changes **only** the four bytes at sector 1095's planet
link from zero to MBF two (`00000082`). This is an explicitly synthetic branch
gate: it does not install a valid second planet or claim a consistent playable
DOS universe. It tests rejection of a positive link independently of unrelated
planet contents.

The first selection still yields 1095. That candidate is rejected; another
helper call selects 1792, where the untouched occupied-fixture run places The
Wanderer. Helper seed/draw counts rise from 41 to **42**. The first two seeds are
`b08105` and `b081b4`; outputs `5d6fb4` and `98e9a7` yield the two candidates via
`floor(3000 * state / 2^24) + 1`. This shows both the extra reseed and retention
of the first output's low byte, rather than advancement through one uninterrupted
LCG stream.

The original prints “Wanderer has successfully warped!” before checking the
candidate. The occupied fixture prints this twice although only one destination
is accepted. The raw record and branch evidence, rather than that optimistic
receipt alone, establish the retry. General rejection distributions, full
occupancy and a finite retry budget are not recovered here; existing bounded
modern safeguards remain in place.

## Instrumentation and untouched comparisons

[Retained assembly](sequence-native/probe.asm) describes both 46-byte diagnostics.
The original 43,185-byte file length, 512-byte MZ header, runtime and all unrelated
code are preserved. A selected five-byte runtime dispatch is replaced with a
jump to main `004b`. At each hit the diagnostic saves flags, decrements a private
CS counter, and either restores flags and executes the displaced five-byte
instruction or emits four raw bytes and exits with DOS status zero. Counter
storage lies inside the replaced `0044..0071` return/cleanup area, not the world
or runtime RNG state. No diagnostic I/O occurs before the selected stop.

Threshold 65,535 counts never reach zero in these fixtures. At main-body return,
the guard writes the remaining counter and `C!`, then exits. A count is exactly
`65,535 - remaining`. **This bypasses the original cleanup/footer and is not
untouched normal completion.** Nth-hit runs terminate earlier. Separate untouched
runs retain the original “Daily Maintenance Completed OK” witness.

The caller variant reads SS:`BP+2` (return IP and CS). Its two extra instructions
reuse the otherwise trailing marker bytes, leaving the payload 46 bytes long.
An unexpected normal return would expose the adjacent unchanged original bytes
`57cd`; all sixty caller controls instead hit their selected boundary.

Every one of the **78** main-body-end counter runs produces exactly the same
entire decoded DAT/ASC file set and bytes as its matching freshly untouched
oracle, despite bypassing the footer. Baseline and repeat untouched outputs also
match one another. This supports these specific instrumented comparisons; it
does not prove instrumentation-neutral timing under arbitrary clocks or inputs.

The new baseline world hash is
`ada65f0695c768cdf59c853ac4800da33c15047ce06eb9332a563da767f1e983`, identical to
the earlier initial-handoff baseline. It differs by 97 bytes from the separate
first-hit milestone's fresh baseline `183706df...`. Both historical recipes and
pins remain unchanged. No individual filename, clock or command is isolated as
the cause; a printed clock string alone still cannot authenticate an exact replay.

## Native anchors and verification

Four fresh REA/Ghidra `read_bytes` observations in
[sequence-native/rea.json](sequence-native/rea.json) independently match relocated
original YTMAINT bytes:

| Address | Bytes | Evidence ID |
| --- | ---: | --- |
| `0x178f3` | 240 | `ev_83e7420f94915b498d61fcbb597e0831fb3d83484d6aa35185ade10ee43a0060` |
| `0x11f51` | 120 | `ev_9f4084c0abfb6edb2d20a37178f239ce0f341f028d23dd433e5effb979bdde70` |
| `0x13311` | 187 | `ev_586646966304423964e134343ec3104f96e2fe82e9c7c3b2cd48e4951404e7a6` |
| `0x13b94` | 252 | `ev_1033598d6eb1a65c191cf946d6a3a4455616507ac1442d12a0ada20a98389519` |

[Native notes](sequence-native/FINDINGS.md) distinguish static branches, existing
record-layout corroboration and dynamic observations. Static reads do not show
execution. Original YTMAINT, BRUN30 and archive bytes remain unchanged.

Portable verification requires Python standard library only:

```sh
python3 scripts/verify_maintenance_sequence.py
python3 scripts/test_verify_maintenance_sequence.py
```

Fresh capture requires DOSBox Staging and absent output directories. Capture the
403 ordinary controls and 60 caller controls separately; their named children
form the combined retained set:

```sh
python3 scripts/recover_maintenance_sequence.py /tmp/yt-maint-sequence-new
python3 scripts/recover_maintenance_sequence.py /tmp/yt-maint-callers-new --callers
```

Expected pins are reviewed evidence, not refreshed by the acquisition script.
The independent corruption suite rejects 49 altered controls/semantic variants.
CI runs the portable verifier and corruption controls. DOSBox, NASM and REA's
native-analysis tools remain research tools, not game/runtime dependencies.

Next: recover full global phase/interception chronology and exact post-maintenance
record/auxiliary replay against the untouched runs. Arbitrary worlds/clocks,
general MBF arithmetic, production BBS gameplay and native Windows crash durability
remain outside this slice. No new Go/PTY gameplay acceptance is claimed.

# Initial-maintenance scan chronology and RNG state bridges

This continues [the reseed/count milestone](RNG_SEQUENCING.md), published in
[PR #87](https://github.com/robbiew/yankeetrader/pull/87). It joins the measured
helper calls to the eager player-scan phases in one inactive-player fixture.
It is research only: no Go gameplay, dependency, original archive, `qb36-v1`
recipe or save-35 changes.

## Questions and scope

The earlier 24,800 ordinary interception draws were not evidence of 24,800
encounters or 496 successful route hops. This slice asks which mobile groups
consume them, how their player loops connect to the candidate scan, and whether
the surrounding RNG states agree with the separately captured reseeds.

There are **332** new returned controls in [chronology-controls/](chronology-controls/):
one untouched completed run, four main-body-end counters and 327 terminating
nth-hit samples. The same reviewed 46-byte diagnostic is reused; the capture
runner imports the acquisition helper, while the independent verifier imports no
capture code. Normal instrumented main-body return bypasses the original cleanup
footer and is not labeled untouched DOS completion.

The fresh untouched run matches every decoded DAT/ASC output from the prior
pinned baseline. All four new complete counters match the fresh untouched file
set and bytes. Counts remain 950 candidate draws, 24,800 ordinary interception
draws, 41 single-draw helper reseeds and 19 shrinking-bound helper reseeds.

## Measured phase ledger

Fresh first/last boundary samples identify **groups 2 through 20** and cached
**player slots 2 through 51**. These are original internal indices, not modern
JSON player IDs. Each group's candidate scan takes fifty eager draws. Its
ordinary interception phase takes the following number of complete fifty-player
scan blocks:

| Group | Candidate draws | Interception scan blocks | Interception draws |
| --- | ---: | ---: | ---: |
| 2 | 50 | 29 | 1,450 |
| 3 | 50 | 21 | 1,050 |
| 4 | 50 | 22 | 1,100 |
| 5 | 50 | 35 | 1,750 |
| 6 | 50 | 38 | 1,900 |
| 7 | 50 | 30 | 1,500 |
| 8 | 50 | 24 | 1,200 |
| 9 | 50 | 20 | 1,000 |
| 10 | 50 | 40 | 2,000 |
| 11 | 50 | 25 | 1,250 |
| 12 | 50 | 23 | 1,150 |
| 13 | 50 | 22 | 1,100 |
| 14 | 50 | 25 | 1,250 |
| 15 | 50 | 34 | 1,700 |
| 16 | 50 | 21 | 1,050 |
| 17 | 50 | 13 | 650 |
| 18 | 50 | 26 | 1,300 |
| 19 | 50 | 35 | 1,750 |
| 20 | 50 | 13 | 650 |
| **Total** | **950** | **496** | **24,800** |

The counts begin as distances between independently pinned helper states. Fresh
state/group/player samples at both ends of each proposed block independently
test that partition. The verifier requires exact LCG advancement from the
candidate's first draw to its fiftieth, then through every counted interception
draw to the next helper entry. The measured group and player indices must agree;
counts alone cannot authenticate an incorrectly shifted phase boundary.

The original outer loop starts at group 2. Group 20's exclusion test contributes
to a combined rejection mask, but it does **not** short-circuit the eager RND at
`3c0e`. Its thirteen scan blocks still consume 650 draws. These are ordinary scan
evaluations despite the excluded group and inactive players; they are not proof
of successful attacks.

### Sector arguments and movement ordering

At the interception RND boundary `3c0e`, the sampled four-byte MBF values are:

| Main DS address | Meaning |
| --- | --- |
| `7b8c` | Mobile group index |
| `7bf0` | Interception player-scan index |
| `7bc0` | Candidate-scan index, sampled separately at `3348` |
| `7b68` | Sector before this route step |
| `7bc4` | Selected next sector passed to the movement helper |

The movement helper `71af` stores the selected destination into the group sector
array before the interception loop. Therefore `7b68` is the **old** sector, not
an up-to-date location or a remaining movement budget. Each sampled old/next pair
is checked as a directed edge in the immutable original input graph. There are
38 such edge pairs: the first and last scan boundary for each mobile group.
All nineteen sampled last destinations retain positive Xannor forces in the
untouched post-maintenance world. These observations and the static route walk
explain the count, but they do not record every one of the 496 intermediate edges
or prove successful completion under arbitrary worlds, encounters or path failures.

## Joined RNG-family chronology

The previously verified sixty helper seeds and 117 helper draw states are reused
only after their own immutable evidence passes verification. The fresh samples
join these families in the selected baseline:

1. Midnight entry seed is `00c805`. The first single-draw helper reseeds from its
   measured TIMER; its output is followed by the three Wanderer draws at `2237`,
   `226c` and `2363`. Their endpoint matches the next single-draw helper's entry.
2. That helper's output is the first mobile allocator's entry, with no additional
   RND step between those observed boundaries.
3. For each of groups 2–20, the shrinking-bound helper takes four draws. Its
   endpoint is the fallback helper's entry; the fallback output is the candidate
   helper's entry. Both intervening helpers reseed from their sampled TIMER and
   preserve the old low byte.
4. The candidate helper output starts the fifty-player candidate scan. The next
   state starts ordinary interception. The complete per-group scan counts in the
   table advance exactly to the next allocator entry, or after group 20 to the
   Mercenary Base restoration helper.
5. After that helper, twenty consecutive desertion draws advance without another
   measured reseed. Fresh before-samples for all twenty draws and the final
   after-sample close the tail. The next state is the single super-planet lottery
   gate; its before/after pair is exactly one LCG step.

This accounts for the baseline's **25,891 literal RND executions**:
`41 + 76 + 3 + 950 + 24,800 + 20 + 1`. The full reseed transforms are retained in
the earlier milestone. The combined state bridges and static control flow support
this bounded family ledger; the samples are not one simultaneous all-event
trace. Unmeasured indirect paths, active-player/battle branches, other clocks
and input worlds remain separate. None of these RNG checks synthesize the full
post-maintenance record/auxiliary bytes yet.

## Native evidence and patch boundaries

Three fresh REA/Ghidra `read_bytes` observations in
[chronology-native/rea.json](chronology-native/rea.json) independently match
relocated original YTMAINT bytes:

| Address | Bytes | Evidence ID |
| --- | ---: | --- |
| `0x13113` | 529 | `ev_98fc8b0a3fcd219b71baf0bda38e8b767819a5358462e2c21e9c556b3e9151ac` |
| `0x139d4` | 1,116 | `ev_658ad14a8bd6dcde639d4f4ed3d0b1d6a29c37ce681e7e947b659598d786bae5` |
| `0x171af` | 188 | `ev_de4563c2b8f859f2df6603802b0a7aa0b73f8fcc4978996cf2685d7700edd827` |

[Native notes](chronology-native/FINDINGS.md) retain exact array/argument mappings,
branch ranges and limitations. Static reads do not establish execution by
themselves. The original executable/runtime hashes and MZ header remain unchanged.

Five-byte diagnostic hooks must respect QuickBASIC runtime dispatch boundaries.
For example `3c13` is a six-byte operation with inline `80`, so it is **not** a
safe five-byte post-RND hook. This milestone samples `3c0e` before the draw instead.
The tail post-draw sites `46b7` and `5386` have complete five-byte dispatches.
Original source bytes are reconstructed independently; no production executable
is patched.

## Reproduction and remaining work

Portable checks use Python standard library and retained artifacts:

```sh
python3 scripts/verify_maintenance_chronology.py
python3 scripts/test_verify_maintenance_chronology.py
```

All 332 controls, three native reads and 51 negative/provenance/semantic tests
pass. The checker first verifies the earlier sequence anchors, then all new raw pins,
patches, source/site identities, clocks/launch/return witnesses, decoded indices,
graph edges and LCG bridges. Acquisition does not automatically rewrite expected
pins. New DOSBox captures require an absent output directory:

```sh
python3 scripts/recover_maintenance_chronology.py /tmp/yt-maint-chronology-new
```

README, the plan, validation notes and CI accompany this research. No new Go,
terminal-gameplay, native Windows crash-durability or live BBS acceptance is
claimed. Next recover exact post-maintenance record/auxiliary replay, starting
from these measured seeds and phase boundaries. General MBF arithmetic and
arbitrary-world dynamic chronology remain outside this slice.

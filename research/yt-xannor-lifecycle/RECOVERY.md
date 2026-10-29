# Xannor HQ and Xannoron lifecycle research

This slice preserves **38 completed original-DOS runs and 76 completed-run save
snapshots**, plus **three separate eight-second relocation stalls with six
snapshots**. Eleven new REA byte observations and one reused random-helper
observation corroborate the decisive branches. These are research artifacts;
Go gameplay and save version 13 were unchanged by the research commit.
The subsequent [version-14 implementation](IMPLEMENTATION.md) adds bounded
home/HQ lifecycle with explicit modern policies.

Target: original `YTMAINT.EXE`, SHA-256
`8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6`.
Unmodified executables run only in disposable DOSBox mounts. The original archive
is neither mounted nor patched. All 4,682 archived hashes pass.

## Questions and evidence boundaries

| Question | Result |
|---|---|
| What recreates Xannoron? | A zero HQ sector planet reference; active-name deletion is unnecessary. A nonzero wrong reference suppresses recreation. |
| What does existing-home restoration do? | Add a random integer 0–24 to ground, force owner -1, and replace an exactly zero bank with 1,000,000. |
| How is regeneration funded/capped? | Maximum named record's stored score and normalized pointed Xannor strength; strict cutoff and integer divisions recovered. |
| Who can be challenged at HQ? | Positive defenders with owner below -1 or above 1. Owner 1 is skipped. |
| When does HQ relocate? | Empty pre-regeneration HQ without a reclaim attempt, or a successful reclaim with surviving HQ force. |
| Which destinations qualify? | Sectors 8..N, rejecting foreign fighters greater than one or planet references greater than one. No capacity exit. |
| Can the phase invent force? | Yes: a zero-bound random helper can return the stale relocation sector number as a new group's strength. |

This answers the bounded lifecycle/rule questions. Full mobile targeting,
ship/planet combat, revenge/cloak search behavior, all malformed-pointer cases,
and bit-exact QuickBASIC RNG/MBF parity remain outside this slice. The top-score
loop checks nonzero name length after earlier cleanup; a complete dead-but-retained
alias matrix was not run, so it is not described as a direct living-player test.

## Isolation and replay

The full-size recipe starts from
`archive/analysis/dos-validation/evidence/YTDATA.DAT`: 3,000 sectors, 1,000 ports,
100 planet slots and fifty inactive player records. It preserves the original
warp graph and ordinary port contents while clearing treasuries/titles, mines,
old sector defenses and group/planet pointers. Four controlled planets establish
The Wanderer, a probe planet, Mercenary Base and Xannoron. Normal fixtures give
HQ sector **1114** 10,000 Xannor fighters and group pointer 1 points there.
Planet production starts at the maintenance date with zero rates/stocks and tiny
reserves; prior ordinary production can still produce measurable MBF fractions.
The complete original maintenance path runs, including later mobile groups.

Human controls copy the archived team-captain player record, declare all further
overrides, place alias Q in protected sector 7, and set its stored score as needed.
No live user accounts are involved. A separate small layout has **21 sectors,
21 ports and 100 planet slots**, with boundaries 51/72/93/193. All twenty Xannor
bookkeeping records and the revenge pointer fit in its sector block. Eight-sector
fixtures would make those bookkeeping accesses overlap later record blocks and
are deliberately not used to prove a relocation stall.

In small controls HQ is 8. Candidates 9–20 hold separate neutral planets; sector
21 is the single candidate under test. The Wanderer can move among remaining
home sectors before the Xannor phase. A freed candidate removes both its planet
reference and its Block14 record. Saturation cases retain a consistent blocked
planet or a two-fighter foreign group. Thus the stall is reached in HQ relocation,
not an earlier Wanderer search or an undersized record-layout accident.

Requested DOS date is 10/25/2026 and time 00:00:00, except two creation controls
requesting 04:00 and 08:00 and next-day children dated 10/26/2026. Captured DOS
clock logs can differ from the requested time by a fraction of a second (for
example 03:59:59.95); the verifier checks within one second, not invented exact
clock/RNG identity. Replays can differ in random outcomes. Preserve the original
samples rather than overwriting them or claiming deterministic runtime replay.

The two child processes read the **exact final world bytes** from `zero-hq` and
`missing-both`, respectively, without reset or new patches. Supporting message,
name and score files are freshly copied from the archived source for each run;
this is a complete world-state chain, not a claim that every side file is chained.

## Xannoron recreation and existing-home mutation

The creation predicate at `20ad..20e5` reads the **current configured HQ sector's
planet reference**. It does not first inspect the reserved planet record's name
or owner. In normal configuration the test effectively means reference == 0.

- `missing-reference` recreates the home while its old record is still active.
- `missing-both` and the two requested-clock variants recreate it too.
- `inactive-record` retains reference 100 and leaves active-name length zero;
  no new home is made and zero production rates are not repaired.
- `wrong-home-reference` keeps reference 2, suppressing recreation even though
  the active Xannoron record becomes unreferenced from that HQ.

Creation uses reserved slot 100 and name Xannoron (length 8), production 100,000
for each commodity and owner -1. Ground begins with `floor(RND*250)`; bank begins
with `RND*10,000,000 + 100,000`, stored with MBF rounding. It clears cargo stocks,
missiles and mines, but **does not clear planet fighters or plasma**. Both active
and inactive stock-reset controls start with fighters37/mines3/plasma5; final
fighters37/plasma5 remain, while mines and cargo/missiles become zero. Therefore
the older zero-stock recreation sample did not prove unconditional empty stocks.

The existing-home block at `2331..23dd` executes immediately after creation too:

```text
ground = prior_ground + floor(RND*25)
owner = -1
if bank == 0: bank = 1,000,000
```

For a newly created record the two ground draws sum to 0..273 in ideal arithmetic,
not merely 0..249. Recorded final values such as 39, 103, 53 and 138 are samples,
not fixed defaults or measured distributions. Existing positive banks stay intact;
a zero bank becomes exactly 1,000,000. The earlier ordinary planetary phase must
be considered before attributing any other growth to this block.

The `captured-planet` control begins owner2/ground500,000/bank1,234 and ends
owner-1/ground500,003/bank1,234, without an HQ fighter reclaim attempt. The title
is overwritten despite the large human garrison; this phase is not a recovered
ground assault. A modern implementation should retain the explicit captured-home
ownership policy established for Mercenary bases.

## Group cache, normalization and regeneration

Group locations occupy field105 of sector records 1–20. Loading reads them into
an array and clears the persisted pointers. For each positive location, only a
sector currently owned by Xannor supplies its fighters to the cache; that sector's
fighter count and owner are then cleared. Foreign-owned pointed groups are not
harvested. Duplicate locations merge into the earlier array entry; because the
first harvest cleared the owner, a repeated location usually supplies zero.
Zero/negative location or zero strength clears that entry. Positive upper bounds
are not checked before the original GET; those malformed-pointer cases were not
executed here.

`duplicate-pointer` puts slots 1–3 at the same HQ. Its entire final world is
byte-identical to `hq-held`, confirming no triple-counting in this control.
The 999-fighter foreign pointed group remains human-owned, while the equivalent
Xannor group is harvested/moved. A split config/pointer control harvests 5,000
fighters at sector1200, then configuration resets location1 to HQ1114. The old
unpointed HQ force can be merged with cached force during final writeback; do not
assume inconsistent pointers are repaired simply by changing a location value.

For top named stored score T and normalized pointed strength X:

```text
regen = floor(T/500)
if X > floor(T/100): regen = 0
```

| T with X=10,000 | Reported regeneration |
|---:|---:|
| 100,000 | 0 |
| 999,999 | 0 |
| 1,000,000 | 2,000 |
| 1,000,500 | 2,001 |
| 10,000,000 | 20,000 |

The strict comparison permits regeneration at equality and can exceed its
cutoff afterward. A foreign HQ owner gives cached HQ strength zero before the
regeneration step. The verifier independently derives these results from each
input world and checks the original reported amount.

These isolated worlds can split HQ force into empty mobile slots and later lose
fighters in combat. **Final HQ or total strength is not the regeneration amount.**
The complete later targeting/splitting/battle algorithm is not claimed recovered.
Anchors: `2436..24ee`, `26c9..29af`, `29b1..2abf`.

## Reclaim battle and relocation

A reclaim attempt requires defenders>0 and `(owner < -1 OR owner > 1)`.
The paired owner controls use the same 100 defenders and stored score10,000,000:
Mercenaries(-2) and human2 trigger a successful attempt; owners0 and1 trigger no
attempt. The literal DOS owner1 exclusion must not be copied into Go's first
real player account. The HQ reclaim battle uses **250** as both strict threshold
and large batch while both sides exceed250; otherwise batch1. `RND <= .5` removes
defenders, higher draws remove HQ fighters. This differs from the Mercenary
200/150 thresholds and its strict casualty-side tie. The 250 threshold is MBF64
at DS:8518; interpreting its first four bytes as MBF32 incorrectly gives zero.

Success clears the old defense count and owner, then relocates with survivors.
The overwhelming-defense control logs failure, retains a surviving human defense
and stays at1114. A zero-score failure also stays at1114, but later mobile action
changes the final owner: a failure message alone cannot establish the final
world's owner or prove that no later reclamation occurred.

At `2d55..2d9f` relocation follows either:

```text
(no reclaim attempt AND HQ strength == this run's regen)
OR (reclaim attempted AND HQ strength > 0)
```

The first branch detects an empty pre-regeneration HQ, including zero==zero;
it is not limited to a positive replenishment. A missing HQ pointer likewise
can cause relocation while old untracked sector fighters remain behind.

Destination search samples sectors8..N and rejects:

```text
(fighters > 1 AND owner != -1) OR planet_reference > 1
```

In the 21-sector controls, an empty candidate21 completes relocation. A human
or Mercenary one-fighter candidate is also accepted; an Xannor two-fighter
candidate is accepted. A human or Mercenary two-fighter candidate blocks forever,
as does a neutral planet reference14. All three blocked searches are stopped
after eight seconds, before mobile/Mercenary phases or completion; they are not
counted as completed maintenance runs. Earlier cache/planet changes are already
visible in the preserved partial world.

No warp or mine check protects candidate selection. Static code also allows a
Wanderer reference1; that particular overwrite path was not isolated dynamically
because The Wanderer moves earlier. Do not describe all planet references as
excluded. Relocation writes both configured HQ and group-location1, clears the
old sector reference only if it equals slot100, and unconditionally installs
reference100 at the new sector. It does not copy or clear the planet record.
Final writeback adds group force to any force already at its location and sets
owner-1, explaining candidate one-fighter absorption without combat.

## Zero-bound random helper invents fighters

With no cached Xannor force and score0, relocation can leave HQ strength0.
The missing-mobile-slot path at `315f..31e5` allows the equality0>=0, calls the
shrinking-bound random helper with count4/bound0, then consumes its old result.
The helper at7939 returns early for a zero bound/count **without initializing
the output**. Its stale value is the last relocation sector selection.

The full-size `zero-hq` run relocates to1475 and reports Group2 strength1475,
starting from zero Xannor fighters and zero regeneration. The small empty-candidate
control relocates to21 and reports Group2 strength21. Final force at21 is21;
with a foreign one-fighter candidate it is22 and owner-1; with a two-fighter
Xannor candidate it is23. The positive-score small control regenerates2,000 and
uses a nonzero bound, providing a separate boundary control.

The static trace subtracts this stale allocation from zero HQ force, creating a
negative cached HQ balance, while later writeback preserves the phantom mobile
force. This is a legacy defect, not a spawning rule to reproduce. Initialize
random-helper results on every path and preserve nonnegative force accounting.
[Readable derived branches](recovered_rules.py) retain the defect explicitly for
research; their synthetic controls do not claim DOS RNG sequence parity.

## Evidence and validation

- [DOS manifest](dos/results.json): 41 cases, with completion/timeout state,
  executable/runtime/source hashes, declared overrides, dates/times and hashes.
- Full-size and small baseline gzip files are reconstructed independently.
- Each case contains before/after world snapshots, original date/time outputs,
  transcript, emulator log and result metadata.
- [REA records](rea/phase-paths.json): 11 complete inline byte observations,
  verified against the relocation-adjusted original MZ load image. The verifier
  also checks the previously preserved helper observation in
  `../yt-mercenary-maintenance/rea/phase-paths.json`. REA sessions were closed.
- The verifier checks the exact two next-day world chains, creation/reserve/
  title/stock accounting, regeneration, normalized duplicate outcome, HQ pointer
  changes, candidate capacity stalls and phantom force controls.

```sh
python3 scripts/recover_xannor_lifecycle.py /tmp/yt-xannor-new
python3 scripts/verify_xannor_lifecycle.py
python3 scripts/verify_mercenary_maintenance.py
python3 scripts/verify_archive.py
```

The destination must not exist. Select cases with `--only`; for child-only replay,
use `--parent-world /path/to/parent/after.dat.gz`. Never point this runner at live
saves or mutate the preserved samples. Timeouts are bounded and no DOS process
remains running. CI validates artifacts without DOSBox or REA.

Seven rehashed negative controls were rejected: preserved human planet ownership
instead of the observed retitle, wrongly cleared fighters, silently removed
phantom force, retained candidate ownership, successful relocation during a stall,
a modified child world and a falsified regeneration report. This distinguishes
semantic verification from mere checksum comparison. The new and existing
maintenance verifiers and all archive hashes pass; Python syntax/link/diff checks
are part of the research commit validation. No Go gameplay checks are claimed
necessary for this documentation/evidence-only change.

## Research recommendations and implementation

Start with **explicit Xannor home identity and bounded home restoration**, using
the same conservative captured-ownership policy as the Mercenary base. At research time,
version13 accepted only Mercenary home identity; extending it required deliberate
validation/migration coverage. Do not infer a home from a legacy name/slot or
move a player's captured planet merely because an HQ pointer moved.

Then add an explicit HQ/group state model with unique participants, safe cache
normalization, current living-player targeting policy, capped nonnegative
regeneration, bounded reclaim work and a finite permitted relocation pool. Reject
all occupied foreign defenses and all unrelated planet references unless an
explicit supported combat/ownership operation handles them. Preserve conservation
when combining existing Xannor forces. Avoid the unbounded retry and stale-result
spawn defects. Full NPC ship combat, revenge/cloak search behavior and exact
QuickBASIC arithmetic remain separate milestones.

The bounded home/HQ portions above are now [implemented](IMPLEMENTATION.md),
including persistent reserve, safe regeneration, reclaim and finite relocation.
Mobile targeting/splitting, NPC ship attacks and revenge/cloak searches remain
separate milestones; the evidence and legacy defects above remain unchanged.

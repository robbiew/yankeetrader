# Mobile Xannor splitting, targeting and route actions

This research preserves **47 completed original-DOS maintenance runs**, 94
before/after world snapshots, one exact next-day world chain, and **22 complete
REA byte observations**. It answers the bounded questions below. The research
commit changed no Go gameplay or save format. The subsequent bounded mobile
[implementation](IMPLEMENTATION.md) retains world version 14.

Target: original `YTMAINT.EXE`, SHA-256
`8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6`.
The runner copies the unmodified executable, BRUN30 runtime and archived DAT/ASC
side files into fresh disposable DOSBox directories. It never mounts the archive
or live BBS saves. All 4,682 original archive hashes remain unchanged.

## Finding ledger

| Question | Answer and evidence boundary |
|---|---|
| Which groups activate? | Slots 2–20, ascending; existing groups bypass missing-slot allocation. Protected-sector results can retry the same group. Static + full-group DOS controls. |
| How does HQ split? | Require HQ force >= stored top score / 2000, **without truncating that threshold**; four shrinking-bound draws allocate force and subtract it from HQ. Equality and 1999/2000/2001 controls confirm the boundary. |
| How is a target chosen? | Separate fallback and preferred candidates, optional top/revenge override, then low-HQ return override. Selection and override ordering are static-derived, with forced-return and top-player controls. |
| Is target state local to a group? | No. Shared preferred/output state can retain a ship's sector after a group dies there, producing subsequent ordinary attacks below the special hunt threshold. Paired full-group controls + helper bytes. |
| Does routing use shortest paths? | The tested directed graph chooses the first equal-length warp and chooses a shorter second branch over a longer first branch. Unreachable paths log an error and hold force. |
| What happens on arrival? | Per-hop mines, sector defense, planetary helper, then eligible ship interception; surviving groups continue along the route. DOS ordering/stopping controls + call-site bytes. |
| Are Xannor hazards the Mercenary rules? | No. Mines use one 1–1000 draw each; defense batches use 5000/500/1 boundaries. Tie direction matches HQ, not Mercenary strict casualty-side ties. |
| Is all NPC combat now recovered? | No. These runs establish dispatch/order, selected aftermath, and sector-defense rules. Full ship/planet battle formulas, revenge behavior, and bit-exact RNG/MBF parity remain separate work. |

## Fixture construction and limits

The full-size baseline derives from the independently verified
[Xannor lifecycle isolation world](../yt-xannor-lifecycle/RECOVERY.md): 3,000
sectors, 1,000 ports, 100 planet slots and cleared old groups/treasuries/mines.
The archived team-captain player template occupies DOS record 2, alias Q. The
basic fixture puts Q in protected sector 7 with stored score 4000 and diagnostic
cloak 10, HQ at 1114 with one fighter, and existing group 2 at sector 100 with
100 fighters. The only outgoing links from 100 and 101 are 100→101→1114.

The high diagnostic cloak explicitly isolates route/planet effects from ship
interception; it is not a claim that modern 0–1 cloak permits a value of 10.
Separate target controls use cloak 0 and valid cloak 1. Initial named score
selects the low-HQ threshold; it is not inferred from the player's modern assets.
The original scoreboard recalculates scores later, explaining the next-day
chain's different regeneration and allocations.

Here initial pointed Xannor strength is 101, above score/100 = 40, so regeneration
is zero. HQ force 1 is below score/2000 = 2, suppressing every missing slot while
forcing the existing group to return to HQ. It is therefore possible to isolate
one moving group despite the complete original maintenance path running.

Full-group target controls populate every slot 2–20 and hold HQ at 1,000,000,
preventing allocation from confounding selection. Q has large ship defenses so
an observed interception does not delete the target; those deliberately declared
ship assets are not reconstructed score inputs. The compact controls use 21
sectors/ports and 100 planet slots, keeping all twenty group pointers and the
revenge pointer inside the sector block. Every group initially has a distinct
location; no out-of-bounds or duplicate pointer is used to manufacture targeting.

The frozen [fixture declarations](dos/recipe.json) define every patch and preset.
The verifier independently reconstructs both baseline layouts and checks all
before-world bytes, not only field summaries. The next-day child consumes the
parent's exact final world bytes without reset or additional patches. Side files
are freshly copied for each run, so this is an exact **world-state** chain, not a
claim that every message/name/score side file is chained.

DOS dates are 10/25/2026 and 10/26/2026 for the child. Most runs request midnight;
valid-cloak controls also request 04:00 and 08:00. Captured clock logs are checked
within one second. Results are preserved observations, not promises of identical
RNG sequences on replay. All 47 runs completed; no timeout is counted as a new
mobile result. The runner still bounds every process at 45 seconds.

## Group allocation and conservation

At `311e–31e5`, a group with location <1 **or** strength <1 needs allocation.
The current HQ cache must satisfy:

```text
HQ >= greatest_named_stored_score / 2000
```

This threshold retains its fraction. The `split-score-1999`, `-2000`, and `-2001`
controls hold HQ=1 and existing mobile force=100. The first two allocate exactly
one fighter to group 3; the third creates no new group and the existing group
returns home. Truncating score/2000 would incorrectly permit that third split.

The integer interpretation of helper `7939` is four successive
`bound = floor(RND * bound) + 1` draws, starting at current HQ strength. Assign
that result to the missing group, subtract it from HQ, and set its location to
the configured HQ. Allocation tests HQ again for each later slot. Existing groups
skip that allocation check but remain subject to the final low-HQ target override.
The `split-high` sample prints groups 2–20; total deployed force remains 110,000,
including the original 100,000-fighter mobile group and 10,000-fighter HQ.

The previously recovered zero-bound stale-result defect still applies when both
HQ and score permit a zero-bound call; it is not repeated as a legitimate spawn
rule here. [Prior direct phantom-force controls](../yt-xannor-lifecycle/RECOVERY.md#zero-bound-random-helper-invents-fighters).
Modern implementation must preserve nonnegative accounting and initialize every
helper result. A bounded modern integer implementation can compare
`HQ * 2000 >= score` instead of rounding the threshold. Exact large/fractional MBF conversion and RNG distributions are
not established by these whole-fighter boundary controls.

## Destination selection and shared pursuit

The static sequence is:

1. Draw fallback sector 1..N until it differs from current location (`31e6–3227`).
2. Normally inspect one new candidate; an active revenge sector permits up to
   25 attempts (`3234–33eb`). Prefer `(fighters > 1 AND owner != -1) OR planet > 1`.
   Otherwise scan cached player records for a matching sector and
   `(RND > cached_cloak OR revenge)`.
3. If the shared preferred value is >7, use it; otherwise retain fallback.
4. Override to the preselected top sector for group 20, or groups 16–19 while
   revenge is active and that sector is nonzero (`3406–3457`).
5. Finally, HQ < topStoredScore/2000 overrides every other choice to the HQ
   (`345c–347a`). This is what makes the route controls deterministic in target.

The candidate predicate, exact ordinary-cloak tie, and revenge flag branches are
static-derived. No new revenge runtime matrix is claimed. Fallback rejection and
protected-sector reactivation have no recovered retry budget. A preferred
planet can be below sector 8; it fails the preferred>7 adoption test, but that
does not make the fallback or intermediate route protected.

Top-player selection uses greatest named stored score with a strict `>` update,
so equal scores retain the earlier record. Special hunting requires score at
least **2,500,000** and a separate detection test involving cached cloak minus
.33 (`2567–25cb`). Its ideal passing comparison is `cached_cloak-.33 <= RND`;
that exact tie is static-derived. A separate .25 draw chooses cached versus
just-read player position. Missing/out-of-range/protected top positions get a
random replacement sector 8..N and clear the top-player ID.

The paired `top-threshold-below`/`top-threshold-equal` controls use 2,499,999 and
2,500,000 with cloak 0 and Q at 250. Only equality announces the special hunt;
group 20 attacks Q there and is destroyed. `top-protected` still prints the hunt
announcement before replacing Q's sector 7; the announcement alone therefore
does not prove the final target. Diagnostic cloak 10 suppresses hunting. Valid
cloak 1 produces no hunt in the midnight sample and a hunt at the two other
requested times; all save cloak about .95 afterward. These are three observations,
not a measured detection probability or an exact RNG boundary experiment.

**Shared pursuit is observable separately from special hunting.** `DS:7bac` is
cleared once at `2fb8`, not at each group's selection. It is also passed as an
output to action helpers. On losing a ship battle, helper `5811` stores the
mobile group's current sector through that output, then clears the destroyed
group's location/strength (`5de4–5e0e`). A following candidate that does not
replace the preferred value can retain that sector (`3302–330e`). A successful
kill or other helper result can clear/change it; this is conditional shared
state, not an unconditional fixed destination for every later group.

In the below-threshold sample, group 3 dies at Q's sector 250; groups 4–19 then
attack Q and die there too, despite no special hunt announcement. Group 20 uses
its separate fallback top-sector override. The hidden-player control preserves
group 3 at sector 250 without ship combat and later groups disperse. The 21-sector
controls additionally show repeated activation lines for groups ending in the
Union, confirming the same-group retry rather than a simple once-only loop.

## Directed routing and per-hop actions

The route builder starts at current location and reconstructs a directed
breadth-first path (`34eb–39d3`). The controlled equal-length branch 101 is chosen
first and kills the group with mines. Reversing warp order chooses 102 and leaves
the mines untouched; a longer first branch loses to a shorter second branch.
A direct warp likewise avoids an unnecessary mined detour. Removing all outgoing
warps reports `Sector path not found` and leaves group pointer/force at 100.
It completes maintenance, not an unbounded path-search stall.

On each entered sector, call `71af` for mines/sector defense, `5efd` for the
planet, then eligible `5811` ship interception. Survivors repeat along the path.
Origin mines/planets are not revisited. A planet that kills the group at 101
leaves later mines at 102 untouched, disproving a whole-route hazard pass followed
by a separate whole-route planetary pass.

Mines use an initial-count loop with one helper-78f3 roll bounded by **1000** per
mine. Cap each hit at remaining force, consume a mine only while a positive hit
can damage positive force, and retain unspent mines after destruction. The
original continues drawing through the initial mine-count loop after force hits
zero; there is no work limit. A 100-fighter sample dies to the first of three
mines, leaving two; a 100,000-fighter sample consumes all three and loses 780.
This is not the Mercenary nested 10,000-bound algorithm.

Foreign nonzero-owner sector defense battles use these whole-fighter batches:

```text
5000 when both remaining sides > 5000
500 otherwise
1 when either remaining side < 500
RND <= .5 removes defenders; RND > .5 removes Xannor
```

The constants at DS:8a80,8a88,8ac2 are MBF64 values 5000,500,1; interpreting their
first four bytes as MBF32 misleadingly gives zero. The 500/5000/5001 controls
corroborate the distinct batch boundaries; the exact tie is static-derived and
checked in the readable model, not forced in the unmodified executable. There
is no recovered battle work cap.

Friendly Xannor and owner-zero defenses are skipped. Unpointed friendly force
stays in its intermediate sector while the mobile group passes, and combines
only if a cached group ends there during final writeback. Winning foreign defense
combat clears the sector title/force and permits the planetary action; a loss
persists defenders and clears the mobile pointer/strength. Mixed controls prove
mine deaths prevent defense combat and defense deaths prevent planetary attacks.

Foreign planets are attacked, not a Mercenary-style stock pickup. Guarded neutral
and human probe planets kill the 100-fighter group; Xannor-owned planets are
skipped and retain their 37 fighters. A zero-ground planet is logically destroyed
and the surviving group continues; the inactive record's stale stock is not loot.
Complete ship and planetary battle formulas remain outside this research.

Protected sectors require care: a directed route **can transit sector 7**, and a
controlled foreign planet there **is attacked**. Union mines are cleared earlier
at `0419–0488`, before Xannor movement. The mine/no-mine transit controls have
byte-identical complete final worlds. That pair proves early cleanup interference;
it cannot establish a special Union exception inside the mobile mine helper.
Modern protected-spawn policy must be explicit rather than copied from routing.

## Verification, replay and subsequent implementation

[Manifest](dos/results.json), [frozen declarations](dos/recipe.json), before/after
snapshots, original transcripts, DOS clock and emulator logs are preserved per
case. The verifier reconstructs all input bytes, checks exact world chaining,
regeneration/allocation/casualty accounting, action order, retained titles/stocks,
clock provenance and all 22 complete REA records against the relocated MZ image.
REA sessions were closed. [Readable branches](recovered_rules.py) provide synthetic
boundary checks without claiming to emulate MBF or the original RNG.

```sh
python3 scripts/recover_xannor_mobile.py /tmp/yt-xannor-mobile-new
python3 scripts/verify_xannor_mobile.py
python3 scripts/test_xannor_mobile_verifier.py
python3 scripts/verify_xannor_lifecycle.py
python3 scripts/verify_mercenary_maintenance.py
python3 scripts/verify_archive.py
```

The destination must not exist. Use `--only` for selected controls and
`--parent-world` for child-only replay. Saved runs are never overwritten. CI
verifies artifacts without DOSBox or REA. Modern engine, live BBS and native
Windows acceptance are not claimed by this research-only commit.

The implementation scope derived from this research is bounded group
allocation/selection, directed movement,
mines and sector-defense actions on the explicit modern HQ model. Keep each
participant unique and conserve overflow; permit no force creation from stale
output. Give targeting/reroutes/mines/battles finite work budgets and protect
Union destinations and transit. Preserve captured homes and normal faction
identity. Make shared pursuit state an explicit supported policy rather than an
accidental local-variable carry. Use the existing living-player and attribution
policies; the DOS named-score/top-player matrix is not a complete modern identity
policy. Full NPC ship/planet combat and revenge/cloak targeting need their own
focused recovery and integration; unsupported encounters should hold safely
rather than silently pass through targets the original attacks.

Validation passed: both new verifier scripts, the existing lifecycle and
Mercenary evidence verifiers, all 4,682 archive hashes, Python syntax, relative
documentation links and diff checks. Nine independently restored, rehashed
negative controls were rejected for their intended semantic reasons: phantom
force, wrong mine remainder, invented planetary pickup, path teleportation,
truncated split threshold, discarded pursuit, changed child input, misattributed
Union cleanup and falsified DOS clock. CI runs these controls without an emulator.
The research commit did not require Go gameplay tests; current implementation
validation is documented separately. Live BBS acceptance remains unverified.

The bounded splitting/selection, movement, mine and sector-defense portions are
now [implemented](IMPLEMENTATION.md), with explicit modern identity, work and
unsupported-encounter policies. The original research observations and remaining
full ship/planet combat boundaries above are unchanged.

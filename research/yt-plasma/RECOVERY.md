# Plasma launch, routing and disruption recovery

**Historical research-stage document.** The subsequent [Go implementation](IMPLEMENTATION.md)
now completes bounded plasma launching in save26. The research-stage statements
below retain their original scope and do not describe today's playable status.

Research completed 2026-10-31. **Research only: no Go gameplay or save-format
change. Plasma firing remains unavailable; save version 25 is unchanged.**
The next implementation is the separate [bounded candidate contract](CONTRACT.md).
This report extends the earlier [damage-absorption study](../yt-combat/RECOVERY.md),
rather than counting its seven plasma sessions again as new controls.

## Evidence and reproducibility

The retained [DOS corpus](dos/recipe.json) contains **62 normally returned controls,
124 full before/after world snapshots and two exact world/auxiliary reload
chains**. Every control retains its exact input, DOS date/time output, program
return marker, raw CP437 log, rendered transcript, complete auxiliary bytes,
source/binary hashes and result metadata. Unfinished input-driver pilots are
excluded. The final capture reuses 58 completed controls after checking exact
case declarations, source identity, normal return and every retained file hash;
the remaining four were freshly run. Reuse does not synthesize an outcome.

All controls preserve the original 3000-sector header and 100-planet table. They
are deliberately controlled worlds: links and defenses are replaced, unused
player records are disabled, planets are cleared/remapped, and inventories,
occupants and timestamps are declared. They are not untouched generated worlds,
frequency estimates or exact random-sequence reproduction. A common startup
unreachable-course message occurs even in the quiet control; projectile course
failure is judged in the actual firing/tracking portion, not by that message's
presence anywhere in the transcript.

The source world is
`archive/analysis/yt-combat/experiments/fixture-planet-transfer/YTDATA.DAT`, SHA-256
`2a63d12af095a59227840946be57fd4b7e4dafb5724d4019de694da7c4194b19`.
The authoritative original `YT.EXE` SHA-256 is
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
The harness copies the original executable, BRUN30, LOCAL, KEYFEED and fixture
assets to disposable directories before DOSBox Staging runs. It neither mounts
archived originals for execution nor patches executable bytes, runtime memory
or a fictitious persistent hole flag. Both reloads use the exact parent's saved
world and complete auxiliary bytes, with no setup patches reapplied, at
DOS00:01:00. Independent controls use 10/24/2026 and an explicitly declared clock,
usually 00:00:00; `adjacent-clock-01` uses 01:00:00.

[Native analysis](NATIVE.md) retains **13 complete byte reads and one reconstructed
MZ load-image observation**, with all 870 relocations independently checked against
the original executable. Its source-range ledger, Evidence IDs, loaded addresses
and profile digest distinguish static interpretation from DOS execution. The
native session was closed after export.

Portable retained-evidence validation needs no emulator:

```sh
python3 scripts/verify_plasma.py
python3 scripts/test_plasma_verifier.py
```

The verifier independently decodes MBF, reconstructs declared setup and the MZ
load image, checks raw/rendered logs, exact inputs and return/clock witnesses,
resource accounting, route/energy receipts, damage/cleanup order, complete saved
world/auxiliary witnesses and both reload chains. All **53 corruption controls** pass (47 DOS semantic/provenance controls and six
native/declaration controls). They rewrite metadata/hashes as appropriate; a self-consistent altered outcome must still be
rejected. These checks verify retained observations and interpreted invariants,
not an implementation of DOS RNG or every QuickBASIC rounding operation.

Fresh disposable captures require local DOSBox Staging and an absent destination:

```sh
python3 scripts/recover_plasma.py /tmp/yt-plasma-new --workers 6
python3 scripts/recover_plasma.py /tmp/yt-plasma-writer-check --only quiet-origin --workers 1
```

The capture tool retains incomplete controls for diagnosis and exits unsuccessfully
if any program fails to return normally. Fresh captures are additional observations;
they must not overwrite the reviewed corpus or silently replace expected casualties.

## Launch admission and accounting

| Question | Retained control and result |
|---|---|
| Empty stock or no turns? | `no-bolts` and `zero-turns` refuse without a launch or resource debit. |
| Last available turn? | `one-turn` fires once, consumes one bolt and ends at zero turns; ordinary shell/cloak handling still applies. |
| Cancellation? | `blank-sector` returns to the shell; zero/negative quantity also cancels. No bolt or turn is spent. |
| Bad sector? | Zero and 3001 reprompt. Invalid input discards stacked remainder; fresh valid input followed by zero quantity exits without firing. |
| Excess or fractional quantity? | Ten requested from nine is refused; `1.9` fires one. Native quantity parsing uses VAL/INT. Modern input should explicitly require whole positive quantities. |
| Self or Earth target? | Both are accepted when connected/current. A current-sector shot actually hits the launcher's ship, including while cloaked. |
| Empty or unreachable course? | Empty sectors can receive a shot. An accepted unreachable shot still consumes one turn and bolt before course failure. |
| Several bolts/repeated shots? | Two bolts create one 5,000,000 pool; repeated single launches consume two turns/two bolts. The exact reload preserves the resulting debit. |

There is no separate final yes/no launch confirmation in the recovered DOS path.
The one-turn and stock writes precede the weapon routine, so DOS rejection and
partial-save behavior must not be mistaken for an atomic modern transaction.
The caller normally remains in sector 100; projectile redirection does not warp
the ship. Self destruction is a separate recorded exception.

## Course, range and black holes

Plasma chooses a directed shortest course through stored exits. Reversing the
first sector's exit order reverses the selected equal-length first hop in
`route-tie`/`route-tie-reverse`. `avoid-route` explicitly avoids 101, yet the shot
still crosses it to 102. Travel avoids do not make physical projectile immunity.

For quantity B, launch energy is `E0=B*2,500,000`; each additional ordinary course
hop subtracts the fixed `E0/50`, rather than a percentage of the remaining pool.
One bolt reaches 101/102/103 at 2,500,000/2,450,000/2,400,000 in the empty three-hop
control. Two bolts reach those sectors at 5,000,000/4,900,000/4,800,000. The 60-hop
requested course enters exactly 50 sectors, ending at sector 150 with 50,000;
it never reaches the requested 160. A short course stops at its target rather
than continuing indefinitely through that target's exits.

Original sensors identify this login's actual holes 592 and 1051 in the selected
full-width fixture. Entering either prints a tracking entry, then redirects
**before fighters, mines, ships or the planet at that entry absorb energy**.
The million fighters at hole 592 remain untouched. These are the login's existing
holes, not patched sector fields.

A redirect chooses a new requested destination and rebuilds a directed route
from the hole. It does not instantly apply damage at the random destination.
At the selected clock the first observed destination is 2368. An unavailable
route dissipates the shot; a supplied 592→2368 route reaches the defended 2368.
The first hop of the rebuilt route retains the current pool without an extra
fixed travel debit. A rebuilt 592→100→2368 route hits the shooter back at 100;
the damage can exhaust the pool before 2368. A course through both holes records
two redirects. The ship itself remains at 100 in these surviving controls.

Native control flow has no explicit redirect budget. A same-sector random
request can re-enter a hole without travel loss. Valid zero random absorption
draws also need not reduce energy. Finite modern route/redirect/absorption limits
are therefore required; these observations do not establish universal DOS
termination or a safe unrestricted billion-bolt implementation.

## Indiscriminate damage and aftermath

One shared energy pool visits sector fighters, sector mines, ships in ascending
record order (fighters before shields), then the linked planet. The mixed control
prints this order, including a second mine phase for a destroyed ship's wreck
mines before the planet. Once energy is exhausted by the first large ship, the
second ship remains untouched. Ship fighters can absorb the volley while its
shields remain unchanged.

Separate controls damage enemy and own sector defenses, the shooter's current
ship, an enemy ship, a cloaked ship, a teammate ship, own and teammate-governed
planets. Physical inclusion must be separated from what modern private/public
receipts are authorized to disclose. Original tracking text exposes names; it
does not establish a modern privacy policy.

The earlier absorption formulas are corroborated rather than replaced: fighter
increments `floor(E/5000)+1`, shield increments `floor(E/10000)+1`, mine increments
`floor(E*0.000001)+1`, and planetary decrement `E*0.000004`; each iteration spends
a single-precision random energy debit promoted to double. Actual losses clamp
to available assets. Exact casualty numbers in these captures are observations,
not golden predictions for fresh clocks or an unimplemented RNG emulator.

`lethal-ship` marks the other ship dead, clears its sector, attributes the kill,
grants saved salvage and drops its five inherited mines; the remaining plasma
then absorbs those mines. `mixed-defense` independently reaches the subsequent
planet after that chain. `self-lethal` ends the caller's login, records death,
sets its sector to zero and drops/absorbs eight carried mines. DOS can leave the
old shield value in a dead record while printing zero shields. Modern lifecycle
cleanup must follow its documented consistent estate policy rather than copying
that stale-field artifact or passing self/team deaths through an enemy-only API.

No transitive recovery of every historical estate helper, concurrency guarantee,
posthumous award or armed retaliation combination is claimed here. The prior
[HQ reward recovery](../yt-xannor-hq-reward/RECOVERY.md) already proves the plasma
owner-check defect; modern HQ credit must retain the actual prior-Xannor-owner
guard rather than rewarding destruction of friendly fighters at HQ.

## Planet projection, damage and retirement

Planet impact first calls the lazy updater. A raw pre-session zero rate is not
necessarily zero at impact: excess stock can become production. The matched
non-firing `planet-zero-projection` and `planet-small-projection` controls place
the same planet record at the caller's sector, decline the ground assault and
save rates near 100/200/300 from stocks 1000/2000/3000 without plasma or ground
loss. The direct-shot raw-zero control consequently reports about 600 production
lost, not evidence that a zero-impact gate was bypassed. Projection times differ
slightly; these are structural comparisons, not exact same-instant arithmetic.

`planet-impact-zero` instead zeros all three rates **and all three stocks**.
It records zero productivity reduction and retirement. Native code tests the
post-update cached ore rate or mutable organic/equipment rates before each damage
iteration; it can reach clamp/save/retirement with no damage iteration. Do not
infer an unconditional initial round merely from the hit/destruction text.

That cached value is ore **production**, not ore cargo. Once damage begins,
positive entry ore production can keep the gate open after mutable ore reaches
zero. The ore-only full/empty-stock controls both lose the same production and
ground when the other categories and their stocks are truly zero. The small
organic-only control has all stocks zero and retires after its small rate pool
is consumed. Native interpretation and these bounded controls do not establish
bit-for-bit MBF boundary behavior for every numeric input.

Surviving impacts reduce ground and each production category, cap stocks to ten
times their corresponding remaining production, and clear an empty garrison's
governor. All-zero productive planets are retired by clearing their active name
length and sector link; the destructive controls also save zero ground/governor.
The retained full bytes distinguish logical retirement from a securely erased
record: inactive records can retain other numeric inventory/bank fields. The
reload of `planet-small` confirms its missing active link and spent bolt/turn.
A modern deletion must remove every landing grant and preserve nonreusable
planet generations; it does not kill the governor's ship or award the bank.

## Implementation boundary

This research supplies launch/routing/impact evidence, not a firing command.
[CONTRACT.md](CONTRACT.md) identifies the current reusable store/death/planet
mechanisms and the missile filters that cannot be reused for indiscriminate
plasma. The next implementation must choose explicit self/friendly/posthumous
source rules, concrete shared work/quantity bounds, fresh sealed confirmation,
private receipt rules, finite failure behavior and schema needs. All origin
costs, casualties, wreck hazards, estates, planet cleanup, HQ reward/revenge and
reports must commit together or roll back together.

Mercenary plasma sales, other disruption/spy branches, exact DOS RNG/MBF parity,
broad balance changes, live BBS gameplay and native Windows crash durability
remain separate. No full Go/terminal regression suite was rerun for this
research-only milestone; its portable evidence checks and immutable-archive
verification are recorded in [validation notes](../../evidence/VALIDATION.md).

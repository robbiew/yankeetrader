# Bounded Xannor revenge and candidate selection

HQ fighter and missile victories now queue a persistent revenge target. Daily
Xannor movement consumes that target once and performs bounded candidate searches
using the [recovered rules](RECOVERY.md), with explicit modern safety policies.

## Queue producer and target lifetime

A player must clear the entire deployed **Xannor-owned** sector garrison at the
current authoritative HQ. Fighter battle and missile impact call the same queue
helper only after that force reaches zero. A non-HQ victory, partial damage,
retreat/loss, Mercenary or human garrison, and planetary destruction do not queue
revenge. NPC maintenance fights do not create human targets. Plasma remains an
unimplemented player weapon; no legacy missing-owner plasma defect is imported.
This revenge milestone originally added no credit reward. The later
[HQ reward implementation](../yt-xannor-hq-reward/IMPLEMENTATION.md) now pays
qualifying victories in the same combat transaction.

`Xannor.Revenge` stores one player ID and ship generation. A later committed HQ
victory replaces the pending target. The target tracks that ship's **current**
position at maintenance, rather than storing the attack sector. Death immediately
clears it; a replacement cannot inherit the old ship's target. Validation rejects
missing, dead or generation-mismatched persisted targets.

The first forward daily Xannor route phase consumes the slot, including when the
target has moved into protected Union sectors, no mobile force exists, or only
one non-Union sector exists. Those cases do not retain a retry for every login.
A valid target outside the Union activates revenge mode and initializes shared
preferred sector. It is an attempt to pursue, not a guarantee of interception:
new preferred candidates, top-player overrides, HQ returns, routes, mines,
sector/planet combat, cloak and finite work still affect outcomes.

Queue creation, garrison/ship inventory changes, later volley effects and
consumption compose inside the existing locked `Store.Update`. Callback or
validation failure rolls back the entire transaction. A committed directory-sync
failure preserves the saved daily marker and cannot replay consumption. Competing
HQ confirmations settle once; an old warning cannot recreate the removed force
or target. All player/session generation checks remain active.

## Candidate selection and finite work

Sorted actual sectors greater than seven form the eligible pool. Fallback is one
uniform draw from that pool excluding the origin, eliminating the DOS rejection
loop and protected-sector shortcuts. When fewer than two eligible sectors exist,
mobile movement stops without a random retry. Directed routes still exclude all
seven Union sectors.

Each activation permits one candidate ordinarily or **at most 25** in revenge
mode. A linked actual planet or foreign defense stronger than one can replace
shared preferred. Once preferred is nonzero, the search exits before scanning
players, including when this candidate did not replace a prior preference. Thus
revenge does not guarantee 25 attempts.

Otherwise examine current living players in ascending modern ID order. Every
visited living player consumes a detection draw before testing sector match or
revenge, including players in other sectors. Ordinary discovery accepts strict
`RND > cloak`; revenge bypasses that discovery comparison while preserving the
draw. Dead players and unused DOS cache slots are excluded. Modern player ID1 is
valid. No stale live/cache discrepancy or out-of-range GET is emulated.

Selection has at most `1 + 25*(1+50)` random draws per activation: one fallback,
at most 25 candidates and 50 current living-player checks each. Top selection has
at most two additional draws for the phase. These fixed selection bounds are
separate from the existing 10000-step per-route budget for hops, mine bursts,
planetary/sector combat and ship detection/combat. At most 19 mobile activations
remain possible. Returned force cannot fund more splits, receiving groups cannot
repeat their activation, and overflow retains a representable holding point.

## Top-player, cloak and override policies

Select the greatest positive stored score among living players, retaining the
lower player ID on equal scores. A positive-score leader always consumes its
initial detection draw even below the 2,500,000 hunt threshold. The top-sector
hunt requires score at least that threshold, `RND >= cloak-.33`, and a current
non-Union position. Otherwise choose a finite non-Union fallback.

Current locked positions replace DOS's separate live/cached position and `.25`
choice. The top sector is preselected once. If a ship later dies during this
transaction, a group may still travel to that sector, but actual encounters only
consider current living ships and retain generation/report-publication checks.
No cached player ID can cause a phantom battle.

After shared preferred adoption, revenge groups 16–19 and all group 20 activations
use the preselected top/fallback sector. Finally, HQ split budget below
`topStoredScore/2000` forces the HQ return and takes precedence over every target.
Exact integer comparison preserves fractional score thresholds.

All groups, including group 20, use the same ordinary ship interception policy:
`RND >= current_cloak-.33`. This corrects the earlier strict-equality gap. Revenge
bypasses **candidate discovery**, not combat cloak. The legacy group 20 endpoint
special call without another cloak check is not introduced. Existing finite ship
battles, private casualty reports, public death/planetary news and no-loot/no-wreck
NPC aftermath remain unchanged.

Cloak continues to decay with turn spending. This milestone does not add a second
daily `.05` subtraction or alter saved energy during selection. It does not claim
bit-exact DOS random streams, cache behavior or MBF rounding.

## Caller status, migration and privacy

Both classic and compact `I`/`INFO` display “Xannor revenge pending for this ship.”
only to the matching current player/generation. Viewing status does not consume
the target. Other callers and public newspaper entries do not expose the pending
identity, sector or force. Actual battle reports continue through `BATTLES`.

Save version 17 adds the optional generation-bound pending target. Version 16 and
earlier supported worlds upgrade with no fabricated target, preserving existing
HQ/reserve, assets, homes and report/radio/news history. Future revenge fields in
legacy-labelled saves are rejected. Read-only loading does not rewrite disk; the
next successful update saves version 17. Older binaries cannot read it; downgrade
requires a matching stopped-world backup. Upgrade all door nodes together.

## Validation

Game regressions cover actual fighter/missile HQ wins and negative owner/location
cases; loss/partial fights; last-write state; death/replacement; invalid/missing
and protected targets; no force/one eligible sector; eager 1/25 search limits;
retained preference; strict discovery versus inclusive interception equality;
groups 16–20 and final HQ precedence; and 32 seeded force-conservation worlds.

Store regressions cover callback/validation rollback, competing HQ confirmations,
missile failure after an HQ-clearing impact, pending state across reload,
concurrent maintenance/login, daily replay/clock rollback, committed durability
failure, death/replacement cancellation and read-only version 16 migration. Door
tests verify private status in both interfaces and no visitor/newspaper leak.

The [real PTY smoke](../../scripts/smoke_xannor_revenge.py) executes ordinary fighter
and missile commands against disposable HQ fixtures, checks saved targets and
private status in both interfaces, then advances maintenance, reads the resulting
battle report and verifies byte-identical same-day replay. Existing affected
smokes expect version 17. Original DOS evidence, models and archive bytes remain
separate, immutable research inputs.

```sh
go test -race -count=1 ./...
go vet ./...
python3 scripts/smoke_xannor_revenge.py
python3 scripts/verify_xannor_revenge.py
python3 scripts/test_xannor_revenge_verifier.py
python3 scripts/verify_archive.py
```

Live BBS acceptance and native Windows durability are not established by local
PTYs or cross-builds. Remaining maintenance phases, equipment and exact DOS parity
continue on the reconstruction plan.

Local validation passed: full race-enabled Go suite and vet; focused late-volley
rollback and partial/finishing-volley regressions; 32 seeded conservation worlds;
16 new/affected terminal smokes; revenge/planetary/ship/mobile/lifecycle evidence
verifiers and ten revenge semantic corruption controls; all 4682 archive hashes;
Linux and Windows cross-builds; changed Python syntax, relative links and
whitespace checks. No live BBS or native Windows run is claimed.

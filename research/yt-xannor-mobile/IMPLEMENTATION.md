# Bounded mobile Xannor groups

Daily maintenance now splits HQ force, selects targets, walks directed routes,
and resolves mines and sector-defense battles using the [recovered mobile
rules](RECOVERY.md). Ship battles, foreign planetary assaults and revenge remain
unsupported; groups hold before those encounters. This is an intentional bounded
slice, not a claim of complete DOS NPC parity.

## Authority, ordering and group identity

The existing version-14 sector defenses remain authoritative. No group pointer
array or save-format change is introduced. At the start of the mobile phase,
sort sectors outside Union 1–7 and snapshot at most 19 non-HQ Xannor groups.
They occupy logical slots 2–20 for that day. Any extra legacy groups remain in
place and retain their force. A group receives at most one activation; arriving
force consumes a pending receiver's activation, while simply passing through a
friendly group leaves its activation available. Newly deployed groups are not
added back into the snapshot.

Normal production/taxes, Mercenary phases, and Xannor home/HQ processing run
before mobile actions; player turn/session resets and score publication follow.
The mobile phase therefore uses the previously published stored score. All
movement, casualties, mine layers and the daily watermark share one locked
atomic transaction. Same-day replay, concurrent maintenance requests and clock
rollback cannot repeat actions. There are no new commands or journal events.

## Splitting and targets

Only the deployed HQ garrison present at mobile-phase entry funds splits.
Contested undeployed HQ reserve cannot launch new groups. Returning fighters,
failed-path refunds and friendly arrivals cannot fund another activation that
day. A missing logical slot requires a positive remaining split budget and
`budget * 2000 >= topStoredScore`. The integer comparison preserves the recovered
fractional threshold. Four shrinking `floor(R*bound)+1` draws allocate force,
which is debited before routing. A zero budget does not draw or create force.
A rejected path refunds the allocated force without replenishing that day's
split budget.

The greatest nonnegative stored score among living players sets the threshold;
ties select the lowest real player ID, including player 1. Dead retained aliases
are excluded. A phase-wide fallback top sector is sampled from permitted sectors.
At score >=2,500,000, the selected living player can become the top target when
`R >= cloak-.33`; protected positions use the fallback. The world lock supplies
one coherent position, so the DOS stale-versus-cached-position draw is omitted.

For each activated group, sample a fallback from permitted sectors other than
its origin, then inspect one preferred candidate. A planet reference, a foreign
defense stronger than one fighter, or a living player passing `R > cloak` can
replace the shared preferred sector. An unqualified candidate retains the
existing preferred value. Slot 20's preselected top sector overrides that value;
finally a low split budget (`budget * 2000 < score`) forces a return to HQ.
There is no revenge state or 25-candidate search in this slice.

Shared pursuit is explicit and lasts only for the daily phase. Winning a sector
battle clears it; losing a mobile group to sector defense records the battle's
sector. Unsupported ship/planet encounters hold safely without fabricating the
DOS ship-loss pursuit event. All selection pools are finite sorted lists;
there is no same-sector rejection loop or protected-sector reactivation loop.
These are modern work/identity policies, not bit-exact RNG-sequence claims.

## Routes and accounting

Use the existing shortest directed-path finder with Union 1–7 excluded from
both endpoints and transit. No path, a same-sector preference, or a capacity
barrier holds the group without teleportation or repeated selection. Origin
hazards are not revisited. Each group shares a 10,000-step budget across hops,
mine bursts and battle rounds.

Before entering a sector containing any live ship, or any planet whose current
owner is not Xannor, stop at the previous sector **before** mines, defenses or
stocks change there. This includes cloaked ships, neutral planets, unguarded
planets and captured faction homes. NPC ship/planet combat has not been
implemented by silently passing through those targets. Origin ships/planets are
not attacked when a group departs.

For supported entries:

1. Consume attributed mine layers FIFO with one uniform integer 1–1000 hit per
   mine, capped at the moving force. Unspent layers keep their owner/order.
   Stop drawing when the group dies or work is exhausted; NPC force destruction
   does not create a player death, wreck or new mine layer.
2. Fight foreign sector defenses with batch 5000 when both sides exceed 5000,
   otherwise 500, reduced to one when either side is below 500. `R <= .5` removes
   defenders; larger rolls remove attackers. The first player and Mercenaries
   are normal eligible defenders. This is separate from HQ's 250 batch and
   Mercenary route's 200/150 thresholds and strict casualty-side tie.
3. Continue through an Xannor-owned planet without taking stocks or changing its
   title, ground, bank or production. Foreign planets and live ships were
   preflighted, so no unsupported combat follows the supported actions.

Mine or defense work exhaustion preserves survivors at the previous sector and
remaining hazards/defenders in place for later days. A won sector battle clears
the defense and permits continued movement. A lost group removes only its own
moving force. The existing player ship, estate, session and attribution state
are not modified by these NPC sector battles.

Passing a friendly group does not harvest it. A transit sector must have capacity
to hold the entire moving group if a later encounter stops it. A partially full
final destination can accept its available capacity, with the remainder held at
the previous sector. Mines at that destination are resolved before the partial
merge. HQ capacity also subtracts persistent undeployed reserve. No overflow is
discarded, and a newly received group cannot immediately move again from its
receiver's pending snapshot slot.

## Compatibility and validation

World version remains **14**. Existing groups are discovered from current sector
ownership after prior daily faction actions. Missiles, player battles and other
ownership changes cannot leave stale mobile group references, because none are
persisted. No migration, inferred faction identity or balance field is added.
Normal version-14 stopped-world upgrade/rollback guidance still applies.

Game regressions cover fractional thresholds, zero-bound safety, failed-path
refunds, returning-force reuse, 19-group limits, friendly transit/merges, top and
HQ override order, cloak boundaries, both casualty thresholds, mine attribution,
work exhaustion, reserve capacity, unsupported encounter preflight, protected
paths and daily score/replay order. Thirty-two seeded friendly worlds enforce
exact force conservation across varying capacity and merge conditions. Store
coverage exercises rollback, concurrent daily movement, reload and failed-save
validation. The process/PTY smoke verifies saved return routes, uniform mine
losses, friendly stocks, safe ship/planet holds, replay and compact/classic
reconnect encounters.

The existing hiring-only regression now freezes production on **both** faction
homes: Mercenary routes can collect Xannoron stocks as well. Its exact tax/hire
assertions remain. The lifecycle smoke counts the entire 2000-fighter regenerated
force across sectors, then isolates landing/capture from deployed fighters.

```sh
go test -race -count=1 ./...
go vet ./...
go build -o bin/yt ./cmd/yt
python3 scripts/smoke_xannor_mobile.py
python3 scripts/smoke_xannor_lifecycle.py
python3 scripts/verify_xannor_mobile.py
python3 scripts/test_xannor_mobile_verifier.py
```

Live BBS acceptance, native Windows durability and exact DOS MBF/RNG parity are
separate validation. Next recover full Xannor NPC ship battles, then planetary
assault/destruction and remaining revenge/cloak search behavior before enabling
those encounter operations.

Validation passed locally: full race-enabled Go suite and vet; both Xannor PTY
smokes, Mercenary hiring/routes/desertion/base and sector-fighter/planet-missile
terminal smokes; mobile/lifecycle/Mercenary DOS verifiers and nine semantic
negative controls; all 4,682 archive hashes; Linux/Windows cross-builds; Python
syntax, changed documentation links and diff checks.


The subsequent [ship-combat research](../yt-xannor-ships/RECOVERY.md) now recovers
the ordinary ship-battle and maintenance aftermath rules in 42 DOS controls. It
does not enable Go ship attacks; the safe holds described above remain active
until transactional NPC combat is implemented.

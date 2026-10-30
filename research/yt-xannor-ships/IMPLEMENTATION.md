# Bounded Xannor ship battles and atomic aftermath

Daily mobile Xannor movement now intercepts current living ships after mines and
sector defenses. It uses the [recovered fighter/shield rules](RECOVERY.md), with
finite shared work, generation-safe death, persistent private reports and atomic
estate updates. The subsequent [planetary phase](../yt-xannor-planets/IMPLEMENTATION.md)
now runs between sector defenses and ships; remaining revenge search is separate.

## Encounters and bounded work

The existing stable daily snapshot admits at most 19 mobile activations. Each
activation retains its 10000-step budget across hops, mine bursts, sector battle
rounds, ship detection and ship battle rounds. A detection attempt consumes one
step even for an unarmed or hidden target. Eligible players are current living
ships in the entered sector, sorted by player ID; ID 1 is a valid modern player.
Protected Union sectors 1–7 remain excluded from routes and NPC death attribution.

Normal ship detection now uses `RND >= current_cloak - .33`. The later
[runtime-aware research](../yt-xannor-revenge/RECOVERY.md) established the equality
boundary; the [revenge implementation](../yt-xannor-revenge/IMPLEMENTATION.md)
corrects the earlier strict Go comparison for every mobile group. Full cloak can evade or
be intercepted; it is not immunity. This phase uses the authoritative persisted
cloak at the transaction's time. It does not add DOS's separate .05 maintenance
cache drain; exact cache/RNG parity remains outside this implementation. The
existing special group-20 target-selection gate remains separate.

Fighters battle first. Batch size is 5000 when both remaining forces exceed 5000,
otherwise 500, reduced to 1 if either is below 500. A fighter round with
`RND <= .5` kills human fighters; higher rolls kill Xannor. If Xannor survive,
shields use the same batch sizes, but `RND >= .5` damages shields and lower rolls
kill Xannor. Cloak does not modify these casualty rounds; missiles never return
fire in this maintenance encounter. Force remains integer and nonnegative.

A surviving group can attack later ships in the same sector and continue its
route. A destroyed group is removed and retains the encounter sector as shared
pursuit output. A successful kill clears that preference. None of these outcomes
adds another activation or replenishes the original HQ split budget.

If work expires during combat, spent force and partial ship damage persist and
the surviving group holds at its previous safe sector. Next-day maintenance
selects a fresh bounded route/target; no detached attacker or unrepresentable
battle reservation is saved. Even a final destination with partially full
friendly defenses must run ship encounters before merging. Overflow returns to
the prior holding point, with every fighter accounted for. Friendly planetary
stocks remain untouched.

## Atomic death and ownership

The route phase runs within the existing process-locked `Store.Update` used by
administrative maintenance and login. Before detection/damage, each target is
checked through the lifecycle validator with current sector, generation, time,
protected-sector policy and explicit Xannor killer. Report/news publication
sequences and clocks are checked at the same point. Exhausted metadata sequences
or an unrecordable target cause a safe hold rather than an unreported death.

Once both ship fighters and shields reach zero:

- Save cause `xannor`, killer -1 and original sector with UTC death time.
- Advance ship generation, clear position, mine departure grace and pending
  docking/landing state. Old live sessions cannot operate on the dead or replaced
  ship, including during a pending prompt or report read.
- Release personally owned ordinary ports and clear their treasuries using
  current ownership; invalidate affected docking quotes. No cached port count is
  trusted.
- Convert personally owned sector fighters to Mercenary ownership, retaining
  their force. The Mercenary phase has already run, so these groups first act in
  later daily maintenance, rather than receiving a surprise extra activation.
- Remove team membership, invalidate shared access and clear a dead captain's
  role. The established visiting-member succession chooses a new captain.
- Retain planetary title, bank and stocks. No planetary capture is invented.
- Consume the destroyed ship's credits, holds, cargo, ground force and weapons;
  award no salvage and create no wreck mines. This deliberately avoids retaining
  spendable stale inventory. Shields save actual zero rather than DOS's old value.

The authenticated replacement path retains account identity, planet ownership,
private reports and the remaining daily turn allowance. A same-day replacement
never refills turns. Normal forward daily maintenance still grants its ordinary
500-turn daily allowance, including when a death occurred in that day's phase.

Death, reports, journal, estate, route force and maintenance date publish in one
save. Callback rejection and failed validation roll everything back. A directory
sync failure after atomic rename remains an explicit **committed durability
error**; retrying maintenance sees the saved date and does not replay aftermath.
Native Windows durability is not established by cross-building.

## Private reports and public news

Each player retains at most the last 32 structured `BattleReports`, including
unread entries. Oldest reports are evicted when that bound is reached. Each
report has a global monotonic ID, UTC time, sector, Xannor/fighter/shield losses,
destruction flag and private unread state. No public journal structure embeds
those counts. A bounded battle can report partial damage even when neither side
is destroyed.

Both compact and classic sessions deliver up to five unread reports per loop.
`BATTLES` reads the recipient's retained history in five-entry pages. Printable
output must complete before acknowledgement; disconnects leave the report
unread. Reads and acknowledgements require the current ship generation. A narrow
recipient-only metadata operation works during hostile encounters without
opening a route around the ordinary resource-mutation gate. Acknowledging one ID
cannot mark a later incoming report read. Delivery is at-least-once if output
succeeds but acknowledgement fails, rather than silently dropping the message.

Only actual deaths produce a public `xannor-death` newspaper entry: alias and
time, formatted as “Destroyed by the Xannor.” Exact casualty counts, surviving
force, sector and private account details are not published in that event.
Reports survive replacement so a victim can read why their previous ship died.

## Save version 15 and migration

Version 15 adds `World.NextBattleReport`, per-player `BattleReports`, Xannor death
attribution and the whitelisted death-news kind. New worlds start at report ID 1.
Version-14 and earlier supported worlds upgrade in memory to an empty report
history; no past NPC attacks or public events are invented. Read-only loads do
not rewrite saves; the next successful update persists version 15.

A legacy version claiming future report state, the new death cause or new news
kind is rejected. Existing identities, assets, homes, HQ/reserve, rankings,
radio/news history and mine attribution survive migration. Older binaries cannot
read version 15. Stop every door node and back up the data directory before
upgrading; rollback requires its matching stopped-world backup and loses later
progress.

## Validation

Game tests cover batch/equality thresholds, fighter-before-shield ordering,
zero shields on death, full-cloak detection boundaries, dead/moved/protected
ships, exhausted generations/sequences, record-order multiple victims,
retained planets, estate/team cleanup, no salvage/wreck mines, shared work
exhaustion, final partial merges, report retention/privacy and validation.

Store tests cover callback and validation rollback, concurrent daily runs,
concurrent fresh login, reload, stale sessions, same-date/clock-rollback replay,
committed durability failures, bound encounter-safe acknowledgement and strict
version-14 migration. Door tests cover both interfaces, history isolation,
failed output, stale generations, deadlines and stopping before unseen pages.

The real GoDoors [terminal smoke](../../scripts/smoke_xannor_ships.py) exercises
saved NPC death/replacement, casualty reports, visitor privacy, public death
news, repeat maintenance, both interfaces and retained planet holds. Existing
schema-sensitive smokes now expect version 15 and remove the new counter when
constructing actual pre-report legacy input. The old mobile safe-ship hold case
is superseded by this combat smoke; planet holds remain checked.

```sh
go test -race -count=1 ./...
go vet ./...
python3 scripts/smoke_xannor_ships.py
python3 scripts/smoke_xannor_mobile.py
python3 scripts/smoke_xannor_lifecycle.py
python3 scripts/verify_xannor_ships.py
python3 scripts/test_xannor_ships_verifier.py
python3 scripts/verify_archive.py
```

Exact DOS RNG/MBF matching, planetary combat, remaining revenge/cloak search,
live BBS acceptance and native Windows durability remain separate boundaries.

Local validation passed: full race-enabled Go suite and vet; 32 seeded ship
casualty-conservation worlds; focused concurrent-login and committed-durability
regressions; new ship, mobile and lifecycle PTY smokes plus Mercenary base/routes,
newspaper, radio, spies, salvage, mines, missiles, teams, sector-fighter and
planet-missile smokes; all three Xannor evidence verifiers and nine semantic
corruption controls; all 4682 archive hashes; Linux/Windows cross-builds; Python
syntax, changed documentation links and whitespace checks.


The next [planetary research slice](../yt-xannor-planets/RECOVERY.md) is now
complete with 71 original-DOS controls and explicit economic-phase boundaries.
The subsequent [planetary implementation](../yt-xannor-planets/IMPLEMENTATION.md)
supersedes foreign-planet holds and upgrades current saves to version 16 while
preserving this ship history. Validation descriptions above record the original
ship milestone; current smokes exercise planetary defenses before ship detection.

# Bounded Xannor planetary assaults and atomic destruction

Mobile Xannor groups now attack foreign planets after mines and sector defenses,
before ship detection. This implements the [71-control research](RECOVERY.md)
with finite work, current ownership, private owner history and atomic cleanup.
It deliberately corrects DOS defects rather than treating them as intended rules.

## Eligibility and combat

Union sectors 1–7 remain excluded. Any linked planet whose current owner is not
Xannor qualifies: human, neutral and Mercenary titles, including captured or
neutralized faction homes. A separate friendly Xannor sector garrison does not
grant immunity. An Xannor-owned home is skipped without taking its stocks.
Home restoration does not forcibly retitle captured planets; an actual mobile
assault can neutralize or destroy them like other foreign planets.

The existing daily snapshot permits at most 19 mobile activations. Each shares
one 10000-step budget across hops, mines, sector fights, planetary dispatch and
rounds, and subsequent ship detection/combat. An unfinished assault saves partial
damage and holds surviving attackers at the previous representable sector.
There is no saved detached army or new activation. Next-day maintenance chooses
a fresh bounded route. A ground victory leaves ships to their existing phase;
planet destruction itself never kills a ship.

Each ground round consumes one ground troop and `floor(RND * 1000) + 1` Xannor
fighters, capped to the remaining force. Positive ground retains its title.
Exactly zero ground neutralizes a nonneutral title, even if the final troop
also destroys the last attacker. It never captures the planet for Xannor.
Neutralization expires every existing landing grant on that planet.

Production is reached only after ground reaches zero, with surviving attackers
and remaining work. This matters for legitimate modern zero-rate planets: a
successful ground defense cannot trigger warehouse capping or deletion.

The production batch is **450 only when at least 450 attackers remain and any
current rate exceeds 500; otherwise it is 1**. This is an explicit modern policy,
not a recovered intended DOS threshold. DOS mistakenly indexed group location
instead of force and could give one attacker a large batch (BUG-015).

On `RND < .5`, damage each of the three rates with an independent
`RND * batch / 3` draw, including components already at or below zero. Otherwise
spend the batch from attackers; equality .5 therefore costs attackers. On exit,
clamp negative rates to zero and cap each cargo stock to `min(old, 10 * rate)`.
No stock increases. All three zero rates destroy a planet only when production
was actually reached. An already empty undefended planet needs a dispatch step
and available production work, but no random draws to destroy.

## Atomic cleanup and reporting

All effects compose inside the existing locked daily `Store.Update`, shared by
login and administrator maintenance. Before planetary mutation, validate public
news publication and the original human owner's private report sequence/time.
Exhausted metadata causes a safe hold. Callback/validation failure rolls back
force, title, stocks, planet links and reports together. A committed directory
sync failure does not authorize replay; the persisted daily marker still wins.

Logical destruction removes the planet map object and sector link and clears
**every player's** matching landing token and landed-planet ID. Missile destruction
uses the same cleanup helper. Old bank, transfer and rename confirmations fail;
reusing the planet slot cannot revive them. Bank and stored fighters, missiles,
mines and plasma are discarded with the object, never converted into loot,
returning Xannor force or ship cargo. No estate, ship death or wreck mines are
created by planetary destruction. Existing ship fights follow only if attackers
and work remain, retaining normal generation guards and separate reports.

The original human owner receives a private snapshot even after neutralization
or deletion. `BATTLES` retains the last 32 combined ship/planetary reports per
player, using the existing global sequence and recipient-only acknowledgment.
Snapshots include planet ID/name, sector, ground before/after, production/cargo
before/after, attacker losses and destruction/neutralization/work-limit outcome.
They do not resolve a current planet ID, so slot reuse cannot rewrite history.
Reports survive ship replacement. Both interfaces deliver unread reports and
acknowledge only successful output. Public newspaper entries contain only the
planet's name and a bounded outcome label, with no location, owner identity,
counts, bank or weapons.

## Save version 16

Version 16 adds optional planetary battle snapshots and a whitelisted planetary
news kind. Version-15 ship reports, counters and news migrate unchanged. Older
versions still use their sequential migrations; none invents past events.
Legacy-labelled saves containing future planetary fields are rejected. Read-only
loading does not rewrite disk; the next successful transaction saves version 16.
Older binaries cannot read it. Stop all nodes and back up the data directory
before upgrading; downgrade requires a matching stopped-world backup.

## Validation

Focused game regressions cover 1/1000 ground losses, mutual exhaustion, defended
zero-rate worlds, 449/450 and 500-rate batch boundaries, .5 ties, independent
commodity draws, caps, empty-world deletion, friendly garrisons, Union protection,
current/captured-home ownership, report preflight, finite work and 32 seeded
conservation worlds. Storage tests cover rollback after destruction, failed save
validation, concurrent maintenance/landing, pending bank confirmations, reload,
replay, committed durability failure and read-only version-15 migration. Interface
tests check owner history, public privacy, both modes and failed-output retention.

The [real terminal smoke](../../scripts/smoke_xannor_planets.py) uses disposable
worlds for ground victory, production/caps, destruction, captured homes, no loot,
repeat maintenance, owner/visitor isolation and compact/classic delivery/history.
Older mobile and ship smokes now test planetary ground defenses rather than the
superseded foreign-planet holds. The lifecycle smoke isolates regeneration from
newly enabled mobile assaults. Original DOS evidence and archive bytes remain
unchanged.

```sh
go test -race -count=1 ./...
go vet ./...
python3 scripts/smoke_xannor_planets.py
python3 scripts/smoke_xannor_mobile.py
python3 scripts/smoke_xannor_ships.py
python3 scripts/verify_xannor_planets.py
python3 scripts/test_xannor_planets_verifier.py
python3 scripts/verify_archive.py
```

Remaining revenge/cloak candidate searches, exact DOS RNG/MBF parity, live BBS
acceptance and native Windows durability remain separate milestones. Cross-builds
and PTYs do not establish native operational acceptance.

Local validation passed: the complete race-enabled Go suite and vet; 32 seeded
planetary conservation worlds; all focused game/store/interface regressions;
15 new/affected real terminal smokes; planetary/ship/mobile/lifecycle evidence
verifiers and their planetary/ship corruption controls; all 4682 original archive
hashes; Linux and Windows cross-builds; Python syntax, changed relative links
and whitespace checks. No live BBS or native Windows run is claimed.

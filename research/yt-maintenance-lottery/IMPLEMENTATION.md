# Bounded super-planet awards and safe inactive-player retirement

Save version 18 implements this milestone using the existing locked, atomic daily
maintenance transaction. The [original-DOS recovery](RECOVERY.md) remains the
research reference; the policies below intentionally avoid its stale-slot,
orphan-owner, duplicate-alias and same-day defects.

## Daily award

After Mercenary and Xannor actions, one random gate enters at `draw>=.5`.
Selection then takes one sorted living-player candidate, one ordinary planet
slot 2–98, and one sorted non-Union sector. There are no retries on an occupied
slot, occupied sector, HQ, defense or minefield. The lottery excludes slots 99/100
to leave room for faction restoration; existing player-created or legacy planets
in those slots are preserved. A full world or no living players completes promptly.

New planets receive a bounded alias-derived name (at most 41 ASCII characters),
current UTC production timestamp, three `draw * draw * 3000` production rates,
1–100 ground and 0–999,999 whole credits. All cargo/weapon stocks start at 0.
No prior record or same-day production is inherited. These use the modern
random source and integer credit rules, not exact BASIC RNG/MBF parity.

The owner, planet/sector link, unread private system radio and public winner
snapshot save together. Only the private message contains the sector. Existing
MESSAGES/INBOX and login delivery handle the notification in both interfaces;
the newspaper displays the public winner. System radio has a distinct stored
kind and sender 0; ordinary callers cannot send from that identity. A full 4096
message archive or exhausted message/news sequence prevents the award rather
than creating an unannounced planet or discarding existing private history.

## Retirement and returning identities

Before economic/NPC phases, a dead account qualifies when **both** its death date
and its most recent authenticated login date are at least 14 UTC calendar days
old. The cutoff is inclusive. Living players, recently killed ships and recently
active identities remain. A separate LastActivity date records successful
compact/classic logins without changing established alias-selection behavior;
legacy LastLogin also counts, and missing activity falls back to world creation.
There is no daily cloak decay or expiry-dependent retirement exemption.

Retirement releases remaining port titles and treasuries, releases planetary
ownership/ground, removes attributed mine layers and residual defenses, removes
team membership with the established vacant-captain succession rule, revokes
landing access and clears a matching revenge target. Other mine layers retain
order and quantities. Ship assets/turns/score become zero. Released planets retain
banks and stock; subsequent production can regrow neutral ground that same day.
The public journal records an alias-only retirement notice. Retirement defers if
its public event cannot be prepared because journal metadata is exhausted.

Player identity, numeric ID, death attribution and private radio/battle snapshots
remain in an inactive record. IDs are **never reused**, including aliases that
match other historical callers. Retired accounts disappear from rankings and
recipient searches. Existing sender/recipient and killer references therefore
remain valid and cannot become another user's history. There are 50 non-retired
player slots, with a finite 256-identity lifetime archive; registration refuses
at archive capacity rather than reassigning an ID. This is an explicit prototype
limit, not an unbounded account archive or an administrative purge facility.

The same authenticated identity can return when an active slot is available.
It receives a new ship generation and 500 turns, keeps its own history and ID,
and gets a retirement notice. Released estates are not restored. Old bound
sessions remain invalid. Another identity receives a new monotonically assigned
ID; full active capacity also blocks reactivation without partial changes.

## Persistence and compatibility

Version 17 and earlier supported saves upgrade in memory without fabricating past
activity, retirements or award events. A read alone does not rewrite the file;
the next successful update persists 18. Legacy headers carrying version 18
activity/retirement/system-message/news fields or expanded identity bounds are
rejected. Existing assets and histories are preserved by migration; normal
subsequent maintenance can retire qualifying accounts. Stop the door and back up
its data before updating all nodes. Older binaries cannot read version 18.

Same-day/rollback maintenance still consumes no draws and makes no changes.
The existing store lock, validation, atomic replacement and explicit committed
DurabilityError apply to the whole operation. Failed callbacks/validation write
nothing; a successful rename with failed directory sync is already committed
and must not be replayed as a resource-spending retry.

## Validation

- Focused game tests cover the inclusive gate/cutoff, current living eligibility,
  fresh initialization, private location, occupied/reserved/hazardous/full
  placement, exhausted metadata, whole-credit bounds, identity/active limits,
  private history, team cleanup, reactivation and strict migration fields.
- 32 seeded worlds each run32 award attempts and validate planet/link/message
  conservation and protected/reserved bounds after every attempt.
- Store tests cover rollback, invalid-save rejection, concurrent daily calls,
  stale sessions, committed durability/replay, retained private participants and
  read-only version 17 migration. Existing version 12/13 fixture builders explicitly
  omit fields absent from those formats.
- The real terminal smoke exercises actual CLI retirement, persisted award
  notification/acknowledgement, public/private separation and same-identity
  return in compact and classic modes. Its award is a saved fixture; deterministic
  game/store tests exercise actual creation. Existing affected radio, newspaper,
  faction, mines, missiles, salvage, spies and team smokes use the current schema.
- Full race-enabled Go suite and vet, the research verifier/eleven corruption
  controls, all 4682 original archive hashes and Linux/Windows cross-builds pass.

Native/live BBS acceptance and native Windows durability remain separate.
Remaining maintenance events (including plague/civil-war parity), HQ credit
rewards, other equipment and exact DOS RNG/rounding require later milestones.

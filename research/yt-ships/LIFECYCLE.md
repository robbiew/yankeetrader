# Modern ship lifecycle foundation — 2026-10-26

This implements the concurrency boundary required before enabling combat. It
uses the [recovered DOS death/online-session evidence](RECOVERY.md), especially
EXP-003/004, the retaliation attribution defect and the 37-to-500 turn refill.
It does **not** enable attacks, self-destruction commands, mines or other hazards.

## Authoritative transitions

Each player has a saved ship generation. A login binds its store access to that
generation. The bound store reloads and checks the player before every callback
under the world lock, and checks views before returning data. This applies to
all existing commands, nested team/planet/port prompts and each autopilot hop.
The game rules also reject destroyed players through the common player helper.
An old login cannot act on a newly constructed replacement ship.

`RecordDeath` is an internal transaction building block. It checks the victim's
current generation and sector. Direct-combat attribution requires an alive,
co-located enemy; teammate kills are rejected. Retaliation permits a different
existing enemy as the killer without rewriting it as self-death. Environmental
and self causes have separate, validated attribution. Future attack code must
still calculate damage, verify weapon/turn/cloak eligibility, and settle all
loot/ownership effects in that **same** transaction.

Death increments the generation, removes the ship from space (sector zero),
records UTC time/cause/killer/former sector, and clears docking/landing sessions.
A dead captain leaves a vacancy for a visiting live teammate. Account team
membership and personally owned planets/ports remain intact in this foundation.
Old ship inventories remain frozen and unusable until replacement; they are not
a source of salvage or new rewards in this implementation. No hazard is dropped.

Fresh login constructs a replacement and increments the generation again.
Replacement cannot be repeated while alive. Known DOS replacement values are
sector 1, 1,005 credits, 10 holds, 25 fighters, 100 shields, one missile and no
cargo, ground forces, mines or plasma. Cloak is not yet modeled. These replacement
values do not change the prototype's existing new-account starting inventory.
Old ship inventory is discarded; account identity, alias, team, personally owned
assets and avoid preferences remain. Retained ownership is a bounded foundation
policy, not a claim that DOS combat estate transfers are fully recovered.

## Turn and date policy

Same-day replacement preserves the remaining daily turn allowance. It never
refills the confirmed DOS 37-to-500 exploit primitive. Normal once-per-UTC-date
maintenance still grants 500 turns on a later date, including to dead accounts;
replacement itself adds no turns. Enemy/retaliation/environmental deaths permit
immediate fresh-login replacement. Self-death requires a later UTC date. Clock
rollback cannot construct a replacement before the recorded death time. This
anti-farming departure from DOS needs balance playtesting with actual combat.

## Storage and validation

World version 4 adds generation and optional death metadata. Versions 1–3 upgrade
in memory and save atomically on a successful update. Ordinary version-3 team
worlds retain their hashes, membership and assets. Older binaries cannot load
version 4; upgrade all nodes together after backing up the stopped world.
Restoring an old binary requires its matching backup and loses later progress.

Validation rejects malformed dead locations, attribution, time and lingering
agreements. Generation counters cannot wrap. A failed settlement callback saves
neither death nor invalidation. There is no production debug/kill command.

Tests exercise enemy/retaliation/self/environmental attribution, cooldowns,
turn preservation, rejected stale/moved/friendly targets, old agreements,
rollback, independent-process generation checks, interrupted purchase/team
prompts and both frontend login paths. `scripts/smoke_lifecycle.py` uses a real
PTY/GoDoors caller and a separate test worker invoking the atomic engine API;
it tests old command chains both before and after another process replaces the
ship. All worlds and worker binaries are disposable.

## Remaining combat work

This foundation is not complete combat or complete EXP-004 exploit-chain
acceptance. Implement fighter/shield rounds, retaliation weapons, cloak, turn
charges, one-time loot settlement, combat asset transfers/death cleanup,
protected-Earth drop invariants, sector defenses and hazard ordering next.
No claim is made about native BBS combat acceptance or exact DOS RNG/MBF parity.

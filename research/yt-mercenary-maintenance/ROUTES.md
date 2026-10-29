# Mercenary daily route actions

Existing Mercenary sector groups now act during daily maintenance, after port
production/tax collection and before new hiring, player reset and score
publication. Hiring remains finite and atomic. Newly hired groups first act on
the following day. This scheduling is a modern policy; DOS moved fresh hires
within the same phase and could repeatedly activate relocated groups.

## Routes and participants

The phase snapshots existing group identities in descending sector order. A
moved group never gains another activation. A Mercenary group receiving incoming
fighters also consumes its pending activation, preventing merged fighters from
moving twice. A full receiver accepting no fighters keeps its pending action.
The subsequent [desertion phase](DESERTION.md) now converts eligible human
groups before this snapshot, giving them the same single route activation.
[Mercenary-base restoration](BASE.md) is now implemented as a later phase.

A source with any planet holds for a draw strictly below .66, regardless of title.
Otherwise one different sector is sampled from the finite permitted destination
list. A valid shortest directed route is required before the source is cleared.
An unreachable destination holds the group without retry or relocation. Unlike
DOS, protected Union sectors 1–7 are excluded from destinations, transit and source
actions; imported Mercenary groups there remain stationary. One valid activation
walks the whole route and handles each intermediate sector.

## Encounter order and conservation

1. Consume mines FIFO before defenses or planetary stock. Each mine resets a
   bound to 10,000 and performs two nested rolls, each floor(random*bound)+1.
   Damage is capped to remaining fighters. A destroyed force stops immediately,
   preserving unused mine counts and their original source-account identities.
2. Friendly Mercenary defenses merge. Positive human-owner defenses receive
   reinforcement for a draw <= .95; other draws cause combat. Negative Xannor
   owners always fight, while still consuming the comparison draw.
3. NPC combat uses 150-fighter batches while both forces exceed 200, otherwise
   one. Draws below .5 remove defenders; ties and higher draws remove Mercenaries.
   Survivors continue after defeating a defense, without revisiting its planet
   for pickup. Defeat removes the attacking group.
4. A planet encountered without a sector defense contributes whole stored
   fighters up to group capacity and ends the activation. Title, ground forces,
   fractional fighters and overflow stock remain with the planet. The origin's
   stored fighters are never picked up just because a group starts there.

Merges/reinforcements cannot exceed MaxQuantity. Excess incoming fighters stop
at the previous sector, preserving their Mercenary owner and remaining force.
There is no forced player ship combat or player death from an NPC group loss.
Ships present at a new defense use the existing encounter checks and confirmed
BRIBE/combat flow on their next action or reconnect. Player mine-entry behavior
and departure-grace rules are unchanged.

## Finite work and transactions

Each group shares an allowance of 10,000 mine bursts/combat rounds across its
whole route. Each burst or round consumes one unit. If a minefield or defense
remains when the allowance expires, surviving attackers hold at the previous
sector; spent mines and combat casualties persist atomically, while remaining
mine layers/defenders remain available next day. No partial destination entry
occurs. This is an explicit modern bounded-work policy, not DOS timing parity.
Route length is bounded by the directed graph and groups are snapshotted once.

The existing locked daily transaction commits route changes, hires, taxes, scores
and date together. Abort or validation failure publishes no partial action. The
same-day/rollback guard prevents replay. Route actions introduced no schema migration or faction owner. Current save
version 13 supports the subsequent [Mercenary-base lifecycle](BASE.md).

## Validation and boundaries

Deterministic tests cover multi-hop travel, failed paths, protected transit,
relocation/merge activation suppression, strict hold/reinforcement/combat
thresholds, the 200/150 batch boundary, eager faction draws, nested mine rolls,
FIFO attribution, remaining mines after destruction, shared work exhaustion,
planet title/ground preservation, fractional stock, capacity conservation and
maintenance replay. The maintenance integration regression fails with the route
phase temporarily omitted and passes with it restored.

A store regression aborts after NPC mine loss, then runs eight concurrent daily
updates and reloads through a fresh store. Exactly one mine is spent, two remain
attributed, the destroyed group is absent, and no player death is created.
The real-process smoke exercises mine aftermath and planetary pickup through
-maint and reconnect, checks exact saved outcomes and idempotence, and observes
the resulting hostile defense in GoDoors. UTC rollover restarts whole disposable
fixtures with bounded retries. CI runs this smoke alongside hiring coverage.

Validation passed: the full Go race suite, go vet, focused regressions, the DOS
maintenance and bribery/hostility verifiers, all 4,682 archive hashes, new route
and hiring smokes, and existing bribery, mine and daily-score terminal smokes. Managed-worktree
Go commands use the same temporary module-file dependency override documented
in IMPLEMENTATION.md; committed module files stay unchanged. CI on this unpublished
branch and live BBS acceptance remain unverified.

[Mercenary-base lifecycle](BASE.md) is now implemented with explicit ownership
policy. Further faction-home combinations remain separate.
[Human-defense desertion](DESERTION.md) is implemented as a separate phase. Full NPC ship combat and exact QuickBASIC RNG/MBF parity remain
separate. These route actions preserve the recovered rule structure while
explicitly adapting protected sectors, work limits, quantity limits and scheduling.

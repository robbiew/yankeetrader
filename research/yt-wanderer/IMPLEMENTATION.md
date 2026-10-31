# Bounded Wanderer lifecycle and special transport

The [57-control recovery](RECOVERY.md) describes original DOS behavior. This
implementation uses the modern planet-generation, login/season and atomic store
contracts. It preserves the recovered route budget, independent planet/ship
positions and hidden destination while fixing unbounded placement, duplicate
references, repeated daily awards and unsafe partial restoration.

## Identity, capacity and migration

Save **25** adds `Planet.Wanderer`. Exactly one marked object may exist, in the
reserved planet slot 1; ordinary planets remain in slots 2–100. A marked planet
cannot also be a faction home. At most 100 total planets are representable.
Identity comes from the validated marker, never a name or a coincidentally reused
slot. Marked planets cannot be renamed. Capturing one uses the existing ordinary
landing/adoption/assault permissions. Captured Mercenary/Xannor homes retain their
separate movement restrictions.

Version 24 upgrades in memory without creating planets, changing resources or
inventing history. Pre-25 saves containing the future marker are rejected.
Read-only loading does not rewrite a save; the next successful update persists
25. The existing generation allocator remains monotonic: normal relocation keeps
the incarnation, while restoration allocates a fresh one. Exhaustion defers
restoration without overwriting anything. Earlier binaries cannot read save25.

The production `-init` path and Genesis explicitly bootstrap a missing Wanderer.
The bare `game.New` constructor remains useful for controlled economy fixtures;
calling same-day maintenance on it does not bypass the daily guard. Genesis
bootstraps both faction homes first, then the Wanderer, validates the entire new
season, and publishes it through the existing atomic reset. No repeated daily
awards or backdated ten-day economic gift is used for initialization.

## Finite lifecycle and phase order

Placement builds one sorted set of sectors whose planet link is empty. Relocation
virtually vacates its origin, so staying there is legal even in a saturated world.
Ports, Earth, Union sectors, mines, defenses and connectivity do not filter this
planet-only placement. One checked random draw selects a candidate. No vacancy,
reserved-slot conflict or exhausted identity allocator defers cleanly, with no
rejection loop or resource debit.

A clean restoration is neutral, named `The Wanderer`, with production 5000/5000/5000,
zero cargo/weapons/garrison, bank 250,000 and the current timestamp. Inactive native
buffer garbage and a ten-day backdate are deliberately discarded.

Production maintenance uses error-aware `RunMaintenance` inside one `Store.Update`.
Forward-only UTC daily guards precede all draws. Retirement and economic/event
updates precede an existing Wanderer's relocation; that relocation clears its
governor and refills its bank only if the post-economy balance is exactly zero.
All other legitimate assets survive normal economics and movement. Every landing
grant is revoked, including when it stays in its source sector. Other ships stay
where they were.

For a Wanderer missing at the start of the run, Mercenary and Xannor restoration
have first claim on scarce space. Clean Wanderer restoration then occurs before
mobile Xannor routes. Existing Wanderers move before the faction routes. This is
an explicit modern priority, distinct from reconstructing every DOS phase.
Later NPC assaults can destroy a relocated/restored Wanderer. It is not recreated
again during that daily run; the administrative receipt describes the final
outcome, including later destruction. A subsequent eligible day may restore a
fresh incarnation. A captured-Wanderer assault can retain an immutable private
planet battle report after its slot disappears.

## Confirmed transport

Both interfaces use the existing landed command (`!` in classic, `THRUST <sector>`
in compact). The prompt explains that the **whole quoted route** must be affordable
at 10 turns per hop, while successful Wanderer transport charges only the first
edge and stops. Fresh confirmation discards queued answers; cancellation does
not draw or spend. The single-use, two-minute sealed intent binds the planet's
marker/incarnation, login/ship/season, permission, budget, path and hazards, plus
the copied finite candidate set. Changed off-route planet occupancy also requires
a fresh quote.

The first planned edge undergoes the ordinary collision/stress check before any
random relocation. Destruction is a committed physical outcome: the failed edge
is uncharged, the stationary collision target survives unchanged, and bounded
fighter losses are reported. On success the planet moves to its independently
selected sector, while the commanding ship follows its planned first edge.
Grant revocation, links, resources, ten-turn fee and reached ship hazards save
together. Mines/hostile defenses apply at the ship's sector; hazards at a different
random planet location do not strike that ship. Existing mine death, escape and
estate handling remains atomic. Successful movement preserves planet generation.

Receipts report saved ship location, actual transport/aftermath turns, remaining
turns/fighters and destruction. Successful random transport says the Wanderer
vanished and its location is unknown. It never prints the private destination,
bank, account identity or token, and creates no public movement news. Maintenance
receipts also omit coordinates. Committed durability warnings and output failures
are joined rather than silently discarding the committed outcome or permitting
an automatic replay. Failed transactions emit no saved-success receipt.

## Validation and limits

Focused game/store/door/CLI regressions cover clean bootstrap and historical
migration, identity validation/exhaustion, finite saturated placement, asset/grant
conservation, once-per-date maintenance, final NPC destruction, private history,
whole-route affordability, split positions, distinct hazard roles, collision,
name-independent behavior, stale candidates/incarnations/daily movement,
concurrent maintenance/movers, late invalid draws, callback/validation rollback,
committed durability warnings, receipt failures and fresh terminal confirmation.
`smoke_wanderer.py` exercises real compact/classic GoDoors sessions, initialization,
budget refusal/cancellation, saved one-edge or stress/collision outcomes, hidden
receipts, reconnect and administrative daily replay. Existing Genesis smoke checks
all three bootstrapped planets. Compatibility fixtures deliberately remove the
new bootstrap only when reproducing an earlier save or isolated DOS scenario.

Exact DOS RNG/MBF parity, actual targeted disruption controls, long-running balance,
live BBS gameplay and native Windows crash durability remain separate acceptance.
See [validation results](../../evidence/VALIDATION.md) for executed checks.

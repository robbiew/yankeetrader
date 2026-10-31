# Planetary thrusters and player forced landing

Implemented on `feat/planet-thrusters-forced-landing`, following the
[55-control recovered contract](RECOVERY.md). This adds bounded modern actions;
original per-edge DOS writes, unbounded loops and MBF rounding are not reproduced.

## Commands and authority

- Classic landed `!` asks for the destination; compact `THRUST <sector>` uses the
  current landing token. Main-sector `!` still launches missiles.
- Denied classic `L` or compact `LAND` offers force entry when carried troops are
  available. Confirm the attempt, enter a strict positive whole commitment, then
  confirm the exact target/quantity separately. Blank, zero, negative, fractional,
  overflowing or excessive quantities cannot charge troops.
- An unowned/dead governor can be adopted separately without charging troops;
  the retained garrison is `floor(oldGround * draw * draw)`. Existing unguarded,
  self and team access continues to retain its governor.
- Two-minute intents bind a full persisted planet base and separately projected
  ground defenses, ship resources/incarnation/epoch, owner team/death, maintenance,
  landing token, copied route/warps/occupancy identities/mines/defense teams. Store
  seals all fields to one cryptographic login nonce; tampering, replay or changed
  state fails before draws. Commit compares persisted state at the original quote
  time, then separately rechecks material ground growth at the commit time. A
  changing projection timestamp alone does not reject every confirmation.
- Preparation does not save, charge, draw combat RNG or publish news. Post-lock
  wall deadlines and pre/post-action checks protect both prepare and commit.

## Bounded outcomes

Shortest directed BFS honors avoid preferences and stored warp-order ties. Check
`hops <= turns/10` before multiplication. The route is bounded by at most 3000
sectors. Each successful hop spends ten turns without ordinary movement's cloak
threshold behavior. Collision or per-edge stress draw `> .995` destroys only the
moving planet; the failed hop is uncharged. Positive fighter losses use two
successive `floor(draw * previous) + 1` draws bounded by current fighters; zero
fighters remain zero. Every previous successful hop remains in the saved receipt.

A reached minefield resolves using the existing attributed mine engine in this
same transaction, including escape, death/estate cleanup and login invalidation.
The planet stays in the reached sector even if mines warp or kill the ship.
Hostile sector fighters stop the route without inventing a paid battle. Every
movement/destruction revokes all landing grants; other ships do not teleport.
The mover returns to its sector interface. Faction identity protects both homes
from transport even after capture, keeping HQ/restoration coordination explicit.
At this milestone no Wanderer or unsupported disruption behavior was implemented.
The subsequent [Wanderer implementation](../yt-wanderer/IMPLEMENTATION.md) adds
its explicit lifecycle and split-destination transport in save25.

Ground rounds use separate selector/magnitude draws and recovered floor-after-
subtraction arithmetic. At most 4096 rounds execute. The selected commitment is
spent exactly once; on capture the surviving attackers become the planet's
new garrison. Defeat retains the governor and remaining defenders. At the work
limit, remaining committed attackers retreat without refund; receipts distinguish
these survivors from casualties. Ground actions spend no turns, ship fighters,
shields or credits and preserve the economy/bank/weapons after normal lazy growth.
Capture revokes other landing grants and grants the attacker fresh landing access.
Typed public news includes only display alias, planet, actual commitment, outcome
and garrison; it does not masquerade as Xannor activity or expose account identity.

All costs/outcomes/links/news/aftermath save once under the world lock. Invalid RNG,
validation errors, deadline expiry or pre-commit storage errors discard the entire
candidate, including any earlier route prefix. Physical collision is a successful
outcome rather than a software failure. Receipts include actual positions, hop and
turn totals, fighter/troop losses, retreats, garrison and remaining resources.
Committed directory-sync warnings retain that exact receipt and end the login;
receipt-output errors are joined with the warning rather than hiding it.

## Save version 24 and slot reuse

`NextPlanetGeneration` starts at 101. Version-1 through version-23 upgrades reserve identities 1–100
by old planet ID, with no reset or identity inference from names/owners. Migration
is in memory until the next successful save. Every ordinary/faction/super-planet
constructor consumes a fresh generation, including Genesis homes. IDs never wrap;
exhaustion refuses new ordinary construction and skips maintenance placement.
Validation rejects zero/duplicate/out-of-range generations and legacy files
smuggling new fields. A new season's epoch makes every prior intent invalid even
when its slot/generation values recur. Binaries limited to save version 23 cannot read version 24.

## Validation boundary

New game/store/door tests cover turn boundaries, collisions/stress and zero
fighters, multi-caller grant revocation, reached mines/hostile/friendly defenses,
strict commitments, capture/loss/adoption/finite exhaustion, seeded conservation,
lazy projection, changed resources/access/routes/hazards, exact replacement/epoch,
rollback, concurrent confirmation, nonce tampering/replay, lock/action expiry,
committed durability and joined output errors. Real terminal coverage exercises
both interfaces' movement, collision, cancellation, assault, adoption and reconnect.
Current command results are in [validation notes](../../evidence/VALIDATION.md).

Live BBS gameplay, native Windows crash durability, maximum-load balance, exact
DOS RNG/MBF behavior and targeted disruption controls remain unverified. The
subsequent bounded Wanderer controls and validation are documented separately.

## PR50 review correction: bind the initial assault preview

Consent and troop selection now stay bound to the originally displayed planet
identity/incarnation, name, sector, governor, projected integer garrison and
assault/adoption status. The fresh sealed intent projects its own snapshot at
its quote time before comparing the preview. A replacement in the same slot with
the same name, a rename, owner/garrison change or elapsed material growth requires
landing again before the final prompt. Carried troop changes likewise require
reconsidering the commitment. Sub-integer growth that does not change the displayed
garrison remains valid; existing commit-time checks cover changes after the final
prompt. The failed preview intent is cancelled without draws or troop spending.

The regression failed before the correction for both interfaces and both consent/
quantity pauses, spending troops despite changed state. It passes after the fix;
separate game checks cover integer growth and changing assault/adoption status.

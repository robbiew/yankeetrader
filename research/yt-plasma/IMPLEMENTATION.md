# Bounded plasma launching and atomic aftermath

Implemented 2026-10-31, separately from the immutable original-DOS
[research](RECOVERY.md) and its [candidate contract](CONTRACT.md). Available for
local testing in compact and classic interfaces. This is a bounded modern
implementation, not exact DOS random-number/MBF parity or live BBS acceptance.

## Player flow

Use `PLASMA <sector> <quantity>` in compact mode or `+;<sector>;<quantity>` in
classic mode. Either spelling also works in the other interface. Omitting both
arguments prompts for destination and quantity. Blank destination cancels;
quantities must be whole positive integers. Launches accept **1–64 available
bolts** and require at least one turn. They cost one ordinary turn and the chosen
inventory, including normal turn-based cloak accounting. The current sector,
Earth and empty sectors are meaningful targets. An unreachable accepted course
still spends the launch, preserving the recovered DOS financial behavior.

The warning explicitly covers friendly, cloaked and own ships/planets, uncertain
hole redirection and spent unreachable shots. It exposes no target roster,
hidden ship name, future random destination or hole pair. Queued commands and
terminal typeahead are discarded before an exact fresh Y confirmation. Cancel,
EOF, expired session, invalid input and changed consent spend nothing.

The quote is bound to the login, season, ship incarnation, warp sequence, origin,
requested target, quantity and an opaque digest of all saved world state plus
that login's disruption identity. All sectors must be sealed because redirection
can reach anywhere. No RNG is sampled while quoting. This is deliberately
conservative: even an intervening unrelated saved radio/rank update requires
reconsideration. Time-based planet projection is applied under the launch lock;
the warning never promises specific projected target statistics.

A random single-use nonce is retained only in the store session. Altered,
cancelled, superseded, cross-login and replayed quotes fail. A submitted valid
quote is consumed on rollback too; retry requires a new warning and consent.
Deadline checks occur after waiting for session/world locks, around the clock
and random draws, and before returning the transaction callback.

## Routing, energy and finite work

The directed breadth-first course uses stored exit order to break ties and
ignores travel avoids. Own-sector shots explicitly process that sector. The
combined launch pool is `bolts * 2,500,000`; each later ordinary course hop spends
the fixed `launch energy / 50`. It is not a separate full pool per bolt, target
or sector. An empty uninterrupted course reaches at most 50 sectors.

A login hole is checked before local defenses or ships. It chooses a new
requested destination uniformly from existing sector IDs and rebuilds a directed
course from the hole. It does not teleport damage or warp the shooter. The first
hop of that rebuilt course keeps the current energy without an extra travel
loss. A missing new route dissipates the accepted launch. Sparse valid maps use
the same sorted existing-sector convention as modern emergency warp; this is not
an attempt to generate invalid IDs from a DOS contiguous-table formula.

Limits apply to the **entire launch**, without resetting on a target or redirect:

| Limit | Bound |
|---|---:|
| Admitted bolts | 64 (160,000,000 initial energy) |
| Entered sectors, including holes | 128 |
| Hole redirects | 32 |
| Absorption rounds, including wreck mines and planets | 100,000 |
| All random draws, including salvage and local hazard aftermath | 200,000 |

Each course search is bounded by the validated maximum 3,000-sector graph. Ship
visits use sorted stable account IDs; retired/dead ships are skipped. The
existing mine/arrival kernels retain their own burst/warp limits inside the
shared draw ceiling. Constant-zero RNG cannot create unrestricted absorption or
redirection. Nonfinite/out-of-range draws, capacity overflow, stale identities,
future-dated reached planets, exhausted counters and work limits abort the
whole store transaction. No minimum fake random debit, partial save or invented
refund is used to force convergence.

Money and stock accounting retain exact integer limits. Energy, nonfinancial
production and fractional damage use bounded float64 calculations; DOS MBF
single/double conversions and seeded random sequences are not reproduced.

## Physical damage and cleanup

One pool encounters sector fighters, FIFO mine layers, ships in ascending ID
order (fighters before shields), then the linked planet. There are no friendly,
self, team or cloak immunity filters. Fighter/shield/mine round increments follow
`floor(E/5000)+1`, `floor(E/10000)+1`, `floor(E/1,000,000)+1`, capped to available
stock. Each round spends a validated random `r*25,000` energy debit, clamped at
zero. Energy left after an early target reaches the following target; it is
never reset to the original bolt count.

Only a reached planet with positive energy enters projection, damage and stock
capping. A planet behind an exhausted fighter/mine/ship interception is left
byte-for-byte untouched. Its lazy update runs before impact, including
warehouse-derived production. The post-update ore rate is cached for loop
eligibility; mutable organic/equipment rates supply their gate branches. Each
round subtracts `E*.000004` from ground and all three rates before spending its
energy debit. Ground is floored/clamped, rates are clamped to zero and stock is
capped to ten times its corresponding remaining rate. Empty ground clears the
governor and landing grants. All-zero production removes the planet and sector
link and revokes all grants, even if other numeric planet fields had remained.
The monotonic planet-generation allocator is preserved. No bank/planet inventory
salvage or governor-ship death is invented. Existing bounded faction/Wanderer
restoration mechanisms apply later; a launch does not restore a destroyed planet.

Plasma uses a new persisted death cause rather than bypassing enemy-only missile
checks. Ship generation invalidation, docking/landing revocation, team succession
and defense-estate handling happen in the same transaction as damage.

- The original launcher remains the attributed source after it dies; later victims
  do not become substitute projectile killers.
- A different living source receives sampled holds, credits, missiles, plasma,
  ground and cargo, even for a friendly casualty. Recipient capacities are checked
  before transfer. All other residual victim ship assets are discarded.
- Self death grants no loot or estate to itself. A dead source receives no later
  loot, ports or HQ award. Its estate becomes unowned under the existing neutral
  cleanup policy. Banks on surviving governed planets remain account assets.
- Self-inflicted plasma death uses the existing self-destruction next-UTC-day
  replacement rule. Friendly/enemy victims use ordinary fresh-login replacement.
  No replacement refills the remaining daily turn budget.
- Carried wreck mines are excluded from salvage: all are dropped once with their
  original carrier's attribution and immediately re-enter plasma absorption.
  Earth disarms them instead. If a surviving launcher is in a remaining wreck
  field, its normal mine/escape/disruption aftermath resolves **before saving**.
  A fatal mine aftermath retains the mine layer's actual owner, including a dead
  owner, and leaves any unspent layers as hazards. This is distinct from blaming
  that mine owner for the earlier projectile victims.

No new missile-retaliation branch is added. Existing armed ships do not fire a
missile merely because plasma hit them. Clearing a positive force at actual
Xannor HQ uses the existing prior-Xannor-owner guard, bounded actual-credit award,
ship-bound revenge and public HQ notice. Friendly or Mercenary defenders at HQ
grant no bounty. Capacity/headroom and a later failure are part of the same save;
the recovered DOS coordinate-only reward exploit is not reproduced.

## Receipts, atomicity and compatibility

The bound store transaction includes origin stock/turns, redirects, every defense,
ship and planet impact, loot, wreck fields, local arrival, death/estate/access
cleanup and qualifying HQ credit/revenge/news. Late failures leave the original
save intact, including failures after a kill or during local mine aftermath.
Concurrent confirmations cannot both spend the same quoted world. Season reset
and ID reuse cannot authenticate an old ship or quote.

Receipts are printed only after a successful visible save, including a committed
directory-sync warning. They show actual saved launch debit, remaining stock and
turns, anonymous impact totals, the launcher's losses, salvage credited before
later losses, wreck drops/disarming and its own local mine aftermath. Ordinary
plasma adds no new public target-name event. Hidden aliases, private banks, the
hole pair and projectile tracking/redirect coordinates are not printed. Existing
HQ victory news remains public; the actual credited amount is private. Surviving
launchers reconnect without firing or redeeming awards again.

A destroyed launcher ends its login after the saved receipt; the receipt does not
create a replacement. A post-rename `DurabilityError` is retained through EOF,
closed pipes and other receipt-write errors and ends the login. It does not
invite a retry of a committed launch. Local hazard escape/recharge can spend
additional turns beyond the launch's one turn; the saved receipt uses the final
action budget, and normal private arrival receipts describe the player's own
movement rather than the hidden projectile route.

**Save schema 26** adds explicit plasma death semantics. Version-1 through
version-25 supported worlds upgrade in memory; read-only loading does not rewrite
files, create projectiles, add inventory or refill turns. Pre-26 worlds containing
a purported plasma death are rejected. Earlier binaries cannot read schema26;
stop the door, back up its data and update all nodes together. Nonces, intents,
trajectories and login hole pairs are not persisted. This schema change does not
claim original DOS import compatibility.

## Validation and remaining work

Game tests cover recovered phases, direct/empty/self launches, FIFO/stored-exit
ordering, 50-entry range, shared energy, zero/invalid RNG bounds, whole-world/hole
consent changes, cloaked/team/self impacts, planetary projections and retirement,
landing revocation, all three death-recipient cases, mine-source conservation,
HQ ownership/headroom and 32 seeded conservation worlds. Store tests cover replay,
real season reset with reused IDs, concurrent quotes, byte-identical rollback
after deaths/loot/late hazards, locks/deadlines, capacities, old-save migration
and committed durability warnings. Both interfaces test separate consent, stale
hidden state, integer parsing, EOF, self-death termination and joined storage /
output errors. The real terminal smoke covers ten compact/classic scenarios and
nonfatal reconnects. See [the validation record](../../evidence/VALIDATION.md) for
completed checks and platform limits.

Mercenary plasma sales, extra spy/intelligence or newspaper event types, exact
DOS RNG/MBF parity, balance tuning, live BBS acceptance and native Windows crash
durability remain separate. The [research corpus](RECOVERY.md) is preserved as
historical evidence rather than rewritten to imply Go implementation parity.

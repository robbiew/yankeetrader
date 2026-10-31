# Plasma launch and disruption: candidate modern contract

Research-stage proposal only. This document changes no Go gameplay or save
format. The fresh [recovery report](RECOVERY.md) and [native analysis](NATIVE.md)
are the authority for this milestone's original-DOS observations. Policies below
are proposed safety requirements for a later implementation; they do not claim
that DOS bounded every loop, sealed confirmations, or saved atomically.

## Evidence already established before this milestone

The earlier [combat recovery](../yt-combat/RECOVERY.md) contains seven plasma
sessions within a twelve-session combat corpus. Its 91 checks include five model
checks; they are not 91 DOS sessions. It establishes a combined launch-energy
pool, `E0 = bolts * 2,500,000`, fixed travel debit `E0 / 50` per additional hop,
and absorption order sector fighters, sector mines, ships, then planet. Ship
fighters precede shields. One observed two-hop shot entered its first target
sector with 2,500,000 and its second with 2,450,000 energy.

For each fighter/shield absorption iteration the recovered increments are
`floor(E / 5000) + 1` and `floor(E / 10000) + 1`, respectively. Mines use
`floor(E * 0.000001) + 1`. Each iteration debits a separate `RND * 25000` from the
shared pool, with original single/double conversions described in that report.
Planet damage subtracts `E * 0.000004` from each production rate and ground
before its energy debit. That older corpus does not establish exact modern
RNG/MBF parity, all route choices, every death path, or every zero-rate planet
boundary; this milestone extends those bounds below.

The original [manual](../../archive/dos-original/YTINSTR.DOC) describes `+` as
plasma launch, limited range and weakening, and damage to anything in its path.
The [change log](../../archive/dos-original/CHANGES.TXT) also warns of self and
cloaked-ship hits. Those are authored descriptions, not newly executed controls.
The separate [HQ reward research](../yt-xannor-hq-reward/RECOVERY.md) supplies
ordinary-command controls that actually damage own, other-human and Mercenary
fighters at HQ, and intercept HQ 101 on a shot whose requested target is 102.
It also confirms a defect: DOS awards the HQ bonus for those non-Xannor forces.
A modern plasma path must not reproduce that missing-owner reward exploit.

## Recovered constraints for the implementation

The completed native analysis and fresh returned controls now extend that older
baseline. The report retains exact case identities, saved accounting and limits;
the following are recovered constraints, not open design alternatives:

- Plasma admission requires a positive turn balance and nonzero inventory.
  An accepted shot debits one ordinary turn and the chosen bolts before routing.
  One remaining turn is sufficient. Blank/zero/negative or oversized quantities
  do not launch; original quantity parsing floors a fractional value. A modern
  whole-number parser should deliberately reject that permissive behavior.
- Own-sector and empty-sector shots are meaningful launches. Own-sector shots
  reach the origin and can damage the shooter, including the tested cloak
  states. Other ship/team and cloaked-ship controls take damage too; missile
  friendly/detection filters are incompatible with those observations.
- The native course helper uses directed breadth-first search and stored exit
  order for ties, with plasma's flag bypassing avoided-sector exclusions. Energy
  enters the first course sector unchanged and loses the fixed `E0 / 50` before
  later hops. An unreachable requested destination still consumes the accepted
  DOS launch; preflight rejection without cost would be a modern policy change.
- A hole is tested before any local absorption. In the retained hole controls,
  sector 592 redirects toward requested destination 2368 while local defenses
  are bypassed. That draw requests a fresh directed course; it does not teleport
  the damage pool. The first hop of the new course has no extra fixed loss.
  Repeated or same-sector deflections have no recovered native counter.
- Ships are visited in player-record order, fighters before shields. A lethal
  impact can spill carried mines back into the earlier mine-absorption phase
  before later ships or planets. The accepted launch is a continuing projectile,
  not a separate independent full-energy attack for each target.
- Planet damage follows the ordinary lazy loader before impact. The raw
  all-zero-rate fixture controls are hit and logically destroyed with and without
  initial ore cargo, but their raw pre-session rates are not proof of zero
  production at impact: lazy loading can normalize/project those rates first.
  Those outcomes do not establish an unconditional first damage iteration or
  bypass of the native pre-iteration production gate. The post-lazy-update impact-entry ore production
  (raw45) is cached at `1a48`, distinct from ore cargo (raw57); positive cached
  ore can sustain iterations even after mutable production reaches zero.
  Mutable organics/equipment determine their own gate branches. Preserve the
  recovered gate placement and final rate/ground clamps and warehouse caps;
  do not infer ore-stock immunity from raw fixtures. The separate
  [missile production research](../yt-missiles/PRODUCTION_DESTRUCTION.md) explains
  the old mapping error but is not a substitute for these plasma controls.

The native planet path clears the governor when no ground survives and logically
removes all-zero-production planets, clearing name length and sector link. It
may continue toward later route sectors with leftover energy. Modern record
removal and generation/access cleanup remain stronger guarantees than DOS's
incremental writes. Shared-helper transitive death/estate behavior, maximal
numbers, original RNG/MBF equivalence and multinode timing retain the explicit
bounds in the report; source bytes alone do not prove those operational details.

## Current source seams and incompatible missile assumptions

| Source | Reusable mechanism and explicit limitation |
|---|---|
| [`game.Player` and validation](../../internal/game/game.go) | Plasma inventory already exists, as do planet production, transfer and salvage. Existing quantity bounds do not by themselves make energy multiplication or a billion-bolt calculation safe. |
| [`PrepareMissile`, `snapshotMissileRoute`, `CommitMissile`](../../internal/game/missiles.go) | Pattern for sealed route/target snapshots and one transaction. Missile admission rejects the shooter's sector; snapshots omit self, teammates and undetected cloaked ships; damage skips friendly defenses and planets. Those filters cannot become plasma filters by copying the missile path. |
| [`Disruption`, `BindDisruption`](../../internal/game/disruption.go) and [store context](../../internal/store/store.go) | Two login-local holes bound to actor, ship generation and season. View does not resample. Plasma may inspect this bound context for its own recovered redirect policy; it must not call player `ResolveArrival` merely because a projectile crosses a hole. |
| [`deathTarget`, `RecordDeath`, `ReplaceShip`](../../internal/game/lifecycle.go), [`SettleShipSalvage`](../../internal/game/salvage.go), [`applyDeathEstate`](../../internal/game/estate.go) | Generation-safe once-only cleanup exists. Enemy combat currently requires a different, living, non-team killer. The `self` cause delays replacement until the next UTC day. Plasma self, friendly or posthumous casualties therefore need an explicit attributed policy; relabeling them as `missile` or `self` silently changes rules or fails validation. |
| [`destroyPlanet`](../../internal/game/planet.go) | Removes the planet, clears the sector link and revokes every landing grant. Numeric planet IDs have generations; recreated planets must not satisfy an old launch confirmation. Modern deletion discards inaccessible residual bank/inventory rather than salvaging them. |
| [`awardXannorHQ`](../../internal/game/xannor_rewards.go) | Requires a positive prior Xannor force at actual HQ and a living current actor; bounded actual-credit receipt and revenge/news are atomic. Plasma must pass the actual pre-impact force, never reward based on coordinates alone. |
| [`launchMissiles`](../../internal/door/missiles.go) and [command dispatch](../../internal/door/door.go) | Both interfaces have an existing fresh-confirmation flow, but no `+` plasma action. A separate plasma receipt must handle own casualties and committed durability warnings rather than inheriting assumptions about enemy-only targets. |

These are source observations at the research branch's base. Historical missile
or disruption contracts describe their own research-stage source, not necessarily
the current implementation.

## Admission, intent and consent

A proposed plasma action accepts a whole positive bolt count within saved stock
and an existing requested sector, including the origin or an empty sector, with
at least one remaining turn. Reject negative, fractional, overflowing or
nonfinite input rather than carrying native numeric exploits forward. Preserve
the recovered one-turn/bolt debit and ordinary cloak accounting. Choose explicitly
whether an initially unreachable target is rejected before spending or accepted
and dissipated as in DOS; do not let a generic path error decide the financial
policy accidentally. No Earth purchase or Mercenary plasma shop is enabled by
this action.

Before mutation, resolve the live actor and session, outstanding encounter gates,
current origin, current plasma stock and turns. Use a separate plasma intent:
season, actor ID, ship generation, `WarpSequence`, origin, requested destination,
count, bound disruption identity, deterministic route inputs and relevant target
incarnations/state. Revalidate under the same lock used to save. A changed world
must require reconsideration without spending or revealing its hidden changes.
A stale original ship must never fire from its replacement's inventory.

The proposed UI names the count and requested sector, describes indiscriminate
friendly/cloaked/self damage and uncertain redirection, and requires a fresh
explicit confirmation after discarding queued typeahead. It does not expose
private holes or concealed target identities to make the warning more specific.
Cancellation, EOF, expired session, stale preview and rejected admission do not
spend bolts or turns. The deadline is rechecked after waiting for the world lock
and before commit; an earlier screen-time check is insufficient.

For random redirection, do not consume RNG during a read-only preview or publish
future random destinations. Capture the hole context and source world conditions
in a sealed internal snapshot, then calculate and apply once under lock. Hidden
state may invalidate a confirmation using a generic reason; it must not become
a target-enumeration interface. Use the recovered directed route and stored-exit
tie ordering, retaining the distinction between ordinary fixed hop loss and a
new deflected course. Any simpler route policy or avoid-list filtering must be
identified as a modern compatibility decision.

## Finite calculation and damage accounting

Preserve one combined energy pool across the launch. Each phase debits that same
pool; do not independently apply the full original bolt count to each target.
Clamp actual losses to available stock, and derive receipts from saved before and
after values. Lazy planet projection precedes its impact, but only a planet
actually reached by positive energy enters the damage/warehouse-cap phase.
Unreached planets must not be changed just because they were in a route snapshot.

Use deterministic sector/ship order recovered by this milestone where possible.
Map iteration, detection state, friendship and target list allocation must not
silently make the trajectory or shared-energy allocation nondeterministic.
Cloak can restrict information without granting physical immunity to an
indiscriminate projectile. Self/team targets require dedicated handling rather
than a visibility or friendly-fire bypass flag on ordinary missiles.

Every loop has a documented finite budget shared by the complete volley:
route/redirect steps, target visits, absorption iterations, retaliation (if
actually recovered and supported), salvage and reports. Energy checks alone are
insufficient: a valid zero RNG draw can leave energy unchanged. The fixed travel
debit also does not prove a graph search or redirect retry terminates. Bound
arithmetic before converting quantities to floating energy and check finite
results after each operation. Exact MBF32/64 conversion is outside this proposal.

On budget exhaustion, invalid randomness, capacity overflow, impossible links or
an invalid generation, abort the whole transaction. Do not save a partial launch,
refund a partially sampled result, silently shorten an unreported volley, or
invent a minimum random debit to force convergence. Select concrete budgets and
maximum admitted launch energy in the implementation with worst-case tests;
ordinary valid inputs should not routinely hit those limits.

## Atomic aftermath and information boundaries

The proposed store transaction includes launch stock/turn cost, all reached
sector defenses and mine layers, every ship and planet impact, terminal death,
source attribution, estate/access cleanup, qualifying HQ reward/revenge, bounded
reports and public events. A failure at a late target rolls back all earlier
impacts, not only the last target. Preserve attribution to the original source
across death-created mine hazards or other chained aftermath instead of replacing
it with the last casualty. Do not allow account IDs or ship slots reused after
replacement/reset to receive an older projectile's loot or blame.

Before implementation, choose and document the supported estate and recipient
outcomes when the shooter dies before later targets, a teammate dies, or a
posthumous source would otherwise receive salvage. Preserve the recovered
wreck-mine return to absorption before later targets, while validating modern
layer attribution and capacity. Existing enemy estate and salvage functions
cannot resolve source/recipient choices implicitly. Separate damage
eligibility, credit/blame and estate-recipient eligibility. A dead source cannot
be revived or credited through a stale ship reference. Likewise, attack-caused
planet destruction does not automatically kill its governor or pay its bank.

HQ reward must preserve the modern prior-Xannor-owner guard. A friendly or
Mercenary force located at HQ may take confirmed indiscriminate damage, but
clearing it earns neither Xannor bounty nor revenge. Qualifying rewards use the
actual bounded addition and remain atomic with later aftermath. Posthumous
eligibility follows an explicit supported policy rather than the original
defective coordinate-only caller.

Return an immutable structured result after the save decision. Show actual bolt
and turn debit, damage that the actor is entitled to know, own losses and final
ship/death status. A physical hit is not automatically a permanent cloak reveal:
prelaunch summaries, saved private histories and public news need separate
visibility rules. Never expose the login's full hole pair, seed, concealed route
redirect destination, hidden ship identity or private bank balance merely because
an internal impact object contains it. Record private victim information only in
that victim's authorized history if such history is added.

A committed `DurabilityError` is not a rollback. Receipts must preserve that
warning across output failures, EOF and disconnect; reconnect must not replay
the launch or pay again. A caller killed by its own volley ends that login after
its saved receipt. Receipt writes do not mutate combat a second time. Modern
schema changes, if needed for new death causes or bounded history, require an
explicit migration and old-save validation; existing inventory alone does not
prove that the save version can stay unchanged.

## Remaining implementation decisions and acceptance

The fresh research answers the launch, route, disruption precedence, shared
absorption and tested planet boundaries above. The implementation still needs
explicit modern choices, separate from any claim of further DOS recovery:

- Concrete global work budgets, numeric launch/energy bounds and error behavior.
- Whether initial route refusal preserves DOS's spent launch or is a preflight
  rejection; redraw/loop exhaustion always aborts a modern transaction intact.
- Dedicated self/friendly/posthumous death attribution, estate and salvage
  recipients, source-death continuation, and replacement timing. Existing cause
  validation must be updated deliberately if new persisted causes are required.
- Interaction with supported protected Earth/spawn and actual Xannor HQ policy.
  Preserve physical hit eligibility without reproducing the missing-owner bounty.
- Visibility of tracked redirects and hidden casualty identities after impact,
  with a clear distinction between what the actor observed and private hole/
  ship state. DOS tracking text alone does not mandate public or durable reveal.
- Report retention, any required migration, committed-error handling and native
  platform durability. No missile retaliation branch is added merely by reusing
  a missile helper; any new response needs its own supported scope.

The later Go milestone should include focused game, store and both-interface
regressions: constant-zero/near-one/invalid RNG; extreme numeric stock and tiny
positive energy; mixed shared-pool absorption; multi-hop and redirected loops;
self/friendly/cloaked impact without prelaunch disclosure; all planet categories
and stocks; exact changed-state confirmation cases; concurrent launch/replay;
source/target replacement and season reset; rollback after a later casualty or
reward; committed durability plus output errors; and real terminal receipts with
reconnect proving no repeated launch. Each finite-limit path must assert unchanged
saved state on abort. Run appropriate evidence checks and update README/playable
status, compatibility and validation claims in the same implementation commit.

Research completion does not make plasma firing playable. Original RNG/MBF
parity, live BBS acceptance and native Windows crash durability remain separate.

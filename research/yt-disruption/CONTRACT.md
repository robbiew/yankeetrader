# Disruption arrival: candidate modern implementation contract

Historical research-stage contract, now implemented in [IMPLEMENTATION.md](IMPLEMENTATION.md).
This document preserves the source-backed proposal for that implementation.
It changes no Go gameplay or save format. The native and completed DOS controls
below establish the recovered behavior; the later policies are explicit modern
safety requirements, not claims that DOS had atomic saves or bounded execution.
See [native analysis](NATIVE.md) and [recovery report](RECOVERY.md) for the retained
observations, control provenance and numerical limits.

## Recovered behavior and remaining boundary

The [native slice](NATIVE.md) identifies two eager, independent session-local
locations with the interpreted formula `INT(RND*(N-2))+2`. They may coincide;
there is no distinctness retry or mines/fighters/planet/reachability filter. For
the ordinary 3000-sector interval this models 2..2999. Raw sector byte 133 is
unmapped, so it is not an encounter flag. No purchasable device or persistent
map-hazard field is established by this slice.

The completed controlled DOS runs corroborate these arrival rules:

- Startup and returned-to-shell arrivals check black holes **before** ordinary
  mine resolution or fighter admission. A match automatically calls the shared
  emergency-warp helper, without manual consent or a positive-turn gate, then
  rechecks the saved destination. Two- and three-warp chains returned normally.
  A zero-turn startup still warped, with no recharge turns available to debit.
- The helper can select any declared sector 1..N, including its current sector or
  another session hole. Heat/recharge accounting is capped by remaining turns;
  the completed meltdown example consumed the entire balance. This describes
  retained outcomes and the native formula model, not exact MBF/RNG equivalence.
- Ordinary movement and autopilot spend their first movement turn before forced
  aftermath. Autopilot stops after the forced warp rather than continuing the
  queued path from an unexpected arrival.
- An ordinary planet route 1→2→3 can pass hole 2 without an intermediate encounter.
  A route finishing at 2, or stopped there by mines/fighters, returns to the shell
  and triggers forced warp. The planet remains 2 while a witnessed ship ends 1.
  Arrival is therefore an origin-command/helper-return boundary, not an automatic
  disruption check after every internal thruster edge.
- Wanderer controls preserve independently selected planet and ship positions.
  At the retained 02:00 clock, the planet ended 3 and the ship 1 after meltdown at
  zero remaining turns; at 03:00 the planet ended 1 and the ship 3. Ship-only forced
  warp does not carry the already relocated Wanderer with it.
- Mines/fighters placed in hole 2 survive the forced departure. Mines reached at
  a later non-hole landing damage the ship, and hostile fighters there reach the
  normal admission flow. The lethal landing control has one black-hole encounter,
  two warp-helper invocations (including automatic mine escape), and saved
  self-death marker 45=2; these must not be described as two black-hole events.
- A startup control with cloak 0.5 finished at 0.5 while turns 500→442. This and the
  native helper's sector/turn-only writes separate forced recharge from the
  ordinary movement cloak thresholds. Generic Go `spendTurn` calls must not add
  an unobserved direct forced-warp cloak debit by accident.
- The 8-sector sensor controls identify the two current-session holes at 3/4 and
  the corresponding arrival controls exercise them. Current-sector display and
  destination scanner warnings can disclose local disruption information. They
  are different from publishing a complete private location pair or the
  Wanderer's independently hidden destination.

A separate unsupported `N=1` diagnostic timed out after 40 seconds, with repeated
reentries at zero turns and no normal program-return marker. It is not a completed
core control or a valid minimum modern universe; it supports only the bounded
nonreturn observation and the native loop explanation. The expanded normal-width
control corpus is reported separately, without treating a narrow forced-branch
layout as a normal-world frequency or distribution measurement.

Exact BRUN30 random-state/MBF reproduction, all extreme numeric boundaries, and
unexecuted combinations of other commands remain unverified. A new login's own
hazards must not be inferred from an earlier login's sensor picture. New missile,
plasma or spy-intelligence behavior is outside this arrival slice. Those limits
do not leave the confirmed startup, returned-shell, precedence, chain or split-
planet/ship rules unresolved.

## Current Go seams: observed source, not new behavior

| Existing seam | Current behavior relevant to the next milestone |
|---|---|
| [`game.Move` / `move`](../../internal/game/game.go) | One adjacent hop spends one ordinary movement turn and clears docking/landing grants; it has no disruption state or arrival resolver. |
| [`game.CommitScannerEntry`](../../internal/game/travel.go) and [`CommitMineEntry`](../../internal/game/mines.go) | Revalidate warning/entry state, move, and resolve reached mines. Scanner danger currently means mines or hostile defenses, not a session black hole. |
| [`FollowCourse`](../../internal/game/navigation.go) and the [door autopilot driver](../../internal/door/door.go) | Revalidate each remaining hop; previous committed hops stay saved. An unexpected arrival must stop the queued remainder, even when coordinates happen to match a planned sector. |
| [`game.CommitWarp`](../../internal/game/travel.go) | Player-commanded warp uses a cached two-draw heat budget bounded to139 steps, at most31 heat, finite sorted destinations including current/avoided/dangerous sectors, a persisted sequence, and reached mine aftermath. |
| [`game.escapeMines`](../../internal/game/mines.go) | Automatic mine escape deliberately chooses a finite safe destination set. Its current heat-loop condition reads `r` while the body overwrites `r`; this differs from the cached manual-warp budget. This is a source discrepancy to audit when extracting shared machinery, not runtime evidence about disruption. |
| [`game.CommitPlanetAction`](../../internal/game/planet_mobility.go) | Collision/stress can destroy the moving planet on an uncharged failed edge. Successful transport saves links/ship/costs and resolves planned ship-edge mines. The Wanderer has independently chosen planet coordinates and stops after one paid edge. |
| [`Store.updateState`](../../internal/store/store.go) | Locks, reloads, validates the bound ship/season and encounter gates, stages spy state, and publishes one save. Callback/validation errors roll back; a `DurabilityError` means replacement already committed. |
| [`Store.ForShip`](../../internal/store/store.go), [login paths](../../internal/door/door.go) and [classic startup](../../internal/door/classic.go) | Each live login binds the captured player/ship generation and season after locked login, and owns ephemeral confirmation/spy/visibility state. There is no disruption-location state today. |

The current manual and mine-escape destination policies are deliberately different.
Native disruption calls the shared emergency-warp helper, but this is not permission
to copy either existing Go destination policy blindly or change the other as an
incidental refactor. A shared verified heat/recharge kernel must keep trigger,
admission, destination selection, cloak treatment and arrival policies explicit
and regression-tested.

## Candidate safety and storage rules

1. **Represent the recovered lifetime explicitly.** Hold the session-local
   locations in the bound login, not in a mutable sector flag or world-global map.
   Initialize once against valid authoritative sectors; repeated
   reads, menus and confirmation previews must not reroll them. Bind them to the
   captured season and ship incarnation. A new login/ship/season gets its own
   documented lifecycle. New persisted replay/accounting metadata, if needed,
   requires an explicit schema/migration contract; do not create hazards while
   read-only loading an old save.
2. **Resolve the origin action and its automatic aftermath together.** One locked
   store transaction must include the accepted movement or paid transport prefix,
   disruption, forced warp charges, reached mines, escape/death/estate effects,
   access revocation, attribution and any publication. A rejected draw, stale
   authority, exhausted metadata or storage failure must not publish an arbitrary
   subset. Previously completed autopilot hops remain separate committed actions.
   Preserve the recovered helper-return timing: an ordinary thruster route does
   not resolve disruption at every internal safe edge; mine/fighter stops end
   that route before the shell's hole-first aftermath is composed.
3. **Do not bypass encounter gates broadly.** Existing store APIs intentionally
   gate unresolved mines/defenses. Introduce only a narrow automatic-arrival path
   with the necessary authority; do not set generic `allowMines`/`allowDefense` to
   make ordinary commands work around an unresolved encounter. Any forced arrival
   surviving hostile fighters must return the caller to the existing encounter
   flow before banking, combat against a different target, or queued navigation.
   Automatic disruption itself must not inherit manual warp's positive-turn gate
   or require a new consent prompt after movement. A voluntary scanner warning
   may still be declined before entering, under its recovered warning behavior.
4. **Bound selection and chaining.** Select from a finite, sorted valid set; reject
   NaN/infinite/out-of-range random draws and invalid/exhausted inputs. Determine a
   finite total budget for disruption reentry, warp work and hazard aftermath.
   If original behavior can loop indefinitely, declare the modern exhaustion
   outcome before implementation and test conservation at that boundary. Do not
   turn a work-limit error into an accidentally committed free escape.
5. **Preserve independent objects.** Ship-only forced warp must not silently move
   the ordinary planet, Wanderer, other landed callers, or their cargo. Preserve
   a surviving planet's incarnation and valid source/destination links, while
   revoking every grant required by its actual movement/destruction. Any change
   to this separation needs specific observed evidence and a deliberate policy.
6. **Retain authority across pauses and retries.** Existing voluntary actions
   require fresh exact confirmation and sealed single-use intents. Include any
   new material arrival state in the originating intent or its bound session
   validation. Recheck captured identity/epoch, location, route, permissions,
   applicable hazards, resources and deadline after world-lock waits. Audit
   zero-cost/same-sector events: an unchanged `TravelShip` alone need not prove no
   warp occurred; manual `WarpIntent.Sequence` already addresses its own case.
   A new sequence, if needed, must have explicit migration/exhaustion semantics.
7. **Separate fees and effects.** Keep the initial movement/transport charge,
   forced recharge and later escape/death costs distinguishable. Clamp integer
   turns and money; never allow negative balances, backdated refunds or a second
   charge on reconnect. Preserve the [existing cloak threshold](../../internal/game/cloak.go)
   for the originating movement rather than treating planetary transport's direct
   debit as ordinary movement. Forced recharge has its own recovered accounting:
   the cloak 0.5 control stays0.5 despite spending 58 recharge turns. Do not
   automatically route forced recharge through `spendTurn` and thereby add
   ordinary-movement cloak decay; sharing/refactoring the existing warp helpers
   requires explicit regression coverage for this distinction.
8. **Preserve death and durability semantics.** Existing mine sources keep their
   attribution; disruption is not permission to invent an enemy killer or award
   remote loot. Any direct fatal disruption requires an explicit supported cause
   and estate/replacement policy. End an obsolete login immediately. A committed
   durability warning must retain the saved result, be joined with any receipt
   output error, and end the session; do not automatically replay it as an abort.
9. **Keep knowledge boundaries narrow.** Do not publish the hidden location pair,
   seed/draw state, account identity, grants or another player's assets in generic
   receipts, public news or errors. Allow the specifically recovered local sector
   labels and destination scanner warnings rather than hiding all detection.
   Say that disruption occurred and report the actor's actual known ship outcome.
   Preserve Wanderer's concealed random planet destination after ship-only warp.
   Spy access to session hazards remains a separately recovered feature, not an
   automatic extension of existing spy output.

## Required regression and acceptance matrix

- Deterministic location initialization: interval edges, duplicate locations,
  minimum/saturated candidate sets, no candidate, nil/NaN/infinite/boundary draws,
  exhaustion and exactly one initialization per declared lifetime.
- Entry-path matrix: startup/reconnect, adjacent movement, accepted/refused scanner
  or mine warning, each autopilot hop, ordinary/Wanderer thrusters, manual warp,
  mine escape, and collision/stress return. Assert where no encounter is expected
  as well as where it is expected. Include a two-hop ordinary planet route that
  passes an intermediate hole without checking it, plus a hazard stop at that
  same hole that does trigger the returned-shell check. Raw133 is a negative
  control only.
- Ordering: initial black hole with mines/defenses, forced landing with mines or
  defenders, reentry into the same/other hole, zero turns, same-sector landing,
  avoided/disconnected sectors and a bounded-chain exhaustion case. A zero-turn
  forced event must still resolve without inventing a positive-turn admission
  requirement. Classify automatic mine escape separately from a black-hole event.
- Conservation: transport and recharge turns separately, cloak boundaries,
  cargo/weapons/scanner/ship hull, unchanged stationary planets, one planet link,
  incarnation stability, no passenger teleportation and correctly revoked grants.
- Authority: changed route/hazards/ship/team/planet/incarnation, maintenance during
  prompts, concurrent movers/warps, reused numeric IDs after Genesis, season reset
  or replacement during lock waits, stale confirmations and same-position replay.
- Atomicity: late invalid draw after an origin move, late mine/death/report failure,
  callback/validation abort, concurrent processes, save/reload, committed directory
  sync warning and EOF/closed-pipe/other receipt failures. Assert whole-save and
  staged session-state boundaries, not only the final sector.
- Both real interfaces: fresh confirmations for voluntary actions, queued input
  discarded on involuntary interruption, no stale course continuation, one truthful
  final receipt and no repeat charge after reconnect. Public/private transcript
  checks must assert absence of hidden coordinates and unrelated account details.

Research completion is not gameplay acceptance. Later implementation must update
README playable/outstanding status, usage, save compatibility and validation in
the same commit/PR. PTYs, unit/race tests and cross-builds remain distinct from
live BBS gameplay and native Windows crash durability.

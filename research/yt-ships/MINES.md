# Non-Earth minefields, aftermath and chained attribution — 2026-10-27

## Research basis and boundaries

This implements existing [46-session hazard evidence](../yt-navigation/HAZARDS.md),
[encounter evidence](../yt-navigation/ENCOUNTERS.md), and the
[chained Earth death observation](LOOT.md#attacker-death-in-mine-aftermath).
No new original-DOS session is claimed. New static analysis of the immutable
YT.EXE (SHA-256 `c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`)
uses the existing runtime-aware listing and six independent REA/Ghidra byte reads.
`mines-rea.json` retains their Evidence IDs, exact ranges, provider and limitations.
`scripts/verify_mine_model.py` reconstructs the relocated load image and checks
those bytes independently before comparing eight injected-RNG model fixtures.
The REA session was closed; REA remains an optional research tool.

Relevant archived subroutine addresses are `1f42:6496..64e3` (burst size and stock),
`65fc..667f` (shield damage/collapse), `6718..6b30` (exposed inventory damage),
`6bfc..6c2e` (escape gate), and `4adb..4b61` (the nested random helper, called at
linear `0x23efb`). These are original DOS segment coordinates; REA reads use
linear coordinates at load segment 0x1000. Static evidence establishes instruction
bytes and interpreted rules, not runtime execution or exact seeded RNG replay.

## Burst rules

A source layer above 19 mines consumes `floor(stock/10)` per burst; otherwise it
consumes one. Thus a 20-mine field resolves as 19 bursts, matching prior DOS probes.
Within each burst:

1. Positive shields lose `floor(RND*1001)*burst`, clamped at zero. Even collapse
   does not also apply the unshielded inventory stage during that same burst.
   Scanner branches are dormant because scanner equipment is not implemented.
2. With no shields, fighters lose a capped nested draw from `40000*burst`.
   The helper performs **three successively shrinking** draws, each
   `floor(RND*previous)+1`; it does not sum three independent rolls. Its loop
   overwrites the passed upper-bound variable after each draw.
3. Cloak loses `floor(RND*burst*100)/100`, clamped at zero. Missiles, carried mines,
   ore, organics and equipment each lose a capped nested draw from `stock*burst`,
   skipping zero stocks in that order. Plasma, ground forces and credits are not
   damaged by this recovered burst path.
4. Recompute empty holds after cargo damage. Remove at most that empty capacity,
   using `nested(empty)*burst`. Cargo never exceeds remaining holds.

Integer quantities use exact binary-fraction scaling, not rounded MBF balances.
`mine_rules.py` is a readable independent model; the Go burst fixtures compare
thresholds, collapse, mixed cargo, fractional cloak and large inventories. They
are model comparisons, not additional DOS sessions or exact MBF equivalence.

Zero remaining holds is lethal. Modern ordering commits that death before any
escape roll, so a destroyed ship cannot warp away. Surviving 1–9-hold ships are
valid and can repair capacity through normal equipment purchases. A surviving
burst consumes the recovered strict escape gate `RND > 0.8` with holds below ten.

## Safe automatic escape

Emergency heat uses the recovered two initial draws and bounded heat rolls;
31 heat spends all remaining turns. Otherwise recharge is `4*heat+floor(4*RND)`,
capped to remaining turns. Turn spending applies ordinary cloak decay. Automatic
escape works at zero turns; it never refills turns or constructs a replacement.
The recovered overwritten destination-adjacent random draw is still consumed.

**Explicit modern policy:** select from sorted, existing sectors other than the
current sector with no minefield or hostile deployed fighters. Earth is always
safe. This avoids the original repeated-hazard/disruption loop. Safe destination
filtering and lethal-before-escape ordering are deliberate policies, not newly
proven DOS behavior. Disruptions, manual warp and persistent engine damage/repair
remain unimplemented; the meltdown modeled here covers escape and turn cost.

## Minefields and attribution

World version 7 saves optional ordered `MineLayer{Owner,Count}` records per sector.
Owner is a stable account ID, or zero for an unowned field. Dead sources remain
valid. Layers from one account merge without reordering; different sources resolve
FIFO. This provenance/FIFO representation is a modern extension: original sector
mine stock did not provide this complete ownership history. Each owner occurs
once per field, at most 51 sources; aggregate stock cannot exceed MaxQuantity.
A 16,000-burst calculation limit bounds resolution. Invalid stock, unknown owners,
Earth mines and malformed legacy mine data are rejected.

After a direct kill, sampled mine loot is consumed once. The unsalvaged remainder
is consumed into a non-Earth layer attributed to the defeated account, then the
attacker resolves that field in the same transaction. The previous non-Earth
mine-bearing-target gate is removed. Earth continues to disarm that remainder;
no field can be created there.

A mine-killed ship drops its own remaining carried mines once, after inventory
blast losses, and stops acting. Those mines retain the new victim's account ID.
Its death records `Cause=mines` and the actual lethal source ID, even if that source
has already died or is the victim itself. Mine death is distinct from voluntary
self-destruction and does not impose a false suicide cooldown. Replacement still
requires reconnect and preserves remaining turns.

Mine deaths retain the existing environmental estate policy: ordinary ports are
released and treasuries cleared, planets retained, team/shared access revoked,
and deployed fighters become Mercenaries. No remote inventory reward or dead-source
estate award is invented. Therefore an attacker can capture a defeated ship's
ports, die in its wreck mines, and release those newly captured ports in the same
atomic chain while retaining the correct source in both death records.

Mines are indiscriminate: ownership and team membership provide attribution,
not immunity. Existing occupants, including docked/landed callers, resolve hazards
before subsequent commands or on reconnect. No mine placement/withdrawal command
is exposed yet; combat wrecks are the production source in this milestone.

## Transactions, movement and sessions

Manual movement warns about actual mine stock and requires a separate exact Y.
Until scanner equipment exists, every mined entry is warned; this is an explicit
modern safeguard instead of DOS's silent entry without an installed scanner.
Preparation copies the source layers; commit rechecks that warning, actor generation,
origin, adjacency, current turns and fighter passage before movement. Changed
mine quantity/provenance requires a new confirmation. Blank/N, stacked approval,
Escape or disconnect consumes no movement turn. Normal entry and all aftermath
save together. Autopilot stops before a mined hop, retaining already completed hops.
Sensors report the actual aggregate mine stock.

The session resolves existing hazards before dispatch and after waiting for input.
Bound-store updates independently reject any ordinary callback starting in a
minefield. Only the dedicated generation-checked `ResolveMines` transaction may
start there, preventing a field arriving between prompt and commit from being
bypassed through movement, purchases or planet actions. Death is saved before
its invalidated session receives the destruction error. Local dock/planet tokens
are cleared when authoritative state changes during escape or another action.

Every callback must return errors. Random-source errors, overflow, stale warning,
late abort or save failure cannot partly commit entry, damage, depleted fields,
loot, either death, generation invalidation, drops or estate cleanup. Chained deaths
are successful outcomes saved atomically; they are not callback errors that would
accidentally resurrect both ships through rollback.

## Validation and compatibility

Tests cover 20-mine depletion, exact burst fixtures, safe zero-turn escape and
meltdown cost, FIFO/unowned/self/dead source attribution, no remote mine rewards,
protected Earth, live small ships, malformed fields, stale warnings and raw-move
rejection. Store tests cover late abort, invalid RNG after partial calculation,
concurrent killing claims, mine-drop overflow rollback, bound-action gates,
old generations, same-day replacement budgets and version-6 migration.

`scripts/smoke_mines.py` exercises real GoDoors PTYs: sensor stock, autopilot stop,
fresh declined/accepted entry and persisted shield damage, followed by a direct
attack whose killer then dies in the defeated target's mines. Both accounts can
replace the same day with 41/37 turns retained and no Earth field. Transcript:
`evidence/mines-smoke.txt`. Controlled one-hold fixtures make lethal aftermath
independent of random damage size; no production binary or RNG is patched.
Existing hazard evidence is verified separately. Native BBS acceptance and exact
DOS RNG/MBF replay are not claimed.

Supported versions 1–6 upgrade in memory and persist on the next successful update;
read-only views do not rewrite saves or replay historical deaths. Version-6 saves
must not already contain minefields, mine deaths or formerly invalid small live
ships. Back up the stopped world and upgrade every node together. Older binaries
cannot read version 7; rollback needs the matching backup and discards later play.

Next: missile/retaliation and sector fighter combat, explicit mine deployment/
withdrawal, scanner equipment and disruption/manual-warp behavior. Full economic
farming-chain playtests and native multi-node BBS durability acceptance remain open.

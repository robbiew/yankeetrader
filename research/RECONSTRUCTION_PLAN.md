# Yankee Trader reconstruction: working plan

Build a modern Go BBS door using godoors, grounded in the supplied original 3.6 binaries, documentation, and repeatable DOS experiments.

## Fidelity and intentional fixes

Preserve the game's commands, setting, strategic systems, and recognizable mechanics. **Fix defects and known exploits in the modern version.** Original behavior is a research reference, not a requirement to retain exploits or broken lifecycle rules.

Track reports, reproduction status, deliberate changes, and regression scenarios in [Issues and exploits](ISSUES_AND_EXPLOITS.md). Distinguish correctness fixes from balance changes requiring playtesting. Preserve archival binaries unchanged.

## Research completed

- Initializer and base data layout: [recovery](yt-init/RECOVERY.md), [DOS validation](dos-validation/RESULTS.md).
- Core maintenance economics and NPC lifecycle: [recovery](yt-maint/RECOVERY.md). Remaining random/combat details are listed there.
- Sector fighter surrender and plasma bolts: [recovery and DOS comparison](yt-combat/RECOVERY.md). Random combat rounds and plasma energy absorption recovered; exact RNG/MBF matching and remaining combat modes are pending.
- Missile damage and planetary ground assaults: [recovery and DOS comparison](yt-missiles/RECOVERY.md). Sector/ship damage distinctions, ground/production ordering, capture, and failed assaults validated in controlled encounters.
- Direct ship duels, cloak, missile retaliation, death and replacement: [recovery](yt-ships/RECOVERY.md). Paired DOS tests reproduce stale-position kills and actions after death; Earth mine hazards and retaliation death attribution are also confirmed. Resolve these lifecycle invariants before implementing combat storage.
- Trading, port prices, ownership, and the Earth spending loop: [recovery](yt-trade/RECOVERY.md). Eleven DOS sessions validate supply-sensitive prices, treasury allocation, purchase costs, and two cooperative equipment cycles.
- Genesis and season reset: [recovery](yt-genesis/RECOVERY.md). Eight DOS sessions validate the 300-port boundary, cancellation, configuration quirks, cached-count weakness, and complete resets; a separate maintenance run validates the required final initialization step.
- Planet creation, transfers, banking, garrisons, production investment, permissions, and relocation: [recovery](yt-planets/RECOVERY.md). Controlled DOS tests establish fractional upgrades, target-balance operations, shared access, cargo priorities, and a repeatable large-balance rounding exploit. In-game lazy production ordering differs from daily maintenance.
- Teams, captain roles/succession, membership, shared access, and asset retention: [recovery](yt-teams/RECOVERY.md). Twenty-one DOS sessions validate the four-member roster, permissions, rejoining after banishment, selective sharing, and post-departure ownership.
- Player calculator formulas: [assessment](ytcalc/FINDINGS.md). Treat unverified spreadsheet formulas as hypotheses.

## Next implementation stages

1. Navigation/encounter research baseline established. Sensors/path/autopilot are implemented; [scanner/cloak/manual warp](yt-navigation/ENCOUNTERS.md), [disruption/mine damage/automatic escape](yt-navigation/HAZARDS.md), [reports/faction encounters](yt-navigation/UTILITIES.md), and [route-commerce/spies/radio](yt-navigation/COMMERCE_RADIO.md) now have controlled DOS evidence. Each report retains explicit untested boundaries. Full NPC daily behavior, exact MBF/RNG equivalence and combat/death/session implementation remain separate. Port acquisition is implemented below; targeted follow-up research should accompany the relevant feature rather than imply complete DOS parity.
2. Completed: port acquisition, buyouts and personal treasury reporting/collection. [Nine targeted DOS sessions](yt-trade/OWNERSHIP.md) validate the buyout branch; Go tests cover atomic payouts, stale confirmations, overflow, replay and concurrent callers.
3. Implemented: [team membership/captain controls and shared planets](yt-teams/IMPLEMENTATION.md), with four-member capacity, visiting-member succession, hashed invitations and authoritative access revocation. Sector defenses/reinforcement and complete resource listings remain part of the combat stage.
4. [Death/replacement and session-generation safeguards](yt-ships/LIFECYCLE.md) are implemented as an internal foundation. [Fighter/shield calculations and one-time credit transfer](yt-ships/DUELS.md) are also implemented internally. [Salvage and estate research](yt-ships/LOOT.md) now has 37 controlled DOS sessions. [Inventory/estate settlement](yt-ships/SETTLEMENT.md) is implemented. Cloak persistence/session visibility and internal attack confirmation are implemented below. Confirmed fighter attacks and protected-Earth mine disposal are implemented below. Non-Earth minefields, automatic escape and chained attribution are implemented below. One-hop missile attacks/retaliation are implemented below. Sector fighter deployment/combat/interception is implemented below. Next integrate wider missile encounters; then NPC behavior, computer functions, communications and Genesis.
5. Continue DOS fixture comparisons, exploit-fix tests, concurrency/disconnect recovery and native target-BBS acceptance.
6. Playtest balance and document intentional departures before release.

The independent rules engine, transactional storage, GoDoors session interface,
join/move/trade/equipment/save loop, planets and coordinated daily economic
maintenance are implemented. Full maintenance, combat and release acceptance
remain separate work.

## Playable Go milestone — 2026-10-24

The standalone [modern Go door](../README.md) now implements persistent join/reconnect, adjacent movement, port docking, cargo trading, Earth equipment, automatic transactional saves and once-per-date port-economy/turn maintenance. Its macOS binary and a fresh 3,000-sector/1,000-port world are ready under `modern/`. GoDoors is used through the existing local checkout without changing that library.

Money is integer-based; Earth equipment cannot recycle owner revenue; maintenance is idempotent and rollback does not grant production; every mutation reloads state under an OS process lock and docking tokens invalidate stale quotes. Five recorded DOS ore-trading examples are executable Go fixtures. This first universe generator and fixed reference prices are provisional; planets, teams, combat, NPCs, acquisition, Genesis and complete maintenance parity are not yet ported.

Validation covers race-enabled unit/session/storage tests, concurrent processes, killed lock-holder recovery, real PTY/GoDoors operation, Door32 local transport, reconnect and stable identity across alias changes. Windows/Linux cross-builds are distinct from native BBS/socket acceptance. See [validation evidence](../evidence/VALIDATION.md).

## Navigation/scanning milestone — 2026-10-25

`S`, free directed `PATH`, and confirmed per-hop `AUTO` are implemented. Thirteen
original DOS sessions establish sensor contents, zero-turn scanning, directed
shortest paths/tie order, cancellation, insufficient turns and per-hop costs.
Compressed saves and transcripts have a provenance verifier and Go fixtures.
REA's first integrated investigation verified YT.EXE's loaded image and checked
sensor dispatch bytes against the runtime-aware listings.

Autopilot saves each hop, stops on Ctrl-X/disconnect/time expiration, and
revalidates authoritative position/turns between hops. The terminal commands keep
the existing `L` look binding. See [the bounded recovery report](yt-navigation/RECOVERY.md)
for evidence and unimplemented hazard/avoid-list boundaries.

The older playable-milestone section above is a historical snapshot: planet
management has since shipped, and the working game now lives at the repository
root, not under `modern/`.

The navigation follow-up adds the 30-slot `AVOID` editor, applies player preferences
to both `PATH` and `AUTO`, and revalidates the remaining course between hops.
Ten more DOS sessions establish editor/routing rules and show DOS resetting the
list on reconnect. Go deliberately persists it. Total navigation evidence is now
23 DOS sessions and 46 compressed save snapshots.

## DOS startup presentation — 2026-10-25

Live BBS follow-up, 2026-10-26: the user confirms that the Go door loads on the
live BBS. This establishes successful loading; gameplay, disconnect, transport
and durability acceptance remain separate checks.

The default frontend now follows the original title/opening, alias registration,
instructions choice, ship-information key pause, sector display and first menus.
Original captures supply cells/colors; dynamic fields use current game data.
`-compact` retains the previous interface. See [startup recovery](yt-startup/RECOVERY.md)
for exact comparisons, unsupported-system boundaries and save compatibility.

## Port ownership milestone — 2026-10-26

`B`/`ACQUIRE`, computer `12`/`TREASURY`, and `$`/`COLLECT` now operate on
persistent personal port ownership. DOS buyouts pay the old owner the purchase
price plus the old treasury. Earth protection, exact money, confirmation
revalidation and atomic capacity checks deliberately prevent ownership/money
exploits. [Recovery and validation](yt-trade/OWNERSHIP.md). Next: team membership and shared
assets (implemented in the following milestone).

## Teams and shared planets milestone — 2026-10-26

`T`/`TEAM` supports creation, joining, personal rosters, captain controls,
resource locations, departure/removal and visiting-member succession. Shared
planet access is revoked against current membership on every transaction.
Fourteen selected archived DOS scenarios provide membership fixtures. The save
format advances to version 3 with explicit upgrade and rollback documentation.
Sector fighter defenses, reinforcement and captain death remain in the combat
stage. [Implementation and validation](yt-teams/IMPLEMENTATION.md).

## Ship lifecycle foundation — 2026-10-26

Saved generations now bind all live session reads/mutations, including pending
prompts. Atomic death/replacement, authoritative target checks and explicit
attribution prevent old sessions acting on a replacement. Same-day replacement
preserves remaining turns; self-death keeps a next-UTC-day cooldown. Version-4
worlds upgrade from earlier supported formats. Separate-process tests and actual
PTY/GoDoors sessions verify the boundary. [Scope and deliberate policies](yt-ships/LIFECYCLE.md).
Attacks, loot and combat ownership transfers remain disabled/unimplemented.

## Ship-duel calculations and credit transfer — 2026-10-26

The internal fighter/shield calculation now matches nine injected-RNG cases from
the archived recovered model. A defeated ship's precomputed credit salvage is
consumed and transferred with death in one transaction, rejecting duplicate,
stale and overflowing claims. Later settlement failure rolls back all damage,
death and rewards. Full loot/estate formulas remain pending; attacks are still
disabled. [Scope, evidence and remaining work](yt-ships/DUELS.md).

## Loot and ownership-transfer research — 2026-10-27

Thirty-seven completed DOS sessions (74 snapshots) now establish salvage sampling,
hold expansion and cargo selection, ordinary-port capture/treasuries, active
planet retention, Mercenary defense conversion and team removal. A chained
attacker death confirms the self-attributed port-release branch. Cached-count,
MBF, hazard and unsuccessful-probe boundaries are explicit. Eight REA observations
are checked against independently relocated original bytes. [Findings and replay](yt-ships/LOOT.md).
Complete atomic inventory/estate settlement is implemented in the following milestone; player attacks remain disabled.

## Atomic loot and estate settlement — 2026-10-27

The recovered sampler now awards and consumes holds, cash, weapons and cargo in
one death transaction. Ordinary-port titles/treasuries, team/access revocation,
planet retention and Mercenary defense conversion share that transaction. Exact
integer sampling avoids MBF balance rounding. New optional defense state uses
world version 5; supported older saves upgrade without replaying past deaths.
Model/conservation/concurrency/rollback tests and separate-process PTY validation
cover this backend milestone. [Scope and deliberate limits](yt-ships/SETTLEMENT.md).
Next: attack eligibility/confirmation and aftermath integration before enabling combat.

## Attack confirmation and transaction foundation — 2026-10-27

Internal attack candidates, generation-bound preparation and commit now connect
zero-cloak duels with full inventory/estate settlement. Current location, life,
team and available force are rechecked before randomness; late settlement failure
rolls back the entire attack under the store lock. Tests cover surviving duels,
full kills, stale/replayed kills and concurrent confirmations. Player attacks
remain disabled. [Scope and validation](yt-ships/ATTACKS.md).
Cloak persistence and session visibility are implemented below. Next: frontend confirmation
and protected-spawn aftermath before enabling combat.

## Cloak persistence and session visibility — 2026-10-27

Version 6 stores finite cloak energy in [0,1]. New/replacement ships start full;
legacy ships preserve their formerly uncloaked behavior. Movement and docking
apply the recovered one-percent decay at remaining-turn multiples of 25. Sensors
use strict RND > cloak detection and generation-bound session reveals without
changing saved target energy. Classic and compact information screens show real
cloak energy. Internal attack confirmation/commit filter current visibility and
use the attacker's saved cloak advantage. [Scope and validation](yt-ships/CLOAK.md).
Frontend attack confirmation and protected-Earth aftermath are implemented below; anti-cloak
purchases, recharge and full combat acceptance remain separate.

## Player-facing fighter attacks and protected Earth — 2026-10-27

`ATTACK` (classic main `A`) lists visible local enemy ships, chooses committed
fighters and requires a fresh separate Y. Queued/stacked approvals and command
repeat cannot approve it. Confirmation commits through the generation-bound
store transaction, with actual saved damage and salvage reported afterward.
Earth disarms unsalvaged victim mines after one-time loot consumption, preserving
replacement/newcomer services and exits. Mine-bearing targets outside Earth are
rejected before randomness until minefield combat is ready; other supported
direct fighter encounters are enabled. Schema remains version 6.
[Scope, tests and real terminal evidence](yt-ships/PLAYER_ATTACKS.md).
Non-Earth minefields/aftermath and chained-death attribution are implemented below. Missile attacks/retaliation are implemented below. Sector-defense combat is implemented below. Next: wider missile encounters. Native BBS combat acceptance remains open.

## Non-Earth minefields, aftermath and chained deaths — 2026-10-27

Version 7 adds bounded, source-attributed mine layers. Non-Earth wrecks consume
unsalvaged carried mines into the field; the attacker's damage, any chained death,
subsequent drop, estate cleanup and original combat settlement save together.
Mine source attribution survives source death; no false suicide cooldown or remote
inventory reward is created. Earth disposal stays mandatory. Current-sector
hazards resolve before actions and reconnect, with bound-session mutation guards.
Sensors show actual mine stock, manual entry requires fresh confirmation and
unchanged warning contents, and autopilot stops before a mined hop. The recovered
burst calculations and safe automatic escape are implemented, with explicit
modern destination/death-ordering policies. [Scope and evidence](yt-ships/MINES.md).
One-hop missile/retaliation integration is implemented below. Sector fighter deployment/combat is implemented below. Mine
placement/withdrawal remains pending. Native BBS combat and long-running balance acceptance remain open.

## Missile attacks and retaliation — 2026-10-27

`MISSILE`/classic `!` now launches fresh-confirmed one-hop volleys at one visible
enemy or a minefield. Mines intercept one missile each; cumulative ship damage,
shield-exhaustion death, sampled loot, remote titles/treasuries, wreck drops and
Earth disposal share one transaction. A surviving enemy can return one volley at
the original attacker despite cloak, with its own ammunition and correct killer
identity; return fire does not recurse or spend defender turns. Version 8 saves
an integer score cache and missile death cause. Score generation remains pending;
zero/default caches use the recovered random-stock fallback without invented scores.
The prior per-shot mine-dropping interpretation is corrected to a scanner flag
check, confirmed by load/store bytes. [Scope and evidence](yt-missiles/IMPLEMENTATION.md).
Sector fighter deployment/interception/combat is implemented below. Next: wider/multi-ship missile
routes, planetary bombardment and mine placement. Scoreboard/complete maintenance
and native BBS combat acceptance remain open.

## Sector fighters — 2026-10-28

Personal final-balance deployment/recovery (`F`/`DEFEND`), friendly reinforcement
(`REINFORCE`, team option 6), confirmed `BREACH` combat, human surrender and
forced/specified emergency escape (`FLEE`) are implemented. Hostile groups guard
ordinary account mutations as well as movement; destination mines resolve after
victory atomically. Hostile fighters intercept missiles before mines and ships,
including return fire. Existing version-8 defense records are reused.
[Recovered rules, explicit policies and validation](yt-combat/SECTOR_FIGHTERS.md).
Next: wider/multiple-ship missile routes and planetary bombardment, followed by
mine placement/recovery. NPC behavior, communications, computer functions, Genesis,
score generation/complete maintenance and native BBS combat acceptance remain open.

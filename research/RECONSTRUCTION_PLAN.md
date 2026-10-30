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
4. [Death/replacement and session-generation safeguards](yt-ships/LIFECYCLE.md) are implemented as an internal foundation. [Fighter/shield calculations and one-time credit transfer](yt-ships/DUELS.md) are also implemented internally. [Salvage and estate research](yt-ships/LOOT.md) now has 37 controlled DOS sessions. [Inventory/estate settlement](yt-ships/SETTLEMENT.md) is implemented. Cloak persistence/session visibility and internal attack confirmation are implemented below. Confirmed fighter attacks and protected-Earth mine disposal are implemented below. Non-Earth minefields, automatic escape and chained attribution are implemented below. One-hop missile attacks/retaliation and sector fighter deployment/combat/interception are implemented below. Routed missile encounters are implemented below. [Mine placement research](yt-ships/MINE_PLACEMENT.md) is complete; voluntary placement is implemented below, while field recovery remains an unverified and unimplemented extension. NPC behavior, computer functions, communications and Genesis remain open.
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
Non-Earth minefields/aftermath and chained-death attribution are implemented below. Missile attacks/retaliation, sector-defense combat and routed missile encounters are implemented below. Voluntary mine placement/recovery and native BBS combat acceptance remain open.

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

## Planetary ground and production bombardment

`MISSILE` launches now reach hostile planetary ground and production after
sector fighters/mines on routed courses. Own/team planets are skipped in transit
and protected as selected targets. The full
planet record is bound to confirmation, and lazy growth, damage, warehouse caps
and deletion save atomically. All-zero production removes the sector link and
revokes every landing token for the planet; ownership, bank and ships are not
salvaged. Mixed visible ship/planet targets are supported in routed encounter
order. Recovered cached-ore eligibility is preserved.
[Scope and arithmetic](yt-missiles/PRODUCTION_DESTRUCTION.md). Mine
placement/recovery and native BBS combat acceptance remain open alongside the
later systems listed above.

## Production damage and destruction research

Controlled DOS cases confirm zero-clamping of production categories, cargo caps
at ten times resulting rates, and logical planet deletion when all rates reach
zero. The ore-only omission hypothesis is disproved: the shared value is cached
ore production. Static recovery identifies a remaining cached/live-rate loop
asymmetry. [Evidence, model and implementation decisions](yt-missiles/PRODUCTION_DESTRUCTION.md).
Implemented in the planetary ground and production bombardment milestone, using
world version 9 to admit zero production categories and bind destruction plus
landing-token revocation to the launch transaction. Cached-ore asymmetry is
preserved for compatibility.

## Wider missile routes and mixed encounters — research

Controlled DOS runs confirmed two- and three-hop attacks, directional outbound
routing, return fire, intermediate fighter/mine interception, intermediate
planet targeting, and sequential ship/planet targets at a shared destination.
See [route evidence and implementation guidance](yt-missiles/WIDER_ROUTES.md).
Disconnected-route rejection and shortest-route selection are implemented as
modern policies. The original game's tie behavior and black-hole handling remain
unverified, as does native BBS acceptance.

## Wider missile routes and mixed encounters — implementation

Missile launches follow a shortest directed warp route. Stored warp order
breaks equal-length ties as a modern policy; the confirmation displays the
selected course. Each sector resolves hostile fighters, mines, visible enemy
ships in player-ID order, then hostile planets. A destroyed ship or planet lets
the shared remaining volley continue. Cloaked ships and teammates remain
excluded; friendly defenses and planets are passed over. Return fire uses a
preflighted route back to the original attacker and resolves route hazards and
hostile planets. A one-way outgoing route without a return path does not
retaliate. Preparation snapshots both routes and encounters, and commit
revalidates them before spending missiles or a turn. No save-version change was
needed. [Rules, DOS evidence, and implementation policy](yt-missiles/WIDER_ROUTES.md).
Native BBS acceptance, DOS tie behavior, black-hole redirection and the later
NPC/computer/communications/Genesis systems remain open.

## Voluntary mine placement — research

Eight controlled DOS sessions and four additional home-sector boundary sessions
exercise the `D` placement command with saved before/after data. DOS requires
carried stock, defaults the amount to zero, spends no turn, refuses amounts
outside available stock, and refuses deployment in sectors 1–7. Sector 8 is the first tested
allowed location. The existing-field probe detonates all initial mines before
the drop, so addition versus replacement of a still-nonempty field remains
unverified. The manual documents dropping mines but no field pickup or
withdrawal action; such a recovery feature is not established as original DOS
behavior. [Rules, probes, snapshots and validation](yt-ships/MINE_PLACEMENT.md).

## Voluntary mine placement — implementation

`D`/`DROP [quantity]` places carried mines in the caller's current sector.
Sectors 1–7 are protected, placement is free in turns, and a fresh exact `Y`
is required after the command queue and terminal typeahead are discarded. The
world snapshots the player's generation, mine stock and current field before
confirmation, then revalidates and saves the stock transfer with the attributed
mine layer in one update. Same-owner drops add to that source's existing layer,
as an explicit modern policy; DOS behavior for placement onto a still-nonempty
field remains unverified. Save version 10 persists departure grace for ships already
present when mines are deployed, preventing an immediate self-detonation after
placement or reconnect. Leaving, dying, or receiving new wreck mines clears that
grace; subsequent entry triggers the field normally. Field recovery remains
unimplemented because no original DOS pickup behavior has been established.

## Own sector fighter finder — implementation

Computer option `11` lists only the caller's deployed sector fighter groups,
ordered by sector, or reports that none were found. It is a read-only query and
does not expose other players' groups. This follows the DOS fixture showing two
owned groups while omitting a nearby enemy group; broader report functions
remain separate work.

## Remote computer reports — implementation

Computer `2`, `9`, and `13` now provide ordinary-port commerce reports, remote
planet reports, and a personal planet finder. Target-sector defenses block
disclosure; the blocked planet query atomically spends one turn. Private
defended planets expose only name/ground forces. Current personal/team access
controls full planet detail. Reports project growth on detached values and do
not change stored assets or issue docking/landing tokens. Remote Earth service
reports, commerce-route forecasts, rankings and the other computer functions
remain open. [Scope, recovered rules and validation](yt-navigation/REPORTS_IMPLEMENTATION.md).

## Nearest-port and trade-route reports — implementation

Computer `14`, `16`, and `17` now provide filtered nearest ordinary ports,
reachable adjacent-port pairs, and current-port adjacent trade forecasts.
Compact commands are `NEAREST`, `PAIRS`, and `PROFITS`. Directed warp counts
include the actual return path, and all routes honor the caller's avoid list.
Reports use current Go prices and report access; forecasts are per-unit price
spreads rather than ship earnings. Four-entry pages refresh after input.
No save-format change is needed. Rankings, communications, spies, newspaper,
NPC behavior and Genesis remain separate milestones.
[Recovered evidence, policies and validation](yt-navigation/TRADE_REPORTS_IMPLEMENTATION.md).


## Direct radio and message history — implementation

Computer `5` sends one confirmed direct radio line; computer `6` displays the
caller's sent and received history. Compact commands are `RADIO`, `MESSAGES`,
and `INBOX`. Save version 11 retains account-level messages and per-recipient
unread state. Delivery acknowledges only successful output; retrying one draft
cannot duplicate it. This implements the recovered one-line send/abort and
retained-history slice. Broadcast/team routing and the DOS multiline editor
remain unimplemented, alongside rankings, spies, newspaper, NPCs and Genesis.
[Evidence boundaries, storage policies and validation](yt-navigation/RADIO_IMPLEMENTATION.md).

## Player/team rankings and score generation — research

27 controlled DOS sessions establish scoreboard entry/OLD/updated behavior,
asset weights, persisted score updates, deployed fighter attribution, summed
team scores, zero/dead-player rows and stable player ties. The port-count pair
confirms that DOS trusts a stale cached count instead of current titles; the
Go implementation should recount authoritative ownership. Existing missile
retaliation consumes the stored score, so cache-publication timing must be
specified before wiring rankings. Go gameplay remains unchanged in this slice.
Next: implement supported player/team rankings and coherent score-cache updates,
with checked arithmetic, explicit zero-score rules and current ownership/team
membership. Multiteam percentage semantics and nonzero NPC rankings remain
unverified. [Findings, evidence and reproduction](yt-rankings/RECOVERY.md).


## Player/team rankings — implementation

Computer `4`, `RANK`, and `RANK OLD` now expose real supported asset totals,
current team sums, authoritative port ownership and personal sector defenses.
An explicit update publishes all score caches atomically; OLD uses stored
scores with current public labels and counts. Zero/dead rows, stable ties,
exact bounded percentages and score saturation are defined. Missile retaliation
uses the published cache; automatic quit/daily cache refresh, historical
scoreboard files, scanners and NPC rankings remain separate work. No save
version change is needed beyond the radio prerequisite's version 11.
[Rules and validation](yt-rankings/IMPLEMENTATION.md).


## Automatic score publication — implementation

Successful daily maintenance and clean logout now publish all account score
caches atomically using the same supported scoring rules as RANK. Maintenance
works without a living caller and retains its once-per-UTC-day/rollback guard.
Logout checks the bound generation and deadline inside the lock, can only
change score metadata during encounters, and reports success after the save.
Declined confirmation, disconnect and stale/expired sessions do not publish
logout scores. Score publication consumes no ship resources and does not resolve
hazards. No new save fields or version change are needed. Historical scoreboard
files, unsupported scanner/NPC scores and full NPC maintenance remain separate.
[Timing, safeguards and validation](yt-rankings/IMPLEMENTATION.md).


## Spies and intelligence reports — research

Original DOS hiring/reconnect evidence is extended with focused static search,
report and movement recovery and controlled two-sector runtime probes. No Go
gameplay or save format changes are included. Next: implement session-bound
hiring, active-spy display and supported intelligence reporting, with explicit
delivery, privacy and zero-warp policies. RNG parity and broader spy/NPC
interactions remain bounded research. [Evidence and reproduction](yt-spies/RECOVERY.md).


## Spies and intelligence reports — implementation

Earth option 9 and compact HIRE now atomically purchase up to three spies for
333,000 credits apiece. Computer 15 / SPIES displays current hunt locations.
Successful moves/autopilot hops, docking and fighter transfers search and move
spies, emitting the runtime-confirmed mine, planet-ground and defender findings.
INTEL holds 30 session-only reports, with output acknowledgement and paging.
Reconnect starts without spies or intelligence history, matching the DOS slice;
the purchase remains spent. Empty-warp sectors safely hold position. World
version 11 is unchanged. Ship/cloak and disruption reports, exact RNG parity,
and other DOS trigger branches remain outstanding.
[Scope, adaptations and validation](yt-spies/IMPLEMENTATION.md).


## Galactic newspaper and news history — research

Thirteen original DOS processes establish computer 8's Today/Yesterday choice,
invalid/lowercase input, empty/missing files, EOF handling, real login and
team-creation events, exact reconnect persistence and maintenance rotation.
The same-day maintenance fallthrough also rotates history despite reporting
maintenance unnecessary; preserve the modern once-per-UTC-day guard instead.
No Go newspaper gameplay or save-format changes are included. Next: implement a
bounded public dated journal and computer 8 / NEWS reading, with atomic event
publication, private-field filtering, explicit UTC retention and safe pagination.
Other event producers and exact long-file/color behavior remain bounded research.
[Evidence, reproduction and implementation contract](yt-newspaper/RECOVERY.md).


## Galactic newspaper and news history — implementation

Computer 8 and NEWS [TODAY|YESTERDAY] now read a bounded public journal in five-entry
pages. Successful authenticated logins and player-facing team creation publish
whitelisted public snapshots atomically with their actions. UTC today/yesterday
retention, a combined 1,024-event cap, stable read snapshots and stale/deadline
checks are explicit. Forward maintenance prunes old history; same-day/rollback
maintenance leaves it alone. Save version 12 upgrades versions 1–11 without
backfilling events. Other event producers, exact DOS colors/long-file interruption,
NPC behavior and Genesis remain separate milestones.
[Implementation rules and validation](yt-newspaper/IMPLEMENTATION.md).


## Mercenary offers and faction refusals — research

Nineteen controlled DOS sessions and 38 saved snapshots establish offer parsing,
blank cancellation versus insulting zero, accepted exact debit/recruitment,
over-budget combat, guarded-planet refusal, weak/zero-force recruitment and
human/Xannor differences. Two REA byte observations correct an inline-runtime
disassembly boundary. Exact negotiation probabilities and an additional hostility
flag remain explicit research limits; no Go bribery gameplay is enabled. Next:
resolve those branches or define a deliberate modern policy, then implement
confirmed transactional bribery using the existing defense/aftermath safeguards.
[Evidence, boundaries and implementation contract](yt-mercenaries/RECOVERY.md).


## Mercenary hostility and negotiation rules — follow-up research

Twenty-four additional original DOS sessions establish same-login anger after
Mercenary casualties, carryover between groups, exact reconnect reset and
planet-reference refusal regardless of planet owner. Three new REA byte reads
and original BRUN30 handlers resolve the eager random draw order, 5%/weak-ship
hostility checks, human retaliation and the strict offer threshold. Portable
verifiers retain all 43 bribe sessions and 86 snapshots; input-consuming sensor
probes are excluded. Exact MBF/RNG reproduction remains outside the modern
integer-money contract. [Resolved rules and evidence](yt-mercenaries/HOSTILITY.md).


## Mercenary bribery — implementation

BRIBE [credits] negotiates in the current sector; BRIBE <sector> <credits> permits
confirmed adjacent entry. Classic encounter B preserves normal B port acquisition
elsewhere. Recovered hostility/refusal rules lead to exact debit and whole-group
recruitment or full-force defense combat. Login-local hostility, one-use quote
tokens, stale/deadline checks, capacity, entry turns and atomic mine aftermath
prevent replay and partial transactions. No save-version change is required.
Daily hiring, NPC route actions and human-defense desertion are implemented
below. Mercenary-base restoration is implemented below; full NPC ship combat remains
a separate milestone.
[Policies and validation](yt-mercenaries/IMPLEMENTATION.md).

## Mercenary daily maintenance — hiring, routes, desertion and base restoration

Recovered tax-funded hiring with both rounding stages, Earth exclusion, no saved
budget carry, group placement and human-defense desertion. Forty-one completed
DOS runs and one bounded timeout cover route walks, merges, mines, defense
combat, planetary fighter pickup without title/ground transfer, and reserved-base
restoration. Static byte checks protect the distinct NPC battle threshold and
nested mine rolls. [Evidence and boundaries](yt-mercenary-maintenance/RECOVERY.md).

Daily maintenance now hires from summed per-port integer taxes with the recovered
rounding rules and finite distinct placement. Protected Union sectors and existing
defenses are excluded. Missing space and the modern force limit discard unused
funding without carry/refund. Tax debits, hires and date persist atomically, once
per UTC day; these phases introduced no schema changes. Base restoration
introduced version 13; current version 14 also supports Xannor HQ/home state.
Game/store regressions and a real
maintenance/reconnect smoke cover saturation, replay and persistence.
[Implementation policies](yt-mercenary-maintenance/IMPLEMENTATION.md).

Existing Mercenary groups now receive one stable daily activation before new
hiring, following a whole directed route outside protected sectors. Mines precede
defenses and planetary pickup. Merging consumes the receiver's pending action;
partial-capacity transfers conserve force. Combat uses the recovered NPC batch
rules with a per-group work allowance. Pickup preserves titles, ground and
fractional/excess stocks. Invalid paths hold in place. No DOS capacity hang,
failed-path teleportation or repeated activation is reproduced. Human-defense
desertion now runs first, converting only eligible human-owned groups outside
the protected Union when RND*100 strictly exceeds their force. Converted groups
join the stable route snapshot that day; publication reflects current ownership.
[Desertion validation](yt-mercenary-maintenance/DESERTION.md). Mercenary-base
restoration now uses explicit identity, validated references and
finite free-slot/sector selection. Captured or neutralized titles are preserved;
only empty reserves on Mercenary-owned homes replenish. Missing homes rebuild
without commandeering legacy slot/name matches. Version-12 saves upgrade without
inferring home identity or creating assets during read-only loading.
[Base lifecycle and migration](yt-mercenary-maintenance/BASE.md).
[Route policies and validation](yt-mercenary-maintenance/ROUTES.md). Exact RNG/MBF
parity and additional faction lifecycle combinations remain research boundaries;
live BBS acceptance is separate.

## Xannor HQ and Xannoron lifecycle — implemented

Thirty-eight completed original-DOS runs, three bounded relocation stalls, two
exact next-day world chains and eleven new REA byte observations establish
recreation predicates, retained/reset stocks, ground/bank restoration, forced
retitling, group normalization/regeneration, reclaim thresholds and relocation
rules. Candidate controls distinguish one/two foreign fighters and expose an
unbounded search. A zero-HQ control ties phantom strength to a stale RNG helper
result. [Evidence, boundaries and proposed implementation](yt-xannor-lifecycle/RECOVERY.md).

Implemented explicit Xannor-home identity, bounded restoration, HQ/reserve state,
living stored-score regeneration, bounded reclaim and finite relocation, with
captured-home ownership preserved. World version 14 migrates without inferring
legacy homes or HQs. Sector defenses remain the unique deployed groups; reserve
preserves unfinished battles. Game/store tests and real compact/classic terminal
coverage validate accounting, capacity, capture, destruction, replay and rollback.
[Implementation policies](yt-xannor-lifecycle/IMPLEMENTATION.md).

Mobile splitting/targeting and route-action research is now complete below.
Full NPC ship combat, revenge/cloak searching and exact DOS RNG/MBF parity remain
separate milestones.

## Mobile Xannor groups — bounded implementation

Forty-seven completed DOS controls, an exact next-day world chain and 22 REA byte
observations establish nontruncated HQ split thresholds, four shrinking draws,
normal/top/HQ target ordering, conditional shared pursuit, directed shortest
paths and per-hop action dispatch. The controls distinguish Xannor uniform mine
damage and 5000/500/1 sector-defense batches from Mercenary behavior. A ship loss
can retain its sector as the next groups' preferred target; special top-player
hunting is a separate 2.5-million-score gate. Union routes and planetary attacks
are possible in DOS, while Union mines disappear in an earlier phase.
[Evidence, boundaries and next implementation](yt-xannor-mobile/RECOVERY.md).

Implemented bounded group splitting/selection, movement, uniform mine damage
and 5000/500/1 sector battles on the explicit HQ model. A stable 19-group daily
snapshot and original-HQ split budget prevent duplicate activations and reuse of
returning force. Shared pursuit is explicit; merges and reserve capacity conserve
force. Union routes are excluded. Live ships and foreign planets cause a safe
hold before unsupported encounter mutations. World version remains 14.
[Implementation policies and validation](yt-xannor-mobile/IMPLEMENTATION.md).

Xannor ship battle research is complete in the following milestone. Planetary
assault/destruction and remaining revenge/cloak search behavior follow it. Exact MBF/RNG parity
and live BBS acceptance remain separate validation boundaries.


## Xannor NPC ship battles — research complete

Forty-two completed original-DOS maintenance controls, an exact next-day world
chain, changed private/public side files and eleven REA byte observations recover
normal interception, 5000/500/1 fighter and shield rounds, record-order multiple
victims, route continuation and maintenance-specific death/estate cleanup.
Valid full-cloak samples distinguish evasion from interception; missile stocks
are unchanged. Diagnostic controls expose dead-record targeting, exhausted
shields retaining old values, and a stale team captain after removal. These
defects must not become modern gameplay rules.

No Go combat or schema changes are included. Next implement bounded Xannor ship
encounters with living-player/session revalidation, explicit NPC attribution,
atomic aftermath and private event delivery. Define estate policies explicitly
before reusing direct-player salvage/wreck rules. Planetary assaults/destruction,
remaining revenge/cloak searches, exact RNG/MBF parity and live BBS acceptance
remain separate. [Evidence and implementation contract](yt-xannor-ships/RECOVERY.md).


## Bounded Xannor ship battles — implemented

Mobile routes now use current living-player eligibility, separate cloak detection
and recovered 5000/500/1 fighter-before-shield combat under the shared finite
work budget. Multiple victims, survival/continuation, partial-work holding and
final capacity-limited merges preserve force. Atomic NPC death invalidates stale
sessions, releases ports, converts personal defenses, removes team access and
retains planets, with no salvage or wreck mines. Actual zero shields replace the
DOS stale-shield defect.

Save version 15 adds bounded private battle history, recipient-only delivery and
BATTLES in both interfaces; public death news excludes casualty counts. Legacy
worlds migrate without invented events. Game/store/door regressions and real
PTY validation cover replay, concurrent maintenance/login, rollback, committed
durability failure, replacement, privacy and output failure.
[Implementation and deliberate policies](yt-xannor-ships/IMPLEMENTATION.md).
Next: Xannor planetary assault/destruction research, then the remaining
revenge/cloak candidate-search behavior. Exact RNG/MBF parity and live BBS/native
Windows acceptance remain separate.


## Xannor planetary assault and destruction — research complete

Seventy-one completed DOS maintenance controls, paired non-arrival/economic
worlds, an exact next-day chain and twenty game/runtime REA observations recover
planetary eligibility, one-ground/1–1000-fighter volleys, independent production
damage, warehouse caps, zero-ground neutralization and logical deletion. A
location-subscript defect enables the 450 production batch with only one attacker.
Earlier economic repair/flooring explains why raw zero/fractional inputs cannot
be treated as the helper's entry state; these boundaries are explicitly verified.

No Go gameplay or save-schema changes are included. Next implement bounded
planetary encounters with corrected force accounting/batch policy, surviving-force
eligibility for production/destruction, atomic title/resource updates, private
owner reports and landing-token invalidation. Keep Union protection and captured
home ownership explicit; remaining revenge/cloak searching and native acceptance
are separate. [Evidence, limits and implementation contract](yt-xannor-planets/RECOVERY.md).


## Bounded Xannor planetary assaults — implemented

Mobile routes now resolve ground and production battles after mines/sector
defenses and before ships, sharing the existing finite work budget. Surviving
attackers are required for production damage/capping/destruction, protecting
legitimate zero-rate planets after ground victory. The corrected large-batch
policy requires 450 attackers and a rate above 500. Current ownership, captured
homes and protected Union sectors remain explicit.

Zero ground neutralizes titles; destruction atomically removes the object/link
and every landing grant, without loot or collateral ship death. Original owners
receive private snapshots in BATTLES; whitelisted public news contains only planet
name/outcome. Save version 16 preserves version-15 ship history and rejects
future fields in legacy-labelled saves. Game/store/interface tests and real PTYs
cover bounded work, conservation, ownership, privacy, stale confirmations, slot
reuse, rollback, concurrency, replay, reload and committed durability failure.
[Implementation and validation](yt-xannor-planets/IMPLEMENTATION.md).

Next: remaining Xannor revenge/cloak candidate-search research. Exact RNG/MBF
parity and live BBS/native Windows acceptance remain separate.


## Xannor revenge and cloak candidate-search — research complete

53 completed maintenance controls, three normally exited player-command controls,
23 complete game/runtime REA observations and ten rehashed corruption controls
recover the HQ-victory pending target, positive-pointer consumption, live/cache
distinction, eager 1/25 candidate search, top-player ties/overrides and separate
cloak gates. Native arrivals distinguish revenge selection from interception.
Runtime operand/flag tracing corrects ordinary `.33` equality to `>=`; the
current Go strict comparison remains an explicit implementation gap.

No Go gameplay or schema changes are included. Next implement persistent, atomic
revenge from actual Xannor-owned HQ defeats, living/generation-safe targets,
finite candidate/fallback work and documented cloak/group 20 policies. Do not
inherit stale-cache/dead-record targeting, plasma's missing-owner guard or
unbounded legacy retries. The report explicitly bounds dense-screen phase
interference, exact ties/draw counts, concurrent cache divergence and malformed
pointer coverage. [Evidence and implementation contract](yt-xannor-revenge/RECOVERY.md).


## Bounded Xannor revenge and cloak candidate selection — implemented

Actual Xannor-owned HQ garrison defeats now queue one current player/generation
from fighter or missile settlement. Last committed victory wins; death cancels;
one forward daily phase consumes the slot, including protected/unavailable cases.
Finite non-Union fallback pools, one/at-most-25 candidates, eager living-player
detection and retained-preference short circuit preserve force and replay guards.
Revenge groups 16–19 and group 20 use top/fallback before the final HQ override.
Discovery equality remains strict; all actual ship encounters now accept `.33`
equality and retain uniform cloak/generation safeguards. Turn-based cloak decay
remains the modern policy, with no stale cache or group 20 combat bypass.

Private INFO status and save version 17 accompany atomic queue/aftermath tests,
rollback/replay/concurrency/durability/migration regressions, seeded conservation
and real fighter/missile PTYs. README is updated in the same milestone.
[Implementation and deliberate policies](yt-xannor-revenge/IMPLEMENTATION.md).
Next: research the remaining daily maintenance phases (lottery, inactivity
deletion and their ordering). HQ victory rewards, other equipment and exact
DOS RNG/rounding parity remain scoped work; native/live acceptance is separate.


## Daily super-planet lottery and inactivity deletion — research complete

Forty-one normally completed DOS runs, exact world/auxiliary-file chains and
18 complete native REA observations establish one-shot award gates, old-dead
retirement thresholds, cloak-expiry deferral and phase ordering. Native controls
cover inclusive cutoff, zero/negative delays, year rollover, ordinary orphan port
titles, roster/captain divergence, two-stage radio removal, retained planet stocks
and timestamps, same-day fallthrough, and earlier-phase RNG interference.

No Go gameplay or save-schema change is included; version 17 remains current.
The independent verifier and eleven rehashed corruptions enforce semantic results,
not only hashes. README is updated in the same research milestone.
[Evidence, limits and next implementation contract](yt-maintenance-lottery/RECOVERY.md).

Next: implement bounded daily super-planet awards and safe inactive dead-player
retirement in atomic maintenance. Keep living/current-generation eligibility,
complete new-planet initialization, ownership/team/history invariants and the
modern replay guard explicit; do not copy stale-slot, orphan-title, duplicate-alias
or same-day legacy defects. Confirm identity/store reference coverage before
choosing how retirement is represented. Remaining maintenance events, HQ credit
rewards, equipment and exact DOS RNG/rounding remain separate scoped work.


## Bounded super-planet awards and safe inactive-player retirement — implemented

Save version 18 adds inactive identity records, successful-login activity dates
and private typed system radio. Old dead accounts retire at the inclusive14-day
cutoff after both activity and death, before economics/NPC phases. Released
ownership/access/mine layers and membership are settled without reusing identity
IDs or deleting private history. Returning authenticated identities get fresh
ships when active capacity allows; the bounded256-identity archive is explicit.

After NPC actions, one-shot living-player awards use ordinary slots and safe
non-Union placement, complete fresh initialization, whole-credit banks and
private sector notices. Public news carries only the winner. Exhausted metadata,
full capacity, occupied/hazardous placement and daily replay cannot partially
award or retire. Version17 migration does not invent historical events.

Focused and seeded game tests, atomic store/concurrency/rollback/durability and
migration tests, real compact/classic terminal coverage, full race suite/vet,
research/archive verification and Linux/Windows cross-builds validate the
milestone. README is updated in the same commit.
[Rules, deliberate policies and limits](yt-maintenance-lottery/IMPLEMENTATION.md).

Next: recover the remaining random port/planet maintenance events, including
plague and civil-war rules, before their bounded implementation. HQ victory
credit rewards, other equipment, exact RNG/rounding and native/live acceptance
remain distinct work.


## Port plague and planetary plague/civil war — research complete

Fifty-six normally completed original-DOS runs, exact same-day/next-day world
and auxiliary chains and 18 complete REA byte observations establish post-growth
port thresholds, conditional rate draws, Earth coverage, caps/commodity switching,
planetary strict gates, civil override, fractional ground damage and bank loss.
The corpus separates growth from events, retains the 08:00 precision-triggered
catch-up defect, and proves stale expense text without a second bank debit.
Ownership/name/link/weapon and public/private reporting boundaries are explicit.

An independent verifier, executable model and 16 rehashed corruption controls
validate semantics, chronology, original bytes and clocks. All 4,682 original
archive hashes pass. No Go gameplay or schema changes are included; save version 18
remains current. README is updated in this same research milestone.
[Recovered rules, evidence, limits and implementation contract](yt-plague-civil-war/RECOVERY.md).

Next: implement bounded port and planetary overcrowding events in atomic daily
maintenance, with strict gates, explicit rounding/quantity policy, safe commodity
selection and whitelisted public news. Preserve current identity/home, private
asset, zero-rate and replay/rollback invariants; do not copy stale expenses or
clock-induced overproduction. HQ credit rewards, other equipment, exact RNG/MBF
parity and native/live acceptance remain separate work.


## Bounded plague and civil-war events — implemented

Daily maintenance now runs one stable port/planet event pass after ordinary growth,
with strict recovered gates, civil-war priority, conditional damage draws, capped
cargo and stable commodity selection. Earth and faction homes participate without
changing their identity/protection rules. Modern rules floor ground to whole units,
keep exact bounded credit debits and avoid stale expenses and rollback catch-up.
Typed public news retains only port counts or planet names. Existing locked atomic
saves include damage, news, date, tokens and scores together. Save version 19 adds
these news types; legacy input upgrades without inventing events or changing assets.
The preceding research-only status and implementation contract are historical.
[Implemented policies, numerical differences and validation](yt-plague-civil-war/IMPLEMENTATION.md).

Next: recover the original Xannor HQ victory credit reward before its bounded
implementation. Remaining equipment/actions, complete random-event/RNG/MBF parity
and native/live operational acceptance remain separate work.

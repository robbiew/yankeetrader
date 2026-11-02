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

## Original implementation stages (historical; current status below)

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

Historical initial slice: the [confirmed-trigger follow-up](yt-spies/triggers/IMPLEMENTATION.md)
now removes fighter transfers, adds weapon/unavailable-query triggers and shares
login-local visibility. Ship/disruption findings are also implemented; current
format is 27. The older trigger/version restrictions below record that milestone.

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

The subsequent HQ reward research and implementation below complete that
follow-up. Remaining equipment/actions, complete random-event/RNG/MBF parity and
native/live operational acceptance remain separate work.

## Xannor HQ victory credit reward — research complete

Thirty-eight completed original-DOS sessions, two exact world/auxiliary follow-ups
and 12 REA byte observations establish fixed current-actor payment, caller gates,
HQ interception along routes, team nonsharing, native precision, public/broadcast
reporting, pause expiry and repeat eligibility. Plasma's absent owner guard is
confirmed through ordinary commands against Mercenary, human and own fighters.
An existing revenge pointer does not suppress payment; a normal reconnect without
a new victory does. Large-balance receipts can claim a million despite no increase.

The independent verifier and 16 rehashed corruption controls check inputs, chains,
financial noninterference, exact arithmetic, fresh messages and original bytes.
README is updated in this same research milestone. No Go gameplay or save-format
change is included. Plague/civil-war implementation is tracked separately in
[PR #43](https://github.com/robbiew/yankeetrader/pull/43).
[Recovered reward rules, evidence and proposed implementation contract](yt-xannor-hq-reward/RECOVERY.md).

The implementation contract above is historical; the implementation below now
completes this follow-up.

## Bounded Xannor HQ victory credit rewards — implemented

Supported fighter and missile victories now require a positive prior Xannor-owned
force at the authoritative HQ, including an intercepted HQ along a missile route.
Only the acting player receives exact integer credit up to remaining capacity;
full accounts receive zero. Saved force removal, credits, revenge, typed public
news and subsequent mine/combat aftermath are one transaction. Private receipts
report the actual addition after save success; public notices retain only the
victor's alias. A counter-volley award belongs to its retaliator. Existing live
rankings and explicit/login/logout/daily score-cache publication remain unchanged.

Each newly restored force may pay on a new qualifying victory. Existing intent
validation and ship generations reject stale/repeated confirmations, and competing
contenders cannot both claim the removed force. No receipt or revenge pointer is
a redeemable payment token. Save version 20 adds typed victory news; upgrades
preserve assets/history without paying old pending revenge or backfilling notices.
README is updated in this same implementation milestone.

Validation: full race-enabled Go suite and vet, focused actor/cap/route/death and
journal tests, atomic rollback/concurrency/durability/migration regressions,
19 real terminal smoke scripts, reward/revenge DOS verification, 16 reward semantic
corruption controls, all 4,682 archive hashes and Linux/Windows cross-builds.
[Implemented policies and validation](yt-xannor-hq-reward/IMPLEMENTATION.md).

Remaining: other equipment/actions, complete random-event/RNG/MBF parity and
native/live operational acceptance. Plasma's recovered ownership defect and DOS
floating-point credit rounding are intentionally not copied.


## Danger scanner and manual emergency warp — research complete

Forty-one fresh completed DOS sessions and ten complete REA byte observations
close purchase/persistence, warning queue, autopilot partial progress and hazardous
warp-arrival gaps. Exact Earth item-5 payment is 250,000 credits; duplicate and
poor purchases preserve funds. W has no purchased-equipment requirement. New
controls establish actual same-sector and same-login avoided-sector landings,
empty-exit destinations, capped recharge, natural meltdown and same-date reload.
Mines resolve on arrival and hostile fighters remain an unresolved encounter gate.

Frozen setup/parent/auxiliary chains, independent semantic verification and 23
rehashed corruption controls pass, alongside existing encounter/hazard checks and
all 4,682 archived-file hashes. Original binaries were not patched; only disposable
world copies were mounted. No Go gameplay or schema changes are included; version
20 remains current. README is updated in the same research commit.
[Recovered rules, retained evidence, limits and proposed contract](yt-scanner-warp/RECOVERY.md).

Next: implement bounded danger-scanner purchasing/persistence and manual emergency
warp in both interfaces, with fresh warnings/confirmations, exact credit/turn
receipts, bounded destination/heat work, atomic arrival/aftermath and stale-session
validation. Preserve protected-Earth and existing attribution/generation rules.
Next-day engine repair, lethal-arrival DOS controls, complete disruption behavior,
other equipment, RNG/MBF parity and native/live acceptance remain separate work.


## Bounded danger scanner and manual emergency warp — implemented

Earth item 5/compact EQUIP scanner 1 now installs one scanner for 250,000 exact
credits, with duplicate/affordability/docking guards, saved receipts and actual
ship-info status. Scanner warnings snapshot real mines and hostile defenses,
respect own/team passage, clear queued travel and preserve completed autopilot
hops. Accepted entry resolves mines while hostile fighters continue blocking
normal actions. Mine scanner loss, death and replacement are persisted.

Manual W/WARP now uses a fresh risk confirmation, bounded heat/destination draws
and exact capped whole-turn debit. It can land in current/avoided/hostile sectors;
mines and fatal estate cleanup save in the same transaction. Receipts separate
random landing/recharge from later automatic escape and its total debit. Login-local
one-use confirmation plus a saved per-account warp sequence prevent replay even
for zero-cost same-sector outcomes. Existing score-cache publication is preserved;
live scores now count the recovered scanner asset value.

Save version 21 adds the boolean scanner and warp sequence, upgrading older saves
without granting equipment or moving ships. Validation includes full race tests,
vet, 64 seeded warp worlds, stale/team/turn/sequence and locked-deadline guards,
rollback/concurrency/durability/migration/fatal-arrival tests, both interfaces and
20 real terminal smoke scripts. The 41-session/10-observation evidence verifier,
23 semantic corruption controls, hazard verifier, all 4,682 archive hashes and
Linux/Windows cross-builds pass. README is updated in the same commit.
[Policies and validation](yt-scanner-warp/IMPLEMENTATION.md).

The preceding research contract is historical. Remaining work includes score
scanners, other equipment, full disruption/black-hole and original RNG/MBF parity,
next-day original-engine repair/lethal-arrival research and native/live acceptance.


## Cloak-energy purchasing and anti-cloak activation — research complete

Thirty-seven completed original-DOS controls and four exact world/auxiliary
reconnect chains establish recharge price, whole-point inputs, capacity and blank
defaults, cancellation and persistence; fixed-price anti-cloak confirmation,
repeat/empty activations, global cached reveals, actual sensor visibility, stored
energy conservation, own FAIL display and the session's cloak-decay suppression.
Reconnecting restores concealment and ordinary turn-boundary decay. Ten complete
REA byte observations corroborate the interpreted QuickBASIC paths. Independent
verification checks declared setup, hashes, exact inputs, every conserved world
byte, actual payments/energy/turns/scores and the loaded native bytes. README is
updated in this same milestone. No Go gameplay/schema change is included; current
version remains 21. Earlier references to unsupported scanner scoring do not
identify a separate score-scanner shop item: danger-scanner value is implemented;
cloak and anti-cloak activation add no asset bonus in these controls.
[Evidence, limits and proposed contract](yt-cloak-equipment/RECOVERY.md).

Next: implement bounded Earth cloak-energy purchasing and login-local anti-cloak
activation with exact credits, fresh confirmation, staged visibility/debit,
incarnation checks, post-lock expiry and accurate saved receipts in both
interfaces. Keep the normal modern cloak-consumption rule, explicitly documenting
the difference from the original decay-suppression side effect. Do not convert
anti-cloak into permanent inventory or erase victims' stored energy. Concurrent
observer/target replacement behavior, large-balance and exact MBF/RNG boundaries,
Earth's paid lottery, Genesis, thrusters/forced landing and native/live acceptance
remain separate work.


## Bounded cloak-energy purchasing and login-local anti-cloak — implemented

Earth item 1/compact EQUIP cloak now buys whole points at 1,000 exact credits, with
classic affordable/missing blank defaults, capacity/docking/deadline guards and
saved debit/balance/energy receipts. Earth item 6/compact ANTICLOAK requires a fresh
500,000-credit confirmation, clears queued approval and stages existing living
ship-generation reveals with its debit. Repeats and empty activations remain paid;
receipts identify the actual new reveals. Other logins, reconnects, replacements
and future targets inherit no activation authority. Victim stored energy/assets,
score publication and ordinary modern cloak decay remain unchanged.

Ordinary failure rolls back world and cache; committed durability warnings retain
both effects and consume the confirmation. Session/cache locks follow world-lock
ordering, keeping staged reveals unavailable to concurrent sensors until outcome.
Save version 21 remains unchanged; no new saved fields or migration gifts. Tests
cover credits/capacity/defaults, stale quotes, session binding, parallel spending,
post-lock expiry, rollback/committed durability, target replacement and real
terminal receipts/visibility in both interfaces. README and CI updated together.
[Implementation and validation](yt-cloak-equipment/IMPLEMENTATION.md).

The research contract above is historical. Remaining work includes Earth's paid
lottery, Genesis, planetary thrusters/forced landing, broader communication/intel,
full random-event/RNG/MBF fidelity and native/live acceptance.


## Earth's paid Pick-6 lottery — research complete

Forty-nine completed original-DOS controls and twelve REA byte observations
establish five-credit admission, exactly six digits, retry behavior, configured
zero-through-nine daily limits and invalid-limit fallback, same-day persistence,
next-date login reset, duplicate-limited order-independent matching, every gross
payout tier and the four-match public-news threshold. Natural fixed-clock tickets
reach the jackpot without binary/RNG patches. Large balances expose MBF fee and
award rounding; native paths show separate pre-input count, prize and fee saves.
The independent verifier checks complete worlds and auxiliary chains, exact
inputs, semantic outcomes and loaded bytes; rehashed corruption controls challenge
these claims. README is updated in this milestone. No Go gameplay or schema
change is included; current version remains 21 and item4 remains unavailable.
[Evidence, boundaries and proposed contract](yt-earth-lottery/RECOVERY.md).

Next: implement bounded paid Earth lottery with exact integer credits, six-digit
multiset matching, validated finite daily quota, fresh ticket confirmation,
post-lock expiry/date/identity checks, bounded draws and atomic fee/actual capped
prize/count/sequence/news settlement. Receipts must distinguish nominal prize,
actual award, fee, balance and remaining plays, including committed storage
warnings. Keep cancellation safe and score publication consistent. Add focused
concurrency, replay, rollback, date, migration and real terminal checks, updating
README in the same implementation commit. Do not copy original floating-point
money defects or pre-input/non-atomic charging order. Full original RNG/numeric
parity, interrupted/concurrent DOS entry, year rollover, Genesis, planetary
thrusters/forced landing and native/live acceptance remain separate work.


## Bounded paid Earth lottery — implemented

Earth item 4 and compact LOTTERY now use six-digit tickets, a five-credit fee,
multiset matching and recovered prize tiers. Fresh literal confirmation clears
queued approvals. Account quotas default to five per UTC date (validated optional
0–9 configuration), persist through reconnect/death/replacement, project forward
without read-time writes and reject rollback or a midnight-stale quote.

Six OS-random digit calls, exact fee/actual capped award, quota and sequence, and
four-plus-match typed public news settle under the existing atomic world lock.
Receipts report actual draw/matches/payment/caps/balance/quota, including committed
storage warnings without replay. Score-cache publication remains explicit and
public news contains no balance, ticket, draw or identity. Save version 22 upgrades
older worlds without gifts and preserves read-only file bytes. Tests cover all
prizes, duplicates/permutations, dates, stale/tampered bindings, parallel net-zero
caps, expiry, rollback/durability/reload/replay and both real terminal interfaces.
README is updated together. [Policies and validation](yt-earth-lottery/IMPLEMENTATION.md).

The preceding research contract is historical. Remaining work includes Genesis
and season-reset implementation, planetary thrusters/forced landing, broader
communication/intel, full original RNG/MBF fidelity and native/live acceptance.


## Genesis endgame and safe season-reset contract — research follow-up

Twenty-four fresh returned DOS controls (thirteen resets, eight refusals or
cancellations, two deliberate faults and one maintenance run), 48 world snapshots,
two exact parent-world/auxiliary follow-ups and thirteen native observations
establish cached admission, threshold/cancel behavior, destructive reset scope,
configuration normalizations, stale scoreboard retention and marker failure/resume
ordering. The tested alias case-pair still yields blank winner announcements;
original BBS identity reconstruction and mid-write/concurrent reset behavior remain
unresolved. The independent verifier checks semantic record layouts, topology,
resource/default changes and provenance; frozen complete output hashes also
preserve native noncanonical zeros and the bounded maintenance witness. README is
updated in the same research milestone. No Go gameplay or schema changes are
included; save version remains 22 and Genesis remains unavailable.
[Research and concrete safe-reset contract](yt-genesis/SAFE_RESET.md).

Historical next-step contract (implemented below): bounded Genesis endgame with authoritative ownership recount,
fresh destructive confirmation, stable season epoch captured inside login, and
winner history in the same atomic replacement as the new world. Audit every
session/cache/acknowledgement path for epoch binding, especially direct spy
acknowledgements; keep the existing world.lock inode. Use finite generation and
explicit bootstrap (New sets maintenance current, so Maintain immediately skips),
carry supported configuration without re-enabling disabled lottery play, and
validate the candidate before admission. Do not claim an unknown old seed or a
Wanderer lifecycle (implemented below). Test same-ID/generation reuse, login/reset
races, concurrent winners, rollback/durability/replay, history/epoch exhaustion,
read-only migration and both real terminal interfaces. Update README alongside
implementation; native/live acceptance and full DOS RNG/numeric fidelity remain
separate.


## Bounded Genesis endgame and atomic season reset — implemented

[Implementation](yt-genesis/IMPLEMENTATION.md) completes the bounded contract:
actual non-Earth title recount, explicit 0/20–300 configuration (default 300),
fresh literal GENESIS confirmation, finite generation and explicit supported-home
bootstrap, monotonic epoch captured inside both login transactions, and a bounded
public winner archive in the same atomic world replacement. Save version 23
migrates legacy worlds to season one without reset or history backfill. Old bound
reads/mutations/scores/acknowledgements/caches and pending intents reject ID reuse.
`G`/`GENESIS` and `SEASONS` are available in both interfaces. README and CI are
updated in this same milestone. See validation log for rollback/durability,
concurrency/process interruption, exact confirmations and terminal coverage.

Remaining candidates: planetary thrusters/forced landing research, native/live
acceptance, full universe generation and numeric/RNG parity, unsupported
communication/intelligence and remaining random events. Explicit season archive
export/admin reset tooling remains unimplemented; Wanderer lifecycle is implemented below.


## Planetary thrusters and player forced landing — bounded research complete

[Follow-up research and contract](yt-planet-mobility/RECOVERY.md) retains 55
normally returned DOS controls, 110 world snapshots, two exact parent/auxiliary
chains and 19 native byte reads plus a verified MZ mapping. Ten-turn route budgets,
first/later collisions and paid prefixes, owner/team/unguarded permission,
reserved-slot handling, mine/fighter arrival, ordinary Earth relocation, ground
commitment/win/loss, faction owners, fractional inputs/defenses, adoption/unrest and
reentry/retry are tested within declared bounds. Raw sector133 is unmapped and its
negative controls are not black-hole evidence. The Wanderer's ship and planet can
end in different sectors. The original route saves per edge and ground combat
charges before its loop; modern atomicity is a deliberate requirement, not a
claim about DOS concurrency or crash safety. Independent semantic/provenance
verification and rehashed corruption controls accompany the corpus. README and
CI are updated in the same research milestone; no Go gameplay/schema change.

Historical implementation contract (completed below): bounded ordinary planetary thrusters and player forced landing
with fresh exact risk confirmation, captured season/ship/planet incarnation,
current team/access and route/hazard binding, whole-number commitments, finite
route/battle work and atomic outcome/cost/capture/destruction/aftermath. Revoke all
landing grants when a planet moves or dies; do not teleport other landed callers.
Protect faction identity explicitly instead of slot/name guesses; retain main !
for missiles and landed ! for thrusters. Audit every planet constructor if a
nonreusable incarnation allocator is added, with an explicit migration. Keep lazy
projection distinct from persisted quote identity, preserve rollback/committed
warnings and return actual saved receipts. Test concurrent movers/attackers,
destroy/recreate ABA, successful-prefix failures, mines/fighter stops, work/RNG
faults and both terminal interfaces. Historical unsupported Wanderer/disruption lifecycle,
full original RNG/MBF parity and native/live acceptance remain separate.


## Planetary thrusters and forced landing — implementation complete

[Implementation contract](yt-planet-mobility/IMPLEMENTATION.md): save24 adds a
validated planet-generation allocator, deterministic older-save migration and
constructor coverage for ordinary creation, both faction restorations, super
awards and Genesis homes. Fresh login-sealed, single-use two-minute intents bind
planet/ship/season/access, copied shortest routes and hazards. Thrusters preserve
physical prefixes/collisions, revoke grants, resolve mines and stop at hostile
fighters in one save. Ground combat has 4096-round work bounds, strict commitments,
explicit no-refund retreats, captured survivors, vacant-government unrest and typed
public player news. Both interfaces return saved resource/casualty/capture receipts
and preserve committed durability warnings. README, terminal fixtures and CI are
updated with this milestone. Current validation is recorded in evidence/VALIDATION.md.

Historical boundary (targeted controls completed below): original
RNG/MBF fidelity, broader long-running balance, live BBS and native Windows durability.


## The Wanderer lifecycle and transport — bounded research complete

[Recovery and implementation contract](yt-wanderer/RECOVERY.md) retains 57
normally returned DOS controls, 114 world snapshots, 9 exact parent/auxiliary chains,
14 native byte reads and 3 verified MZ load images/1006 relocation fixups. Independent
verification and 55 rehashed corruption controls bind setup, clock/keys, returned
program markers, semantic mutations, privacy and frozen complete world/auxiliary
witnesses. A bounded nonreturning no-candidate probe and a complete but later
NPC-confounded destruction run are classified separately.

Recovered daily movement follows the first slot1 link, clears its governor and
refills exact-zero bank. Missing references cause partial restoration; an inactive
but linked record does not. Duplicate links, same-day replay and backward-date
repeat economics are native defects/limitations, not modern safety requirements.
YT-INIT invokes maintenance bootstrap; standalone RMT-INIT does not. Special
transport requires its full quote but charges/stops after one edge, with the
planet and ship at different destinations and distinct hazard roles. Native
receipts hide the random planet destination. Later NPC destruction must be
separated from a successful preceding relocation.

Research-stage contract (completed below): bounded Wanderer bootstrap/restoration/daily movement and special
transport with persistent identity, explicit capacity/migration, finite candidate
selection, protected existing assets, once-per-date maintenance, atomic links/
resources/title/grants/aftermath, fresh incarnation on restoration and appropriate
hidden-location receipts. Integrate Genesis explicitly without repeating daily
awards or backdated catch-up grants. Keep normal movement incarnation stable,
never identify the mobile planet by name/slot accident, and preserve existing
faction-home rules. README is updated in this research milestone; save version 24 and Go
gameplay are unchanged. Historical scope: targeted disruption transport is recovered below; exact RNG/MBF, balance and
native/live acceptance remain open.


## The Wanderer lifecycle and special transport — implementation complete

[Save25 implementation](yt-wanderer/IMPLEMENTATION.md) adds explicit unique mobile
identity in reserved slot 1, 100-planet capacity and asset-preserving older-save
migration. Initializer/Genesis bootstrap a clean current-dated neutral planet.
Forward-only daily maintenance relocates an existing Wanderer after economics,
clears its governor, refills only a zero bank and invalidates all grants. Missing
restoration follows faction-home placement priority, precedes mobile Xannor work,
and allocates a fresh incarnation. Final daily receipts account for subsequent
NPC destruction without recreating it twice in one run.

Confirmed thrusters bind finite candidate occupancy and existing ship/season/
planet/access/route hazards. The full quote must be affordable; successful transport
spends 10 turns, stops after one edge and places ship/planet independently. Planned
collision/stress precedes random placement; reached ship hazards remain atomic.
Fresh confirmation, rollback, stale-incarnation/candidate checks, warning handling
and hidden-destination receipts apply in both interfaces. README, schema migration
assertions, isolated historical fixtures and the Wanderer terminal check are part
of this milestone. See evidence/VALIDATION.md for executed checks.

Targeted disruption controls are completed below. Remaining: disruption gameplay, exact DOS RNG/MBF fidelity, broader balance,
season archive export/admin reset tooling and native/live acceptance.


## Disruption and black-hole arrival — bounded research complete

[Recovery](yt-disruption/RECOVERY.md), [native observations](yt-disruption/NATIVE.md)
and [candidate implementation contract](yt-disruption/CONTRACT.md) retain 61
returned controls/122 full snapshots, four exact world/auxiliary reloads, 15 native
byte reads and a relocated MZ image with 870 fixups. One unsupported one-sector
40-second no-return diagnostic is separate. Narrow declared tables and normal
3000-sector/full-header controls have independent setup verification. The latter
locate real session holes through the original sensors and exercise both arrivals.

Recovered: two independent session-local locations may coincide; startup and
returned-shell arrivals force warp before mines/fighters, even at zero turns,
and recheck destinations. Autopilot stops. Safe internal planetary edges do not
check disruption until helper return; hazard stops return early. Forced warp
moves only the ship, preserving ordinary/Wanderer planet positions. Heat/turn
receipts, later mine escape/death, hidden-location privacy and changed-session
sensors are checked separately. Raw 133 is not a hole flag; exact RNG/MBF parity
is not claimed. The native loop has no chain cap, so modern bounded exhaustion
needs an explicit policy. Current Go mine-escape heat-budget recomputation is a
source discrepancy to audit during the shared-kernel work, not an incidental fix.

Research-stage next step (implemented below): bounded session-local disruption and automatic arrival composition
with finite selection/chains, narrow encounter authority, captured ship/season
identity, fresh voluntary intent checks and one atomic origin/aftermath save.
Keep transport and recharge costs distinct, preserve independent planet positions,
stop queued navigation, retain killer/estate rules and committed durability
warnings, and expose only supported local warnings/private saved receipts.
Update README, tests and validation together. This research changes no Go code or
save25 fields. Historical remaining work (arrival implementation completed below): exact random/numeric parity, unrelated
disruption combat/spy branches, balance and native/live acceptance.


## Bounded disruption arrivals — implementation complete

[Implementation](yt-disruption/IMPLEMENTATION.md) binds two independently sampled,
possibly duplicate interior holes to each live ship/season login. Save25 remains
unchanged; the existing warp sequence now counts forced warps and invalidates
travel/mine/bribe/defense/attack/missile confirmations. Startup, ordinary movement,
accepted warnings, manual/mine escapes and planetary helper returns compose
hole-first arrival with the origin action and reached aftermath in one save.
Ordinary thruster intermediate-edge timing and independent Wanderer/ship positions
are retained. Adjacent bribe/breach approaches skip a hole's fighters before
payment/combat. Forced recharge does not decay cloak. Shared heat accounting
caches the original two-draw budget while retaining separate destination policies.

Work is capped at 32 disruption warps, 139 heat steps per warp and existing mine
burst bounds. Exhaustion or invalid/stale inputs abort the whole action, rather
than publish an arbitrary prefix or free escape. Local sensors/scanners expose
observed warnings; generic news and saves conceal the hidden pair. Both interfaces
print committed known-position/resource receipts, stop queued navigation and
retain committed warnings through output failures. README, regression/real PTY
checks, quiet historical-fixture selection and CI include the milestone.

Remaining: exact DOS RNG/MBF parity, unrelated disruption combat/spy branches,
broader balance, season archive export/admin reset tooling and native/live BBS
acceptance. Consult evidence/VALIDATION.md for checks actually executed.


## Plasma launch, routing and disruption research (2026-10-31)

Completed the [research slice](yt-plasma/RECOVERY.md): 62 normally returned DOS
controls, 124 full world snapshots, two exact world/auxiliary reload chains,
13 native byte reads and a reconstructed MZ load image with 870 relocations.
Original binaries and the archive remain unchanged. This extends the older
absorption corpus rather than recounting those sessions as new work.

Recovered positive-turn/stock admission and launch debit, blank cancellation and
fresh invalid-input reprompts, directed BFS/tie order/avoid bypass, fixed launch
energy attenuation and the 50-entry empty-course limit. Actual login holes reroute
the projectile before absorption and rebuild a course; they do not teleport the
ship. Controls cover self/friendly/cloaked hits, shared fighter/mine/ship/planet
absorption, wreck mines, death and saved salvage, lazy warehouse-derived production,
true zero-impact-rate retirement and logical planet cleanup. Native interpretation
and raw execution remain separate; whole estates, exact RNG/MBF parity, protected
world policy and every maximal input are not newly proved.

Independent portable verification and 53 rehashed corruption controls are wired
into CI. README and validation notes describe the research boundary. No Go gameplay
or save change: schema25 and the published disruption implementation are preserved.

**Next implementation:** [bounded plasma launch and atomic aftermath](yt-plasma/CONTRACT.md).
Choose concrete shared work/quantity bounds and explicit self/friendly/posthumous
source policies; add fresh sealed consent, privacy-aware saved receipts and a
single store transaction for the origin cost, redirects, damage, deaths, wrecks,
estates, planet removal and qualifying HQ reward/revenge. Do not copy missile
friendship/cloak/self filters or the DOS HQ owner-check exploit. Other spy/disruption branches, live BBS acceptance and native Windows durability
remain separate.


## Bounded plasma launch and atomic aftermath (2026-10-31)

Implemented the [researched plasma contract](yt-plasma/IMPLEMENTATION.md) on a
separate feature branch. Both interfaces now expose `PLASMA`/`+` with fresh sealed
consent and 1–64 available bolts. Own/empty and unreachable courses retain their
explicit recovered financial behavior. Directed BFS/stored-exit ties, avoids
bypass, fixed energy attenuation, hole-first rerouting and shared defense/mine/
ship/planet absorption are bounded by per-launch limits. No RNG is consumed by
read-only previews; all possible redirect targets are covered by the sealed world
and login context. Changed or replayed consent cannot spend resources.

Ship deaths use schema26's explicit plasma cause, with self/friendly/posthumous
attribution, consistent ship cleanup and living-recipient estate rules. Self
plasma death keeps the next-UTC-day cooldown; other victims receive normal fresh
login replacements without refilling turns. All carried wreck mines are excluded
from salvage, attributed to their carrier, absorbed before later targets and
resolved locally before saving when they endanger the surviving launcher. Earth
remains mine-free. Reached planets project lazily and receive bounded damage,
caps, governor clearing and generation/access-safe removal. Unreached planets
are untouched. Qualifying HQ rewards/revenge/news remain atomic and retain the
actual-Xannor-owner guard. No invented missile retaliation is introduced.

The store consumes a login-local nonce and commits costs, consequences, hazards,
loot, deaths, estates, cleanup and HQ publication together. Private saved receipts
omit concealed aliases, private banks and projectile/hole coordinates; late
failure, concurrency, real reset with reused IDs and committed output/storage
errors have focused regression coverage. Version1–25 saves upgrade without assets;
README documents save26 and actual playable/remaining status. The original DOS
corpus is unchanged. See validation notes for executed checks and limits.

Remaining work includes additional spy/intelligence and
public-message/newspaper paths, exact original RNG/numeric parity, balance tuning,
live BBS acceptance and native Windows crash durability. Those are separate from
this completed bounded firing path.


## Mercenary plasma acquisition — removed sales backlog correction (2026-10-31)

The [versioned acquisition research](yt-mercenary-plasma/RECOVERY.md) closes the
previous Mercenary plasma-sales item as obsolete. DOS 3.3 added a Mother Ship at
5,000,000 credits per bolt; 3.4 explicitly removed it after adding planetary
production. The Mercenary home planet added in 3.6 is a distinct capture target.
Current Earth/planet dispatch evidence and copied-world DOS controls corroborate
planetary acquisition within their stated search boundary. No claim of exhaustive
universal absence, historical 3.3 purchase semantics or new purchase API is made.

No Go gameplay or save26 change. README and prior plasma backlog references are
corrected together; portable acquisition evidence verification is included in CI.
Remaining candidates are broader spy triggers/notifications,
multiline editing, remaining newspaper events, original
universe/save parity, balance and native/live acceptance.

## Ship, cloak and disruption spy intelligence

Historical detection slice: the [trigger/cache follow-up](yt-spies/triggers/IMPLEMENTATION.md)
now shares detections with sensors and attack eligibility, without saved cloak
changes or persistent target warnings. Current format remains 27.

Six new completed DOS controls establish ship details, full-cloak suppression,
a positive partial-cloak shimmering report, ordered multiple ships, caller
exclusion and login-local disruption reporting. The Go spy network now exposes
these findings with generation-bound private detection memory, nested-copy
isolation and unchanged saved cloak/combat visibility. World version 26 stays
unchanged. Original RNG odds/ties, target notification and broader triggers
remain open. [Evidence and bounded policies](yt-spies/intelligence/IMPLEMENTATION.md).

## Team radio

Nine completed DOS controls establish roster fanout, self-copy, independent
read flags and recipient-at-send membership semantics. `RADIO TEAM` and computer
5 now confirm the roster and save every private copy atomically, rechecking
membership and aliases before commit. Existing version-26 mailbox records,
history and delivery are reused; no migration is required. Tests cover stale
drafts, concurrent retry, failures and compact/classic terminal flows.
[Evidence, policies and limits](yt-team-radio/IMPLEMENTATION.md). Broadcast,
multiline editing and native BBS acceptance remain open.


## Broadcast public records and shared lifetime — extended research

The [extended radio research](yt-broadcast-radio/extended/RECOVERY.md) supplements
the separate PR #58 private-copy implementation. Original ALL uses a global
record per line with budget30, decremented by two on automatic delivery;
computer history does not decrement it. The original also writes a public
newspaper header/body. Exhaustion and maintenance are distinct from calendar
expiry. Current Go fanout remains an explicit adaptation, not shared-record
parity.

The [research disposition](yt-broadcast-radio/extended/CONTRACT.md) requires
an explicit choice before adding newspaper publication or a shared global
archive. Private/team mail must remain private, publication and acknowledgements
must be atomic and bounded, and any new persisted scope needs deliberate
migration. No Go gameplay or save26 change is included in this research.

## Bounded broadcast radio

Six completed DOS controls establish the shared ALL record and 30/28/26 read
transitions, including repeat-reader delivery. Go now offers explicit
`RADIO ALL` / computer 5 with atomic private copies for current active accounts,
including the sender. Independent unread flags and no future-account inheritance
are deliberate modern policies, not shared-counter parity. The existing
version-26 mailbox format is reused. [Evidence and policies](yt-broadcast-radio/IMPLEMENTATION.md).
Multiline editing, complete original counter lifetime and native BBS acceptance
remain separate.


## Broadcast newspaper publication — implemented

ALL now requires an explicit public-text/alias preview before fresh Send. One
bounded typed public event and all private copies save together; private/team
mail is not published. Version 27 upgrades versions 1–26 without backfilling old
broadcasts. Retried drafts, rollback, committed-warning receipts and public/private
reading scopes have regression coverage. See
[implementation](yt-broadcast-radio/IMPLEMENTATION.md) and
[validation](../evidence/BROADCAST_NEWSPAPER_VALIDATION.md).
The shared DOS delivery counter, multiline editor, live BBS and native Windows
durability remain separate. Earlier save26/research-only boundaries above are
historical and superseded only for this public-publication slice.

## Bounded multiline radio editor

The opt-in editor now supports List, Continue, confirmed first-match Edit, Send
and confirmed Abort for up to 20 lines. Direct, team and ALL documents commit
atomically using version-27 records. Earlier editor deferrals above are historical;
character-level wrapping/backspace parity and live BBS acceptance remain open.
See [native controls and implementation](yt-radio-editor/IMPLEMENTATION.md).


## Spy triggers, observer visibility and target notifications — implemented

The 36-control original-DOS matrix and three exact target-relogin auxiliary chains
recover command gates and per-spy last-report suppression. Native evidence adds
20 complete byte ranges, all 870 relocations and four direct main-code trigger
encodings. The old2253 fighter-deployment interpretation is corrected to shared
missile/plasma launching. Accepted fighter transfers do not advance spies in the
tested DOS path; unavailable Computer-9 planet queries consume a turn and advance.

Spy detection shares an observer-local cache with sensors and attack eligibility,
while saved target cloak remains unchanged. No persistent target warning was
observed on the tested detection route; do not invent one from the old backlog.
The confirmed triggers and login-local shared cache are implemented with atomic
action/report publication, current-session/generation/season checks and accurate
private receipts. Fighter transfers are free of spy progression; missing/blocked
planet queries spend one turn. Weapon scans run before impact, but new grants
cannot expand confirmed missile targets. Single-use login-bound missile seals
reject altered, cancelled and replayed quotes. Save version stays 27. See the
[implementation and validation](yt-spies/triggers/IMPLEMENTATION.md) and
[scoped contract](yt-spies/triggers/CONTRACT.md).
See [recovery and limits](yt-spies/triggers/RECOVERY.md).


## Planet-creation newspaper and private port-sale notices — researched

The [34-control follow-up](yt-newspaper/events/RECOVERY.md) recovers one public
planet-creation line after accepted creation, with no additional turn charge and
no success entry for the tested negative paths. Four exact actor reload chains
preserve world/auxiliary provenance. Native evidence anchors 21 complete reads,
four bounded direct-call searches and 870 relocations.

Correct the broad acquisition-public-event backlog: ordinary owned/unowned,
renamed, teammate and repeated purchases do not append public purchase news in
the tested paths. Owned buyouts instead send a private old-owner system packet
with the old port name, sector and asking price; the legacy sender-2 label is
The Mercenaries. Treasury payout and asking price are distinct. A name refusal
after Sold repeats the dialog rather than undoing accepted acquisition.

No Go or schema-27 changes are included. Next: implement bounded public planet
creation and private seller notices with atomic action/notification saves,
explicit schema/system-origin policy and accurate receipts. Preserve current
unsupported Earth ownership and naming safety policies unless deliberately
aligned separately. Do not invent a public port purchase announcement or backfill
old actions. [Implementation contract](yt-newspaper/events/CONTRACT.md).

## Atomic public planet-creation news

Public ordinary creation is implemented in save28: accepted name/alias snapshots
save with the planet, sector reference and debit, with deadline/session guards and
rollback/committed-warning coverage. Earlier creation deferrals above are historical.
Private former-owner sale notices remain unimplemented; public acquisition news
is not a recovered DOS feature. [Rules and validation](yt-newspaper/events/IMPLEMENTATION.md).

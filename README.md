# Yankee Trader: Resurrection

Version **0.1.0**, with the original game by Alan Davenport, based on Yankee Trader Version 3.6. A reconstruction for local play and BBS doors, built with Go/GoDoors. The first playable milestone supports persistent players, sector navigation, cloak-aware adjacent-sector sensors, directed path finding and confirmed autopilot, cargo trading, Earth equipment purchases, automatic saves, and planet creation, production, transfers and banking, plus port buyouts, personal treasury collection, teams/shared planets, and daily port/planet production and turn maintenance. The original DOS distribution and research evidence are untouched. The app name, semantic version, original creator and version, and repository link come from [`internal/version`](internal/version/version.go); run `./bin/yt -version` to display the release identity.

The full CI validation job has a bounded 90-minute budget: retained research
verification and terminal smoke run sequentially. All tests, evidence checks and
release-package checks remain required.

## Start here

This README combines player instructions, operator procedures, feature rules and
reconstruction notes. Use the current status below for the playable scope, the
feature sections for in-game behavior, and the linked evidence for validation
details and limitations.

| If you want to... | Start here |
|---|---|
| Try a local game | [Play locally](#play-locally) and [DOS-style startup](#dos-style-startup) |
| Run a BBS door | [Run as a BBS door](#run-as-a-bbs-door) and [validation limits](evidence/VALIDATION.md) |
| Check what is playable | [Status](#status) and [Fidelity and deliberate changes](#fidelity-and-deliberate-changes) |
| Build and test | [Build and validate](#build-and-validate) |
| Back up, export, restore or reset a season | [Season administration](#season-administration), [Storage and recovery](#storage-and-recovery), and the [sysop guide](docs/SYSOP.md) |
| Read detailed game rules | [Planet management](#planet-management), [Teams](#teams), [Combat preparation](#combat-preparation), and [plasma](#bounded-plasma-launching) |
| Find the next unfinished task | [Current reconstruction plan](research/RECONSTRUCTION_PLAN.md#current-work) — verified implementation inventory and remaining work; older milestones are historical |
| Review the reconstruction | [History](#a-little-history), [screenshots](#screenshots), [research](research/) and [validation evidence](evidence/) |

## Screenshots

Captured from the current Go game in an 80×25 local ANSI terminal session.
The opening artwork capture includes the centered Resurrection version subtitle;
the startup smoke check verifies its alignment.
Click any screenshot to view it at full size.

<table>
  <tr>
    <td align="center"><a href="evidence/startup/title.png"><img src="evidence/startup/title.png" alt="Yankee Trader: Resurrection title screen" width="400"></a><br>Title screen</td>
    <td align="center"><a href="evidence/startup/opening.png"><img src="evidence/startup/opening.png" alt="Opening ANSI artwork" width="400"></a><br>Opening artwork</td>
  </tr>
  <tr>
    <td align="center"><a href="evidence/startup/sector.png"><img src="evidence/startup/sector.png" alt="Sector view and main command prompt" width="400"></a><br>Sector view</td>
    <td align="center"><a href="evidence/startup/info.png"><img src="evidence/startup/info.png" alt="Ship information and player statistics" width="400"></a><br>Ship information</td>
  </tr>
  <tr>
    <td align="center"><a href="evidence/startup/help.png"><img src="evidence/startup/help.png" alt="Main command menu" width="400"></a><br>Command menu</td>
    <td align="center"><a href="evidence/startup/computer-help.png"><img src="evidence/startup/computer-help.png" alt="Ship computer menu" width="400"></a><br>Ship computer</td>
  </tr>
</table>

## Release downloads and sysop quick start

Release packages provide Linux x86-64/ARM64 tarballs and a Windows x86-64 ZIP,
including a standalone executable, [sysop cheat sheet](docs/SYSOP_CHEAT_SHEET.md),
full save/restore guidance, credits, third-party notices and build provenance.
The published [v0.1.1-sysop.1 tester build](https://github.com/robbiew/yankeetrader/releases/tag/v0.1.1-sysop.1)
is Linux x86-64 only and includes playable `qb36-v1` plus the Door32 negative-handle
fix. The Windows x86-64 and Linux ARM64 packages from v0.1.0 predate that profile;
use a current source build for those platforms. Native Windows/live-BBS acceptance
remains pending.

Tagged `vX.Y.Z` builds create a **draft** [GitHub Release](https://github.com/robbiew/yankeetrader/releases)
with SHA-256 checksums; a maintainer reviews and publishes it. Archive verification
rejects Windows separators/drive syntax and noncanonical member paths on every host. Existing data is
kept outside the versioned package directory. No Go compiler or DOS distribution
is required to play. See [release building and publishing](docs/RELEASING.md).

## Status

**Complete pre-maintenance DOS initializer replay is verified research:** a
model synthesizes all **4,151 records / 568,687 bytes** in each of twenty retained
controls. This extends merged RNG/graph/port recovery with configuration, inactive
players, complete sectors/HQ and inherited inactive planet records. Fresh
scoreboard-path, January 1 and leap-day controls check raw buffer/zero residues.
Production generation keeps its current Go streams and safeguards; save format
is **35** for the playable profile described below. No DOS save importer is supplied. See [complete replay evidence and limits](research/yt-initializer-replay/RECOVERY.md),
[graph/port replay](research/yt-port-replay/RECOVERY.md) and
[raw RNG recovery](research/yt-rng-seeding/RECOVERY.md).
The [pure Go source generator](research/yt-initializer-replay/GO_IMPLEMENTATION.md)
now reproduces all twenty complete native targets using portable golden fixtures;
Go tests require no Python, emulator or original executables. It returns bounded
in-memory source bytes, preserving the original defects for comparison. Fresh
[January 9/10/11 controls](research/yt-initializer-replay/JANUARY10.md) across
2026–2028 verify the class-dependent January 10 zero residue; that date is now
admitted without changing any previously supported source fingerprints.
**Playable QB generation is available in this source build and the Linux x86-64
v0.1.1-sysop.1 tester build** (the v0.1.0 packages predate it). To initialize a separate
world, use `-init -generation-profile qb36-v1 -qb-state 0xc805 -qb-date 2027-01-01`.
The saved typed recipe records the profile, raw 24-bit post-RANDOMIZE state,
explicit source date and SHA-256 of the complete original source candidate.
Both Genesis and administrative resets preserve the recipe and repeat the map,
port names/economy and initial HQ, using current UTC maintenance watermarks and
separate modern bootstrap randomness. Existing worlds upgrade without rerolling
or acquiring a recipe. Stored Genesis confirmations own independent copies of
the complete recipe and raw state, preventing caller mutation of a pending quote.
Unknown/incomplete recipes and pre-35 saves claiming one
are rejected. This is QB generation with documented modern adaptations, not DOS
save interoperability or exact original maintenance.

The profile fixes geometry at 3,000 sectors/1,000 ports, requires a 2026–2028 date
and rejects explicit `-seed`, `-dos-warps` or `-dos-ports`.
It rejects original duplicate ports, protected HQs and disconnected maps without
publishing a save or silently reseeding. The raw state accepts unsigned decimal
or `0x` hexadecimal, including zero; it is not derived from a clock or modern seed.
Use these flags only with `-init`; ordinary play/maintenance reads the saved recipe.
See [sysop setup and reset instructions](docs/SYSOP.md#playable-qb36-v1-worlds),
[compatibility contract](research/yt-initializer-replay/COMPATIBILITY_CONTRACT.md)
and [projection adaptations](research/yt-initializer-replay/PROJECTION.md).
A reset durability warning means the reset committed; inspect the active season
before retrying, and never treat that warning as a rollback.

The [full QB world acceptance campaign](evidence/QB_FULL_WORLD_CAMPAIGN.md) exercises
3,000 sectors/1,000 ports, multiple controlled UTC maintenance dates, session
reconnects and a legitimately earned default 300-port Genesis. Daily same-date
retries must be idempotent; reset checks preserve source provenance/layout and
reject stale logins after player-ID reuse. Evidence verification binds reset
watermarks to the counted UTC days and reconciles every session input with the
action trail, trade/equipment receipts and summary counts. This is production session/store
acceptance with simulated terminal input and an injected game clock. The separate
Door32 TCP/PTY campaign covers transport/concurrent callers; live BBS and native
Windows acceptance remain outstanding.


**DOS warp-generation rules are available for new worlds:** `-dos-warps` enables
nearby reciprocal links, occasional sixth-slot wormholes, isolated-sector repair
and directed return shortcuts toward Earth. Combine it with `-dos-ports` for both
recovered rule sets; either flag can be used independently. Saved choices survive
Genesis and administrative resets. Existing worlds keep their maps on upgrade.
Save **34** adds the warp profile. The seeded Go random sequence, finite retry
safeguards and omission of DOS's redundant Earth self-warp are deliberate modern
choices; this is not exact DOS seed-to-map or MBF arithmetic parity.
[Recovered rules, phase controls and tests](research/yt-warp-generation/RECOVERY.md).


**DOS port generation and pricing are available to test in new worlds:** initialize
with `-dos-ports` to use recovered names, production, trade coefficients and startup
price references. Initial stocks materialize ten production days. The setting is
saved and survives Genesis and administrative resets; existing worlds keep their
ports and fixed reference prices. Without `-dos-warps`, the warp graph remains the established modern graph.
The seeded Go random sequence remains modern, and duplicate/orphaned DOS ports are deliberately prevented.
Save **33** adds the generation profile; older saves upgrade without rerolling.
[Recovered rules, DOS controls and limits](research/yt-port-generation/RECOVERY.md).
The evidence verifier checks every sector-to-port link before and after maintenance,
including missing/fractional links; corruption controls use the independent later-clock
world so repeat-run equality cannot mask missing semantic checks.


**Xannor direct-combat turn bonuses are available to test:** confirmed sector-fighter
combat credits one turn per complete 200 Xannor casualties, within the current
500-turn daily allowance. Partial battles qualify; entry is charged before the
cap is measured. Forced fighter combat after a refused bribe also qualifies;
missile/plasma kills and other factions do not. The saved receipt and newspaper
show actual credited turns, including capped awards. This is separate from the
existing Xannor HQ credit prize. [DOS controls, rules and validation](research/yt-xannor-turn-bonus/RECOVERY.md).
The DOS verifier checks saved casualties/turns and independent normal-return evidence;
the human-defense control explicitly refuses surrender before destroying its fighters.
Required native observations are pinned by address and full length; zero-length and
truncated code/constant reads are rejected.
Save **32** adds the bonus event; upgrades do not backfill rewards for old battles.


**Extended newspaper reports are available in-game to test:** new registrations,
successful team joins, general ship deaths, captured ports and actual salvage,
sector-fighter surrender/casualties, mine encounters and fighter-wreck explosions,
missile/plasma impacts and retaliation, planetary bombardment/destruction and
thruster explosions now publish typed public snapshots with their actions.
New-player registration replaces its initial login entry; failed joins and
cancelled/rolled-back actions publish no success event. Names and actual outcome
quantities survive later renaming/removal. Existing private mail and port-sale
notices remain private. [Inventory, DOS evidence and validation](research/yt-newspaper/remaining/RECOVERY.md).
Evidence verification also checks the newly allocated DOS account and initial ship,
and exact team announcements against saved membership; rehashed false reports and
unchanged-world substitutions are rejected.
Save **31** adds these event payloads; back up the stopped door and upgrade all nodes.


**Private port-sale notices are available in-game to test:** an ordinary owned-port
buyout saves the seller's notice with ownership transfer, buyer debit, seller
price-plus-treasury payment and treasury clearing. The private message retains
buyer alias, old port name, sector and asking price; it is delivered through the
former owner's inbox/history under the system label The Mercenaries. Buyers,
teammates and other accounts cannot read it. No purchase news is published.
Save **29** adds the typed notice without backfilling previous sales.
[Rules, capacity and validation](research/yt-newspaper/events/PORT_SALE_IMPLEMENTATION.md).

**Planet-creation news is available in-game to test:** successful compact `CREATE`
and confirmed classic planet creation publish `  -  <alias> made a planet: <name>`.
The accepted name and alias are immutable public snapshots, saved with the planet,
sector link and 25,000-credit debit. Rejected, expired, cancelled and failed saves
publish nothing; creation still costs no turns. Save version **28** introduced this
explicit typed event without backfilling existing planets. Private port-sale notices
are implemented separately in save version 29; no public purchase announcements are added. [Rules and validation](research/yt-newspaper/events/IMPLEMENTATION.md).

**Spy triggers and shared visibility are available in-game:** accepted movement,
docking, validated missile/plasma launches and charged unavailable planet queries
advance this login's spies. Fighter transfers and free information reads do not.
Spy, sensor and anti-cloak detections share a private login cache used for attack
eligibility; saved target cloak stays unchanged. Action saves publish reports and
new grants together, with receipts preserving committed storage warnings.
This spy milestone introduced no schema change; that milestone used save **29**. [Rules and validation](research/yt-spies/triggers/IMPLEMENTATION.md).

Broadcast newspaper publication is now available in-game to test. `RADIO ALL`
(or classic computer option 5) previews the public text and sender alias, then
saves one newspaper entry with all private copies. Abort publishes neither.
Direct/team mail stays private. Save version **29** introduced this upgrade for older supported saves
without publishing historical mail; back up the stopped door and update all nodes.
[Publication rules and validation](research/yt-broadcast-radio/IMPLEMENTATION.md).

Bounded plasma launching is now available in-game to test. Use `PLASMA <sector> <quantity>` or classic `+` with 1–64 bolts and fresh confirmation. The shared energy pool follows directed routes, can be redirected by login-local black holes and can damage friendly, cloaked or your own ships and planets. Costs, damage, wreck mines and death/estate cleanup save atomically. Save version **26** introduced explicit plasma death semantics; back up the stopped door and update all nodes together. [Rules and limits](research/yt-plasma/IMPLEMENTATION.md).

Mercenary plasma sales are removed historical behavior, not an unfinished DOS 3.6
feature: the mother ship was added in 3.3 and removed in 3.4. The 3.6 Mercenary
home planet is a capture target; plasma comes from planetary stocks. See
[acquisition research](research/yt-mercenary-plasma/RECOVERY.md).

### Playable feature overview

The current Go game has the following features available to test. This is not a
claim of complete DOS parity or live BBS acceptance; see
[validation evidence](evidence/VALIDATION.md) for tested environments and limits.

| Feature area | Available to test |
|---|---|
| **Seasons and persistence** | Saved players and ships, reconnects, daily turns, production and banking interest, bounded super-planet awards, inactive dead-account retirement, plague and civil war; confirmed Genesis endgame, atomic universe reset, public winner history and old-login guards. |
| **Navigation and trading** | Sector movement, adjacent sensors, cloak detection and recharging, login-local anti-cloak, danger-scanner warnings, confirmed emergency warp and autopilot, bounded black-hole arrivals, path finding, avoid lists, cargo trading, Earth purchases, paid lottery, port buyouts and treasury collection. |
| **Planets and teams** | Planet creation, naming, production, banking, investment, cargo and weapon transfers, garrisons, confirmed thruster transport and forced landing; The Wanderer's daily relocation/restoration and one-edge transport; team creation/joining, captain controls and shared planet access. |
| **Combat** | Confirmed planetary ground assaults and ship fighter attacks, routed missiles and retaliation, confirmed plasma launches with bounded black-hole routing, planetary bombardment and destruction, sector-fighter deployment/recovery, reinforcement, breach combat, surrender and escape; death, loot, port settlement, replacement ships and minefields. |
| **Mercenaries and Xannor** | Mercenary bribery/recruitment, tax-funded hiring, daily routes, desertion and base restoration; Xannor HQ/home restoration, reclaim battles, bounded mobile groups, combat aftermath and ship-bound revenge. Direct Xannor fighter casualties can earn capped turn bonuses; HQ victories award up to 1,000,000 exact credits and publish a victory notice. |
| **Computer and communication** | Rankings, commerce and planet reports, planet/port finders, trading forecasts, direct/team/broadcast radio and message history; spies report mines, planets, defenses, ships and login-local disruptions. Newspaper coverage includes logins, planet/team creation, combat outcomes, daily events, HQ victories and confirmed public broadcasts. |
| **Presentation and door sessions** | DOS-style menus, ANSI/CP437 or plain text, compact commands, local play and Door32 sessions. Exit music is enabled for detected SyncTERM/CTerm terminals. |

**Multi-caller simulation completed:** six concurrent simulated BBS callers played
through Door32 processes to a configured 20-port Genesis victory, including
trade, contested buyouts, private/team/public radio, disconnects and real session
expiry. Pending old callers were rejected even after player IDs and initial ship
generations were recreated. The campaign found and fixed a deadline-input issue:
expired reads now report session expiry and reject late input. Forced termination
after carrier loss fails the campaign. A committed black-hole arrival that consumes
all turns during movement or login/reconnect can restart the entire disposable
world only when its saved balance and final sector match the committed receipt.
Startup output is retained with the action log. Retries are bounded to three attempts with
all evidence retained; timeouts, invariant failures and abnormal exits still fail.
Per-node stderr is captured separately. The exact Linux PTY hangup diagnostic
`write /dev/stdout: input/output error` is accepted only after deliberate carrier
loss and natural exit; unexplained nonzero exits and forced stops still fail.
Session-expiry and ended-season checks inspect the separately captured error and
exact exit status, alongside unchanged-save assertions.
The full validation job allows 60 minutes so expanded evidence and terminal checks can
finish, including runner cleanup; every validation command remains enabled.
[Findings, captures and reproducible driver](evidence/MULTICALLER_DOOR_CAMPAIGN.md).

### Not shipped yet

- Remaining random-event and exact DOS RNG/numeric parity.
- Additional unconfirmed spy command paths and character-level DOS editor wrapping/backspace parity.
- Exact general DOS maintenance and DOS save import/export, plus complete MBF arithmetic, other RND variants and unresolved rule parity. The bounded playable `qb36-v1` generator is implemented.

See [Play locally](#play-locally) for commands and the feature sections below for detailed rules and current limits.

## Season administration

See the [sysop save and data guide](docs/SYSOP.md) for live exports, stopped-door
backups, archive extraction and validation, restoring or moving a game, identity
mappings, upgrades and rollback. DOS save import/export remains unsupported.

Export a consistent, private snapshot without changing play:

```sh
./bin/yt -data data -season-export /secure/backups/season-1.json
```

To end a season administratively, name its exact current number and a new archive
path. This command removes all current players, teams, assets and messages and
creates a fresh universe. It records **administrative reset; no winner** in
`SEASONS`, preserves earlier season results, sector count, Genesis threshold and
lottery quota, and ends old logins through the season guard. The archive is saved
and synchronized before the new world is committed under the existing world lock.

```sh
./bin/yt -data data -admin-reset 1 -season-export /secure/backups/season-1-before-reset.json -seed 77
```

The expected season number must be positive (explicit zero is rejected) and prevents
an old command from resetting a later season. Administrative resets also support
eight-sector test worlds; faction homes are created only where capacity permits,
while player-triggered Genesis retains its required-home checks.
Existing files and symlinks are never overwritten. The destination directory must
already exist. A reset cannot be combined with play, initialization or maintenance.
The seed defaults to 36; choose a new seed to change the generated layout.
History remains bounded to 128 completed seasons; export does not clear that limit.

Archives contain the complete validated world, including private identities, mail,
team credentials and assets. Keep them in a private backup directory; do not publish
them. Files are created with owner-only permissions on POSIX. Archive format 1
contains `Exported`, `World`, and `WorldSHA256` (SHA-256 of the compact JSON World
value). It is a consistent snapshot, not a continuous backup: ordinary export may
be followed immediately by further play. This command also exports retained public
season results, but cannot reconstruct full worlds already discarded by Genesis.

An archive may remain if reset fails after export. Inspect the current season
before retrying with a new filename. A durability warning explicitly says the reset
committed: do not repeat it. Stop every node before restoring a backup. A full
rollback requires extracting the archived World into world.json using the matching
binary and restoring all nodes together; it discards subsequent progress and may
reuse an earlier season number, so no old process may remain connected. There is no
automatic archive import or public archive hosting command.

Validation: `python3 scripts/smoke_season_admin.py` exercises export, checksums,
reset, conflicting flags, archive collision and stale reset rejection using a
disposable world. Go tests cover concurrent resets, private snapshot fidelity,
old login invalidation, history/settings retention, migration and committed
storage warnings. Native Windows crash durability and live BBS acceptance remain
separate checks.

## A little history

Yankee Trader is Alan Davenport's text-based BBS space strategy game, combining
exploration, trading and warfare. Its roots are in the Trade Wars 2 code base:
following Chris Sherrick's first Trade Wars in 1984, Davenport released Trade
Wars 1000 in 1987. The game took the Yankee Trader name in 1989, and its final
DOS release, version 3.6, arrived in 1994.

[Zharous's Yankee Trader strategy guide](https://yt.starflt.com/22-2/) records
that history and reports that Davenport's original QuickBASIC source was lost.
This project reconstructs the game in Go using the preserved DOS distribution
and captured behavior as references.

## DOS-style startup

The default interface adapts the preserved DOS title and opening art with
Resurrection branding, and reproduces the new-player
alias confirmation, instructions choice, ship-information pause, sector display
and first command menus. Use an 80×25 ANSI terminal for the recovered colors and
layout. Local terminals receive UTF-8 box characters; ANSI BBS callers receive
raw CP437. Door32's emulation field selects the remote display; `-ascii` forces
plain text. No terminal-size probes are required.

Press a key at the title, then a separate key after the opening artwork. Each
page stays visible until its own keypress. New players enter an in-game alias (Enter uses the
Door32 real name, or the local name), confirm with `Y`, and choose whether to read
the original instructions. Press a key after ship information. At the main
prompt, Enter redisplays the sector, `?` shows the original two-column help,
`C` enters the ship's computer, and `Q` asks for confirmation. Commands finish
with Enter and can be stacked with semicolons. A trailing `/` saves a command
line for Ctrl-R replay; `/R2` through `/R20` repeat a command.

In this interface `L` follows DOS and lands on a planet; `LOOK` displays the
sector. The compact interface keeps its existing `L` look binding. Use
`-compact` to skip the startup screens and retain the prior command workflow.
The computer connects options 2 (port report), 3 (autopilot), 4 (player/team rankings), 5 (send radio), 6 (message history), 7 (avoid slots),
8 (Galactic newspaper), 9 (planet report), 10 (path finder), 11 (your deployed sector fighters),
12 (port treasuries), 13 (your planets), 14 (nearest ports), 15 (active spies), 16 (port pairs),
and 17 (adjacent-port trade forecasts) to the implemented game rules.

The original menus and manual include features still under reconstruction.
Selecting an unavailable action says so; danger-scanner status reflects the installed hardware. Ship balances and inventory come from the current Go world,
including its existing deliberate differences from DOS starting equipment.
The startup screens identify this project as Yankee Trader: Resurrection
0.1.0, say “Original game by Alan Davenport” and “Based on Yankee Trader
Version 3.6,” and link to the
[GitHub repository](https://github.com/robbiew/yankeetrader). No registration
code is required. Original DOS artwork remains preserved in the archive.

See [startup evidence and limits](research/yt-startup/RECOVERY.md) and the
[title](evidence/startup/title.png), [ship information](evidence/startup/info.png),
and [main menu](evidence/startup/help.png) captures.

## Play locally

From the repository directory, build the game, create a world, and start a local
session (see [Build and validate](#build-and-validate) for prerequisites):

```sh
go build -o bin/yt ./cmd/yt
./bin/yt -data data -init
./bin/yt -data data -local Player
```

On Windows, build with `-o bin/yt.exe` and use `.\bin\yt.exe` in place of
`./bin/yt`. Replace `Player` with your local player name. For later sessions,
run only the local-play command with the same name and data directory.

For a separate new world, run `./bin/yt -data another-world -init`. Initialization refuses to overwrite an existing world; skip that step if you already have one. `-local` is for trusted local play; do not give remote callers control over that flag or the data directory. The data files live in `data`, separately from the DOS game. Every successful action saves before its result is displayed. Quitting or disconnecting never restores spent resources or turns.

To try the recovered economy in a separate new world:

```sh
./bin/yt -data dos-economy -init -dos-ports -seed 36
./bin/yt -data dos-economy -local Player
```

`-dos-ports` is initialization-only. Port locations, names, prices and acquisition
costs differ from the default world; use the commerce report before trading.
Existing worlds cannot be switched by passing this flag on login or maintenance.
Both season reset paths retain the saved choice. Add `-dos-warps` at initialization
to use the recovered warp rules too. This is bounded generation-rule parity work,
not a claim of exact DOS universe or `.DAT` save compatibility.

Try this route to buy a fighter, buy five ore at sector 2, and sell it at sector 3:

```text
P; EQUIP fighters 1; M 2; P; BUY ore 5; M 3; P; SELL ore 5; I; Q
```

For the default uniform-port world (without `-dos-ports`), the expected starting-player result is 1,005 credits, 26 fighters, no cargo, sector 3, and 495 turns. Terminal commands are case-insensitive and can be stacked with semicolons.

| Command | Action |
|---|---|
| `?` | Help |
| `I` | Ship information |
| `LOOK` | Current sector, warps, and port (`L` in compact mode) |
| `M <sector>` | Move through a listed adjacent warp; one turn |
| `S` / `SCAN` | Scan adjacent sectors: ports, planets, ships and outgoing warps; free |
| `D` / `DROP [quantity]` | Place carried mines in the current sector outside sectors 1–7; fresh Y confirmation; no turn cost |
| `PATH <from> <to>` | Display a shortest directed warp route and turn cost; free |
| `AUTO <sector>` | Plot from your current sector, confirm with Y/N, then move one turn per hop |
| `AVOID` | Show your saved routing preferences; free |
| `AVOID <slot> <sector>` | Set slot 1–30; sector 0 clears that slot; free |
| `P` | Dock and display current prices; one turn |
| `T` / `TEAM` | Team menu: create/join, roster/resources, leave and captain controls |
| `B` / `ACQUIRE` | Buy the current port after explicit `Y` confirmation |
| `TREASURY` / computer `C`, `12` | Report personally owned port balances |
| `PORTREPORT [sector]` / computer `C`, `2` | Remote ordinary-port commerce report; free |
| `PLANETREPORT [sector]` / computer `C`, `9` | Remote planet report; missing planet or hostile sector defenses costs one turn and advances spies |
| `RANK` / computer `C`, `4` | Rank players and teams from current assets and save all player scores; free |
| `RANK OLD` / computer `C`, `4`, `O` | Stored scores with current aliases, teams and port counts; free |
| `BATTLES` | Your private Xannor battle history; last 32 reports retained |
| `NEWS [TODAY|YESTERDAY]` / computer `C`, `8` | Read retained public news in five-entry pages; free |
| `HIRE <sector> [sector ...]` / Earth option `9` | Hire up to three spies per login, 333,000 credits each; choose every starting sector |
| `SPIES` / computer `C`, `15` | List this login's current spy hunt locations; free |
| `INTEL` | Read this login's last 30 intelligence reports in five-report pages; free |
| `RADIO [alias, player number, TEAM or ALL]` / computer `C`, `5` | Compose a private message or confirmed team/ALL copies, then Send or Abort; free |
| `MESSAGES` / computer `C`, `6` | Your sent and received message history; free |
| `INBOX` | Unread received messages; free |
| `MYPLANETS` / computer `C`, `13` | List personally owned planets and sectors; free |
| `NEAREST [all\|own\|team\|enemy\|unowned]` / computer `C`, `14` | Nearest accessible ordinary ports, with directed warp distances; free |
| `NEAREST <ore\|organics\|equipment> <buy\|sell>` | Filter nearest ports by **your** trade action |
| `PAIRS` / computer `C`, `16` | Reachable adjacent-port pairs with complementary goods and a directed route back; free |
| `PROFITS` / computer `C`, `17` | Trade forecasts for your current port's outgoing adjacent ports; free |
| `$` / `COLLECT` | Collect all personal port balances from any sector |
| `BUY ore 5` / `SELL ore 5` | Trade cargo in the direction the port supports |
| `EQUIP fighters 1` / `EQUIP scanner 1` / `EQUIP cloak 10` | Buy Earth equipment; cloak is in whole percentage points |
| `ANTICLOAK` | Confirm a 500,000-credit activation for the current login while docked at Earth |
| `W` / `WARP` | Confirm a random emergency warp and its recharge/meltdown risk |
| `LEAVE` | Leave port |
| `Q` or Escape | Exit |

`RANK` publishes current player scores together, using supported ship assets,
actual ordinary-port ownership and personally deployed sector fighters. Team
rankings sum current members. `RANK OLD` reads the last published score values;
new accounts can show zero until an update. Dead accounts show zero, ties use
account/team order, and percentages use each list's leader. Rankings work with
zero turns and cost no assets. Reports show public totals, without private
account or planetary-bank fields.

Missile retaliation uses these published scores. Scores refresh on an explicit
updated ranking request, clean logout, and successful once-per-UTC-day
maintenance. An abrupt disconnect, declined logout or expired/stale session
does not trigger logout publication.
An installed danger scanner contributes its 250,000-credit asset value to live
scores; stored-score publication keeps the existing timing above. Individual scores
cap at 9,000,000,000,000,000 points. Other unsupported equipment, NPC rankings and
historical scoreboard files remain outside this slice. See [scoring rules,
cache timing and validation](research/yt-rankings/IMPLEMENTATION.md).

Direct radio accepts one printable ASCII line of up to 74 characters. Confirm a
recipient alias or player number, enter the body, then choose `S` to send or `A`
to abort. Message text and Send/Abort are separate inputs: semicolons and a
trailing slash in the body stay literal. Sender and recipient can read saved
history in five-message pages; other players cannot. Aliases are saved with the
message, and account history survives ship replacement. Sending costs no turns
or assets and works for offline recipients.

Unread messages appear at login and between commands, up to five per check;
`INBOX` reads the rest. A message becomes read only after successful terminal
output. A disconnect or simultaneous sessions can cause a repeated notification;
read messages remain in history, and senders receive no read receipts. The world
retains at most 4,096 messages and refuses new sends at capacity without deleting
history. `RADIO TEAM` (or `TEAM` at computer option 5) confirms the current roster
and sends one private copy per member, including you. All copies save together;
if membership or team details change while composing, confirm again. Each copy
has its own unread flag and archive slot. Former members retain their addressed
copies; new members cannot read old team mail. Team sending uses the existing
version-26 mailbox format without a migration. [Team rules, DOS evidence and
validation](research/yt-team-radio/IMPLEMENTATION.md). The bounded multiline editor is described below. Evidence checks compare exact decoded
mailbox fields, preserve scanner equipment and anchor root auxiliary files and
login identities to the source fixtures, with rehashed corruption controls.
`RADIO ALL` (or `ALL` at computer option 5) confirms all current active accounts,
including you. Its final preview explicitly warns that the literal text and your
alias also become public in the Galactic Newspaper. Send atomically saves every
private copy and one public entry; Abort saves neither. Offline and dead accounts
receive their own copies; retired and future accounts do not inherit private mail,
but any eligible newspaper reader can see the public entry. Direct/team text stays
private. Each copy has its own unread flag and archive slot; the entire broadcast
must fit the 4,096-message archive. Roster changes require confirmation again.
Public entries share the existing rolling 1,024-event today/yesterday journal.
Receipts report saved copies and publication; committed storage warnings end the
session and remain warnings even if the terminal cannot print the receipt.
Version 27 introduces typed public broadcast news without backfilling old private
copies. Independent radio read flags remain a deliberate adaptation of the DOS
shared delivery counter.
[Broadcast evidence, policies and validation](research/yt-broadcast-radio/IMPLEMENTATION.md).
Native BBS acceptance remains open.

Use `RADIO EDIT <alias, player number, TEAM or ALL>` for the opt-in multiline
composer, or enter `EDIT <recipient>` at computer option 5. Recipient aliases
beginning with `Edit ` retain their complete name after the editor keyword. Enter up to 20
printable ASCII lines of 74 characters; a blank line opens List, Send, Abort,
Continue and Edit. Continue appends to the last line. Edit replaces the first
case-sensitive matching section and asks before keeping it. Abort requires
confirmation. Editor Send opens a complete preview; a fresh final `S` saves all
lines and recipient copies together, including one public newspaper event per
ALL line. Expiry, interruption or a changed recipient snapshot saves nothing.
The one-line composer remains available. Overlong input is rejected rather than
DOS character-level wrapping, and public lines render as separate typed events.
World version 27 is unchanged. [DOS controls, limits and validation](research/yt-radio-editor/IMPLEMENTATION.md).

See [radio scope and validation](research/yt-navigation/RADIO_IMPLEMENTATION.md).

Sensors work even when no turns remain. `AUTO` asks before moving; an empty answer cancels. You can stack the response, for example `PATH 1 3; AUTO 3; Y; I`. Ctrl-X stops autopilot between hops. Every completed hop saves immediately and remains spent after interruption or disconnect. Courses stop if another session changes your position or leaves too few turns. See [navigation recovery and DOS comparisons](research/yt-navigation/RECOVERY.md).

`PATH` and `AUTO` honor your 30 private avoid slots, including the start and destination. For example, `AVOID 1 2` routes around sector 2; `AVOID 1 0` clears that preference. Manual `M` movement and sensors still work normally. Avoid edits cost no turns and persist across logins—an intentional improvement over the DOS session-only list. If a list edit makes a plotted course unsafe, autopilot stops before the next hop and keeps completed moves saved. Existing saves begin with an empty list.

Sensors show actual public sector/ship data. Danger-scanner purchasing and manual emergency warp are implemented below; sector-defense deployment and combat are available as described below. Minefields and safe automatic escape are implemented in the later milestones below. Cloak detection and direct fighter attacks are implemented in the later milestones below. Default worlds start without minefields; non-Earth combat wrecks can create them.

The default planet interface now follows the original DOS landing/report, help and transfer menus, with cyan text, original columns, gray answers and captured warning/receipt colors. Press `L` to land (or create a planet when none exists), `?` for planet help, `D` to redisplay, `N` to rename, `1`–`6`/`9` to take an item, Enter/`A` to take all, `T` to deposit items, `B` for the bank, `$` to invest, `F` to set the planetary garrison, and `L` to leave. Bank and garrison prompts ask for a **final target**, not a transfer amount. Empty bank/investment/garrison inputs cancel; empty take quantities choose the displayed maximum. Planet creation requires purchase and name confirmation. Landed `!` uses planetary thrusters. Denied landing can offer a separately confirmed ground assault; see [movement and ground actions](research/yt-planet-mobility/IMPLEMENTATION.md). See [37 captured planet stages and comparison boundaries](research/yt-planet-screens/RECOVERY.md).

Planet renaming uses the original name/confirmation prompts and colors. Blank names cancel; `N` at confirmation retries; Enter accepts. Names receive DOS word casing/space cleanup and are clipped to 41 characters. Renaming costs no credits or turns and uses the current landing permission, including shared/unguarded access. Reserved names and the final special planet slot remain protected. See [rename rules, 45 DOS captures and comparison boundaries](research/yt-planet-rename/RECOVERY.md).

Port colors, commodity columns, dotted labels, Earth menu spacing, and purchase prompts are checked against 35 original DOS screen captures from ten isolated sessions. The comparisons cover the port body through the current prompt, including Earth redraws, purchases, sales, ownership, full holds, and declined trades. Live timestamps and unsupported-item affordability remain dynamic; startup history, caller/status details, timing, and invalid-input behavior are outside this visual comparison. See [port screen evidence](research/yt-port-screens/RECOVERY.md).

Remote computer reports do not move, dock, land, or bind a trading price. Hostile
sector fighters hide both port and planet reports; only the blocked planet query
spends a turn, and it is refused when no turns remain. A defended foreign planet
shows just its name and ground forces. Unowned, unguarded, personally owned, and
currently shared team planets expose full reports. Full reports project current
production and interest without changing stored stock or money. The personal
planet finder excludes teammates' assets. Remote Earth equipment reports remain
unavailable; dock at Earth for its shop. See [report rules and validation](research/yt-navigation/REPORTS_IMPLEMENTATION.md).

Nearest-port and trade-route reports honor your avoid list and port-report
access. `B`/`S` in nearest results means **you buy/sell**. Team filters include
your own ports and current teammates' ports; enemy filters exclude both and
unowned ports. Results include projected quotes and whole-unit stock/demand.
Earth's equipment service is excluded. Reports also work with no turns left.

`PAIRS` and `PROFITS` show one positive commodity combination per port pair,
including approach, outward and return warp counts. A return route can require
several warps; a pair with no route back is omitted. The spread is the sum of
the two per-unit price differences, independent of cargo holds. It does not
promise ship earnings or account for cash, docking turns, or later changes in
prices and stock. Mines and defenses can still interrupt travel. Long reports
page four entries at a time; Enter shows more and Q stops. Each page refreshes
current access and prices, so changing state can change the remaining results.
See [trade-report scope and validation](research/yt-navigation/TRADE_REPORTS_IMPLEMENTATION.md).

In the default DOS-style interface, `P` opens Earth's numbered shop or the current port's cargo report. Earth keeps the original item numbers: `1` cloak energy, `2` holds, `3` fighters, `4` paid lottery, `5` danger scanner, `6` anti-cloak activation, `7` ground forces, `8` shields, `I` ship information, and `0` leave. Item `4` buys a five-credit, six-digit lottery ticket after a fresh Y confirmation; blank at ticket entry cancels. The default quota is five plays per UTC date, preserved across reconnects and replacement ships. Compact callers dock and use `LOTTERY [six digits]`. The saved receipt reports the actual draw, matches, fee, prize/cap adjustment, balance and plays remaining. An empty ordinary equipment quantity cancels that purchase. Cloak energy uses its displayed affordable/missing default on blank input; zero cancels. Selecting item `5` buys one scanner for 250,000 credits immediately, without a quantity prompt; duplicate or unaffordable purchases do not charge. The shop refreshes your credits after each saved purchase.

Ordinary ports offer commodities in ore/organics/equipment order. Enter a quantity (`0` skips), then agree with `Y` or Enter; `N` declines. Enter at the quantity prompt selects the displayed maximum, limited by current stock/demand, cargo space, cargo aboard, and credits. Invalid quantities skip that commodity without a transaction. Docking costs one turn, including a visit with no purchases. A replaced or expired docking session cannot complete an old prompt. `-compact` keeps the explicit `BUY`, `SELL`, and `EQUIP` workflow.

Other cargo names are `organics` and `equipment`. Earth sells `holds` (500 credits), `fighters` (100), `shields` (50), `forces` (750), and one `scanner` (250,000). Use `EQUIP scanner 1` in compact mode. Quantities must be whole, positive numbers. Cargo capacity is shared across all three cargo types. Earth equipment costs remain an economic sink.

## Run as a BBS door

Use the directory containing that node's Door32 drop file and the same absolute data directory on every node:

```sh
/path/to/yankeetrader/bin/yt \
  -data /path/to/yankeetrader/data \
  -drop /path/to/node1 \
  -system mybbs
```

`-system` is a stable namespace for the BBS. Identity uses this value plus the positive user-record number on Door32 line five; alias is display information. Changing an alias does not create a fresh ship. Keep the system value stable. Local identities are separate from Door32 identities.

GoDoors handles standard I/O on macOS/Linux and inherited Door32 sockets on supported Windows hosts. Linux/macOS sessions accept unused Door32 communication handles such as `-1`, using the BBS-provided standard I/O streams. Rebuild older binaries with the GoDoors revision below to pick up this startup fix. The door honors the drop file's remaining session time (1–1,440 minutes). The DOS-style interface supports ANSI/CP437 and plain text; `-compact` retains the original printable-ASCII command interface. Neither requires terminal probing.

Door sessions never depend on cursor save/restore (neither `ESC 7`/`ESC 8` nor `CSI s`/`CSI u`). Some terminals and BBS stdio bridges drop restore, which used to scramble the opening art and leave typing stranded after the prompt's live clock (reported from SyncTERM through a stdio-mode door). The opening art no longer contains save/restore. Remote callers' prompt clock is redrawn using only carriage return and relative cursor-forward moves, and it pauses once a typed command reaches the right margin. The local console also keeps its status-row clock. `scripts/smoke_prompt_clock.py` drives a Door32 stdio session against a terminal model that honors no save/restore at all.

Native macOS PTY and simulated BBS Door32 stdio sessions over localhost TCP were
exercised, including multiple concurrent callers through victory. This is not
acceptance under a production BBS or a native Windows inherited socket.
[Campaign results and limits](evidence/MULTICALLER_DOOR_CAMPAIGN.md). Test the
target BBS transport before deployment.

## Daily maintenance

[Independent maintenance calendar controls](research/yt-maint/CALENDAR_CONTROLS.md)
now cover next-day, New Year, leap-day and non-midnight initial worlds. Twelve
original-DOS runs support 24 complete six-file comparisons with zero byte
mismatches. Bounded noon integer-minute and unnamed-lottery-candidate branches
are modeled; exact host refill witnesses are validated. This remains research,
with no gameplay/save-35/source-fingerprint changes or arbitrary-world claim.


[Supplemental runtime streams](research/yt-maint/RNG_TRACE.md) preserve five
historical instrumented captures with 127,618 checked seed/draw events and
explicit probe-induced differences against independently hash-pinned native worlds. These complement the newer first-hit,
sequencing, chronology and record-replay research below; they do not replace its
native controls or establish additional gameplay/save compatibility.


**Maintenance seed boundaries are now measured:** 151 terminating DOS probes
and six untouched paired runs recover entry `RANDOMIZE -TIMER`, two positive-TIMER
helper reseeds and a selected first-hit Wanderer draw chain. Raw states preserve
zero residues and the old low byte.
[First-hit evidence and timing limits](research/yt-maint/RNG_FIRST_HITS.md).

**Repeated maintenance draws are now measured for the initial-world fixture:**
independent counters cover all 43 literal RND sites. Nine execute, totaling
25,891 draws; the two helper paths reseed 41 and 19 times. Nth-hit state and caller
observations distinguish the four-draw shrinking-bound helper from occupied-sector
candidate retries. An explicitly synthetic occupied-destination control adds one
Wanderer selection attempt. Untouched comparisons, retained raw records and
independent corruption checks bound these findings. This is the historical
sequencing scope; later bounded replay closes selected post-maintenance outputs.
Arbitrary-world draw chronology and general MBF parity
remain open, and gameplay/save format 35 are unchanged.
[Sequencing evidence, diagnostic limits and portable checks](research/yt-maint/RNG_SEQUENCING.md).

**The initial-fixture scan ledger is now joined:** 332 additional controls identify
mobile groups 2–20 and cached player slots 2–51. The ordinary interception phase
consumes 496 fifty-player scan blocks, including eager draws for excluded group
20. Measured state bridges join helper reseeds, candidate/interception scans,
twenty desertion draws and the lottery gate. Sampled old/next-sector arguments
match directed original warp edges. These bounded observations do not claim
496 successful encounters or full post-maintenance record replay.
[Phase chronology, native evidence and limits](research/yt-maint/PHASE_CHRONOLOGY.md).

**A bounded maintenance record model is now available for research:** it derives
all sector, planet, configuration and inactive-player bytes, plus all five
auxiliary files, from before-inputs, original constants and measured clock values.
The new host-clock profile now matches **all six untouched output files exactly**
(570,059 bytes) across six fresh controls and four historical targets. It derives
all TIMER inputs from paired host observations without adding guest instructions;
the original transition is at port 607. The earlier guest-instrumented profile
and its four-byte timestamp discrepancy remain retained without masks or
target-derived correction. This closes the bounded clock gap for one initial
world/date/emulator recipe, not arbitrary maintenance prediction or a
playable/save-35 change. [Clock-neutral evidence, complete comparison and limits](research/yt-maint/CLOCK_NEUTRAL.md).
The [historical record-model report](research/yt-maint/RECORD_REPLAY.md) remains
reproducible; its entry capture command emits all four required controls,
including the raw startup TIMER seed witness.

**The clock/date matrix now extends that research:** all 48 DOS controls agree
within eight explicit recipes, including actual midnight rollover and the native
`24:00:00` scoreboard string. Before-only replay is exact for seven recipes;
the eighth seed exposed a mobile-Xannor/Wanderer interaction. The explicit
[Wanderer encounter replay](research/yt-maint/WANDERER_ENCOUNTER.md) now closes
that selected gap: all eight recipes / 864 individual file comparisons match,
plus 108 comparisons against six fresh untouched/observed controls. Fourteen
separate diagnostics confirm shared pursuit, draw ordering and 6923 casualties;
public news and the 307700 score match the 3077 saved survivors. Earlier strict
replay reports remain reproducible. This is research, not a new gameplay feature
or save-format change. Per-writer dates/clocks, saved-base-year day366
on Jan1,2027, and an extra inactive-player lottery draw are retained rather than
normalized away. [Clock/date evidence and remaining encounter work](research/yt-maint/CLOCK_MATRIX.md). Fresh clock/date captures use the bounded controller; retained observations continue to authenticate the original acquisition source. The preserved acquisition source remains byte-exact across Git newline-conversion settings. Independent fresh-world calendar controls and the same-saved-world clock matrix are both retained.

**Occupied placement and faction-cache boundaries now have additional research:**
[the twelve-recipe matrix](research/yt-maint/PLACEMENT_COLLISIONS.md) retains
72 unchanged-executable full runs and 12 separate early cache probes. All six
outputs agree across each recipe's observed/unobserved runs. Source-qualified
placement replay matches 432 accepted-target checks, and a before-only cache
primitive matches all 480 captured location/force fields. Multiple rejections,
fractional/negative/raw-zero gates and duplicate/foreign-owner pointers are
explicitly bounded. The [complete collision-record replay](research/yt-maint/COLLISION_RECORD_REPLAY.md)
now integrates those twelve fixtures: 216 complete comparisons / 1296 files are
byte-exact, and 2265 independent raw RNG witnesses agree with calculated states.
Captured old RNG states and cache probes are not synthesis inputs. Gameplay and
save 35 are unchanged; arbitrary evolved-world maintenance remains separate.

[Active-planet and foreign-route controls](research/yt-maint/OCCUPIED_ROUTE_CONTROLS.md)
now retain ten fixtures / 60 full DOS runs with six-mode output equality. Named
occupied planets, prior economy RNG advancement, ground defense and actual
foreign-force losses/score receipts are independently verified across 360 files.
The [complete before-only profile](research/yt-maint/OCCUPIED_RECORD_REPLAY.md)
now matches 180 complete comparisons / 1080 files with 1872 independent RNG-state
checks. The separately captured convergence/evolved chain is linked below; gameplay
and save 35 are unchanged.

[Final convergence and an exact three-day chain](research/yt-maint/CONVERGENCE_CHAIN.md)
now retain 18 full runs, 12 early-cache probes and 144 exact six-file inheritance
links. Eighteen final pointers share one physical force, loaded once on the next
day; all 480 source-owned cache cells are independently checked. The
[before-only replay of the evolved chain](research/yt-maint/EVOLVED_CHAIN_REPLAY.md)
now matches 54 full comparisons / 324 files, with modeled-only six-file handoffs,
501 RNG-state audits and all captured cache fields predicted.
[Evolved clock/date controls](research/yt-maint/EVOLVED_CLOCK_CONTROLS.md) now add
48 full runs and 288 exact inherited-file links, selecting mine and positive-ground
NPC defenses. Their [separate before-only replay](research/yt-maint/EVOLVED_CLOCK_REPLAY.md)
now matches 144 complete comparisons / 864 files and 1278 independent RNG-state
audits, including modeled-only handoffs, exact mine residues and casualty-backed
news/scores. Gameplay and save 35 are unchanged.

[Evolved foreign-force and surviving-combat controls](research/yt-maint/EVOLVED_COMBAT_CONTROLS.md)
now retain 48 full DOS runs / 288 exact six-file handoffs. They preserve a surviving
Mercenary offense, its later stale Xannor pointer, continuing neutral-planet defense
and extinct/neutral controls. All eight stages agree across six modes. The
[before-only combat replay](research/yt-maint/EVOLVED_COMBAT_REPLAY.md) now matches
144 complete comparisons / 864 files and 1242 independent RNG-state audits.
It derives actual Mercenary casualties, repeated activation and stale pointers;
gameplay and save 35 are unchanged.

[Longer survivor handoffs](research/yt-maint/SURVIVOR_CHAIN_CONTROLS.md) now extend
four actual November 4 states through November 5/6: 48 full DOS runs, 288 exact
six-file links and eight equal six-mode output groups. They select later foreign
defense and Wanderer attacks, preserve mines/raw pointers and retain a distinct
news/score clock. Their [before-only five-day replay](research/yt-maint/SURVIVOR_CHAIN_REPLAY.md)
now matches 144 complete comparisons / 864 files and 1182 new-stage RNG-state
audits, using only modeled parents. Surviving-defender NEWS damage must equal
actual physical loss; inflated positive counters are rejected. Gameplay and save
35 remain unchanged.

[Gateway hazard and fighter-pickup controls](research/yt-maint/GATEWAY_HAZARD_CONTROLS.md)
now retain 72 complete DOS runs / 432 output files across six explicit two-day
fixtures. Independent audits verify 396 unchanged input links and 36 declared
YTDATA transformations, exact six-mode outputs, mine-before-pickup and
defense-before-pickup outcomes, fatal mine residue and day-two production after
the minimum-rate clamp.
Their [before-only gateway replay](research/yt-maint/GATEWAY_HAZARD_REPLAY.md) now
matches 216 complete comparisons / 1296 files and 1962 independent new-stage
RNG-state witnesses. A pure declared transformation is applied once to the modeled
November 4 parent; both children then use complete modeled handoffs. Mine damage,
guard combat, pickup, minimum-rate clamps and exact public receipts are derived
without captured-state seeds. Gameplay and save 35 remain unchanged.

Unsupported gateway pickup totals are rejected before any stock or force bytes
change; supported transfers preserve the exact source-specific stock zero.

[Occupied-origin departure and friendly-force controls](research/yt-maint/DEPARTURE_MERGE_CONTROLS.md)
now retain 96 primary two-day DOS runs plus six supplementary controls and two
explicit failed-observer diagnostics. They select holds, departures, silent
friendly merging and a larger Wanderer-stock pickup. Fourteen of sixteen stage
groups are six-mode equal; two retain disclosed port-clock/supply differences,
with matching NPC outcomes and other five files. A strict persisted exit receipt
fixes the observed acknowledgement race without changing DOS event acquisition.
Their [before-only departure/merge replay](research/yt-maint/DEPARTURE_MERGE_REPLAY.md)
now predicts both children from a modeled parent and the declared fixture edits.
All 48 direct observed-source comparisons / 288 files and 2505 new-stage RNG witnesses
match. Across all target modes, 270 of 288 complete comparisons are exact; 18 retain
the disclosed port-clock differences with no masked bytes. Departure, silent
merging, larger Wanderer pickup and its bounded fractional discard are derived.
Gameplay, dependencies and save 35 remain unchanged.

[Fighter-stock conversion controls](research/yt-maint/STOCK_CONVERSION.md) now
retain 72 complete original-DOS runs across twelve exact binary stocks. All six
output files match across each fixture's six observation modes. The selected
pickup call floors positive SINGLE stock, including half ties and adjacent values,
clears the whole stock with its original raw zero, and suppresses taking-zero
receipts. Audits distinguish 360 unchanged input links from 72 declared data-only
transformations. Their [before-only replay](research/yt-maint/STOCK_CONVERSION_REPLAY.md)
now computes all twelve fixtures from a modeled parent. All 216 comparisons / 1296
files and 1656 new-stage RNG-state witnesses match. Whole transfer, fractional
discard, original raw clears and public receipts are derived before targets open.
All 54 new tests pass. Historical replay guards, production Go, dependencies,
generation fingerprints and save 35 remain unchanged.
[PR #106](https://github.com/robbiew/yankeetrader/pull/106) is verified merged into main.

[Friendly-force and planet-stock controls](research/yt-maint/FRIENDLY_STOCK_CONTROLS.md)
now retain 48 complete original-DOS runs / 288 output files, six-mode equal in all
eight cases. A held friendly garrison is included once with incoming force and
whole stock; taking text uses the combined pre-stock count, while capture text is
suppressed. Empty/subunit stock clears silently. Planet governors remain intact.
PR #107 and its separate replay PR #108 are merged into main.
Their [before-only composition replay](research/yt-maint/FRIENDLY_STOCK_REPLAY.md)
now derives the four-day modeled chain, fifteen declared edits, held garrison,
combined receipt actor, stock floor/clear and governor preservation. All 144
complete comparisons / 864 files and 1104 new-stage RNG-state witnesses match;
28 new tests pass. Historical guards, gameplay, dependencies and save 35 remain
unchanged.

[Departed-garrison stock controls](research/yt-maint/DEPARTED_STOCK_CONTROLS.md)
add 48 original-DOS runs / 288 output files with six-mode equality. Four/eight-second
controls select departure before pickup, followed by later same-scan activations;
two/six-second controls hold. The incoming force picks up stock without absorbing
the departed 37 fighters. Empty/subunit stock clears silently.
Their [before-only replay](research/yt-maint/DEPARTED_STOCK_REPLAY.md) now
derives departure, repeated activation, exact actor/capture text and all six
files from a modeled parent before targets open. All 144 comparisons / 864 files
and 1152 new-stage RNG witnesses match; 34 new tests pass. The public ledger
requires every next occupied descending sector and rejects a coherently
truncated scan even when force totals and scores still agree. Held-garrison replay
PR #108 is merged into main as `dcc04c23`. No gameplay, save 35, dependency or
source-fingerprint changes. The [neutral-owner and mine-stock controls](research/yt-maint/NEUTRAL_OWNER_STOCK_CONTROLS.md)
now retain 36 complete native runs / 216 output files, six-mode equal in six cases.
Positive neutral physical fighters transfer once to the arriving Mercenaries;
mine damage reduces the incoming force before entering fighters and stock add.
The four-second friendly-mine case retains changed Xannor activity and a separate
37-fighter survivor at sector 356. Twenty new provenance/composition tests pass.
Their [before-only replay](research/yt-maint/NEUTRAL_OWNER_STOCK_REPLAY.md) now
derives all six cases from the modeled parent before targets open: neutral
transfer, incoming-only mine losses, stock, Xannor changes and repeated moves.
All 108 comparisons / 648 files and 855 new-stage RNG witnesses match; 40 new
replay tests pass. The independent publisher also enforces original governor
bytes and the exact spent-mine subtraction zero, rejecting numerically equal
residue corruption. No Go, dependency, source-fingerprint or save 35 changes.



[Defender-survival stock controls](research/yt-maint/DEFENDER_STOCK_CONTROLS.md)
now retain 48 original-DOS runs / 288 output files, six-mode equal across four
fixtures and their unchanged next-day handoffs. Mercenary attacks lose while
Xannor defenders survive, including a one-fighter balanced-case survivor. Stock
is not picked up and grows through ordinary next-day production. Seventeen new
tests verify the exact losing receipt, preserved raw bytes and complete handoffs.
Their [before-only replay](research/yt-maint/DEFENDER_STOCK_REPLAY.md) now derives
the five-day chain before target reads: fatal offense, actual surviving defenders,
the exact losing receipt and uncollected next-day stock. All 144 comparisons /
864 files and 1074 new-stage RNG witnesses agree; 39 new tests pass. The publisher binds
battle entry/exit to source clocks, helper progression and final RNG witnesses,
rejects coherent casualty/resurrection forgeries, and preserves the inherited
raw departure pair on the extinct next day. PR #112's owner/mine replay remains separate. Gameplay/save 35 unchanged.

[Original initial-maintenance controls](research/yt-maint/INITIAL_MAINTENANCE.md)
now retain eight copied-original DOS runs, including direct initializer launches,
before/after split boundaries, exact repeats and bounded clock changes. They
verify NPC bootstrap, record/side-file changes and clock-sensitive outcomes;
exact maintenance RNG/MBF replay remains research. This changes no gameplay,
`qb36-v1` source fingerprints or save 35. Portable evidence and 20 corruption checks
run in CI, including independent launch-command and applied CPU validation; the playable profile retains its documented modern bootstrap.


```sh
./bin/yt -data data -maint
```

Port purchases cost `floor(sum of production / 10) + 1` credits and no turns. Buying an owned port pays its former owner the price plus its treasury, then clears that account. Earth cannot be bought. Confirmation defaults to cancellation and expires after five minutes; changed ownership, location, price or funds rejects the sale. Ownership changes invalidate docking agreements in the sector. Treasury collection is free, remote and personal; insufficient credit capacity rejects the entire collection. See [ownership evidence and deliberate fixes](research/yt-trade/OWNERSHIP.md).

Maintenance runs automatically at login as well. Days use **UTC**. On a new date it updates port supply, taxes ordinary port treasuries by `floor(treasury/10)`, restores players to 500 turns, and invalidates outstanding docking sessions. Repeating the command on the same day, or moving the clock backward, does not repeat daily phases. A missed interval gets at most ten days of port production; missing days do not accumulate extra player turns. Taxes and Mercenary desertion, routes, hiring and base restoration run once when advancing the maintenance marker, not once for every missed day.

Planet maintenance also produces stocks and weapons, grows rates and ground defenses, and pays bank interest. Inactive dead-player retirement runs before production; bounded Mercenary and Xannor actions and the one-shot super-planet lottery follow it. Other remaining daily phases are deferred. Cloak decay follows turn spending, rather than daily maintenance.

## Fidelity and deliberate changes

Implemented rules have links to the recovered evidence:

- Starting 1,005 credits, 25 fighters, 10 holds and 500 daily turns: [initializer evidence](research/dos-validation/RESULTS.md).
- Supply-sensitive cargo prices, quantity limits, demand depletion and owner commissions: [trading recovery](research/yt-trade/RECOVERY.md). Five saved DOS examples are exported in `internal/game/testdata/dos-trading.json` and checked by Go tests. These compare ore cash/cargo/treasury outcomes; they do not claim exact QuickBASIC RNG or floating-point equivalence.
- Port taxes and the repeated-maintenance defect: [maintenance recovery](research/yt-maint/RECOVERY.md).

Default generation retains the established seeded, reachable ring graph and uniform ports with fixed reference prices **20/30/40**. New worlds can independently select recovered map rules with `-dos-warps` and the recovered economy/startup price references with `-dos-ports`. These profiles use the modern seeded Go random stream and documented safety corrections. The separate bounded `qb36-v1` profile selects the recovered source recipe. Default size is 3,000 sectors and 1,000 ports; `-sectors` allows 8–3,000 for small test games. Shields start at zero; shield initialization parity remains an unresolved rule question.

Known defects intentionally fixed here:

- Spendable money is `int64`, preserving one-credit debits at large balances across saves. It never uses MBF single precision.
- Earth cannot have an owner, and equipment spending cannot fund an owner treasury.
- Clock rollback preserves the last production watermark; it never awards ten days of goods.
- Daily phases have an actual persisted guard against same-day repeats.
- Each action loads authoritative state under the world lock. Failed actions commit nothing.
- Dock tokens expire after five minutes and are invalidated by movement, another docking, reconnect, or maintenance. Old sessions cannot apply a previous quote after another session changes the player's position.

Technical limits are 50 active accounts with a 256-identity lifetime archive (IDs are never reused), 1,000 cargo holds, 1 billion units per noncargo equipment category, and 9 quadrillion credits per account. These bounds are explicit prototype constraints, not claims about DOS overflow behavior.

Sector-defense deployment/combat and reinforcement, plus bounded Mercenary daily behavior, are playable. Xannor HQ/home lifecycle and bounded mobile groups are also implemented below. Full RNG/MBF universe integration, DOS save import/export and remaining terminal parity questions are future work. Initializer seeding and selected complete pre-maintenance record replay are now verified research; see the complete replay recovery report. Bounded Genesis resets are implemented below. Their recovered rules are in `research`.

## Storage and recovery

**Save rollback compatibility:** This build uses world version **35**, adding typed QB recipes and repeat-layout resets; version 34 added the opt-in DOS warp generation profile; version 33 added the opt-in DOS port generation/pricing profile; version 32 added the Xannor turn-bonus journal operation; version 31 added extended typed public newspaper events; version 30 added administrative season results without winners and version 29 introduced typed private port-sale notices. It retains public planet-creation and ALL-broadcast newspaper entries, along with explicit plasma death semantics, Wanderer identity, nonreusable planet generations, season epochs, public winner history, lottery replay protection, scanners, NPC history and attributed hazards. Supported version-1 through version-34 worlds upgrade in memory and persist on the next successful update; read-only loading does not rewrite saves or grant assets. Experimental legacy memberships without team metadata and pre-26 saves claiming a plasma death are rejected. Pre-27 saves claiming public broadcast news are also rejected. Pre-28 saves claiming planet-creation news are rejected. Pre-29 saves claiming port-sale system notices or typed sale payloads are rejected. Pre-30 saves claiming administrative reset records are rejected. Pre-31 saves claiming extended news kinds or combat payloads are rejected. Pre-32 saves claiming Xannor turn-bonus events are rejected. Pre-33 saves claiming a port generation profile are rejected. Pre-34 saves claiming a warp generation profile are rejected. Pre-35 saves claiming QB recipes are rejected. January 10 recipes require this updated build; earlier save-35 binaries reject that formerly unsupported date. Older binaries cannot read version 35. Existing maps, ports, prices and supplies are not rerolled by upgrade.

Version 25 introduced The Wanderer's explicit identity in reserved planet slot 1; migration creates no free planet, and eligible restoration allocates a fresh incarnation. Version 24 introduced nonreusable planet generations. Season migration does not reset the world or invent past winner history, and names never infer a faction home or special planet identity. Back up the data directory with the door stopped and upgrade every node together. To revert binaries, restore their matching backup; that discards later progress. Migration preserves existing account assets and history; ordinary later maintenance may retire qualifying inactive dead accounts.

`world.json` is the versioned authoritative save. `world.lock` is a persistent lock-file name backed by an OS lock: process death releases the lock without deleting it. All processes must use the same data directory on a local filesystem. Network filesystems are not supported or tested.

Updates serialize through the lock, validate the complete world, write and sync a temporary file, then replace the save atomically on macOS/Linux. The containing directory is also synced there. Windows uses its file lock and replacement APIs but has not received native crash/durability acceptance. Orphan `.world-*` files are never treated as committed saves. Existing/corrupt saves are never silently reinitialized. Back up the data directory while the door is stopped, or take a filesystem snapshot.

If a save error occurs, stop and inspect the filesystem before retrying a purchase: an error syncing the directory after replacement can mean the new state is visible even though durability was not confirmed.

## Build and validate

CI allows 60 minutes for the complete race, evidence, terminal and cross-build
sequence. Wanderer-aware maintenance fixtures isolate unrelated production and
random encounters while retaining their resource, replay and durability checks.

Requires Go 1.23+ and a local GoDoors checkout at commit [`2bb91d527ae926b436a5a65eb380441eb937e6a9`](https://github.com/robbiew/godoors/commit/2bb91d527ae926b436a5a65eb380441eb937e6a9) or a descendant. That revision fixes `OpenSession` rejecting unused Unix Door32 handles such as `-1`; it also includes the timed-input API and preserves partial escape sequences across the 1 ms autopilot polls. `go.mod` currently replaces `github.com/robbiew/godoors` with `../godoors`, matching this workspace. For another checkout, point that replacement at the matching GoDoors source before building. CI and release builds pin this GoDoors revision. The Unix handle regression and GoDoors suite pass locally, along with Yankee Trader startup and door tests; live Scorpio BBS acceptance remains pending.

```sh
go build -o bin/yt ./cmd/yt
go test -race ./...
go vet ./...
python3 scripts/smoke.py
python3 scripts/smoke_startup.py
python3 scripts/smoke_prompt_clock.py
python3 scripts/verify_port_screens.py
python3 scripts/smoke_port_parity.py
python3 scripts/verify_planet_screens.py
python3 scripts/smoke_planet_parity.py
python3 scripts/smoke_planet_parity.py --ascii
python3 scripts/verify_planet_rename.py
python3 scripts/smoke_planet_rename.py
python3 scripts/smoke_planet_rename.py --ascii
python3 scripts/verify_startup_evidence.py
python3 scripts/smoke_navigation.py
python3 scripts/verify_navigation_evidence.py
python3 scripts/verify_avoid_evidence.py
```

The smoke script also exercises planet creation, banking, investment, cargo transfers and reconnect. The smoke script uses a disposable world and real PTYs. It exercises GoDoors input/output, trading, equipment, movement, reconnect, repeated maintenance and Door32 local sessions with an alias change. Transcript: [local smoke evidence](evidence/local-smoke.txt). Both smoke scripts rewrite their transcripts under `evidence/` on every run; commit the refreshed files when door output changes.

The Mercenary-route smoke fixture starts with The Wanderer missing so normal
restoration runs after route actions. This keeps mine/pickup assertions isolated
from unrelated random Wanderer movement; gameplay behavior is unchanged.

The tests also cover rejected-action rollback, malformed saves, competing goroutines/processes, a killed lock holder, stale docking tokens, exact-money persistence, and DOS trading examples. Successful cross-compilation is recorded separately from native runtime/BBS validation in [validation evidence](evidence/VALIDATION.md).

## Planet management

The explicit commands below apply to `-compact`. The default interface uses the DOS planet menus described above.

`CREATE <name>` spends 25,000 credits and creates a planet in the current sector (one per sector, slots 2–100). It starts with production rates 1/1/1, stocks 10/10/10, 30 fighters, ground defense 1 and an empty bank. Creation does not land the ship or spend a turn.

| Command | Action |
|---|---|
| `LAND` / `PLANET` | Land, or display the landed planet |
| `BANK <target>` | Set the bank balance; move the difference to/from ship credits |
| `INVEST <credits>` | Spend credits to add credits/250 to each production rate |
| `TRANSFER cargo` | Unload all ship cargo; apply the recovered stock-based rate improvement |
| `TRANSFER fighters [quantity]` | Unload fighters; omitted quantity means all |
| `TRANSFER missiles [quantity]` | Unload missiles; mines and plasma work the same way |
| `TAKE <item> <quantity>` | Load whole units of cargo or weapons |
| `A` / `TAKEALL` | Load equipment, organics, ore in that order, then weapons |
| `GARRISON <target>` | Set planetary ground forces using the ship's ground forces; zero releases ownership |
| `LEAVE` | Leave the planet or port |

Owners, members of the same nonzero team, and visitors to unguarded planets can land. Permission and current position are rechecked on every action. Team membership and shared access are available through the team menu. Missile bombardment and separately confirmed ground assaults are available. A vacant unowned or dead governor can be adopted without spending carried troops; unrest reduces the existing garrison. Teammates and unguarded foreign visitors retain their existing access and governor.

Production uses elapsed time capped at ten days. Visiting grows rates before production; daily maintenance produces before growing rates, matching the two recovered DOS paths. Banking reevaluates surplus production after changing the balance. Fractional stock is retained; only whole units move aboard. See [planet recovery](research/yt-combat/RECOVERY.md) and the packaged reports in `research/yt-combat` for the original evidence (report filenames are preserved).

Money remains exact integer credits, including interest. This deliberately fixes the DOS large-balance banking exploit: even a one-credit deposit debits the ship. Empty transfers cannot increase production; failed or competing actions cannot duplicate goods. Clock rollback preserves the production watermark. Movement, reconnect and maintenance invalidate landing authorization.

Version-1 through version-34 worlds upgrade to version 35 in memory and are saved atomically on the next successful update, preserving existing players and assets. The local `data` and `bin` directories are ignored by Git. The original DOS distribution and full recovery workspace are preserved under `archive/`; portable supporting reports and compressed DOS snapshots are included under `research`.

## Complete recovery archive

The [complete archive](archive/README.md) includes the original DOS distribution, full experiments, Ghidra projects, player spreadsheet and [art/menu gallery](archive/analysis/art-menus/index.html). Run `python3 scripts/verify_archive.py` to verify all imported checksums. This repository is the working home for future recovery; the old Downloads folder is no longer required.

On exit, the original DOS tune plays only when GoDoors positively identifies
SyncTERM or another CTerm-compatible terminal using its device-attributes query.
Unknown terminals and `-ascii` sessions receive no music bytes. Music uses the
CTerm `CSI |` introducer and SO/SI terminators, avoiding the legacy `CSI M`
sequence that ordinary ANSI terminals interpret as delete-line.

## Teams

Press `T` (or `TEAM`) for the team menu. Create a team with a name of 3–41 printable characters and a four-character invitation password, or select a listed team to join. Passwords are case-insensitive, entered separately at a masked prompt, and stored as bcrypt hashes. Do not stack passwords with commands. Teams hold up to four members; joining and team management spend no credits or turns.

Members can view the roster and teammate planet locations, share defended teammate planets, and confirm departure. New deaths also remove membership. Only the current captain can rename the team, change its invitation or remove another member. Removal permits rejoining until the password changes. If the captain leaves, the next member to visit the menu or log in succeeds them. Empty teams disappear.

Leaving or removal immediately revokes shared landing sessions that no longer have access. Planets and ports retain their individual owners; port treasuries remain personal. Sector defenses can be deployed/recovered with `F`/`DEFEND`, and teammates may reinforce them with `REINFORCE` or team option 6. See [team implementation and evidence](research/yt-teams/IMPLEMENTATION.md).

## Combat preparation

Confirmed direct fighter attacks are now available; minefield aftermath is implemented, with sector-defense combat available as described below. The engine now records death and replacement atomically and binds each logged-in session to its ship generation. Old commands and pending prompts cannot act after death or use a replacement ship. Fresh-login replacement preserves remaining turns, while ordinary daily maintenance remains the only turn refill. Self-death has a next-UTC-day cooldown; enemy retaliation keeps its actual killer attribution. These internal transitions have no production kill/debug command. See [lifecycle scope, policies and validation](research/yt-ships/LIFECYCLE.md). Internal fighter/shield calculations, sampled inventory salvage and complete modeled estate transfers are implemented; player-facing fighter attacks connect these operations, including attributed minefield aftermath outside Earth. [Duel and settlement scope](research/yt-ships/DUELS.md).

## Loot and death-related ownership

Internal settlement samples holds, money and weapons separately, then chooses cargo from the salvaged holds. Awards consume the victim's inventory exactly once. Recipient limits reject the complete transaction, and cash stays integer-based throughout sampling and transfer.

A new enemy death transfers ordinary ports with their treasuries intact. Self/environmental death releases those ports and clears their treasuries. Planets remain owned by the victim. Death removes team membership and revokes shared guarded-planet access; owned sector fighters become Mercenaries. Captured/released ports invalidate old docking agreements. Replacement preserves remaining turns and retained planets.

Sector defenses have deployment/recovery, reinforcement, confirmed combat and missile interception, with real sensor reports and hostile-warp blocking. Default worlds have no deployed defenses. Direct fighter attacks are enabled for supported encounters. Non-Earth wreck mines now form attributed minefields and resolve against the attacker. Earth safely disposes of its unsalvaged mines. [Settlement rules, upgrades and validation](research/yt-ships/SETTLEMENT.md).

Cloak energy persists per ship, decays by one percentage point when a spent turn
leaves a multiple of 25 turns, and starts full on new/replacement ships. Legacy
saves retain zero cloak. Sensor detection is private to each session and never
drains the observed ship. See [cloak scope and validation](research/yt-ships/CLOAK.md).

### Confirmed fighter attacks

Use `ATTACK` to list visible local enemies and choose a ship number and committed
fighters, or `ATTACK <ship number> <fighters>`. Classic main-menu `A` enters this
dialog; the planet-menu `A` take-all binding is retained. A separate exact `Y`
confirms one attack. Blank, N, Escape or disconnect cancels; stacked answers,
queued keys and command-repeat syntax cannot supply approval. Fighters, defenses,
loot and ownership save together, and direct fighter attacks spend no turns.

Earth safely disposes of unsalvaged victim mines after loot is consumed once.
Mine-bearing targets outside Earth are enabled, with wreck drops and chained
deaths resolved atomically. Other supported direct duels are available; one-hop missile attacks and counterfire are implemented below; sector-defense combat is available below. See [scope and validation](research/yt-ships/PLAYER_ATTACKS.md).

### Minefields and chained deaths

Non-Earth wrecks drop only unsalvaged carried mines, once, with their source
account retained. Mines threaten all occupants, including their source and team.
Manual entry requires a fresh warning confirmation; autopilot stops before a
mined hop. Sensors report the actual stock. Current-sector hazards resolve before
commands or on reconnect, and save-lock guards prevent spending or moving away
through a newly arrived field. Small surviving ships may emergency-warp to a
safe destination even with no remaining turns.

Mine deaths retain their actual source even if that source already died. They
release ports rather than award remote loot, and do not become voluntary suicides.
Earth remains free of mines. This build now uses save version 27; follow the stopped-world
backup and all-node upgrade guidance. `D`/`DROP [quantity]` places carried mines
in the current sector outside the protected home seven, with a fresh confirmation
and no turn cost. Ships already safely present can depart without triggering the
new field, even after reconnect; departure clears that grace and reentry triggers
the mines. New wreck mines remain immediate hazards. Sector-field recovery is not
implemented; the DOS manual has no
recovered pickup command. See [mine placement research](research/yt-ships/MINE_PLACEMENT.md)
and [minefield rules and validation](research/yt-ships/MINES.md). Routed missile
encounters and sector-fighter combat are available below.

### Missile attacks and retaliation

Use `MISSILE <sector> <quantity>` or classic `!`; omitted arguments are prompted.
The confirmation displays the selected shortest route (ties use stored warp
order) and visible targets along it. Launches need a fresh separate Y and cost
one turn plus all selected missiles. Hostile sector fighters intercept first,
then mines, visible enemy ships in player-ID order, and hostile planets in each
sector. Destroyed ships and planets let remaining missiles continue down the
route. Hidden ships and teammates are skipped; friendly defenses are bypassed,
and friendly planets are passed over. The shortest-path and tie-break behavior
are modern policies; the DOS tie rule is unknown.

A surviving ship actually hit may return one volley if a directed route leads
back to the launcher. The response uses its own preflighted route and resolves
intermediate defenses, mines and hostile planets; it can target the original
attacker through cloak. Return fire does not consume the defender's daily turns
or recurse. Both volleys, interceptions, ship and planet damage, loot, deaths,
port transfers and mine drops save together. A ship whose shields reach zero is
destroyed even if escorts remain, as in the recovered missile path. Prototype
new ships still start with zero shields: purchase shields at Earth before combat.

Return-volley sizing uses the saved `StoredScore` cache. New/migrated accounts
start at zero and use the recovered random 1..stock fallback until a ranking update, clean logout or new daily maintenance publishes real
supported asset scores. Positive cached scores use the recovered
retaliation formula. See
[missile scope, rules and validation](research/yt-missiles/IMPLEMENTATION.md).

### Sector fighters

`F <total>` / `DEFEND <total>` sets the final size of your current-sector defense;
`F 0` recovers it. Deployment is prohibited in Union sectors 1–7. Existing legacy
groups there may be reduced or recovered. `REINFORCE <quantity>` and team option 6
add fighters to an existing personal or teammate group without changing ownership.
Only its owner may recover a group; all transfers enforce ship and defense capacity.

Hostile defenses stop ordinary movement. Use `BREACH <current-or-adjacent sector>
<fighters>` to commit a force. Choose whether to accept human surrender, then give
a fresh separate Y to fight. Surviving defenders may surrender when outnumbered
strictly more than ten to one; NPCs and Mercenaries refuse. Uncommitted fighters
stay aboard. Exhausting the committed force forces emergency escape; `FLEE` also
escapes a current hostile group, with a fresh confirmation and possible loss of
all remaining turns. Adjacent entry spends one movement turn. Victory resolves
any destination mines in the same saved transaction. Defeating a group does not
kill its owner or capture a port. [Rules, policies and validation](research/yt-combat/SECTOR_FIGHTERS.md).

### Planetary ground and production bombardment

`MISSILE <sector> <quantity>` can strike hostile planets along a routed course
after sector fighters and mines intercept the volley. A fresh warning names the
route and visible ships/planets. Own/team planets are passed over, while a
personal or teammate planet cannot be selected as the destination. Mixed visible
ship/planet encounters are supported in sector order. Missiles first reduce
ground forces by a random fraction of 25 each; after ground reaches zero, each
remaining missile independently damages all three production rates. Rates clamp
at zero and matching warehouses cap at ten times their resulting rate. Recovered
cached-ore round eligibility is preserved. If all rates reach zero, the planet
is removed from its sector and every landing token for it is revoked. The launch,
interception, growth, damage and deletion save atomically. Planet bank, ownership,
attacker cash and ships are not transferred by destruction. [Bombardment rules and evidence](research/yt-missiles/PRODUCTION_DESTRUCTION.md)
and [routed encounters and remaining validation](research/yt-missiles/WIDER_ROUTES.md#remaining-research-and-validation).
Ground/production bombardment, destruction, mixed encounters and continuation
after destruction are implemented. Remaining work concerns original DOS RNG and
rounding fidelity, numeric boundaries, unresolved routing/target-ordering rules,
and native BBS acceptance testing.

Spies now report other living ships' names, team numbers, fighters and shields,
plus this login's space-time disruptions. Partial-cloak detection may produce a
shimmering notice; successful detections share the login cache used by sensors,
anti-cloak and attack eligibility, bound to target ship generation and season.
Saved cloak energy and durable radio stay unchanged. No persistent target warning
is added for the tested detection path. Exact DOS RNG odds remain unresolved. [Recovered controls and policies](research/yt-spies/intelligence/IMPLEMENTATION.md).
This feature added no further save fields; the current world version is 29. The DOS evidence verifier
checks complete ordered ship records, including exact shield values; corruption
controls reject altered values even when transcript hashes are refreshed.

Spies are available at Earth for 333,000 credits each, up to three per login.
Choose their starting sectors through Earth option 9 or compact `HIRE` while
docked. Computer option 15 / `SPIES` lists their locations. Successful movement
(including autopilot hops), docking, validated positive missile/plasma launches and charged
unavailable planet queries search each
spy's current sector, then move it along a random outgoing warp. Reports cover
mines, planet names/ground forces, other owners' sector defenses, ships and
this login's disruptions. Repeated
findings in the last reported sector are suppressed; zero-warp sectors safely
hold position. Spy work has no extra turn charge beyond the triggering action.

Reports appear between commands; `INTEL` retains the last 30 for this login.
Spies and intelligence history end on disconnect or logout; hires are not
refunded. Direct/team radio history remains persistent and separate. Exact
cloak-detection odds and unconfirmed command paths remain open. Sector-fighter
transfers, mines and free information reads do not advance spies. Missing-planet
or hostile-defense-blocked `PLANETREPORT` / computer option 9 queries spend one
turn; successful planet reports remain free. A spent unreachable plasma launch
advances once, while rejected missile routes do not. Pre-impact spy grants never
expand a sealed weapon confirmation.
[Research](research/yt-spies/RECOVERY.md) and [implementation policies and validation](research/yt-spies/IMPLEMENTATION.md).

The Galactic newspaper is available through computer option 8 and
`NEWS [TODAY|YESTERDAY]`. It records successful logins and team creation with
public alias/name snapshots. History uses UTC calendar dates, retains today and
yesterday, and caps the combined journal at the newest 1,024 events. Five-entry
pages are free to read; Enter continues and Q stops. Private radio and spy reports
remain separate. Repeated maintenance preserves history; old saves start with
empty news rather than reconstructed events. Combat, acquisition, registration
and other newspaper event types remain outside this slice.
[Research](research/yt-newspaper/RECOVERY.md) and [rules, migration and validation](research/yt-newspaper/IMPLEMENTATION.md).

### Mercenary bribery

`BRIBE [credits]` negotiates with the current hostile fighter group;
`BRIBE <adjacent sector> <credits>` enters and negotiates with an adjacent group
for one turn. Classic B also works during an encounter. Enter a positive whole
amount and confirm with a fresh Y. Accepted offers pay that exact amount and
recruit the entire group. Refusal or insult can commit all ship fighters to combat;
even a generous offer can be refused. Mercenaries remember your attacks until
reconnect, and planet guards refuse to negotiate. Ordinary B still buys ports.

Payment, recruitment, entry and mine aftermath save atomically. Unresolved groups
continue blocking normal actions. The current save format is version 27. See the
[recovered rules](research/yt-mercenaries/HOSTILITY.md) and
[implementation policies and validation](research/yt-mercenaries/IMPLEMENTATION.md).

### Daily Mercenary hiring and routes

[Original-DOS maintenance evidence](research/yt-mercenary-maintenance/RECOVERY.md)
now establishes tax-funded hiring, group allocation, route movement, mines,
defense encounters, planetary fighter pickup and reserved-base restoration.
The evidence includes 41 completed runs and a bounded capacity-stall control.
The DOS “captured planet” message does not transfer ownership or ground forces.
Daily maintenance now uses ordinary-port taxes to hire Mercenary sector fighters.
Hiring preserves both rounding stages: one small group, or ten equal groups for
larger budgets. New groups occupy distinct undefended sectors outside the Union
(sectors 1–7). A full universe completes normally; unused funding and rounding
remainders are discarded without carry or refund. Fresh hires first move on the
following daily run.

The same locked save commits taxes, groups and the daily date, including when
maintenance runs at login. Saves now use version 27. Existing groups can travel one complete permitted route
per day, encountering
mines and sector defenses. They can merge, reinforce human defenses, fight, or
stop at a planet to take whole stored fighters; planet titles and ground forces
remain unchanged. Protected Union sectors are excluded from routes. Combat and
mine work is bounded, leaving unfinished encounters for later days.

Before movement, human-owned sector groups outside the Union can desert when a
random draw times 100 is strictly greater than their fighter count. Groups of
100 or more cannot desert. Conversion preserves fighter count and changes only
the deployed group's owner; ship fighters, planets and ground forces are untouched.
Converted groups join that day's normal Mercenary route phase. NPC ship combat
remains outstanding.
[Desertion rules and validation](research/yt-mercenary-maintenance/DESERTION.md).
[Hiring policies](research/yt-mercenary-maintenance/IMPLEMENTATION.md) and
[route rules and validation](research/yt-mercenary-maintenance/ROUTES.md).

### Mercenary base restoration

Daily maintenance now creates a missing Mercenary Base in a free planet slot and
an eligible sector outside the Union. It prefers slot 99 while preserving all
existing planets; full capacity defers creation safely. Mercenary-owned bases
regain 150,000 ground forces only when empty, and 25,000,000 bank credits only
when the bank is zero. Normal production remains active. Base identity survives
renaming or capture: human-owned and neutralized bases retain their titles and
resources, without automatic retitling, replenishment or duplicate creation.
A destroyed base can rebuild on a later daily run.
[Base policies, migration and validation](research/yt-mercenary-maintenance/BASE.md).

### Xannor HQ and Xannoron lifecycle

Daily maintenance now creates Xannoron when safe space is available, restores
Xannor-owned ground/bank reserves, regenerates HQ fighters from living players'
previously published scores, and resolves bounded HQ reclaim battles. Empty or
successfully reclaimed HQs can relocate, combining friendly force without loss.
Full capacity safely defers creation or relocation. Captured and neutralized
homes keep their title, resources and location; only an Xannor-owned home moves
with its HQ. Defenders appear in the existing encounter and report interfaces.
Introduced in version 14 and retained in version 27, saved HQ state preserves unfinished HQ battles across restarts and upgrades
normal version-13 worlds without inferring homes from names or slots.
[Rules, adaptations and validation](research/yt-xannor-lifecycle/IMPLEMENTATION.md)
are grounded in [38 completed DOS runs](research/yt-xannor-lifecycle/RECOVERY.md).
Mobile targeting, ship/planetary attacks and revenge/candidate selection are
implemented below. Exact DOS RNG/rounding parity remains a future milestone.

### Mobile Xannor groups

Xannor forces now split from HQ and receive bounded daily movement outside the
Union. They select targets, follow directed routes, hit attributed mines, fight
sector defenses and combine friendly force without duplication or overflow.
Returning fighters cannot be sent out again that day. Normal encounters and
sensors show the resulting deployed groups after reconnect.

Groups now assault foreign planets before intercepting ships. Captured homes
retain their title and resources outside actual combat; friendly planetary
stocks are not picked up. Target searches, mine bursts and
battles have finite work budgets. The current save version is 27.
[Policies and validation](research/yt-xannor-mobile/IMPLEMENTATION.md) build on
[47 completed DOS controls](research/yt-xannor-mobile/RECOVERY.md). Revenge and cloak candidate-search implementation is described below.

### Xannor ship-combat research

[42 original-DOS maintenance controls](research/yt-xannor-ships/RECOVERY.md) now
establish ship detection, fighter-before-shield battles, casualty thresholds,
multiple victims, route continuation and NPC death/ownership cleanup. They also
expose dead-record targeting and stale shield/captain defects to avoid in Go.
The subsequent implementation now enables bounded transactional Xannor ship
combat. Planetary assaults and revenge/candidate selection are implemented below.

### Xannor ship battles and private aftermath

Mobile groups now intercept living ships outside the Union, fighting ship
fighters before shields within the same finite route budget. Surviving groups
can attack multiple ships and continue their route. A death atomically invalidates
the old ship, releases ports, converts personal sector fighters to Mercenaries,
cleans up team access and preserves planetary titles. NPCs receive no salvage,
and these deaths create no wreck mines.

Both interfaces deliver private casualty reports after login; `BATTLES` reads the
last 32 retained reports. Public news announces deaths without disclosing force
counts. Save version 27 preserves reports through replacement and upgrades old
worlds without inventing past battles.
[Policies, migration and validation](research/yt-xannor-ships/IMPLEMENTATION.md).

### Xannor planetary assault research

[71 original-DOS controls](research/yt-xannor-planets/RECOVERY.md) now recover
ground volleys, production damage, warehouse caps, neutralization and logical
destruction, with paired economic controls and runtime byte evidence. They also
expose a production-batch subscript defect and distinguish stale inactive fields
from surviving resources. The implementation below uses these rules with
explicit corrections for modern ownership and finite combat.


### Xannor planetary assaults and destruction

Mobile groups now fight ground troops, damage production and cap warehouses
before intercepting ships. Zero ground neutralizes a title; surviving attackers
can destroy a planet when all production reaches zero. Union sectors remain
protected, and captured homes follow their actual ownership. Large production
batches require enough attacking force, correcting the DOS subscript defect.

Destruction removes the planet and expires every landing/confirmation grant,
without creating loot or collateral ship deaths. Both interfaces deliver private
owner reports through `BATTLES`; public news reveals only planet name and outcome.
The shared route work limit, atomic daily save and replay guard apply throughout.
Save version 27 preserves existing ship history and upgrades older worlds without
inventing events. [Rules, migration and validation](research/yt-xannor-planets/IMPLEMENTATION.md).
Native/live BBS acceptance remains outstanding; revenge/candidate selection follows below.


### Xannor revenge and cloak search research

[53 original-DOS maintenance controls and three player-command controls](research/yt-xannor-revenge/RECOVERY.md)
now establish HQ revenge creation/consumption, candidate search, separate cloak
checks, top-player selection and group overrides. They distinguish up-to-25
search attempts from guaranteed retries and correct the ordinary interception
comparison at exact equality. A readable model and 23 game/runtime byte
observations preserve the rules and limits.

The subsequent implementation below enables these features with current living
targets, Union protection and explicit cloak policies. Exact DOS RNG/MBF parity
and native/live BBS acceptance remain separate.


### Xannor revenge and bounded candidate selection

Defeating Xannor-owned HQ sector fighters with fighters or missiles now marks the
victorious ship for the next daily revenge attempt. `I`/`INFO` shows that private
pending status in both interfaces. A later victory replaces the target; death or
replacement cancels it. Ordinary Xannor kills, partial attacks and other factions'
HQ garrisons do not queue revenge. Qualifying victories also pay the bounded
credit reward described below in the same atomic combat save.

Daily maintenance consumes the pending target once, including when it has reached
the protected Union or no mobile route is available. Groups try at most 25
candidates in revenge mode and one ordinarily, with finite safe fallbacks and
current living players. Shared pursuit, top-player overrides and final HQ return
ordering are preserved. Discovery uses strict `RND>cloak`; actual ship encounters
now permit equality at `cloak-.33` for every group. Revenge never removes the
combat cloak check, and cloak remains turn-based.

Save version 27 retains the ship-generation-bound pending target introduced in
version 17, along with existing assets and histories. Queue creation and daily
consumption save atomically with combat/maintenance, and replay does not repeat them.
[Rules, migration and validation](research/yt-xannor-revenge/IMPLEMENTATION.md).


### Daily lottery and inactivity research

[41 completed original-DOS controls and 18 native byte observations](research/yt-maintenance-lottery/RECOVERY.md)
now establish the one-shot super-planet lottery, inclusive old-dead-player cutoff,
cloak-expiry deferral and maintenance ordering. Exact saved chains show New Year
handling, delayed radio removal, same-day reprocessing and stale planet-slot
catch-up growth. An independent verifier and eleven rehashed negative controls
preserve these findings.

This research introduced no gameplay changes. The implementation below now
ships bounded awards and safe retirement, keeping the modern replay guard,
identity/history invariants and complete new-planet initialization.


### Daily super-planet awards and inactive-player retirement

Once per advancing UTC maintenance day, dead accounts inactive for at least
14 days since both death and last authenticated login retire before production.
Living or recently killed/active players stay. Retirement releases remaining
estates and mines, frees an active slot, and preserves the identity, death
attribution and private histories. The same authenticated caller can return with
a fresh ship when capacity allows; released estates are not restored. Player
numbers are never reassigned. The bounded archive retains up to 256 identities.

After NPC actions, one lottery gate and finite player/slot/sector selections can
award a fully initialized planet. Failed occupied, defended, mined, HQ or reserved
placement gets no retry. The winner receives private system radio naming the
sector; public newspaper news names only the winner. MESSAGES/INBOX and ordinary
login delivery handle the award. Full private-message capacity prevents an award.
Save version 27 records these changes atomically with maintenance; replay and
clock rollback do not repeat them. [Policies, migration and validation](research/yt-maintenance-lottery/IMPLEMENTATION.md).


### Daily plague and civil-war events

Daily maintenance now applies a single bounded outbreak pass after ordinary
port/planet growth. Ports, including Earth, contract plague when total updated
production exceeds 1,000,000. Eligible rates use the recovered random reduction
formula, cargo is capped, and the highest-stock commodity becomes the one sold.
A near-cutoff rate can increase and an outbreak can remain above the threshold.
Planetary plague uses production-based random gates; ground-based civil war takes
priority, reduces production/ground and additionally spends a random whole-credit
amount from the post-interest bank. Plague never debits its bank.

Events preserve titles, names, links and weapon stocks. Ground results are floored
to whole units; zero production remains valid. Same-day/rollback safeguards and
atomic saves prevent repeated damage. Existing daily docking/landing sessions
expire. Newspaper entries report the port count or planet name without exposing
private forces, balances or expenditure. No legacy stale expense text is copied.

Plague/civil-war news was introduced in version 19 and is retained in version 27
with existing assets and history.
Read-only migration does not rewrite old saves. If news IDs are exhausted or its
clock is ahead, unreportable damage is deferred. See the
[implementation policies and validation](research/yt-plague-civil-war/IMPLEMENTATION.md)
and [56 original-DOS controls, 18 native byte observations and recovered limits](research/yt-plague-civil-war/RECOVERY.md).

### Xannor HQ victory credit rewards

[38 completed original-DOS sessions and 12 native byte observations](research/yt-xannor-hq-reward/RECOVERY.md)
establish the fixed million-credit reward, current-actor recipient, fighter/missile
eligibility, routed HQ interception, team nonsharing, repeat eligibility and
public/broadcast notices. They confirm a plasma owner-check defect and native
single-precision rounding that can enlarge or erase the credited bonus. Exact
parent-session chains separate a fresh restored-HQ victory from reconnect replay.
An independent verifier and 16 rehashed corruption controls preserve the findings.

The supported fighter and missile commands now pay the acting player when they
clear a positive Xannor-owned force at the current HQ, including a missile route
that reaches HQ before its requested destination. Payment is exactly
`min(1,000,000, MaxMoney - ship credits)`. Teammates, planetary banks and port
treasuries receive no direct payment. An existing revenge target does not prevent
a new qualifying victory against a restored force from earning another award.
Empty targets, partial damage, cancelled/stale confirmations and ordinary
reconnects do not pay.

The receipt appears after a successful save, including forced combat after a
refused Xannor bribe, and states the credits actually added,
including one or zero at the ship credit limit. Force removal, payment, revenge,
public news and subsequent combat/mine aftermath save together. Later destruction
still follows ordinary death and replacement rules; the receipt reports the
addition before that aftermath. Public newspaper news names the victor without
revealing private amounts or balances, and counter-volley awards belong to the
retaliating actor. Existing score publication rules remain in effect.

HQ victory news was introduced in version 20 and is retained in version 27. Older saves upgrade on the next
successful write without retroactive rewards or invented notices. Full race tests,
19 real terminal smoke scripts, evidence checks and Linux/Windows cross-builds
passed locally; live BBS acceptance and native Windows durability remain separate.
See [implementation policies, compatibility and validation](research/yt-xannor-hq-reward/IMPLEMENTATION.md).
Plasma, exact legacy floating-point behavior and interrupted DOS writes remain
outside this milestone.



### Danger scanner and manual emergency-warp research

[41 new completed DOS controls and 10 native byte observations](research/yt-scanner-warp/RECOVERY.md)
now establish the 250,000-credit scanner purchase, duplicate/affordability rules,
installation persistence and precise warning/autopilot boundaries. Accepting a
warning completes only that hop; declining a later hop retains earlier moves.

Manual warp needs turns, not purchased equipment. Controls verify same-sector,
avoided and empty-exit destinations, capped recharge, a natural meltdown and
same-date reconnect. Mined arrivals apply damage; hostile fighters remain an
encounter gate, including with a scanner installed. An independent verifier and
23 rehashed semantic corruption controls validate the retained evidence.

This was the research-only milestone. Its contract is now implemented below;
score scanners, other equipment, exact RNG/MBF parity and native/live acceptance
remain separate work.

### Bounded danger scanner and manual emergency warp

Earth item `5`, or compact `EQUIP scanner 1`, installs one persistent scanner for
250,000 exact credits. Its saved receipt reports the actual debit and balance;
ship information shows installed status. New and upgraded ships start without a
scanner. Reconnect preserves it; replacement ships require a new installation.
Mine damage can destroy an installed scanner and saves that loss with the damage.

An installed scanner reports actual mines and hostile sector fighters, with
own/team exemptions. Each warning clears queued travel and requires fresh input.
Accepting completes only that hop, including mine damage, then stops autopilot;
declining retains completed hops and spends no additional turn. Hostile fighters
remain an encounter gate. Existing conservative mine confirmations and blocked
fighter entry remain available to ships without scanners.

`W` or `WARP` offers a fresh emergency-risk confirmation in both interfaces,
including during hostile fighter encounters. It requires at least one turn and
no purchased equipment. Landing may be in the current, avoided or any other
existing sector. Recharge fixes the bounded heat budget from its first two random
draws, then uses available whole turns; later heat draws cannot change that budget
or shift the destination/recharge draw order. Meltdown spends every remaining
turn. Receipts identify the random landing, recharge, any additional arrival-escape
debit and actual total turns spent.

Destination, turns, cloak consumption, access invalidation, mine damage/scanner
loss and any death/estate cleanup save atomically. Hostile fighters at the landing
remain unresolved. Existing automatic mine escape may lead to a later safe sector;
the receipt distinguishes that outcome. Cancellation, stale/expired warnings and
failed saves never print a success receipt. A committed storage warning cannot
replay a zero-cost/same-sector warp from an old confirmation.

Save version 27 preserves scanner ownership and a monotonic warp sequence. Older
saves upgrade on their next successful write without granting equipment or moving
ships; read-only loading leaves files unchanged. Full race tests, vet, 20 terminal
smoke scripts, evidence verification, archive checks and Linux/Windows cross-builds
passed locally. Live BBS and native Windows durability remain unverified.
[Implementation policies, compatibility and validation](research/yt-scanner-warp/IMPLEMENTATION.md).


### Cloak-energy purchasing and anti-cloak activation — research complete

This historical research contract is implemented in the following section.
Original-DOS controls establish Earth item 1 at 1,000 credits per percentage
point, whole-point quantity handling, missing/affordable blank defaults,
over-capacity rejection, consecutive purchases and saved recharge across reconnects.
Earth item 6 costs 500,000 credits for one login's activation. Fresh acceptance
clears cached cloak and exposes ships without changing their stored energy;
repeated and empty activations still charge. Declines preserve resources.

The buyer's native information display reports FAIL while active, despite intact
stored energy. A paired turn-boundary control confirms that the original session
flag suppresses the buyer's ordinary cloak decay. Reconnect rebuilds concealment
and restores normal decay; a linked recharge remains saved. Those were recovered
rules at the research stage, with no permanent anti-cloak installation.

The research retains 37 completed DOS controls, four exact world/auxiliary
reconnect chains and ten complete REA byte observations, with independent
verification and 23 corruption controls, including rehashed semantic attacks.
The proposed implementation keeps
exact debit, staged session effects, current ship generations, accurate receipts
and normal modern cloak consumption. That research stage made no Go gameplay
or schema changes and retained version 21; the implementation below completes it. Full concurrent-observer and replacement-target DOS
behavior, exact numeric/RNG parity and native/live acceptance remain separate.
[Recovered rules, evidence, limits and proposed contract](research/yt-cloak-equipment/RECOVERY.md).


### Bounded cloak purchases and login-local anti-cloak — implemented

Earth item `1` or compact `EQUIP cloak <points>` buys whole percentage points at
1,000 exact credits each. The classic blank default is bounded by missing energy
and affordability; zero cancels. Full, over-capacity, malformed, unaffordable,
remote and expired purchases do not charge. Recharge persists across reconnects;
its post-save receipt reports points, exact debit/balance and energy before/after.

Earth item `6` or compact `ANTICLOAK` confirms a 500,000-credit activation for the
current login. Queued answers are cleared and a fresh Y is required. It reveals
existing cloaked ship incarnations to that login without changing victims' saved
energy, locations or assets. The receipt reports actual newly revealed ships;
repeat and empty activations still charge, with zero new reveals stated plainly.

Debit and staged visibility publish together. Failed or expired saves expose no
unpaid reveal; a committed storage warning preserves both committed effects and
cannot replay its confirmation. Reconnect discards activation, another login does
not inherit it, and replacement/future ships need a new reveal. Information keeps
the real stored energy and labels active anti-cloak separately. Ordinary cloak
consumption continues, deliberately avoiding the original decay-suppression side
effect. No new score bonus or public event is generated.

The cloak milestone added no saved fields; its existing state is retained in
version **29**. Recharge uses the existing cloak field and
anti-cloak state is never serialized. No migration grants energy, credits or
reveals. Full race tests, vet, focused rollback/concurrency/expiry/durability
coverage, both interfaces and affected real terminal scripts pass, along with
research verification, archive checks and Linux/Windows cross-builds. Live BBS
acceptance and native Windows durability remain unverified.
[Implementation, deliberate differences and validation](research/yt-cloak-equipment/IMPLEMENTATION.md).


### Earth's paid Pick-6 lottery — research complete

This research contract is implemented in the following section.
Original-DOS controls establish Earth item `4` at five credits per six-digit
ticket, leading zeroes, input retries, finite configured daily limits and saved
same-day eligibility. The next-date login resets the used count. Digits match
without regard to order, with each duplicate used once; one through six matches
advertise 100, 1,000, 10,000, 100,000, 1,000,000 and 100,000,000 credits. Only four
or more matches append public lottery-win news.

The 49 completed controls include all payout tiers, a permuted natural jackpot,
duplicate limits, affordability, repeat/reconnect/day chains and large-balance
boundaries, with twelve complete REA byte observations. Independent verification
checks exact setup, keyboard/world/auxiliary chains, credits/counts/scores/news,
conserved bytes and native bytes, with rehashed semantic corruption controls.
Native money rounding can erase the fee or distort a jackpot. The proposed
implementation uses exact credits, bounded draws, guarded dates and atomic
fee/prize/play-count/news saves with accurate capped receipts.

That research milestone changed documentation and evidence checks only; item `4`
was then unavailable and version **21** unchanged. The implementation below
completes the playable flow in version **22**.
It is separate from the implemented daily super-planet lottery. Interrupted or
concurrent original callers, year rollover, full RNG/MBF parity and live/native
acceptance remain unverified.
[Recovered rules, evidence, limits and next implementation contract](research/yt-earth-lottery/RECOVERY.md).


### Bounded paid Earth lottery — implemented

Earth item `4` or compact `LOTTERY [six digits]` buys a ticket for five exact
credits after a fresh Y confirmation. Leading zeroes survive, duplicates match
once each and position does not matter. The default five-play UTC quota persists
across reconnects, death and replacement; optional `LotteryDailyLimit` accepts
0–9 (zero disables; omission uses five). Blank ticket entry and declined or stale
confirmation spend neither credits nor a play.

Six OS-random digits determine the recovered prize tiers, up to 100,000,000.
Fee, actual capped prize, daily count, monotonic replay sequence and four-or-more
match public news save atomically. Receipts state entered/drawn digits, matches,
fee, gross/actual prize, cap reduction, balance and remaining plays. Public news
contains only alias, matches and actual prize, with nominal prize in its wording.
A committed storage warning retains the saved settlement, ends the login and cannot repay it. Receipt-output failures, including EOF, preserve the storage warning and still end the login.

Lottery state was introduced in save 22; current save 26 upgrades supported older
worlds without granting tickets, money
or history; read-only loading leaves files untouched. Both interfaces, all prize
tiers, quota/date/cap guards, rollback/concurrency/replay and actual random terminal
receipts are tested. Exact DOS RNG/MBF/animation parity, live BBS gameplay and
native Windows durability remain separate.
[Implementation, compatibility and validation](research/yt-earth-lottery/IMPLEMENTATION.md).


### Genesis endgame and safe season reset — bounded research complete

Fresh original-DOS controls confirm the default 300-port endgame, threshold
bounds, cancellation and the cached-count weakness: cached ownership can win with
no actual ports, while actual ownership with a stale zero cache is refused. The
initializer clears accounts, titles and most auxiliary history, but can retain a
stale scoreboard. A missing initializer leaves a handoff marker that later resumes
without fresh confirmation; an invalid dropfile consumes it before failing.

The 24 returned controls include thirteen successful resets, eight refusals or
cancellations, two expected fault outcomes and one first-maintenance run, with
48 world snapshots, two exact reload edges, thirteen native byte observations
and 42 rehashed corruption controls. Zero-disabled lottery settings become one, out-of-range cargo caps become 50,
and standalone Genesis bounds differ from the in-game gate. A tested case-paired
alias mapping still produces a blank winner, so that native identity path remains
unresolved. Mid-write DOS crashes and concurrent resetters were not tested.

The proposed Go contract recounts actual non-Earth ownership, captures the winner
before replacing accounts, archives bounded season results inside the same atomic
save, and binds every login/cache/intent to a new monotonic season epoch. It also
requires finite generation, complete bootstrap before admission, unchanged lock
identity, rollback/durability handling and accurate saved receipts. These were
implementation requirements at the research baseline; the implementation below now provides the bounded reset contract.

**Historical research milestone:** Genesis was unavailable and save version 22 unchanged at this point; the implementation below supersedes that restriction. README, plan and
CI evidence checks are updated with this research; no Go gameplay or live-world
reset is included.
[Evidence, findings, boundaries and next implementation contract](research/yt-genesis/SAFE_RESET.md).


### Genesis endgame and safe season resets — implemented

Use main command `G` or `GENESIS` in either interface. The default requirement is
300 **actual personally owned non-Earth ports**; team titles and stored-score
caches cannot qualify. The prompt explains that the entire universe, its players,
assets and messages will be replaced. Only a separately entered, exact uppercase
`GENESIS` confirms; queued commands, blank, No, lowercase and chained answers do
not authorize a reset. The quote expires after two minutes or changed state.

The old winner's public result and the new season are saved in one atomic world
replacement. Fresh ports, Mercenary Base and Xannoron/HQ are initialized before
admitting new players; same-day maintenance cannot repeat bootstrap. Old logins,
private caches and pending confirmations reject the new epoch even if player
numbers and ship generations are reused. Classic login rechecks the authenticated
BBS identity under the same lock. The saved receipt ends the winning
login; reconnect to register in the new season. `SEASONS` displays public winners.
History is bounded to 128 completed seasons; a full archive safely refuses a reset.
History pages reuse one immutable snapshot, with a live season check after each
paging pause rather than reopening and validating the save for every row.

New worlds can use `./bin/yt -data test-world -init -sectors 32 -genesis-ports 20`
for a reachable test threshold, or `-genesis-ports 0` to disable Genesis. Omission
retains the default 300; explicit values must be zero or 20–300. Small universes
never silently reduce the default. Supported settings survive reset, including a
zero-disabled lottery. New seeds are recorded; legacy seed provenance is unknown.

Genesis state was introduced in save 23; current save 26 requires upgrading all
nodes together after a stopped-world
backup. Pre-replacement failures preserve the old world. A post-rename durability
warning is a committed reset: its receipt is retained, the login ends and replay
is refused. Full Go race/vet, local process-interruption, evidence, real terminal
and cross-build validation are recorded in the validation log. Live BBS acceptance,
native Windows crash durability, full DOS generation/numeric parity and The
exact disruption RNG/numeric fidelity remain separate work; bounded arrival and Wanderer lifecycle are implemented below.
[Implementation and safety contract](research/yt-genesis/IMPLEMENTATION.md).


### Planetary thrusters and forced landing — implemented for testing

Landed `!` in the classic planet menu, or `THRUST <sector>` in compact mode,
quotes the shortest directed route using your avoid list and stored warp-order
route ties. Confirm separately: the full quote requires 10 turns per hop. Only
completed hops are charged. A collision or rare stress failure destroys the
moving planet and can lose fighters while retaining completed progress; the
stationary planet is preserved. Reached mines resolve atomically, and hostile
sector fighters stop the route for their normal encounter. Movement or destruction
revokes every landing grant, leaves other callers' ships in place, and returns
the mover to the sector interface. Both faction homes stay immovable after capture.
Main-sector `!` retains its missile command.

Denied `LAND`/classic `L` offers forced landing when carried ground is available.
Choose a positive whole quantity, then confirm separately. No turn fee applies.
The entire commitment leaves the ship; a capture puts surviving attackers on the
planet, keeping its bank, weapons and economy. Defeat keeps the other governor.
Combat stops after at most 4096 rounds; surviving committed attackers retreat
without refund and are reported separately from casualties. Vacant government
adoption spends no carried troops and records the actual unrest-reduced garrison.
Self/team/unguarded ordinary access retains its governor.

Both actions save costs, links, capture/destruction, supported mine aftermath and
public ground news together. Confirmations expire after two minutes, are sealed
to one login and are consumed even when an attempted commit rolls back. Changed
ships, planet incarnations, permissions, routes, hazards or material ground growth
require a new confirmation. Receipts describe the actual saved result, including
prefix progress, troop losses/retreats, remaining resources and committed durability
warnings; a durability warning ends the login. Planet incarnations were introduced in save 24; current save 26 upgrades older
worlds without resetting them. See the [implementation and validation contract](research/yt-planet-mobility/IMPLEMENTATION.md)
and [55-control DOS recovery](research/yt-planet-mobility/RECOVERY.md).

Disruption arrival is implemented below. Complete DOS RNG/MBF parity, live BBS
gameplay and native Windows crash durability remain separate acceptance.


### The Wanderer lifecycle and transport — available in-game to test

[The focused recovery](research/yt-wanderer/RECOVERY.md) retains 57 normally
returned DOS controls, nine exact world/auxiliary reload chains, 14 native byte
reads and three verified executable load images. An independent verifier and
55 rehashed corruption controls check the corpus. Two diagnostics keep a bounded
no-vacancy timeout and later Xannor interference separate from isolated outcomes.

Daily native relocation clears The Wanderer's governor, refills its bank only
when zero, and regenerates missing sector links through a partial P.H.O.E.N.I.X.
restore. A linked but inactive record is moved without regeneration. Same-day
and backward-date native maintenance can repeat movement/economic effects;
those defects are not a requirement to weaken modern daily guards. Direct
YT-INIT includes maintenance bootstrap, while standalone RMT-INIT needs a later
maintenance run to create The Wanderer.

Special thrusters require the full quoted route budget but stop after one paid
edge. The ship follows its planned next sector while the planet chooses an
independent empty sector. Ship-arrival hazards apply at the ship's location;
mines/fighters at the planet's different location do not damage that ship. The
native UI conceals the random destination; implemented receipts preserve that
knowledge boundary. Finite placement, persistent mobile identity, fresh restoration
incarnations, atomic relocation/grant revocation and explicit season bootstrap are
covered by the [implementation contract](research/yt-wanderer/IMPLEMENTATION.md).

Introduced in save 25 and retained in save 26, explicit identity validates a unique marked Wanderer in reserved slot 1, allowing 100 total
planets. Initialization and Genesis bootstrap a neutral clean planet with rates
5000/5000/5000, bank 250,000, no stocks/weapons/garrison and a current timestamp.
Older-save migration creates no assets; eligible forward-only daily maintenance
restores it if absent. Existing daily movement follows economic updates, clears
its governor, refills only an exactly empty bank, preserves other legitimate
assets and revokes every landing grant without moving other ships. Faction homes
have priority over a missing Wanderer when space is scarce. Later NPC destruction
is reported accurately and never triggers a second restoration in that run.

While landed, classic `!` or compact `THRUST <sector>` requests the existing fresh
risk confirmation. The whole route must be affordable; success charges 10 turns,
moves the ship one planned edge and relocates the planet independently. Planned
collision/stress occurs first; ship hazards use the ship's reached sector. A
successful receipt reports actual costs and the ship's position, then says the
planet's location is unknown. No public movement notice or secret destination is
printed. Same-day maintenance, stale quotes and warning/reconnect paths cannot
repeat spending or restoration. `-maint` prints a saved final lifecycle outcome
without coordinates, retaining committed storage warnings and output errors.

Local regression and terminal checks are recorded in [validation](evidence/VALIDATION.md).
Disruption arrival is implemented below; full original RNG/MBF parity, live BBS
acceptance and native Windows durability remain separate.

### Disruption and black-hole arrivals — research and implementation complete

[The recovery](research/yt-disruption/RECOVERY.md) retains **61 normally returned
DOS controls**, four exact world/auxiliary reload chains, 15 native byte reads and
one independently reconstructed executable image. Narrow branch controls and
full 3000-sector header controls are distinguished. A separate unsupported
one-sector, 40-second nonreturning probe is diagnostic only. Independent
verification checks world/auxiliary conservation, receipt arithmetic, raw logs,
privacy and provenance, with 65 rehashed corruption tests.

Two independently drawn login-local holes may coincide. Arrival checks them
before local mines/fighters and automatically warps even with zero turns, then
rechecks the destination. Autopilot stops after the interruption. Ordinary planet
routes can pass a bare intermediate hole, but their final/helper-return arrival
can send the ship away while leaving the planet behind. Wanderer controls confirm
independent final ship/planet positions. Local sector/scanner warnings reveal
observed danger; generic news does not disclose the hidden pair or random planet
location. Raw sector field 133 does not identify a black hole.

Run `python3 scripts/verify_disruption.py` and
`python3 scripts/test_disruption_verifier.py` to check retained evidence; optional
fresh DOS reproduction uses `scripts/recover_disruption.py` in a new disposable
directory. [Native rules](research/yt-disruption/NATIVE.md) separate static
interpretation from observed outcomes. The [research-stage contract](research/yt-disruption/CONTRACT.md)
was the research-stage proposal; [the implemented rules](research/yt-disruption/IMPLEMENTATION.md)
now apply in both interfaces. The arrival feature retains its existing fields in save 26; the hidden pair is local to
the captured ship/season login and the existing warp sequence invalidates stale
confirmations, including same-sector/zero-cost warps.

Entering a hole automatically warps the ship before local mines/fighters, even at
zero turns. Installed scanners warn before voluntary entry; refusal spends
nothing. Each forced recharge preserves cloak and may consume all remaining
turns. The actual destination can be current, avoided, disconnected or hazardous.
Reached mines, escape/death and hostile encounter gates still apply. Planetary
routes check disruption on helper return, leaving a transported planet behind
when only its ship warps. Autopilot and queued commands stop on interruption, including when another login moves the same ship into this login’s disruption sector between commands or while input is waiting. A forced current-sector arrival returns to a fresh prompt before dispatch.

One atomic save includes the origin action and reached aftermath. A chain is
bounded to **32 forced disruption warps**; exceeding it aborts the entire action
without a partial resource debit or free escape. Saved receipts report each known
warp, final sector and actual spent/remaining turns, conceal the hidden pair and
Wanderer destination, and retain committed storage warnings through output
failures. Reconnecting selects new login-local holes; it does not replay the old
receipt. See [validation](evidence/VALIDATION.md) for executed checks. Exact original
RNG/MBF parity, unrelated disruption combat/spy branches, long-running balance and
native/live acceptance remain open.


## Plasma launch, routing and disruption research

The [plasma recovery](research/yt-plasma/RECOVERY.md) extends the older absorption
study with 62 normally returned original-DOS controls, two exact reload chains,
13 native byte observations and a reconstructed load image. It separates
indiscriminate physical damage from what a receipt may reveal, and distinguishes
[recovered native rules](research/yt-plasma/NATIVE.md) from the proposed
[bounded implementation contract](research/yt-plasma/CONTRACT.md).

**Historical research boundary:** this stage changed no Go code or save version
25 and did not make firing available. The [implementation below](#bounded-plasma-launching)
now supplies that playable flow in save 26. Exact DOS random/numeric parity,
live BBS acceptance and native Windows durability remain separate.

Run `python3 scripts/verify_plasma.py` and
`python3 scripts/test_plasma_verifier.py` to verify the retained corpus and all
53 corruption controls. The optional capture writer runs only disposable copies;
see the research report for its command and environment requirements.


## Bounded plasma launching

Use `PLASMA <sector> <quantity>` or classic `+;<sector>;<quantity>`; omit both
arguments for prompts. A launch accepts 1–64 available bolts and costs one ordinary
turn. Own and empty sectors are valid targets; even an unreachable accepted shot
spends its turn and bolts. A fresh exact Y is required after queued input is
cleared. Cancel, stale consent, invalid input, expiry and failed transactions spend
nothing. An intervening saved world change requires a new confirmation because a
redirect can reach any sector.

The shared energy pool follows directed shortest paths in stored exit order,
ignoring travel avoids, and weakens by a fixed launch-energy fraction per extra
hop. Login-local holes reroute before local absorption. Sector fighters, FIFO
mines, ships (fighters before shields) and planets share the same pool, including
new wreck mines. Friendly, cloaked and own targets can be hit. Only reached
planets receive lazy projection, damage and warehouse caps; destruction removes
their active record, link and landing grants without salvaging their bank.

All damage, loot, estates and local mine/escape aftermath save in the same
transaction. Earth disarms wreck mines. Different living sources may receive
salvage even after a friendly casualty; self or dead sources receive no new loot
or estates. Original projectile and mine-layer attribution remain distinct.
Self-inflicted plasma death requires next-UTC-day replacement and never refills
turns. No new missile retaliation is added, and friendly defenders at Xannor HQ
earn no bounty. Saved private receipts show anonymous impact totals and your own
losses/credits without hidden target names, private banks or projectile routes.
Fatal actions and committed storage warnings end the login.

Save **26** upgrades supported older saves without new inventory. Work limits
are 128 entered sectors, 32 redirects, 100,000 absorption rounds and 200,000 random
draws for the entire launch; exceeding a limit aborts intact. Nonfinancial float64
arithmetic is bounded, with exact integer money/stock accounting. Original DOS
RNG/MBF parity, live BBS acceptance and native Windows
crash durability remain separate. See [implementation policies and tests](research/yt-plasma/IMPLEMENTATION.md)
and [real terminal evidence](evidence/plasma-smoke.txt).


Plasma validation passed the full race suite/vet, all 51 terminal/control commands
(including ten new compact/classic plasma scenarios), all 60 evidence/control
commands and Linux/Windows cross-builds. Public-history terminal readers also
handle additional pages from legitimate daily awards, with a forced paging
fixture; production newspaper rules are unchanged. Historical captures remain
preserved. [Validation scope](evidence/VALIDATION.md).


## Mercenary plasma sales — historical feature removed

The original change log explicitly added a Mercenary Mother Ship selling bolts
for 5,000,000 credits in **3.3**, then removed it in **3.4** when planetary
production replaced that supply. The defended Mercenary home planet added in
**3.6** is a different feature. This closes the obsolete sales backlog item;
there is no current purchase API or shop to implement for DOS 3.6 parity.

[Acquisition research](research/yt-mercenary-plasma/RECOVERY.md) distinguishes
versioned documentation, bounded current-binary inspection and isolated DOS
controls. Current planetary take/deposit paths remain the supported supply
mechanism. Restoring a Mother Ship shop would be a new optional design rather
than a recovered 3.6 rule. **Historical research boundary:** this research changed no Go gameplay or save26 fields.

Validation retained 17 completed DOS controls, two exact reload chains and 12
native byte observations with all 870 relocations checked. Reloads reset the DOS
clock to midnight; the report now matches the retained clock witnesses. All 38 corruption
controls pass; all 4,682 archive hashes remain unchanged. Run the acquisition
verifier and corruption controls with Python 3:

    python3 scripts/verify_mercenary_plasma.py
    python3 scripts/test_mercenary_plasma_verifier.py


## Broadcast radio: shared lifetime and public-news research

[Extended broadcast research](research/yt-broadcast-radio/extended/RECOVERY.md)
supplements the separate [broadcast implementation PR #58](https://github.com/robbiew/yankeetrader/pull/58).
Original DOS ALL writes one public radio record per line, also publishes the
text to the newspaper, and spends a shared delivery budget on startup reads.
Computer history does not spend that budget. This differs from PR #58's
documented private-copy adaptation with independent recipient read flags.

**Historical research boundary:** this research changed no Go gameplay or save26 fields. The
[follow-up contract](research/yt-broadcast-radio/extended/CONTRACT.md) separates
public newspaper projection and an original-style shared archive from the
existing adaptation. The public-newspaper implementation described above now
implements the publication slice; an original-style global archive remains separate.

Validation retains 16 completed DOS controls, four exact reload edges and four
explicit mailbox-budget variations. Eleven native byte observations and both
YT/maintenance load images independently match all 978 relocations; all 43
corruption controls pass. Run the portable checks with Python 3:

    python3 scripts/verify_broadcast_lifetime.py
    python3 scripts/test_broadcast_lifetime_verifier.py


## Atomic broadcast newspaper publication

Version 27 saves one public sender-alias/text snapshot with all addressed ALL
copies in the same transaction. Preparation and final commit recheck journal time,
sequence, recipient roster, live ship, season and draft lifetime. Partial batches,
capacity failures, stale state and aborted saves leave both archives unchanged.
Retained-draft retries do not append another entry, even after the original public
entry has expired. Public reading never acknowledges anyone's private copy.

Local validation for this milestone is recorded in
[broadcast publication validation](evidence/BROADCAST_NEWSPAPER_VALIDATION.md).
Live BBS acceptance and native Windows crash durability remain unverified.

Radio compatibility follow-ups explicitly distinguish historical version-26 private
copies from current version-27 public ALL publication; older binaries cannot read
version-27 saves.

Editor evidence rejects newspaper publication of aborted FIRST/SECOND input,
including rehashed captures with an empty mailbox.

The Xannor planetary smoke fixture defers unrelated Wanderer restoration using
exhausted planet-generation capacity, isolating captured-home return assertions
from random HQ occupancy while retaining the exact return-force check.


## Spy triggers and login-local shared visibility

Thirty-six normally returned DOS controls, three exact target world/auxiliary
reload chains and 20 complete native byte observations distinguish actual command
triggers from free information reads. The native load image verifies all 870
relocations; a bounded complete main-code search anchors four direct trigger
encodings. The implementation follows the confirmed fighter-transfer, positive-launch and
unavailable-planet-query gates, with atomic private-state publication.

The public/private boundary stays intact: no new radio packet or spy newspaper
warning was observed in the tested detection path. Ordinary login news is
accounted for separately. Shared visibility is observer-local, and neither the
saved target cloak nor another login's detection state is cleared by these
findings. The original shared cache is corroborated by sensor and declined
attack-choice controls, without claiming exact RNG or battle-outcome parity.

Portable validation and rehashed corruption controls:

    python3 scripts/verify_spy_triggers.py
    python3 scripts/test_spy_triggers_verifier.py

The independent checker verifies fixture/actor identity, declared patches, raw
logs, clock/return markers, ordered reports, action-specific resource effects and
exact auxiliary chains. [Recovery](research/yt-spies/triggers/RECOVERY.md),
[native evidence](research/yt-spies/triggers/NATIVE.md) and the
[separate implementation contract](research/yt-spies/triggers/CONTRACT.md) retain
remaining limits. All 74 portable evidence/control commands, all 42 new
corruption controls and all 4,682 archive hashes passed for the research slice.
The [implementation](research/yt-spies/triggers/IMPLEMENTATION.md) adds gameplay
and regression/terminal coverage without changing schema 27 or dependencies.
The Xannor mine-only terminal fixture isolates its occupied HQ route from unrelated
Wanderer planetary combat; production faction behavior is unchanged.
Live BBS acceptance and native Windows durability remain unverified.

## Planet-creation news and private port-sale research

The original newspaper adds `  -  <alias> made a planet: <accepted name>` once
successful creation charges 25,000 credits. It spends no turn, including when
starting at zero turns. Declined/default purchase consent, insufficient credits,
blank/reserved names, occupied sectors and saturated slot flags do not publish a
creation success. Name refusal repeats naming; only the final normalized,
41-character-bounded name is recorded. Current Go naming safety policies remain
unchanged by this research.

The port-acquisition backlog is corrected: no public purchase entry was observed
in the tested paths. Owned-port buyouts create a private notice for the former
owner, naming the buyer, old port name, sector and asking price. DOS uses system
sender -2, displayed as The Mercenaries. A 31-credit purchase with 777 in treasury
pays the seller 808; the notice names the asking price, not that total payout.
Unowned purchases have nobody to notify. Initial refusal cancels; declining a
rename after Sold retries the name and is not purchase cancellation. Reloads
preserve the public creation entry and private seller routing without replaying
settlement; the buyer cannot read the seller-only notice.

The retained 34 controls/four exact world-and-auxiliary reload chains are checked
independently alongside 21 native observations, four bounded searches and all 870
MZ relocations. Six tests reject 54 negative variants while allowing an unrelated
elapsed-display change. All 76 portable evidence/control commands and 4,682
archive hashes passed. [Recovery](research/yt-newspaper/events/RECOVERY.md),
[native evidence](research/yt-newspaper/events/NATIVE.md) and
[future implementation](research/yt-newspaper/events/CONTRACT.md) distinguish
observed behavior from modern atomic-save/private-history policies. No gameplay,
schema-27 or dependency changes were made by that research milestone. The creation
follow-up introduced schema 28, and private seller notices are now implemented in
schema 29. Live BBS acceptance, concurrent DOS
writers and native Windows crash durability remain unverified.

    python3 scripts/verify_newspaper_events.py
    python3 scripts/test_newspaper_events_verifier.py


The acquisition controller now applies its 30-second deadline to initialization
as well as execution, and kills/reaps its owned target on timeout without relying
on a responsive Frida connection. Six stalled attach/create/load/readiness/
resume/execution regressions verify cleanup before the outer Python timeout.
The original controller used for retained observations is preserved byte-for-byte
under `research/yt-maint/clock-neutral-acquisition/`; the unchanged manifest still
authenticates those original acquisition bytes. No retained observations or
native hashes were regenerated or redefined by this error-path fix.

Supplemental [tax-funded hiring controls](research/yt-maint/TAX_HIRING_CONTROLS.md)
now retain 24 original-DOS runs across two evolved-world treasury fixtures, two
days and six capture modes. All six output files agree across modes; independent
provenance, treasury debit, literal hiring receipt and raw-zero preservation
checks pass, with six acceptance/corruption tests. This reuses recovered hiring
rules. The before-only five-day replay now composes the modeled three-day prefix,
one treasury edit, tax debits, new-group placement and same-day movement/combat:
72 complete comparisons (432 files), with zero byte mismatches. Twenty-two replay
acceptance/corruption tests include source-derived RNG, casualty and placement
checks. Historical zero-treasury APIs remain strict; general positive-treasury,
active-player and unconstrained hiring worlds remain outside this bounded replay.
No gameplay policy, save format or sysop command changes.

The hiring audit now binds per-group acceptance/rejection checkpoints, rejecting
regrouped attempt lists even when their flattened RNG draws agree. Treasury
admission preserves Earth's excluded raw bytes as well as ordinary-port zeros.

The shared BRUN30 primitive now supports raw-single `RND(argument)`: zero preserves
state, positive arguments advance once, and negative arguments replace the raw
state before advancing. [Native argument controls](research/yt-rng-seeding/RND_ARGUMENTS.md)
retain 16 diagnostic runs / 1,024 exact state-value pairs, eight independent
acceptance/corruption tests and portable Go fixtures. Existing argumentless RNG,
RANDOMIZE, twenty initializer goldens, gameplay streams and save 35 are unchanged.

[Raw-SINGLE INT recovery](research/yt-mbf-int/RECOVERY.md) now qualifies negative
flooring, byte/precision carries and exact zero residues using 16 original-runtime
diagnostic runs (1,024 raw pairs / 51 distinct inputs). The new isolated
`internal/qbmbf.IntSingle` primitive matches every raw result, with ten portable
verifier tests and Go native vectors. Existing positive-stock guards, gameplay,
save format and twenty initializer goldens are unchanged. The SINGLE
contract remains separate from the FIX and DOUBLE supplements below; general
MBF arithmetic is not implemented.

[Raw-SINGLE FIX recovery](research/yt-mbf-fix/RECOVERY.md) now adds truncation
toward zero as a separate `internal/qbmbf.FixSingle` operation. Eight original
runtime diagnostic runs match 512 exact raw records / 28 distinct inputs,
including negative zero residues and the difference from INT flooring. Eight
portable verifier tests and Go native vectors accompany README/plan and CI
updates. Gameplay, saves, generation fingerprints and prior evidence are unchanged.

[Raw-DOUBLE INT/FIX recovery](research/yt-mbf-double/RECOVERY.md) now adds separate
eight-byte `IntDouble`/`FixDouble` primitives. Twenty-four original-runtime
diagnostic runs match 1,536 exact raw records / 42 distinct encodings, including
56-bit precision boundaries that IEEE float64 cannot preserve. Eleven independent
verifier tests and portable Go vectors retain all zero residues and distinguish
flooring from truncation. Existing SINGLE APIs, gameplay streams, saves and
initializer fingerprints are unchanged; general MBF arithmetic remains separate.


[Raw-SINGLE to signed16 recovery](research/yt-mbf-int16/RECOVERY.md) now qualifies
both original memory/FAC conversion entries in measured default mode 0. Ninety-six
single-operation native controls cover 48 encodings: 70 successful conversions
and 26 exact native Overflow outcomes. The isolated `qbmbf.Int16Single` rounds
halves away from zero and reports overflow explicitly; native errors return DOS
ERRORLEVEL 0, so verification checks exact error bytes rather than exit status
alone. Portable Go vectors, nine verifier tests and CI accompany this bounded
recovery. Gameplay, saves, source fingerprints and sysop procedures are unchanged.
The mode-4 branch and general MBF arithmetic are separate from this default-mode
contract; the DOUBLE conversion supplement below is independently qualified.


[Raw-DOUBLE to signed16 recovery](research/yt-mbf-int16-double/RECOVERY.md) now
qualifies both default-mode DOUBLE conversion entries with 104 independent native
controls over 52 raw encodings: 74 results and 30 exact native Overflow outcomes.
`qbmbf.Int16Double` retains all 56 significand bits and reports overflow explicitly.
One-ULP controls below rounding ties distinguish the native result from float64
demotion, including at the positive signed16 limit. Ten independent verifier tests,
full-trace portable Go vectors, README/plan and CI updates accompany this isolated
operation. Existing SINGLE operations, native captures, initializer fingerprints,
gameplay, saves and sysop procedures are unchanged. The mode-4 supplement below
qualifies a separate runtime branch; other MBF arithmetic remains separate.


The [conversion scope audit](research/yt-mbf-int16/CONVERSION_SCOPE.md) removes the
previously listed signed32/LONG conversion backlog: Microsoft documents that
QuickBASIC 3.0 has no LONG integer type (introduced in 4.0). The qualified BRUN30
integer paths are signed16; internal 32-bit calculations or DOS offsets do not
establish a missing LONG language conversion. The separately visible mode-4
branch is now qualified below; other measured MBF arithmetic remains future work.
This corrects planning only; no gameplay, save, evidence or sysop behavior changes.


[Explicit mode-4 signed16 conversion](research/yt-mbf-int16-mode4/RECOVERY.md) now
qualifies all four SINGLE/DOUBLE memory/FAC entries under a declared diagnostic
mode-setting intervention. Across 224 first-attempt controls (including a separately
frozen DOUBLE integer-boundary supplement), 168 conversions and 56 exact native
Overflow outcomes match independent rational flooring. The isolated
`Int16SingleMode4`/`Int16DoubleMode4` APIs floor toward negative infinity with
explicit range failure; default-mode rounding APIs are unchanged. Twelve verifier
acceptance/corruption tests, full-trace Go fixtures, CI and plan updates accompany
this bounded result. No normal mode-4 gameplay caller is inferred, no caller is
switched to it, and saves/source fingerprints/sysop procedures remain unchanged.
Other MBF arithmetic and source-selected call-site integration remain separate.


The [mode-selector caller admission audit](research/yt-mbf-mode-selector/RECOVERY.md)
now retains seven post-startup observations, one for every shipped compiled EXE,
using an untouched runtime and preserving both original startup calls. Every
observed selector is 0. A separately labeled eight-file byte inventory finds five
runtime comparisons and no match for 319 enumerated direct-store signatures;
indirect/later writes are not excluded. An empty provider reference result is
retained without treating it as absence proof. Twelve audit/regression tests and
CI preserve those limits. Existing sector IDs agree numerically in both modes,
while stock pickup uses a distinct MBF INT path supporting values above signed16.
No mode-4 replay migration is admitted; normal late callers remain unestablished.
No gameplay, numeric API, source fingerprint, save or sysop behavior changes.


[Raw-SINGLE addition](research/yt-mbf-add/RECOVERY.md) now qualifies the original
INT3F/81 FAC-plus-memory entry with 82 new native controls: 78 results and four
exact Overflow outcomes. `qbmbf.AddSingle` retains native ties-to-even rounding,
exponent-gap skipping and directional zero residues instead of substituting host
float32 arithmetic. Nine existing HQ reward controls are reused as addition-then-INT
regressions; their native captures and modern gameplay policy are unchanged.
Twelve independent verifier tests, portable raw Go vectors and CI accompany the
new primitive. Cancellation/underflow clears only the initial FAC exponent;
two zero aliases select the right encoding. The direct-entry supplement below
now qualifies memory-to-memory and memory-to-FAC forms; the inline supplement below qualifies address resolution;
subtraction, DOUBLE arithmetic and multiplication/division remain separate.
This isolated API changes no gameplay, source fingerprint, save or sysop behavior.


[Direct addition entry-state parity](research/yt-mbf-add-entries/RECOVERY.md) now
qualifies INT3F/7f memory-to-memory and INT3F/83 memory-to-FAC addition using the
existing kernel evidence and 184 new entry-specific controls: 176 results and
eight exact Overflow outcomes. `AddSingleWithFAC` reuses the qualified arithmetic
with an explicit initial FAC, preserving independent zero-result residues. For
entry83, the right operand is the initial FAC; swapping arguments to `AddSingle`
is incorrect for two zero aliases. Twelve verifier tests, full-trace Go vectors,
CI and plan updates accompany this isolated API. Existing entry81 behavior,
gameplay, source fingerprints, saves and sysop procedures are unchanged. Inline
entry85 resolution is now qualified by the supplement below; other arithmetic remains separate.


[Inline SINGLE addition](research/yt-mbf-inline-add/RECOVERY.md) qualifies the
INT3F/85 address wrapper using retained kernel evidence, three missing source
reads, 138 new first-attempt controls (90 resolver-only, 48 full successful
additions) and a static audit of 35 maintenance callers. The descriptor reached through the segment at
SS:[BP-2] selects one of two separate caller-header bases; selectors have
8-byte stride, high-bit aliases and 16-bit wrapping. `SingleAddInlineOffset`
computes offsets only; full additions reuse `AddSingleWithFAC`. Explicit synthetic
frame/header interventions and a resolver-only return stub are documented;
resolver-only cases never dereference unsafe addresses or claim arithmetic.
Portable traces, eight corruption/acceptance tests, Go native comparisons and CI
cover both protocols. Normal complete maintenance, arbitrary frames and general
unwind remain unqualified; bounded inline Overflow diagnostics are qualified below. Gameplay, save 35 and sysop policy are unchanged.


[Direct SINGLE subtraction](research/yt-mbf-sub/RECOVERY.md) now qualifies
INT3F/97 memory-minus-memory, /99 FAC-minus-memory and /9b memory-minus-FAC.
`SubtractSingle` and `SubtractSingleWithFAC` reuse the qualified addition model
after a register-equivalent right-sign flip, including raw zero aliases. The 266
new native controls (251 results, 15 exact Overflow outcomes) exercise all three
entry/FAC contracts and preserve independent
unnegated FAC residues on cancellation/underflow. Original operand memory, RNG
and mode are checked on successful returns; overflow retains exact diagnostics.
A static original-byte audit covers 43 direct maintenance callers. Portable Go
vectors, twelve verifier tests, CI and the plan accompany this isolated API.
Inline 9d is qualified by the following supplements; DOUBLE subtraction remains separate. Gameplay, save 35, source
fingerprints and sysop procedures are unchanged. Inline addition belongs to the
separate [PR #128](https://github.com/robbiew/yankeetrader/pull/128).


[Inline SINGLE subtraction](research/yt-mbf-inline-sub/RECOVERY.md) now qualifies
bounded successful INT3F/9d execution in explicit synthetic frames. All 89 new
controls completed: 23 resolver-only and 66 full successful subtractions. They
reuse #128's shared resolver and #129's subtraction API; the helper's documented
scope now includes both 85 and 9d. All four selectors at five archived direct
maintenance callers are covered with archived header bases. Portable native Go
comparisons, eleven corruption/acceptance tests, shared verifier checks and CI
preserve opcode/marker separation, sign-flipped zero aliases, unnegated FAC
residues and selected/poison memory. General unwind and complete maintenance
remain unqualified; the following supplement covers bounded fatal diagnostics. Gameplay, save 35 and sysop behavior are unchanged.
PRs #128, #129 and #130 are merged into main.


[Bounded inline Overflow controls](research/yt-mbf-inline-overflow/RECOVERY.md)
now cover both 85 addition and 9d subtraction in declared bootstrap/frame contexts:
twenty first-attempt runs yield twelve exact native fatal diagnostics and eight
finite controls. A new pre-entry protocol captures the runtime error route/hook,
saved BP/SP, module stack and original versus synthetic BP, including 16/32-byte
frame padding. Existing Go arithmetic correctly rejects the overflowing pairs;
no new numeric implementation is needed. Portable raw fixtures, twelve verifier
tests, Go native comparisons, source authentication and CI preserve the exact
consumed-selector error addresses and keep fatal output null. No post-error FAC,
register/RNG preservation, arbitrary unwind, ON ERROR/RESUME, complete maintenance
or live BBS behavior is claimed. Gameplay, source fingerprints, save 35 and sysop
procedures remain unchanged. Direct SINGLE multiplication is qualified by the following supplement.


[Direct SINGLE multiplication](research/yt-mbf-multiply/RECOVERY.md) now qualifies
INT3F/8f memory-times-memory, /91 FAC-times-memory and /93 memory-times-FAC.
`MultiplySingle` and `MultiplySingleWithFAC` preserve original FAC residue for
zero/underflow, flush underflow before rounding, retain exact guard/sticky bits
and ties-to-even, and reject overflow. The 115 new first-attempt controls retain
106 results and nine exact Overflow diagnostics. Existing source observations
were reused; only four missing tail bytes were queried. A static original-byte
inventory identifies 60 direct caller sites and separately excludes 12 inline 95
sites. Portable Go traces, fourteen verifier tests, CI and plan/report updates
accompany the isolated APIs. No production caller, generator policy, source
fingerprint, save 35 or sysop behavior changes. The following supplement covers
inline 95; broader arithmetic and native post-error state remain separate.


[Inline SINGLE multiplication](research/yt-mbf-inline-multiply/RECOVERY.md) now
qualifies bounded INT3F/95 execution by composing the existing resolver and
`MultiplySingleWithFAC(left,FAC,FAC)`. All 81 first attempts completed: 25
resolver-only frames, 42 numeric returns and 14 exact Overflow diagnostics. The
existing twelve source call sites and all five selectors are reused; no new
source query or arithmetic implementation is needed. Fourteen verifier tests,
complete portable Go frames, CI and plan/report updates preserve right-FAC zero
residue, safe/wrapped addressing separation and declared error/frame contexts.
General unwind, ON ERROR/RESUME, arbitrary frames, complete maintenance and live
BBS behavior remain unqualified. Gameplay, source fingerprints, save 35 and sysop
behavior are unchanged. Direct SINGLE division follows below.


[Direct SINGLE division](research/yt-mbf-divide/RECOVERY.md) now qualifies
INT3F/87 memory divided by memory, /89 FAC divided by memory and /8b memory
divided by FAC. `DivideSingle` and `DivideSingleWithFAC` preserve prior-FAC
zero/underflow residue, retain exact quotient remainder for rounding and expose
distinct Overflow and Division by zero errors, with divisor-zero precedence even
for 0/0. Existing source evidence was reused; only the missing 91-byte kernel
tail and 18-byte error text were queried. All 105 first-attempt controls completed:
75 numeric returns, 14 exact Overflows and 16 exact Division by zero diagnostics.
A static inventory matches 24 direct maintenance sites to original bytes.
Portable Go traces, twelve corruption/verifier tests and CI checks accompany the
isolated APIs. Gameplay, source fingerprints, save 35 and sysop behavior are
unchanged. Inline /8d, arbitrary error/unwind contexts, DOUBLE arithmetic and
complete maintenance remain separate. The following supplement qualifies bounded inline /8d.


[Inline SINGLE division](research/yt-mbf-inline-divide/RECOVERY.md) now qualifies
bounded INT3F/8d execution by composing the existing resolver with
`DivideSingleWithFAC(left,FAC,FAC)`. No new source query or arithmetic algorithm
was needed. All 93 first attempts completed: 15 resolver-only controls, 54 numeric
returns, 10 exact Overflow errors and 14 exact Division by zero errors. The
separate protocols preserve right-FAC zero residue, ordered operands, safe/wrapped
addressing boundaries, consumed-selector error addresses and declared padded
frames. The bounded maintenance listing has no inline /8d callers; these are
synthetic controls. Seventeen verifier tests, portable Go traces, CI and plan/report
updates accompany the shared resolver documentation. Gameplay, source fingerprints,
save 35 and sysop behavior are unchanged. General unwind, hooks/RESUME, arbitrary
frames, DOUBLE arithmetic, complete maintenance and live acceptance remain
unqualified. The [reconciled current plan](research/RECONSTRUCTION_PLAN.md#current-work)
marks these SINGLE arithmetic slices and existing DOUBLE INT/FIX/signed16
conversions complete. Direct raw-DOUBLE addition is qualified by the following
supplement; bounded inline /86 is qualified by its own supplement below. Other
DOUBLE binary arithmetic remains separate.


[Direct raw-DOUBLE addition](research/yt-mbf-double-add/RECOVERY.md) now qualifies
INT3F/80 memory plus memory, /82 FAC plus memory and /84 memory plus FAC.
`AddDouble` and `AddDoubleWithFAC` preserve all 56 significand bits, directional
zero aliases, the native exponent-gap cutoff and seven prior-FAC residue bytes
on cancellation/underflow. Bounded integer alignment avoids float64 demotion;
Overflow returns a rejected result without claiming native post-error state.
Existing entry/ABI/error observations were reused; only the missing 352-byte
kernel tail was queried. All 145 first attempts completed: 136 numeric returns
and nine exact Overflows. Sixteen verifier tests, complete portable Go traces,
CI and plan/report updates accompany the APIs. The original-byte inventory has
14 direct callers and four separately excluded inline /86 sites. Gameplay,
source fingerprints, save 35 and sysop behavior are unchanged. The following
supplement qualifies bounded inline /86; other DOUBLE arithmetic and general
unwind remain separate.


[Inline DOUBLE addition](research/yt-mbf-inline-add-double/RECOVERY.md) now
qualifies bounded INT3F/86 by composing the shared offset resolver with
`AddDoubleWithFAC(left,FAC,FAC)`. All entry/kernel/caller source was reused; no
new source query or arithmetic algorithm was needed. The four retained source
caller sites use selectors 80/8a; new address controls also exercise their actual
header words. All 113 first attempts completed: 19 resolver-only controls,
80 numeric returns and 14 exact Overflows. Distinct eight-byte protocols preserve
seven-byte FAC residue, low significand bits, unchanged operand/poison blocks
and consumed-selector error addresses in declared baseline/padded frames.
Wrapped offsets remain address-only; complete reads use safe eight-byte spans.
Eighteen verifier tests, portable Go traces, CI and plan/report updates accompany
the shared resolver documentation. Gameplay, source fingerprints, save 35 and
sysop behavior are unchanged. Next: audit retained direct DOUBLE subtraction
evidence/callers before choosing missing controls. Other DOUBLE arithmetic,
general unwind, complete maintenance and live acceptance remain separate.

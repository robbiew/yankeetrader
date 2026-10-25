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

1. Complete the remaining navigation/encounter research: danger scanners, cloak visibility, emergency warps and NPC/utility commands. The first sensor/path/autopilot slice is now implemented; see [navigation recovery](yt-navigation/RECOVERY.md).
2. Add port acquisition, buyouts and treasury collection with targeted DOS validation of the untested buyout branch.
3. Add teams and shared assets, preserving transactional role/membership checks.
4. Add combat and death/respawn with active-session invalidation before enabling dangerous sectors, then NPC behavior, computer functions, communications and Genesis.
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

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

1. Recover remaining navigation/scanning, NPC encounters, and utility commands, with exploit reproduction included. Planet management, trading, major combat modes, maintenance, and Genesis now have evidence-backed first-pass specifications.
2. Build the independent rules engine, transactional storage, godoors session interface, and sysop tools.
3. Deliver a playable join/move/scan/trade/equipment/save loop, followed by ports, planets, and coordinated maintenance.
4. Add combat, death/respawn, teams, computer functions, communications, and NPC behavior.
5. Compare intended mechanics against DOS fixtures and test deliberate exploit fixes, concurrency, interrupted maintenance, disconnects, and restoration.
6. Playtest balance changes and document all intentional departures from original 3.6 behavior before release.

## Playable Go milestone — 2026-10-24

The standalone [modern Go door](../modern/README.md) now implements persistent join/reconnect, adjacent movement, port docking, cargo trading, Earth equipment, automatic transactional saves and once-per-date port-economy/turn maintenance. Its macOS binary and a fresh 3,000-sector/1,000-port world are ready under `modern/`. GoDoors is used through the existing local checkout without changing that library.

Money is integer-based; Earth equipment cannot recycle owner revenue; maintenance is idempotent and rollback does not grant production; every mutation reloads state under an OS process lock and docking tokens invalidate stale quotes. Five recorded DOS ore-trading examples are executable Go fixtures. This first universe generator and fixed reference prices are provisional; planets, teams, combat, NPCs, acquisition, Genesis and complete maintenance parity are not yet ported.

Validation covers race-enabled unit/session/storage tests, concurrent processes, killed lock-holder recovery, real PTY/GoDoors operation, Door32 local transport, reconnect and stable identity across alias changes. Windows/Linux cross-builds are distinct from native BBS/socket acceptance. See [validation evidence](../modern/evidence/VALIDATION.md).

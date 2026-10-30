# Genesis and universe reset

This is the historical first recovery. A [bounded safe-reset follow-up](SAFE_RESET.md)
adds 24 fresh returned DOS controls, thirteen native observations and a concrete
implementation contract. Genesis is still unavailable in the Go door; research
does not perform a live reset or change save version 22.

Recovered from the original YT.EXE and RMT-INIT.EXE and validated in isolated DOSBox runs. Original files remain unchanged. This is the global `G` endgame command, distinct from buying a planet with a Genesis Device.

## Eligibility and confirmation

YT.EXE reads configuration record 1, MBF32 offset 105, into `1c48` (submodule `1f42:be3e..be47`). On load, a value **below 20 becomes 200** in memory (`bea0..beb4`). Values from 20 through 300 are usable. A value **above 300 disables Genesis**, even for a player who owns enough ports.

The `G` handler (`1000:2728..2858`) asks `Are you that Trader ... [y/N]`. Default/No cancels. Yes compares the player's cached owned-port count (`4e5e`, player offset 117 loaded at `a521..a52a`) with the effective threshold. Equality succeeds. There is no additional wealth, score, rank, sector, or NPC-defeat test in this handler. No recount of port records occurs.

The normal default is **300**, confirming the stored initializer default and YTCONFIG display. YT-INIT's printed 450 is stale. DOS evidence:

| Scenario | Configuration | Stored count | Actual owned ports | Outcome |
|---|---:|---:|---:|---|
| gen-299 | 300 | 299 | 299 | Rejected; explicitly says one short |
| gen-300 | 300 | 300 | 300 | Complete reset |
| gen-cancel | 300 | 300 | 300 | No cancels; existing world retained |
| gen-disabled | 301 | 301 | 301 | FUNCTION DISABLED; world retained |
| gen-counter | 300 | 300 | 0 | Complete reset; trusts counter |
| gen-custom | 2 | 2 | 2 | Rejected; effective requirement 200 |
| gen-custom200 | 2 | 200 | 200 | Complete reset; stores normalized 200 |
| gen-20 | 20 | 20 | 20 | Complete reset; preserves 20 |

The deliberately inconsistent counter fixture establishes a missing integrity check, not a demonstrated player-accessible way to forge that counter.

## Successful endgame

`1000:2829..2855` closes files, writes a handoff string to `RMTINIT.TMP`, and chains to **RMT-INIT.EXE**. It does not invoke YT-INIT. The remote initializer consumes/deletes the marker and rebuilds the current game's files. No further reset confirmation was required in these local game-triggered runs. An independently launched RMT-INIT has a separate confirmation path; that standalone path was inspected but not exercised here.

Four complete reset runs were captured. The standard 300-port world retained its 568,687-byte size (4,151 records ×137) but every record changed. All 50 human-player slots were cleared, including the winner. All 1,000 ports became unowned; Earth returned to sector 1. Sector warp data was regenerated, the Xannor HQ was reselected, and all planet slots were marked inactive. Some inactive records contain reused configuration-buffer values rather than zero bytes; activity markers matter when interpreting these records.

The initializer reuses configured population limits, starting resources, daily turns, lottery limit, deletion limit, cargo limit and scoreboard filename. Customized tests retained 777 turns/day, 31 starting fighters, 4,321 credits, 17 holds, 9-day deletion limit, 7 lottery plays, and 850 maximum holds. It **resets the game year to 6324**, even when the previous value was 7000. It sets last maintenance to yesterday and port production timestamps ten days back, with stock initially zero.

It replaces today's/yesterday's newspapers, resets the alias file to `Dummy,Dummy,Dummy,Dummy`, and replaces radio messages with initialization announcements. The test newspaper and congratulations messages had an empty winner name. These fixtures use simplified LOCAL alias mappings; this does not yet establish whether ordinary BBS door mappings preserve the winner name. There is no durable winner-history file created in the observed path; archive winner/season results explicitly in the modern implementation.

**RMT-INIT does not run maintenance.** `gen-postmaint` copies the completed reset, then runs the original YTMAINT on the same DOS date. That run completed successfully, advances last-maintenance day 296→297, fills Earth's stock to ten days of production, and creates The Wanderer, Mercenary Base, and Xannoron. This corroborates the original YTSYSOP.DOC instruction to run maintenance after RMT-INIT. Full-reset and post-maintenance snapshots are preserved separately.

## Evidence and reconstruction decisions

- `archive/analysis/yt-combat/experiments/gen-*`: isolated DOS logs, input streams, before/after saves, and copied original executables. Some sessions end at the emulator deadline; successful resets are established by completion messages and full file-state checks, not by normal logout.
- Archived `archive/analysis/yt-genesis/{qb-annotated.txt,qb-listing.txt,listing.txt,decompiled.c,program.txt}` and Ghidra logs: remote initializer recovery. Runtime-aware listing is more useful than automatic C output for QuickBASIC. `annotate.py` resolves near-data descriptors. Some variable-length runtime table calls remain undecoded.
- `recovered-genesis.bas`: semantic pseudocode for eligibility and handoff.
- Historical `archive/analysis/yt-genesis/fixtures.py` and `scenarios.json` record the original construction/input provenance; their old `analysis/` paths are not active regeneration commands. Do not run old fixture writers against the preserved archive. Use the repository-root `scripts/recover_genesis_reset.py` command in the follow-up report with a fresh disposable destination. `gen-postmaint` remains the archived copy of completed `gen-300` with YTMAINT run on 10/24/2026.
- Historical `archive/analysis/yt-genesis/validate.py` preserves the old assertions. The active portable follow-up verifier is `scripts/verify_genesis_reset.py`, with rehashed corruption controls in `scripts/test_genesis_reset_verifier.py`.

For Go, make a season reset transactional, invalidate existing sessions, archive the winner before deleting players, regenerate the world and complete initial maintenance before reopening play. Recount owned ports in the same transaction used for eligibility. Treat the hidden <20→200 fallback and >300 disable behavior as explicit compatibility/configuration decisions rather than silently copying them. Crash recovery and concurrent sessions during a DOS reset remain untested; atomicity is a requirement for the new implementation, not an asserted DOS guarantee.

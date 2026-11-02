# Recovery evidence

These notes record reverse engineering of Yankee Trader 3.6 and the subsequent
Go implementation milestones. They distinguish observed DOS behavior, static
leads, validated outcomes and deliberate modern policies. Historical reports are
not promises of complete modern parity, and a research-era “next” or
“unimplemented” statement is not the current project backlog.

Start with the [current reconstruction baseline and ordered backlog](RECONSTRUCTION_PLAN.md#current-implementation-and-next-work--checked-2026-11-02),
checked against merged main through PR #72 on 2026-11-02, then extended by the
opt-in port-parity slice using save format **33**.
The [root README](../README.md#playable-feature-overview) describes playable
features and usage; the [sysop guide](../docs/SYSOP.md) covers modern save exports,
backups and restoration. DOS save import/export remains unsupported.

Recent completed work includes [season administration](../README.md#season-administration)
(save 30), [extended newspaper events](yt-newspaper/remaining/RECOVERY.md)
(save 31), and the [direct Xannor fighter-casualty turn bonus](yt-xannor-turn-bonus/RECOVERY.md)
(save 32). Newspaper registration/team/combat coverage is implemented; general
“remaining newspaper events” deferrals in older reports are historical. Private
port-sale notices are implemented as private mail, not public acquisition news.
The [port generation and startup pricing slice](yt-port-generation/RECOVERY.md)
is implemented as an opt-in new-world profile (save 33). Original warp generation
is next; precise RNG/numeric parity and target-BBS acceptance remain separate
boundaries.

Included here:

- [Port generation and startup pricing](yt-port-generation/RECOVERY.md): fresh pre/post-maintenance DOS worlds, recovered naming/economy rules and the opt-in save 33 implementation; exact DOS graph/RNG remains separate.

- Recovery reports for initialization, maintenance, planets, teams, trading, combat and Genesis, plus the spreadsheet assessment.
- Runtime-aware annotated YT.EXE listings used to recover planet routines.
- Compressed before/after saves, logs and keystrokes for all 24 counted DOS planet experiments. `planet-snapshots.json` contains hashes of their **uncompressed** bytes. No executable is embedded in these snapshots.
- Original-DOS sector mine-placement transcripts, inputs, emulator logs and compressed before/after saves, with an independent verifier for stock, field and turn deltas.
- Compact Go golden fixtures in `../internal/game/testdata`, with original snapshot hashes. Nineteen planet scenarios supplied the initial implementation fixtures. Relocation and ground-force assault are now implemented separately; their original experiments remain archived as historical evidence.

Run `python3 scripts/verify_planet_evidence.py` from the repository root to check the packaged snapshots and golden provenance. Go tests run without Python or the original DOS distribution.
Run `python3 scripts/verify_mine_placement.py` to validate the mine-placement sessions and expected outcomes.

The complete DOS distribution, workbook, Ghidra project, original validators and raw experiments are preserved in [`../archive/`](../archive/README.md). Original EXE hashes are in `executable-inventory.json`. Historical reports and logs retain their original source locations as provenance.

From the repository root, regenerate the compact planet fixtures with `python3 scripts/export_planet_evidence.py archive`. Refresh this research bundle with `python3 scripts/package_research.py archive`. The exporter retains the DOS money-rounding results as evidence; Go tests explicitly expect corrected, conserved balances instead.

Older experiment scripts expect DOS files beside `analysis/` and write results into that tree. Prepare a disposable workspace with `python3 scripts/prepare_recovery_workspace.py /tmp/yankeetrader-recovery`, then run them there. The destination must not already exist. See the archive README for details.

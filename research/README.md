# Recovery evidence

These notes record reverse engineering of Yankee Trader 3.6 and the subsequent
Go implementation milestones. They distinguish observed DOS behavior, static
leads, validated outcomes and deliberate modern policies. Historical reports are
not promises of complete modern parity, and a research-era “next” or
“unimplemented” statement is not the current project backlog.

Start with the [current reconstruction baseline and ordered backlog](RECONSTRUCTION_PLAN.md#current-work),
checked against merged main through PR #150, using current save format **35**.
The twenty-control source generator, safe projection, playable `qb36-v1` recipes,
Genesis/admin reset integration and bounded multi-day acceptance are implemented.
Direct and bounded inline SINGLE arithmetic, SINGLE/DOUBLE INT/FIX and signed16
conversions are also complete within their documented native controls.
[Direct DOUBLE addition](yt-mbf-double-add/RECOVERY.md) and
[direct subtraction](yt-mbf-subtract-double/RECOVERY.md) are qualified by native
controls. [Bounded inline addition](yt-mbf-inline-add-double/RECOVERY.md)
is merged in PR #138; do not repeat it. [Bounded inline subtraction /9e](yt-mbf-inline-subtract-double/RECOVERY.md)
is now qualified separately with synthetic controls. [Direct DOUBLE multiplication](yt-mbf-multiply-double/RECOVERY.md) is now
qualified by its separate native corpus and Go APIs. [Bounded inline /96](yt-mbf-inline-multiply-double/RECOVERY.md) is qualified
separately with synthetic controls. [Direct DOUBLE division](yt-mbf-divide-double/RECOVERY.md) is now qualified,
including distinct early/late underflow residues and both error kinds. [Bounded inline /8e](yt-mbf-inline-divide-double/RECOVERY.md) now qualifies
that separate synthetic entry/frame slice. Direct division PR #144 is merged; the inline PR now targets main. After its merge, audit
remaining runtime/maintenance gaps against implemented APIs and open work.
The [root README](../README.md#playable-feature-overview) describes playable
features and usage; the [sysop guide](../docs/SYSOP.md) covers modern save exports,
backups and restoration. DOS save import/export remains unsupported.

Earlier completed gameplay milestones include [season administration](../README.md#season-administration)
(save 30), [extended newspaper events](yt-newspaper/remaining/RECOVERY.md)
(save 31), and the [direct Xannor fighter-casualty turn bonus](yt-xannor-turn-bonus/RECOVERY.md)
(save 32). Newspaper registration/team/combat coverage is implemented; general
“remaining newspaper events” deferrals in older reports are historical. Private
port-sale notices are implemented as private mail, not public acquisition news.
The [port generation and startup pricing slice](yt-port-generation/RECOVERY.md)
is implemented as an opt-in new-world profile (save 33). The [warp-generation slice](yt-warp-generation/RECOVERY.md) adds independently
opt-in DOS map rules (save 34), including repaired connectivity and Earth shortcuts.
The [RNG seeding follow-up](yt-rng-seeding/RECOVERY.md) verifies raw seeding and
selected exact graph replay; the complete bounded source generator is now
implemented separately. General numeric/runtime parity, production DOS maintenance
and target-BBS acceptance remain separate boundaries.

Included here:

- [QuickBASIC RNG seeding](yt-rng-seeding/RECOVERY.md): raw timer/seed/RND traces, preserved zero residue, shared primitive and bounded exact graph replay.

- [DOS warp generation](yt-warp-generation/RECOVERY.md): native ordinary/long-edge, repair and shortcut controls, positive-half-up rounding and independent save 34 map profile.

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

- [Exact graph/port stream replay](yt-port-replay/RECOVERY.md): six complete clock targets, raw 137-byte port records, twelve native phase states and independent corruption checks; research only.

- [Complete pre-maintenance initializer replay](yt-initializer-replay/RECOVERY.md): all 4,151 records synthesized across ten bounded targets, including configuration/planet FIELD inheritance, sector FAC residues and fresh date/path/auxiliary controls. Research only.

- [Proposed QB production compatibility contract](yt-initializer-replay/COMPATIBILITY_CONTRACT.md): explicit raw state/date, exact source versus modern projection, admission failures, saved provenance and repeat-layout reset policy. Design only; next implementation is the bounded Go source generator and portable fixtures.

- [Pure Go initializer source generator](yt-initializer-replay/GO_IMPLEMENTATION.md): ten complete native golden cases and RNG endpoints, portable hash fixtures, original DATA verification and bounded no-partial-output failures. Safe playable projection remains next.

- [Safe QB source projection/admission](yt-initializer-replay/PROJECTION.md): unpublished modern candidates, collision/protected-HQ/connectivity rejection, current UTC stocks/watermarks and independently seeded required-home bootstrap. CLI/save/reset integration remains next.

- [Direct SINGLE comparison flags and branch conditions](yt-mbf-single-compare/RECOVERY.md): 216 native controls, retained source/ABI, 203 original-byte direct callers; isolated Go primitive and immutable evidence checks.

- [Direct DOUBLE comparison flags and branch conditions](yt-mbf-double-compare/RECOVERY.md): 486 native controls, retained source/ABI, thirty direct callers, full four-word ordering; inline /a6 excluded.

- [Bounded inline SINGLE comparison /a5](yt-mbf-inline-single-compare/RECOVERY.md): 275 full native flag/branch controls and 21 resolver-only controls, sixteen static callers, reused resolver/direct APIs; inline DOUBLE remains separate.

- [Bounded inline DOUBLE comparison /a6](yt-mbf-inline-double-compare/RECOVERY.md): 329 full eight-byte flag/branch controls, nineteen resolver-only controls and seven static callers; retained resolver/direct evidence reused.

- [Raw sign/zero-test entries /a7–/aa](yt-mbf-sign-zero/RECOVERY.md): 248 native flag/branch controls, 102 original-byte callers and a four-byte source supplement; existing comparison-against-zero primitives reused.

- [Bounded pure Go clean-port maintenance replay](yt-maint/GO_CLEAN_PORT_REPLAY.md): 32 existing native blocks / 32,000 exact records, portable before-only inputs, unchanged independent Python reference and guarded research-only API.

- [Bounded Go inactive rank-cache/watermark writer](yt-maint/GO_INACTIVE_RANK_REPLAY.md): 1,632 exact native fields across 32 retained runs, before-only synthesis and complete unrelated-byte preservation; active rankings excluded.

- [Bounded Go initial Wanderer creation/placement](yt-maint/GO_WANDERER_BIRTH_REPLAY.md): 29 whole native records and links, three declared later-encounter exclusions, raw TIMER seeding and inherited bytes; other NPC phases excluded.

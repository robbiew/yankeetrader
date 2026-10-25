# Recovery evidence

These notes record reverse engineering of Yankee Trader 3.6 before the Go port. They distinguish DOS behavior, static leads and validated outcomes. The Go implementation intentionally fixes documented defects; historical reports are not promises of complete modern parity.

Included here:

- Recovery reports for initialization, maintenance, planets, teams, trading, combat and Genesis, plus the spreadsheet assessment.
- Runtime-aware annotated YT.EXE listings used to recover planet routines.
- Compressed before/after saves, logs and keystrokes for all 24 counted DOS planet experiments. `planet-snapshots.json` contains hashes of their **uncompressed** bytes. No executable is embedded in these snapshots.
- Compact Go golden fixtures in `../internal/game/testdata`, with original snapshot hashes. Nineteen planet scenarios are relevant to this implementation; relocation and ground-force assault cases remain archived for future work.

Run `python3 scripts/verify_planet_evidence.py` from the repository root to check the packaged snapshots and golden provenance. Go tests run without Python or the original DOS distribution.

The complete DOS distribution, workbook, Ghidra project, original validators and raw experiments are preserved in [`../archive/`](../archive/README.md). Original EXE hashes are in `executable-inventory.json`. Historical reports and logs retain their original source locations as provenance.

From the repository root, regenerate the compact planet fixtures with `python3 scripts/export_planet_evidence.py archive`. Refresh this research bundle with `python3 scripts/package_research.py archive`. The exporter retains the DOS money-rounding results as evidence; Go tests explicitly expect corrected, conserved balances instead.

Older experiment scripts expect DOS files beside `analysis/` and write results into that tree. Prepare a disposable workspace with `python3 scripts/prepare_recovery_workspace.py /tmp/yankeetrader-recovery`, then run them there. The destination must not already exist. See the archive README for details.

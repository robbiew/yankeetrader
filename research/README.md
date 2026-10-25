# Recovery evidence

These notes record reverse engineering of Yankee Trader 3.6 before the Go port. They distinguish DOS behavior, static leads and validated outcomes. The Go implementation intentionally fixes documented defects; historical reports are not promises of complete modern parity.

Included here:

- Recovery reports for initialization, maintenance, planets, teams, trading, combat and Genesis, plus the spreadsheet assessment.
- Runtime-aware annotated YT.EXE listings used to recover planet routines.
- Compressed before/after saves, logs and keystrokes for all 24 counted DOS planet experiments. `planet-snapshots.json` contains hashes of their **uncompressed** bytes. No executable is embedded in these snapshots.
- Compact Go golden fixtures in `../internal/game/testdata`, with original snapshot hashes. Nineteen planet scenarios are relevant to this implementation; relocation and ground-force assault cases remain archived for future work.

Run `python3 scripts/verify_planet_evidence.py` from the repository root to check the packaged snapshots and golden provenance. Go tests run without Python or the original DOS distribution.

The complete DOS distribution, workbook, Ghidra project, original validators and other raw experiments remain preserved at `/Users/robbie/Downloads/YT36`. Historical reports may refer to those larger, unbundled experiments or original uncompressed filenames. The original EXE hashes are in `executable-inventory.json`; this repository contains no DOS EXEs, runtime binaries or generated Go executables in tracked source.

To regenerate the compact planet fixtures from that full archive, run `python3 scripts/export_planet_evidence.py /Users/robbie/Downloads/YT36`. To refresh this research bundle, use `scripts/package_research.py` with the same archive path. The exporter retains the DOS money-rounding results as evidence; Go tests explicitly expect corrected, conserved balances instead.

# Complete recovery archive

This directory consolidates the recovery workspace as of 2026-10-25. Original files are copied byte-for-byte; the Downloads source remains intact. This private repository is the working home for future recovery.

- `dos-original/`: original DOS distribution, executables, documentation and artwork. Original author notices are retained; inclusion here does not grant redistribution rights or apply a new license to the original game.
- `analysis/`: complete experiment fixtures and outputs, disassembly, recovery notes, Ghidra projects/scripts, and saved tool preferences. Existing internal relative paths are preserved.
- [Art/menu gallery](analysis/art-menus/index.html): open locally in a browser.
- `references/ytcalc.xls`: original player helper workbook.
- `manifest.json`: source provenance, sizes and SHA-256 for every imported file, plus an explicit exclusion list. Verify with `python3 scripts/verify_archive.py` from the repository root.

Generated caches, compiled Python files, transient locks and machine runtime settings are excluded. Experimental DOS saves are reproducibility fixtures; the live Go save remains ignored under `data/`.

`research/` at the repository root remains the compact curated evidence package used by the Go tests. Its selected reports/snapshots overlap this complete raw archive intentionally; keep the original fixtures immutable. Historical scripts and reports can contain absolute Downloads paths: inspect their input/output configuration before rerunning them, and direct new work into disposable directories. Do not run DOS executables on a host directly; use an isolated emulator copy.

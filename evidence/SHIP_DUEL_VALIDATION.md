# Ship-duel calculations and credit settlement validation — 2026-10-26

Passed locally:

- `go test -race ./...` and `go vet ./...`.
- Nine injected-RNG comparisons against the pinned archived recovery model,
  independently checked by `scripts/verify_ship_duel_model.py`. These are model
  cases, not additional DOS sessions or captured DOS random streams.
- Fighter/shield batch and threshold boundaries, cloak adjustment, final fighter
  accounting, bad inputs/draws and the one-million-round resource guard.
- Atomic precomputed credit-salvage tests: consumption from the victim, overflow,
  moved/stale/friendly targets, still-defended ships, replay after replacement,
  concurrent claims and complete rollback after a later estate step aborts.
- Linux/amd64 and Windows/amd64 cross-builds.
- Archive verification: all 4,682 original files unchanged.
- Formatting and `git diff --check`.

There are no frontend or save-format changes in this milestone; the helpers are
not connected to any player command. New PTY/BBS combat acceptance is therefore
not claimed. Full loot distributions, equipment/estate effects, cloak visibility,
retaliation and attack commands remain pending. The recorded 6,689-credit DOS
example supplies a test transfer amount, not a newly recovered sampling formula.

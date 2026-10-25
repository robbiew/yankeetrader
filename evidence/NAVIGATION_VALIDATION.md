# Navigation/scanning validation — 2026-10-25

Implemented on local branch `codex/navigation-scanning`, based on `fe1c02e`.
The original checkout's uncommitted work was left untouched.

Passed on macOS arm64 with Go 1.27.3 and the existing local GoDoors checkout:

- `go test -race ./...`: game, store, door and CLI packages.
- `go vet ./...`.
- `python3 scripts/verify_navigation_evidence.py`: 13 original DOS sessions,
  26 full save snapshots, sensor transcripts, directed paths and Go fixture
  provenance.
- `python3 scripts/verify_archive.py`: all 4,682 archived files verified.
- `python3 scripts/smoke_navigation.py`: real PTY/GoDoors sensors, path display,
  cancelled and accepted autopilot, persisted destination/turn cost.
  [Transcript](navigation-smoke.txt).
- `python3 scripts/smoke.py`: existing trading/equipment, planet, reconnect,
  repeat-maintenance and Door32 local-transport regression scenarios.
  [Transcript](local-smoke.txt).
- Linux amd64 and Windows amd64 cross-builds completed. These establish
  compilation only, not native Windows/Linux terminal, socket, or BBS acceptance.

Unit/session tests additionally cover stopping on Ctrl-X, preserving other typed
keys during polling, confirmation disconnects, output failure after one committed
hop, stale position, and turns spent by a competing session. Completed moves
remain saved; rejected moves/courses do not consume turns.

REA 6.8.0/Ghidra 12.1.4 verified the original YT.EXE loaded image and provided
bounded string searches and exact dispatch/display bytes. The evidence bundle
was exported and the analysis session closed. Original executable identity and
all DOS runtime outcomes are linked in the
[recovery report](../research/yt-navigation/RECOVERY.md).

The worktree has an ignored local `go.work` pointing to
`/Users/robbie/GitHub/godoors`; the committed `go.mod` is unchanged. Its native
`bin/yt` is built for local play. Use a new data directory for this checkout;
the existing player's world was not migrated or modified.

No live BBS acceptance, complete DOS navigation parity, combat-hazard support,
or native Windows durability claim is made by this milestone.

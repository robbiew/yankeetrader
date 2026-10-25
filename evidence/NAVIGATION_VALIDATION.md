# Navigation/scanning validation — 2026-10-25

Validation host: macOS arm64, Go 1.27.3. The declared minimum Go version is
1.23; these results do not establish execution on that minimum toolchain.
Use GoDoors commit `9364a49ddd7c396ccbfcdd3c240c104ea9178551` or a descendant
at `../godoors`, or point the module replacement at that checkout.

From the repository root, the following checks passed:

- `go test -race ./...`: game, store, door and CLI packages.
- `go vet ./...`.
- `python3 scripts/verify_navigation_evidence.py`: 13 original DOS sessions,
  26 full save snapshots, sensor transcripts, directed paths and Go fixture
  provenance.
- `python3 scripts/verify_avoid_evidence.py`: 10 additional DOS sessions and
  20 save snapshots covering avoid slots, route effects and DOS reconnect reset.
- `python3 scripts/verify_archive.py`: all 4,682 archived files verified.
- `python3 scripts/smoke_navigation.py`: real PTY/GoDoors sensors, path display,
  cancelled and accepted autopilot, persisted destination/turn cost, avoid-list
  reconnect/clear, Ctrl-X and queued-key preservation.
  [Transcript](navigation-smoke.txt).
- `python3 scripts/smoke.py`: existing trading/equipment, planet, reconnect,
  repeat-maintenance and Door32 local-transport regression scenarios.
  [Transcript](local-smoke.txt).
- Linux amd64 and Windows amd64 cross-builds completed. These establish
  compilation only, not native Windows/Linux terminal, socket, or BBS acceptance.

Unit/session tests additionally cover stopping on Ctrl-X, preserving other typed
keys during polling, confirmation disconnects, output failure after one committed
hop, stale position, turns spent by a competing session, and avoid-list changes
while confirmation is open or between committed hops. Completed moves
remain saved; rejected moves/courses do not consume turns.

REA 6.8.0/Ghidra 12.1.4 verified the original YT.EXE loaded image and provided
bounded string searches and exact dispatch/display bytes. The evidence bundle
was exported and the analysis session closed. Original executable identity and
all DOS runtime outcomes are linked in the
[recovery report](../research/yt-navigation/RECOVERY.md).

Build the native executable with `go build -o bin/yt ./cmd/yt` before running
the PTY scripts. They create disposable worlds. The DOS recovery runner locates
`dosbox-staging` on `PATH`; `--dosbox` selects another executable path.
The archived `local-smoke.txt` transcript is retained unchanged because its
elapsed-time production values vary on each run.

No live BBS acceptance, complete DOS navigation parity, combat-hazard support,
or native Windows durability claim is made by this milestone.

Review follow-up: the door tests also pass against the exact minimum GoDoors
revision `9364a49ddd7c396ccbfcdd3c240c104ea9178551`. The portable DOS launcher
was checked with a missing executable (clear diagnostic, no destination created)
and by rerunning the `avoid-slot30` probe through PATH discovery; the recorded
alternate route and unchanged turn balance were reproduced.

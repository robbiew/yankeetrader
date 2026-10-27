# Port ownership validation — 2026-10-26

Implemented port acquisition, forced buyouts, personal treasury reporting and
remote collection. No save schema changes are required.

Passed locally:

- Nine original DOS sessions / 18 compressed snapshots, hash/provenance checks
  and executable Go golden cases (`scripts/verify_ownership_evidence.py`).
- `go test -race ./...`: game, session, command and storage tests, including
  simultaneous buyouts/collections, cancelled/disconnected/stale confirmations,
  capacity overflow, preview purity, personal ownership and docking invalidation.
- `go vet ./...` and macOS build; Linux/amd64 and Windows/amd64 cross-builds.
- `python3 scripts/smoke_ownership.py`: actual PTY/GoDoors buyout, seller payout,
  later commission to the new owner, remote collection, repeated collection,
  reconnect. Transcript: [ownership-smoke.txt](ownership-smoke.txt).
- Existing `scripts/smoke.py`: trading, equipment, planets, reconnect,
  maintenance and local Door32 identity regression.
- Existing navigation, avoid, encounter/follow-up, hazard, utility and commerce
  evidence verifiers; archive verifier still confirms 4,682 unchanged files.
- `git diff --check`.

Cross-builds are not native transport acceptance. The earlier user-confirmed
live-BBS load predates this feature. New ownership gameplay on the live BBS and
exact DOS screen-cell parity for the new prompts remain unverified.

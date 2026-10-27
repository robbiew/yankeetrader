# Team milestone validation — 2026-10-26

Implemented `T`/`TEAM` membership, captain controls, visiting-member succession,
team planet locations and authoritative shared-planet access revocation.

Passed locally:

- `go test -race ./...` and `go vet ./...`.
- Fourteen archived DOS membership cases / 28 source save hashes verified by
  `scripts/verify_team_evidence.py` and executed as Go fixtures. Tests cover
  creation, join, wrong invitation, full roster, departure, removal/rejoin,
  captain-only password changes and visiting-member succession.
- Additional tests cover concurrent last-slot joins and successor visits,
  invitation rotation, malformed saves, versions 1/2 upgrading to version 3,
  asset/balance/avoid-list preservation, role changes during a prompt, interrupted
  creation and immediate revocation of active shared landings.
- `scripts/smoke_teams.py`: actual PTY/GoDoors masked creation/join, shared bank,
  private port accounts, removal/rejoin, retained assets and captain succession.
  Transcript: [team-smoke.txt](team-smoke.txt).
- Existing PTY smoke for trading/equipment/planets, ownership, navigation,
  startup, ports and all 14 planet rename cases in ANSI and ASCII. Existing
  reference evidence was preserved; the rename builder now supplies valid team
  metadata for its controlled team-access fixture.
- macOS build; Linux/amd64 and Windows/amd64 cross-builds.
- Archive verification: 4,682 files unchanged. `git diff --check` passes.

CI now includes the team/ownership verifiers and PTY smoke scripts. These new
team changes have only been validated locally; PR #11's passing CI concerns its
separate port-ownership head, not this branch's new team commit. Native BBS
team acceptance, exact DOS team-menu screen cells, sector defenses and fighter
reinforcement remain pending. Save format 3 and rollback instructions are
covered in [the implementation report](../research/yt-teams/IMPLEMENTATION.md).

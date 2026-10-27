# Ship lifecycle foundation validation — 2026-10-26

Implemented internal atomic death/replacement and saved generation checks across
live session reads and updates. Attacks, hazards and loot remain disabled.

Passed locally:

- `go test -race ./...` and `go vet ./...`.
- Engine tests for enemy, retaliation, self and environmental attribution,
  same-day 37-turn preservation, next-day maintenance, self cooldown, stale or
  moved targets/attackers, teammate rejection, repeat death/replacement,
  generation overflow, stale dock agreements and malformed dead saves.
- Store tests with a separate OS process performing death/replacement, proving
  that the old generation's callback never executes. Aborted settlement rolls
  back both death and generation. Version-3 upgrade preserves team hashes,
  membership, account assets, money and avoidance preferences; read-only loading
  does not write the save. Earlier version-1/version-2 upgrade tests also pass.
- Session tests for death/replacement during purchase confirmation, team password
  entry and an idle command chain, plus replacement through both frontends.
- `GOCACHE=/tmp/yankeetrader-go-cache python3 scripts/smoke_lifecycle.py`:
  real PTY/GoDoors caller plus independent test worker; old commands rejected
  before and after replacement; fresh authenticated login preserves 37 turns.
  Transcript: [lifecycle-smoke.txt](lifecycle-smoke.txt).
- Existing PTY smoke for trade/equipment/planets, ownership, teams, navigation and
  startup. Existing reference evidence was preserved after those checks.
- macOS build; Linux/amd64 and Windows/amd64 cross-builds.
- Team/ownership evidence verifiers and all 4,682 immutable archive files.
- Formatting and `git diff --check`.

The research basis is the existing original-DOS lifecycle/online experiments;
no new DOS session is claimed by this milestone. This implements the bounded
session/death safety layer, not the entire EXP-004 salvage/respawn exploit chain.
Combat settlement and asset-transfer rules, protected-sector hazard drops, exact
RNG/MBF behavior and live-BBS combat acceptance remain pending. CI includes the
new lifecycle smoke, but this commit has not been pushed for CI.

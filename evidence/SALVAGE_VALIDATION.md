# Loot/estate implementation validation — 2026-10-27

Passed locally:

- `go test -race ./...`, `go vet ./...`, Go formatting and `git diff --check`.
- Nine independent research-model fixtures for six-stock RNG order, capped hold
  expansion and cargo sampling without replacement (`verify_salvage_model.py`).
- Rational-arithmetic comparisons for exact stock scaling up to MaxMoney,
  including near-one, subnormal and half-boundary random inputs.
- Inventory conservation, replay after replacement, cash/weapon overflow,
  invalid random draws, stale targets, small frozen inventories, ordinary-port
  capture/treasuries, self/environmental release, team access revocation, unchanged
  planets, Mercenary defense conversion, protected Earth and hostile movement.
- Store tests for concurrent full claims and complete rollback of damage, loot,
  estate and generation when a later phase aborts. Version-4 upgrade preserves
  existing committed deaths/assets; version-1/2/3 upgrade tests also pass.
- `smoke_salvage.py`: real PTY/GoDoors caller plus separate test worker; old victim
  commands stop, sampled inventory/titles/defenses persist, captured treasuries
  can be collected remotely, and replacement preserves 37 turns. Transcript:
  [salvage-smoke.txt](salvage-smoke.txt).
- Existing PTY smoke for trade/equipment/planets, ownership, teams, navigation,
  startup and lifecycle. Existing reference evidence was restored after checks.
- macOS build; Linux/amd64 and Windows/amd64 cross-builds.
- Research verifiers: 37 loot/estate DOS cases, nine duel-model cases, 14 team
  cases, nine ownership cases; all 4,682 archive files unchanged.

World format is now 5. There is no new player attack, defense placement or mine
command. No native-BBS combat or exact DOS RNG/MBF parity is claimed. The separate
worker uses the internal API only in disposable tests. Simultaneous-kill ordering,
weapon/cloak eligibility, mine aftermath, public combat integration and full
farming-chain acceptance remain pending. See [settlement scope and migration
rules](../research/yt-ships/SETTLEMENT.md). CI includes the new model verifier and
PTY smoke but this implementation commit has not been pushed for CI.

# Sector fighter implementation

This milestone reuses version-8 `SectorDefense` records. No save version change.
The existing [combat recovery](RECOVERY.md) contains the original DOS fixtures:
strictly greater than ten-to-one surrender, one offer per battle, human joining,
NPC refusal, batch=max(1,min(remaining forces)/20), and the cloak-adjusted
`RND + cloak/10 < .45` attacker-loss branch. Human IDs in the reconstruction
start at 1, rather than the original's reserved record slots. Main F is a final
balance, not an incremental deposit (annotated main 1d84–1e78); its Union guard
is at 1d11. No new DOS execution is claimed by this implementation.

## Commands and transaction rules

- F/DEFEND sets a personal final balance; zero recovers it. Capacity is checked
  before either balance changes. Only owners can withdraw. Union sectors 1–7
  prohibit additions; legacy groups there remain recoverable.
- REINFORCE/team option 6 transfers to an existing personal/teammate group and
  preserves its title. DOS allowed gifts to hostile groups; this implementation
  deliberately restricts gifts to friendly groups.
- BREACH binds the source ship generation, route, defense title/quantity and
  mine layers. A fresh warning must match the locked state. The caller chooses
  surrender acceptance in advance, then confirms with a separate Y. This policy
  avoids pausing a save transaction or rerolling a battle at a midcombat prompt.
- Adjacent entry spends one turn before combat, including cloak decay. Fighting
  a current group spends no extra movement turn. Uncommitted forces stay aboard.
  Surrender capacity overflow refuses the whole transaction.
- Exhausting the committed force forces the existing safe emergency warp.
  This is an explicit modern policy: the caller cannot continue normal actions
  stranded behind a hostile group. FLEE is available for current hostile groups,
  even at zero turns. Escape heat can consume all remaining turns.
- Ordinary bound-store mutations are blocked by current hostile groups. Mine
  hazards retain priority and can resolve despite a group. Read-only views remain
  available. Group battle does not kill an owning account, settle its estate or
  capture a port. Winning resolves destination mines in the same transaction.
- Hostile sector fighters intercept each missile for floor(RND*5000) cumulative
  kills, capped at remaining defense strength. Unspent rounds reach mines, then
  a ship. Own/team defenses are bypassed. Return fire follows the same ordering;
  a ship never reached by the initial volley does not retaliate.

The save lock rechecks ship generation, membership, route and warning state.
Invalid RNG, stale warnings, expired sessions or aftermath errors save nothing.
Commands discard pending input and disable command repetition at confirmations.

## Validation and limits

Eight Go fixtures are independently compared to the preserved Python research
model by `scripts/verify_sector_model.py` (model comparisons, not DOS runs).
Game tests cover final balances, owner/team access, Union recovery, overflow,
strict surrender boundaries, NPC refusal, forced escape, cloak-decay ordering,
stale warnings, destination mines and missile interception/retaliation gates.
Storage tests cover blocked callbacks, bound identity, expired confirmation and
rollback after entry/surrender when mine aftermath fails. The real PTY smoke
covers deployment/recovery, queued confirmation refusal, deterministic human
surrender and a defense-only missile target; it is included in CI.

Native BBS gameplay and long-running balance acceptance remain open. Planets,
long missile routes and multiple visible ship targets remain gated. Voluntary
mine placement, production NPC behavior and score generation remain separate.

Validated locally: race-enabled tests across all Go packages (with changed game,
storage and door packages rerun after the final tests), `go vet`, eight model
fixtures, startup/navigation/team/lifecycle/salvage/cloak/attack/mine/missile/sector
PTY suites, and Linux/Windows amd64 builds. The preserved combat verifier passed
91 checks over 12 captured sessions, including five model checks; missile/ship
verifiers passed 80/141 checks in a disposable recovery layout. Archive integrity
passed for all 4,682 files. This evidence does not establish native BBS acceptance.

# Persisted cloak and session visibility — 2026-10-27

Follow-up: [player-facing fighter attacks](PLAYER_ATTACKS.md) now use these visibility APIs; pending-command statements below describe the original cloak milestone.

## Recovered rules and implementation

[Ship recovery](RECOVERY.md#cloaking-and-anti-cloak) establishes new/replacement
ships with full cloak and a 0.01 reduction when spending a turn leaves a count
divisible by 25. `Player.Cloak` saves a finite fraction from zero to one. Movement
and docking, the two currently implemented turn-spending operations, share this
rule and clamp at zero, including a final turn leaving zero. Autopilot uses normal
movement. Daily turn replenishment and free actions do not consume cloak. Floating
fractions model energy, never money; exact MBF/RNG equivalence is not claimed.

[Encounter evidence](../yt-navigation/ENCOUNTERS.md#sensor-visibility-and-team-passage)
establishes strict `RND > cloak` detection. Zero cloak needs no draw; full cloak
cannot be revealed by this sensor rule. A reveal displays a shimmer once, then
remains visible to that observing session without further draws. The target's
stored energy and both players' turns remain unchanged by scanning. Detection
order follows stored warp order then sorted player ID. Invalid random values
reject the entire scan before committing any new reveal to the session cache.

`Visibility` is private to a single Run invocation and bound to the observer's
ship generation. Each revealed target is also bound to its generation. Reconnect
starts a fresh cache; this is an explicit modern policy because the bounded DOS
sensor experiments did not establish every reconnect-cache detail. Neither another
observer nor a replacement target inherits a reveal. Visibility records are not
saved in world.json, and no global reveal or anti-cloak purchase is added.

Production sensors use `ScanVisible` with the session cache; the old stateless
`Scan` is conservative and never reveals a cloaked ship. Information screens show
the caller's actual cloak percentage. Sensor reports do not expose cloak fractions
or hidden ship identities/equipment. The cache does not override authoritative
life, sector, team or generation checks.

`VisibleAttackCandidates` and `PrepareVisibleAttack` filter the internal local
candidate list using current saved energy and this session's reveals.
`CommitVisibleAttack` rechecks that visibility in the same transaction as damage
and settlement. The older `CommitAttack` now only permits uncloaked targets.
Duel odds use the attacker's current saved cloak. Low-level `AttackCandidates`
and `PrepareAttack` remain raw engine building blocks, not frontend visibility
APIs. No public attack command is enabled in this milestone.

## Save compatibility

World version **6** adds cloak. Supported versions 1–5 upgrade in memory and save
on the next successful mutation; read-only loading does not rewrite the file.
Existing ships retain zero energy, preserving their previously uncloaked behavior.
No hidden energy or free cloak reward is invented for legacy accounts. A legacy
header carrying nonzero new cloak data is rejected rather than silently altered.
New accounts and newly constructed replacements start at one. Other inventories,
remaining turns, ownership, teams and committed deaths are preserved.

Older binaries cannot read version 6. Back up the stopped data directory and
upgrade all nodes together; reverting requires the matching backup and discards
later progress. No schema field contains session reveals.

## Validation and remaining work

Tests cover strict equality, zero/full/fractional cloak, one-time shimmer,
repeated scans, no saved mutation, session isolation, replacement invalidation,
observer binding, invalid RNG with no partial reveal, turn boundaries/clamping,
replacement initialization and no turn refill. Store tests cover persistence,
read-only legacy loading, durable migration and malformed old saves. Attack tests
cover hidden-target rejection before RNG and the saved attacker cloak advantage.
A session test verifies repeated hidden/visible sensors and actual energy output.
`scripts/smoke_cloak.py` runs real GoDoors PTYs through registration, repeated
sensor scans, information and reconnect, checking both transcript and saved data.
The transcript is in `evidence/cloak-smoke.txt`; CI repeats the test.

Earth cloak recharge/anti-cloak purchasing, deliberate global-reveal balance,
frontend attack confirmation, retaliation, mine aftermath, sector-defense combat
and native BBS combat acceptance remain pending. No new DOS sessions or binary
patches were needed: this milestone implements the existing bounded evidence.

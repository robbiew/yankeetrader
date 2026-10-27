# Attack confirmation and transaction foundation — 2026-10-27

`AttackCandidates`, `PrepareAttack` and `CommitAttack` connect the existing duel
and settlement engines internally. There is still no player-facing attack command. The subsequent [cloak milestone](CLOAK.md) adds persisted energy, visibility-aware APIs and commit-time target filtering; the zero-cloak-only limits below describe this original foundation.

Candidates are live, different, local ships outside the attacker's positive team,
sorted by player ID. They are **not** visibility-filtered targets: cloak energy
and session detection have not been implemented. A future frontend must filter
candidates before presenting confirmation. No save format changes are required.

Confirmation records both ship generations, encounter sector and committed force.
Commit reloads both players through the enclosing store transaction and rechecks
life, generations, co-location, current team membership and available fighters
before consuming randomness. A replacement cannot inherit an old confirmation.
Current defenses are intentionally read at commit time, rather than quoted or
frozen while another caller acts. Confirmation does not reserve fighters or
promise unchanged target defenses. A surviving duel is another attack if invoked
again; this API has no session confirmation nonce or expiry yet.

The zero-cloak fighter duel applies only losses to the attacker's total fighters;
uncommitted fighters stay aboard. Final damage, death generation invalidation,
loot consumption and estate transfer run within the same store Update. Callers
must return every error so a late loot failure rolls back damage as well. Direct
fighter duels spend no turns and trigger no missile counterfire, following the
bounded observations in [ship recovery](RECOVERY.md). Earth attacks were observed
in that recovery; this internal operation adds no new Earth immunity rule.

Tests reject stale locations/generations, new team protection, spent force and
already destroyed targets before randomness or mutation. Store tests exercise a
complete killing attack with title/treasury and credit awards, replay rejection,
a late invalid loot draw rolling back the entire attack, and two simultaneous
confirmations yielding exactly one killing settlement. A surviving duel verifies
uncommitted fighters, target defenses and unchanged turns.

Next: persist cloak energy and implement session visibility/reveal decisions,
then frontend confirmation handling and protected-spawn mine aftermath. Missile
retaliation, sector defenses and full combat acceptance remain separate. This
milestone does not claim DOS RNG/MBF equivalence or native BBS combat acceptance.

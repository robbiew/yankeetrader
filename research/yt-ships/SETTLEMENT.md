# Modern loot and estate settlement — 2026-10-27

Implements the [37-session DOS recovery](LOOT.md) as internal engine operations.
Attacks, defense placement and minefield combat remain unavailable to players.
The current frontend can observe resulting inventories/ownership and collect
captured treasuries; no production kill/debug command is added.

## Inventory awards

`SampleSalvage` takes six separate random draws in DOS order: holds, cash,
missiles, plasma, ground forces and carried mines. Zero stocks still consume a
draw. Sampled holds expand the recipient's capacity, capped at 1,000 total holds.
Cargo is sampled without replacement from the victim's original hold contents,
including empty slots, for the number of new holds actually awarded.

Money never passes through a floating-point balance. Sampling computes the
integer floor of the exact binary RNG fraction times the integer stock using a
128-bit product. Tests compare against rational arithmetic at the 9-quadrillion
credit limit and around floating-point boundaries. Original MBF quantization and
seeded DOS RNG replay are intentionally not reproduced.

`SettleShipSalvage` checks the current defeated victim, generation, sector,
attacker and team protection before randomness. It computes awards without
mutation, preflights all recipient cash/weapon capacities, then commits death,
estate effects and inventory transfer. A capacity or random-source error rejects
the whole settlement. Every awarded hold, credit, weapon and cargo unit is
subtracted from the victim. Remaining inventory is frozen until replacement;
there is no second claim against it. Dead ships may therefore retain fewer than
ten holds, but live ships must still have at least ten.

The caller must run final damage and settlement in the **same store Update** and
return any error. Aborting a later aftermath phase rolls back damage, awards,
ownership, membership and generation together. An old victim generation cannot
claim again after death or replacement. A destroyed killer is not an eligible
recipient; simultaneous/mutual-kill aftermath still needs an explicit future
ordering policy before combat is exposed.

## Estate rules for every new death

All paths using `RecordDeath`, including the older explicit-credit helper, apply
the same estate cleanup:

- A live human killer receives the victim's ordinary port titles with treasuries
  intact. The transfer set comes from actual ownership, not a cached count.
- Self-death releases ordinary ports and clears their treasuries, as observed in
  the chained DOS mine death. Environmental death with no human recipient uses
  that same release policy; this extension is explicit rather than a newly
  claimed DOS environmental-identity result. Cleared treasuries are a sink.
- Planet owners, banks and defenses remain unchanged.
- Team membership is removed. Empty teams disappear; a departing captain leaves
  a vacancy for the established visiting-member succession rule. Guarded shared
  landing sessions whose permission was lost are revoked immediately.
- Docking agreements at every captured/released port are invalidated, including
  agreements held by callers other than the victim or killer.
- Owned sector fighter groups retain their quantity and become Mercenaries.

Replacement preserves retained planets and remaining daily turns. It does not
restore removed membership, transferred ports or released treasuries. No mines
are dropped in this milestone; minefield storage/aftermath and safe non-Earth drop
handling remain pending. Earth cannot hold a sector defense and cannot be owned.

## Minimal sector-defense state and saved worlds

World version **5** adds optional sector-defense records (owner and fighter
count). Mercenary/Xannor owner codes are explicit. Unknown owners, empty/overfull
forces, destroyed human owners and defenses at Earth are rejected. There is no
placement, withdrawal, donation or fighting command yet. Sensors show actual
counts and owner names when a defense exists. Movement permits personal/team
forces and rejects hostile ones; autopilot rechecks this through ordinary moves.
No default new world contains deployed defenses.

Supported versions 1–4 upgrade in memory and persist on the next successful
update. Version-4 data must not already contain the newly introduced defenses.
Older committed deaths are **not replayed** during upgrade: no retroactive loot,
port transfer or membership change is invented. Existing retained dead members
can still be removed by a captain, as covered by the earlier review fix.

Older binaries cannot read version 5. Back up the stopped world, upgrade all
nodes together, and restore the matching backup to roll back binaries; this loses
later progress. Read-only loading does not write an upgrade.

## Evidence and limits

Nine injected-RNG fixture comparisons use `loot_rules.py`, grounded in the DOS
observations. They are model comparisons, not additional DOS sessions. Exact
money extremes are checked independently with rational arithmetic. Tests cover
resource conservation, new-hold/cargo capacity, overflow/error purity, generation
replay, team revocation, titles/treasuries, planet retention, defense conversion,
protected Earth, save upgrade and replacement.

Store tests run competing claims and abort a transaction after damage and full
settlement, proving that all effects roll back together. A real PTY/GoDoors smoke
uses a separate test-only process to settle a defeat while the victim is online:
its old command chain stops, the winner's inventory and captured treasury persist,
remote collection works, and the victim's fresh login retains 37 turns. No game
executable is patched, and the test worker is not a production command.

Remaining work: player attack selection/confirmation and weapon/cloak checks,
retaliation and simultaneous-kill ordering, minefields/aftermath, defense placement
and combat, native BBS acceptance, exact DOS RNG/MBF equivalence and full economic
exploit-chain playtesting. Existing ship-generation and protected-spawn safeguards
must remain in that integration.

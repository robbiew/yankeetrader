# Go ship-duel calculations and credit settlement — 2026-10-26

This milestone ports the recovered direct fighter/shield calculations and adds
a one-time credit transfer primitive. Attacks remain disabled: this is not yet a
complete attack command or complete combat estate/loot implementation.

## Recovered calculations

`ResolveShipDuel` takes a committed force, defending fighters/shields, the
attacker's cloak fraction and an injected random source. It uses integer batch
sizes `max(1, min(attackers, defenders)/20)`, the recovered `.45` casualty
threshold with attacker cloak adjustment, and the separate shield stage with
strict `>100` batch boundaries and `.5` threshold. It has no sector-fighter
surrender branch or automatic missile counterfire. It reports final committed
survivors, defender inventories and losses; uncommitted fighters belong to the
calling attack transaction and are not removed by this pure calculation.

Nine controlled random streams are compared with the immutable archived Python
model `archive/analysis/yt-ships/recovered_rules.py`. Its checksum is pinned by
`scripts/verify_ship_duel_model.py`. These are **model comparisons**, not nine
new DOS sessions and not exact DOS RNG/MBF parity. The underlying original-DOS
observations and bounds are in [the ship recovery](RECOVERY.md).

Inputs and random draws are validated. A calculation exceeding one million
rounds returns an error and no partial result. This intentional resource bound
protects future transactions from degenerate draws/large one-fighter shield
battles. A future frontend must report a rejected calculation without charging
or saving partial damage. The guard's practical balance implications need
playtesting before combat is enabled.

## One-time credit salvage primitive

`SettleCreditSalvage` accepts a **precomputed** integer credit amount for a
currently defeated enemy ship. It does not choose the loot amount or percentage.
It validates recipient capacity and available victim credits, then invokes the
existing authoritative death transition and transfers the amount out of the
victim's inventory. All failure checks precede mutation. The victim must have
zero fighters/shields and must still match the expected sector/generation;
current attacker eligibility, team protection and attribution are rechecked by
the death transition. A destroyed recipient cannot receive credit salvage.

The caller must compose damage, this settlement and all future estate effects
inside one store transaction. On error it must return that error so the complete
transaction rolls back. Replay of the same death, including after replacement,
fails. Concurrent claims have one winner and one payment. The victim's remaining
credits stay frozen under the existing lifecycle policy until replacement;
there is no extra reward source and no equipment/ownership transfer here.

The test amount 6,689 credits reproduces the recorded `ship-kill` transfer amount
from a 12,345-credit victim, but does **not** establish the DOS sampling formula.
Modern settlement consumes those credits from the dead victim; the observed DOS
record retained its full pre-salvage balance. The modern departure prevents the
same credits from remaining available to a later settlement path.

## Validation and remaining work

Race-enabled tests, vet, model provenance checks and Linux/Windows cross-builds
pass. Engine tests cover phase/batch/threshold boundaries, accounting, invalid
inputs/draws and calculation limits. Storage tests cover competing claims,
recipient overflow, stale/moved/friendly targets, generation replay and complete
rollback after a later estate phase fails. No save format change is required.

Next recover/validate the full credit/equipment loot distributions and ownership
transfers, then implement target visibility/confirmation, weapon eligibility,
production randomness, retaliation and protected-spawn hazard drops before
exposing attacks. Native-BBS combat and the full salvage/respawn exploit chain
remain unverified. Existing research archives are unchanged.

### Subsequent research

The [loot/estate follow-up](LOOT.md) now supplies 37 controlled DOS sessions for
the distributions and ownership effects listed above. These recovered rules are
not yet wired into the internal Go helpers or player commands.

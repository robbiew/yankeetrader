# Planetary ground bombardment

`MISSILE <adjacent sector> <quantity>` now supports a hostile planet with no
eligible visible enemy ship in the same sector. The existing fresh confirmation
names the planet, reports its saved ground forces, and identifies this as ground-only
bombardment. Personal and teammate planets are protected. One movement turn and
the whole selected ammunition quantity are spent, as with ship volleys.

## Recovered arithmetic and supported boundary

The original ground loop at `1f42:7c20..7cb4` subtracts `RND*25` from a fractional
ground balance per missile and consumes one missile. It converts the final balance
to an integer after the loop. Lazy planet updates precede impact. The previously
captured fixed-clock DOS case fired 20 missiles at 5,000 forces and saved 4,766;
that is one observed random outcome, not a fixed loss coefficient. See
[the original recovery](RECOVERY.md).

This slice requires `quantity <= saved ground / 25`, using integer division,
before any ammunition or turn is spent. Every valid draw is below 25, so the
entire volley is guaranteed to remain in the ground phase, including when no
sector interception occurs. The last missile may leave a fractional balance
that floors to zero, but no missile remains to attack production. Ground below
25 therefore cannot be bombarded in this slice. This conservative restriction
also applies if sector fighters or mines could absorb some rounds.

Hostile sector fighters intercept first, then sector mines. Only remaining rounds
strike the planet; a wholly intercepted volley does not load/update the planet.
At impact the planet's existing lazy update runs, then fractional losses are accumulated and the remaining ground
balance is floored once. No capture, owning-account death, planetary
counterfire or direct production/stock/bank damage is introduced. Normal lazy
growth and interest still apply. A ground-only strike changes no planet title.

The confirmation binds the complete planet record, alongside existing ship,
sector defense and mine warnings. Changed ownership, ground, stock, bank,
production, timestamp, removal or replacement requires a new warning. Invalid
random draws, clock reversal, expired sessions and later callback failures roll
back ammunition, turns, interception, lazy updates and impact together.

## Evidence and limits

`planet-ground-rea.json` retains a fresh Ghidra byte read of the shipped loop at
linear address `0x27040` (151 bytes). The verifier independently relocates the
original MZ image, checks its SHA-256 and compares all returned bytes. The original
hash remains `c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
Six Go arithmetic fixtures are checked independently against the preserved Python
research model by `scripts/verify_planet_missile_model.py`. These comparisons use
injected RNG; they do not reproduce the DOS RNG or MBF32 intermediate rounding.
No new DOS session was executed for this slice.

Tests cover interception ordering, fractional rounding, the final zero-ground
boundary, lazy growth, own/team exclusions, mixed-encounter refusal, stale records,
invalid RNG and transactional rollback after interception/update. The PTY smoke
checks oversized-volley refusal, queued-confirmation cancellation, the planet
warning and exact agreement between the receipt and saved ground/ammunition/turns.
CI runs both the independent verifier and terminal smoke.

Production bombardment, clamping/destruction and the ore-only loop-entry case
still need focused DOS fixtures. Longer/one-way missile routes and multiple ship
or mixed visible ship/planet encounters remain blocked. Native BBS combat and
long-running balance acceptance remain open.

# Bounded plague and civil-war maintenance

Implemented from the [56-run DOS recovery](RECOVERY.md). This milestone adds
playable daily port plague, planetary plague and civil war, with atomic economic
changes and typed public newspaper entries. It deliberately does not reproduce
stale expenses, negative-time catch-up or exact MBF/RNG streams.

## Daily order and bounds

Inside the existing locked store update: retire eligible inactive dead accounts;
process ports in ascending ID order; append the aggregate port-plague count;
process planets in ascending ID order; then run the existing taxes, Mercenary,
Xannor, lottery, turn/token reset and score-publication phases. Each object gets
ordinary economic growth before its event test. All linked ports, including Earth,
and all planets, including protected-sector planets and faction homes, participate.
Faction home restoration/reserve repairs remain later, separate actions.

The saved UTC maintenance day prevents same-day replay and backward-day updates
before any draw. Missed days produce one event pass, with the existing ten-day
cap on ordinary economic growth. There are no retries until cured and no search
for another event target. Docking, banking and landing do not trigger outbreaks.
Existing daily docking/landing token invalidation prevents pre-event sessions
from spending stale quotes or retaining access after the daily world changes.

## Port plague

After growth and surplus-driven production promotion, a production sum strictly
above 1,000,000 triggers a single pass, without an outbreak roll. Each rate strictly
above 500 independently becomes `RND*rate + 500`; rates at or below 500 consume no
draw. Production remains within the existing 1..1e12 bound and cargo is capped
at ten times the resulting production. The formula can increase a near-cutoff
rate, and a port may remain above the outbreak threshold until a later day.

Every daily port update also chooses the first commodity with maximum supply.
That coefficient becomes positive; the others become negative, preserving their
magnitudes. All-zero supply deterministically chooses ore instead of inheriting
another port's selection. This switching applies to quiet ports too. It does not
change Earth equipment purchases, title restrictions or its separate tax exemption.

Public news stores only the affected count, not a list of owners, balances or
port locations. New universes contain at most 1,000 ports; the count validator
also accommodates up to 3,000 distinct linked ports in otherwise valid worlds,
matching the existing sector limit.

## Planetary selection and damage

Let S be post-growth production summed across the three commodities and G be
post-growth ground forces. Every planet consumes three independent gate draws:

```text
plague = R1*S > R2*1,000,000 + 100,000
civil_war = R3*G > 1,000,000
```

Civil war takes priority when both gates pass. Equality does not trigger either
event. No minimum-one production repair is introduced: current zero-rate planets
remain valid. An event consumes three independent production multipliers. Cargo
is capped at ten times the corresponding reduced rate. Positive ground consumes
two draws and becomes `floor(G * (1 - R4*R5))`, fitting the modern whole-unit
representation. Zero ground consumes no damage draws.

Civil war alone consumes one additional bank draw and removes `floor(RND*bank)`
from the post-interest balance. This uses the exact rational value of the binary
random fraction multiplied by integer credits, avoiding a rounded-up extra credit
near the money limit. Plague never spends bank funds. No remembered expense is
shared between planets, and no financial details are copied to public news.
Production and cargo keep their existing bounded float64 representation; this
is an explicit modern numerical policy, not exact single/double MBF emulation.

Events preserve owner, name, links, faction-home identity and weapon stocks.
Weapon and ground production before damage and later faction repairs can still
change those quantities for their own reasons. Reaching zero ground does not
neutralize or delete a planet; existing live access rules still apply.

## Reporting, retention and exhausted metadata

`NEWS [TODAY|YESTERDAY]` and the classic computer newspaper display the typed
`port-plague`, `planet-plague` and `civil-war` events. Planet events retain only the
planet-name snapshot; the port entry retains only the count. No ground, bank,
expense, owner identity, authentication key or arbitrary message text is stored.
Snapshots remain valid after renaming or destruction. Standard paging, two-day
UTC retention, 1,024-entry cap and monotonic IDs apply.

A full retained journal evicts old entries normally. If IDs are exhausted or the
journal clock is ahead of maintenance, defer damage that cannot be reported.
Ordinary growth, commodity selection and the other daily phases still proceed;
there is no hidden loss, partial debit or attempt to overwrite metadata. Planet
gates remain eager, but deferred damage consumes no damage draws. If the final
available ID is used for port news, later planetary damage waits for a future
reportable pass. Sequence exhaustion requires operator attention; IDs are never
reused or wrapped.

## Save compatibility and atomicity

Save version **19** recognizes the three new news types and optional `PortCount`.
Normal version-1 through version-18 inputs follow existing migration checks and
upgrade in memory without changing economic values, accounts, sessions or history.
Read-only loading leaves the original file intact; the next successful write
publishes the upgrade. Legacy-version input claiming new event fields is rejected.
Older binaries cannot load version 19: back up the stopped world and upgrade every
node together. Outbreak history is never invented during migration.

The existing store publishes assets, production, bank debits, news, daily tokens,
maintenance day and scores in the same validated atomic replacement. Callback or
validation errors leave the old bytes untouched. A directory-sync failure after
rename is a committed-durability error: reload the saved day instead of retrying
damage. Concurrent maintenance callers serialize and only one runs the day.

## Validation and limits

Focused game tests cover exact thresholds, eager/conditional draw counts, Earth,
post-growth selection/interest, one-pass high rates, near-cutoff increases, stable
commodity ties/zero fallback, public privacy, caps, whole-credit boundaries,
civil override, no stale debit, zero rates/ground, homes/titles/weapons, 1,000 ports
and 99 planets, journal capacity/exhaustion and 32 seeded deterministic worlds.
Store tests cover abort/validation rollback, eight simultaneous callers, reload,
same-day/backward replay, committed durability and version-18 migration/rejection.
Door tests render actual deterministic outbreaks in both interface modes.

The real [terminal smoke](../../scripts/smoke_overcrowding.py) uses disposable
worlds and actual CLI maintenance for deterministic port outbreaks and replay.
It uses retained typed planetary news for UI assertions; deterministic game/store
and door tests exercise actual planetary selection, damage and bank changes.
Affected terminal scripts assert version 19. CI includes the new smoke alongside
the retained DOS verifier and its 16 rehashed corruption controls.

Live BBS acceptance, native Windows file durability, exact original random streams
and MBF parity remain unverified. No equipment actions or unrelated random-event
families are added by this milestone.

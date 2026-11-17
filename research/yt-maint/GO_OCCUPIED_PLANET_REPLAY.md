# Bounded Go ordinary/occupied-planet economy

`ReplayOccupiedPlanets` ports the existing `replay_maintenance_active_planets.py`
phase through a separate research API. It does not broaden `ReplayEvolvedPlanets`
or the initial/convergence CLI profiles. Inputs are one independently modeled
complete world, a 24-bit modeled RNG state and source-ordered record/date/raw
TIMER-minute clocks. The API returns an owned world and modeled statistics, or
nil world/zero statistics on error; caller storage is never changed.

Admission covers default geometry, pre-day306 watermark, inactive humans and
zero, one or two active ordinary planets in slots 2/3 (records 4053/4054). Each
active record has a padded ASCII name, prior-day date 305, three 1000 cargo rates,
500000 ground, owner 0 or -1, otherwise numerically empty fields and exactly one
physical sector link. Every active planet needs its own ordered day306 midnight
clock. Arbitrary banks, stocks, inherited reserved fields, active humans, later
days, additional slots and unknown owners fail without partial publication.

The phase preserves each source SINGLE assignment around fractional elapsed,
cargo/fighter/weapon production and rate growth. Ground and bank floor the full
wider expression before storage; this ordinary profile does not adopt the
evolved profile's extra SINGLE conversion or bank bonuses. Three eager event
draws per active planet evaluate the actual plague/civil-war predicates; selected
damage remains excluded. Final date and raw TIMER bytes are stored separately.
Untouched fields and exponent-zero residues are retained. No-active-planet cases
return a copy without advancing RNG state.

## Existing evidence and independent qualification

`export_occupied_planet_fixture.py` wraps the existing ten-case Python occupied
replay. Initial inputs come from the original baseline plus the existing declared
fixture construction. The phase before-world is captured after modeled ports;
the after-world and RNG receipts are calculated before any native target opens.
Neither native case before-worlds, after-targets nor captured RNG endpoints enter
synthesis. Only the comparison layer opens those retained targets and witnesses.

Thirty modeled phases across three source-clock observations per case contain
24 planet updates and nine no-active-planet phases. Go tests match every complete
phase-world hash, elapsed/rate/ground receipt, event draw and final modeled state.
They also feed actual Go capped-port output directly into this API in all 30
cases, rather than substituting a Python phase before-world.

The exporter separately revalidates **180 complete six-file comparisons /1080
native files and 1872 RNG witnesses**, plus the existing occupied native-source
packet. These qualify the complete Python runs; intermediate phase hashes and
RNG receipts remain modeled oracles, not new native phase observations. Original
packets, acquisition source attribution and hashes are unchanged; no captures were
added. Source fingerprints and portable compressed modeled inputs are retained.

Tests enforce exact write bounds, copied outputs, immutable clocks/worlds and
atomic late refusals. A synthetic exponent-zero TIMER control checks raw residue
preservation and the 504999 wider-floor ground result at exactly one elapsed day;
it is not a new native execution. Exporter controls reject changed input/receipt
or source identities, corrupted native outputs and poisoned RNG witnesses,
enforce synthesis-before-target read order and allow equivalent recompression.

```sh
python3 scripts/export_occupied_planet_fixture.py --check
python3 scripts/test_export_occupied_planet_fixture.py
go test ./internal/qbmaint -run TestOccupiedPlanet
```

## Remaining scope

[Bounded foreign-defense combat](GO_FOREIGN_DEFENSE_REPLAY.md) is now qualified
separately, as is [strong neutral-planet ground assault](GO_NEUTRAL_GROUND_ASSAULT.md).
Next integrate the existing rules into bounded routing. Casualties,
news, faction scores and complete occupied-world six-file Go composition remain
separate. The convergence chain/CLI v2 and Windows path fix are already merged;
do not repeat them. Modern gameplay, save 35, production maintenance, release
packages and native Windows/live BBS acceptance are unchanged.

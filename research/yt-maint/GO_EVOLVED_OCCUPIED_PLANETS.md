# Bounded Go evolved occupied-combat planet economy

`ReplayEvolvedOccupiedPlanets(before, EvolvedPlanetInputs)` derives the retained
planet economy children on days 307/308. Input is a complete modeled world,
calculated phase-entry RNG state and ordered record/date/raw TIMER-minute rows.
Output is an independent world plus `EvolvedPlanetStats`; any error returns nil
world and zero statistics without changing caller storage. No captured world,
expected endpoint, filesystem, host clock or modern save enters the API.

## Admission and source order

This is distinct from clean day-306 occupied economy and named convergence
planets. It admits The Wanderer, Mercenary Base and Xannoron, with optional
neutral Route Haven at slot 2. Names, governors, complete active inventory,
unique physical links, inherited reserved fields, prior dates/minutes, bounded
rates/stocks/banks/ground and midnight clocks are checked before arithmetic.
The first child's Wanderer/Base date remains 296; later child dates are 307.
Very small positive assets below 2^-24 remain outside this IEEE-backed bounded
quantization path. Active humans and selected plague/civil damage are excluded.

Only the already qualified arithmetic kernel is shared with convergence replay;
its public admission is unchanged. Stock/rate production, SINGLE assignments,
INT flooring, bank interest, old-bank ground bonus and minimum resource bases
follow the source order. Fractional elapsed time is preserved and intervals above
ten days clamp to ten. Three eager event draws occur per active planet; their
actual predicates are evaluated. A selected event on the last planet discards
the entire private phase result. Sampled raw TIMER bytes are saved unchanged.

## Reused evidence and validation

The exporter wraps `replay_maintenance_evolved_combat_planets.maintain` while the
existing complete Python chains run. Four occupied parent profiles each have two
children and three source observations: **24 modeled phase worlds, 78 planet
updates and 234 eager draws**. Three-home and optional four-planet inventories
are separate, not forced into a single layout. In replay comparison the three-day
chain finishes before its first native after-target is opened; only original parent before
files enter synthesis. RNG observation bytes cannot supply a modeled state.

The independent retained qualification remains **144 six-file comparisons /864
files and 1242 child RNG witnesses**; prefix witnesses are checked independently
without counting them again as new child evidence. Native observations, hashes,
frozen acquisition sources and numeric controls are unchanged. Phase snapshots
and state receipts are modeled intermediate oracles, not newly captured native
phase measurements.

Go tests compare complete phase hashes, all row/rate/elapsed/draw receipts,
calculated states, permitted writes, unchanged raw timestamps and input/output
ownership. Independent real-LCG event selection exercises a late atomic failure.
Synthetic admitted boundaries check fractional elapsed minutes and rounding the
complete interest expression to SINGLE before INT. Unsupported worlds, dates,
names/owners, fields, links and clock inventories fail atomically. Historical
convergence/initial-occupied APIs still reject these contexts. Existing chain
and occupied composition tests protect the shared arithmetic extraction.

Four portable exporter controls reject missing rows, altered worlds/clocks/
states/sources, corrupt native output and poisoned RNG witnesses. They enforce
complete synthesis before 864 target-file reads and allow equivalent gzip
transport only when every uncompressed byte agrees. CI runs them with the
fixture check and the existing race-enabled Go suite.

```sh
python3 scripts/export_evolved_occupied_planet_fixture.py --check
python3 scripts/test_export_evolved_occupied_planet_fixture.py
go test ./internal/qbmaint -run 'TestEvolvedOccupiedPlanet|TestEvolvedPlanet'
```

The API ends before evolved occupied-combat home/mobile continuation. That phase,
its tail/reports and complete three-day Go parent come next, before stock/gateway
four/five-day composition. Recipe/CLI profiles are unchanged. General production
maintenance, arbitrary worlds/events, DOS save interoperability and live BBS/
native Windows acceptance remain separate.

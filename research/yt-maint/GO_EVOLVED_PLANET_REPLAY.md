# Bounded Go evolved-planet economy

`qbmaint.ReplayEvolvedPlanets(before, inputs)` computes only the ordinary planet
maintenance phase for the retained three-day convergence profile. Inputs are a
complete modeled before-world, explicit per-record source DATE/raw TIMER-minute
pairs, and an independently modeled 24-bit RNG state. It returns a new complete
world and calculated phase receipts. It opens no files or native targets, accepts
no observed endpoint corrections, and mutates no caller-owned world, clocks or
RNG. Every error returns no world and empty statistics, including an excluded
event selected after earlier planets have already been calculated privately.

Day 306 admits only Convergence Haven; days 307/308 admit The Wanderer,
Convergence Haven, Mercenary Base and Xannoron in physical record order. Admission
checks default geometry, inactive human players, exact names/owners, inherited
reserved fields, one sector link per active planet, bounded banks, ground, rates
and inventories, and complete source midnight clock attribution. Nonzero assets
must be at least `2^-24`; this narrower Go numeric gate keeps the bounded
IEEE-backed source conversions away from MBF underflow and IEEE subnormal loss.
All retained positive assets exceed .09. This is not general raw MBF conversion
or an admission of arbitrary evolved planets, active human worlds or event damage.

The calculation preserves the existing Python source assignment order:

- fractional elapsed time, with negative/over-ten-day catch-up capped to ten;
- total-rate floors for fighter and weapon production;
- bank bonuses derived from the old bank before interest;
- SINGLE conversion before interest/ground integer floor;
- separate SINGLE bonus, stock, surplus-rate and natural-growth assignments;
- three eager RNG draws per active planet, evaluating plague/civil predicates;
- exact raw source TIMER bytes, including inherited zero residues, on writeback.

Only this phase's date, inventory, ground, bank, rate and timer fields change.
Its calculated event draws, elapsed time, ground and rates are modeled receipts,
not additional native endpoint observations. Existing initial replay APIs and the
research CLI's initial-only v1 profiles remain unchanged; modern gameplay and
save 35 are unchanged. Native Windows/live BBS acceptance is not established here.

## Evidence reuse and validation boundaries

No native captures or new numeric primitives were added. The exporter
`export_evolved_planet_fixture.py` authenticates the existing convergence corpus
and native source packet, then instruments the already recovered Python
three-day chain. Each phase input world and RNG state comes from synthesis;
no native child before-world, captured RNG state or after-world enters it.
All three modeled days exist before native targets are opened. Each child is
fed the previous complete modeled output by the existing Python chain.

The exporter checks all **54 complete native six-file comparisons /324 files**
and **501 independent native RNG witnesses**. It stores nine modeled economy
phase input worlds, source clocks, complete phase-world hashes and calculated
receipts. This does not turn an intermediate phase into a direct native oracle:
Xannoron's later NPC ground increment remains outside economy, and full native
file equality is established by the existing Python chain after subsequent phases.

Go tests compare all **nine complete modeled phase worlds /27 planet updates**
against those independently implemented, native-qualified Python results. They
also check RNG continuation and every event draw, unchanged bytes outside the
phase writer, exact TIMER bytes, input immutability, independent returned memory,
profile refusals and failure after an earlier planet was processed. Synthetic
regressions check interest rounding before floor, old-bank ground bonuses, the
rollback catch-up cap and explicit zero RNG state; they are not new native runs.
Exporter controls reject altered before bytes, clocks, state, source inventory,
phase oracles, native files and poisoned RNG witnesses. Portable gzip containers
are checked by complete decompressed bytes, allowing recompression.

```sh
python3 scripts/export_evolved_planet_fixture.py --check
python3 scripts/test_export_evolved_planet_fixture.py
go test ./internal/qbmaint -run TestEvolvedPlanet
```

Full Go evolved maintenance is still separate: the qualified Go port and planet
phases do not yet replace the Python evolved NPC and auxiliary composition.
[Existing-home/mobile continuation](GO_EXISTING_HOME_CONTINUATION.md) now has its
own bounded Go API and composes directly with this phase, as does the
[evolved tail](GO_EVOLVED_TAIL_REPLAY.md). Next migrate day-one convergence
admission and auxiliary output against the [existing chain](EVOLVED_CHAIN_REPLAY.md).
Do not reacquire completed controls or repeat port/planet/continuation recovery.

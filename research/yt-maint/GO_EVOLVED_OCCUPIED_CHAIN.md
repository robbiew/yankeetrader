# Complete bounded Go evolved occupied-combat three-day chain

`ReplayEvolvedOccupiedChain(before, []EvolvedOccupiedDayInputs)` now composes the
four retained occupied-combat profiles over source days 306–308, November 2–4,
2026. It accepts exactly three pinned original files and three source recipes.
No child world, expected file, observed RNG endpoint, event correction or captured
cache array can enter this API. The result is three owned six-file bundles with
calculated receipts; any error returns nil, including failure on the last day.

## Separate admission and daily order

The original YTDATA pins correspond to `route-mercenary-37`,
`route-mercenary-100000`, `route-neutral-37` and `route-planet-neutral`. Original
name/news side pins remain those enforced by the occupied-day306 API. Six other
occupied originals and the convergence original remain excluded. Existing
initial/convergence/occupied APIs retain their old guards; no numeric primitive,
phase admission or gameplay/save policy is broadened for this wrapper.

Each recipe provides the source day, its own startup seed, 1000 ordered port
DATE/TIMER-minute samples, ordered planet clocks, labelled home/tail helper
prefixes and independent news/score clocks. Creation clocks are present only on
the first day. Cross-phase calendar identity, complete schedules and consecutive
days are checked before private synthesis. A new DOS process starts each day:
its startup seed is not replaced with the previous process's final state.

Day306 calls the existing `ReplayOccupiedFiles`, preserving its full original
pin, capped-port, economy, home creation/combat, tail and report checks. Its
`OccupiedStats` receipt is returned through the first result's `Initial` pointer.
Children have nil `Initial` and separate calculated child phase receipts:

1. `ReplayEvolvedPorts` reads the previous Go world's full-stock port records.
2. `ReplayEvolvedOccupiedPlanets` starts from the explicit new-day seed.
3. `ReplayEvolvedOccupiedHomeMobile` receives its calculated world/state.
4. `ReplayEvolvedOccupiedTail` receives the calculated mobile world/state.
5. `ReplayInactiveRanks` finalizes ranks and watermark exactly once.
6. `ReplayEvolvedOccupiedAux` receives the prior Go files, current finalized world
   and calculated mobile/tail ledgers, then the new world joins its five files.

Only the resulting six files feed the next iteration. Names remain unchanged,
yesterday news rotates from the previous Go-generated news, and private messages
remain empty. Ports draw no RNG; all within-day phase states derive directly.
The API has no filesystem, host clock, native target or modern save input.

## Existing evidence and portable recipes

A small new exporter wraps the existing Python chain and original tail boundary
hooks. Its portable data contains only original before bytes, source-clock
recipes and modeled full-day hashes/state receipts. It does not duplicate child
or phase worlds as composition inputs. All three modeled days finish before
replay comparison opens a native child target; independent native verification
runs separately. Prefix RNG witnesses remain independently checked.

Twelve recipes (four originals × three source observations) produce **36 complete
six-file Go results /216 output files**, matching existing native-qualified Python
hashes. The independent retained child audit remains **144 six-file comparisons /
864 native child files and 1242 child RNG witnesses**. Existing occupied-day306
qualification still covers the parent. These inventories are distinct; 36 modeled
results are not presented as newly acquired native runs. No observation bytes,
fixed hashes, frozen acquisition sources or native corpus artifacts changed.

Tests read only original before bytes as synthesis inputs and verify every day,
all six hashes, independent startup/within-day state handoffs, previous-news
rotation, readonly inputs/recipes and output ownership across every day/file.
Atomic controls cover pins, wrong/missing/reordered days, creation contexts,
mixed calendars, schedule extents and late port/planet/home/tail/report failures.
Nil results mean no partial day bundle is published after a later failure.

Five exporter controls reject changed original bytes, recipes, receipts, hashes
and source fingerprints; allow byte-equivalent gzip transport; enforce synthesis
before 864 native child-target reads; and reject corrupt native files and
poisoned RNG witnesses. The existing package race/vet checks and new fixture
commands run in CI.

```sh
python3 scripts/export_evolved_occupied_chain_fixture.py --check
python3 scripts/test_export_evolved_occupied_chain_fixture.py
go test ./internal/qbmaint -run TestEvolvedOccupiedChain
```

The separate [research recipe/CLI v4](REPLAY_CLI.md#evolved-occupied-combat-three-day-profile-v4)
now exposes this complete chain using these recipes, preserving existing v1–v3
decoding and fresh bundle publication. Later four/five-day stock/gateway extensions still need their own
fixture transforms and child-phase admissions. General production maintenance,
DOS save import/export and native Windows/live BBS acceptance remain separate.

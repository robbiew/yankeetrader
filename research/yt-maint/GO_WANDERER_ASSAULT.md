# Bounded Go neutral Wanderer assault primitive

`qbmaint.ReplayWandererAssault` ports the existing before-only production branch
in `scripts/replay_maintenance_wanderer.py` (main5efd and owner655b..6586). It is
an explicit research primitive, not a change to ordinary mobile replay or modern
planet combat. Existing source and late-clock captures were reused; no native
capture, executable query or observation hash was added or changed.

## Exact admitted operation

Inputs are an independently modeled encounter-prefix world, group 2..19,
sector 8..3000, force 1..10000 and 24-bit RNG state. The sector must link the
named active Wanderer, with no screens/hazards/mines. Owner/ground and all three
warehouses must be numeric zero; production rates must be in (500,5000].

Each round takes a gate draw. Below .5, three separately drawn damage fractions
update the rates, each using qualified raw `MultiplySingle(draw,450)`,
`DivideSingle(product,3)` and `SubtractSingle(rate,damage)`. Each operation
rounds separately as in the original array assignments. At or above .5, force
loses 450 even if fewer fighters remain: the recovered positive-location
subscript defect is preserved in research, never modern gameplay.

The bounded loop rejects small-rate/deletion paths, ground defenses, ownership,
populated warehouses, screening and unqualified aftermath. A finite 4096-round
guard prevents unbounded work. Only three production fields and owner are
written. Original owner-zero residue `00002000` is assigned; raw ground/stock
zero residue and all other world bytes remain inherited. Stats expose raw
nonpositive force, round/damage/draw counts, final raw rates and modeled RNG
state. The moving group's zeroing and shared pursuit are caller integration,
not world writes performed by this primitive. Errors return no partial bytes or
stats; successful output owns its storage.

## Existing repeated late-run validation

The exporter authenticates the clean-port calendar/matrix source and observation
chain, then instruments only the existing Python model in memory to retain its
before-only encounter inputs. It does not instrument DOS, alter captures or use
a native target as input. All 18 calls in a run have identical inherited world
bytes except the preceding modeled Wanderer changes; this is asserted before
export. The complete independent Python six-file synthesis still matches all
native outputs before the final Wanderer record is retained as a native oracle.

Derived portable prefix containers are compared by complete decompressed bytes,
independently of Python/zlib gzip encodings. Source/step/native metadata remains
exact; recompression is accepted and altered uncompressed bytes are rejected.
Original native gzip observations are never rewritten.

Each of the three observed late-clock runs follows the same groups 2..19
scenario. Go chains start with a Python-modeled prefix and feed each Go output
into the next assault call. All 54 modeled step records/stats match; each final
137-byte Wanderer record equals its native observation. These are three repeated
native final records, not 54 native intermediate-state captures or independent
parameter scenarios. Explicit force/state inputs and intermediate records are
Python-model expectations; final record bytes are native oracles. Inter-call
routing, reseeds and shared pursuit are not yet modeled by this Go primitive.

Tests also exercise the exact .5 gate with a labeled synthetic inverse-RNG state,
force 1 losing 450, input/output isolation, inherited zero bytes and atomic
admission. Existing ordinary-profile six-file tests continue unchanged. The
three late profiles are still outside `ReplayInitialMaintenance`; full Go mobile
routing/pursuit, tail, auxiliary encounter news and six-file integration need a
separate explicit extension. Modern gameplay/save format 35 is unchanged.

```
python3 scripts/export_wanderer_assault_fixture.py --check
python3 scripts/test_export_wanderer_assault_fixture.py
go test -race ./internal/qbmaint ./internal/qbrng ./internal/qbmbf ./internal/qbinit
go vet ./internal/qbmaint ./internal/qbrng ./internal/qbmbf ./internal/qbinit
```

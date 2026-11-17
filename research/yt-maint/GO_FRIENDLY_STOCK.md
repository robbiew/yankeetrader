# Bounded Go held-friendly garrison and planet-stock pickup

`ReplayFriendlyStockMercenary` consumes a modeled pre-Mercenary world and
`EvolvedTailInputs` containing the calculated incoming RNG state and explicit
source target-helper clocks. It returns an owned phase world and calculated
receipts, or nil world/zero statistics on every error. It does not read targets,
native endpoints, files or host clocks. It ends before lottery, final metadata,
news and scoring; it is not a complete four-day Go replay or playable policy.

## Qualified source order

The existing Python replay synthesizes its original three-day parent, applies
the declared joint fixture edits and finishes child economy/mobile routing before
the phase exported here. These are modeled phase inputs, not native before-world
corrections. All eight original force/governor/stock combinations remain exact:

| Friendly force | Governor | Stock | Final physical force | Taking actor/amount |
| ---: | ---: | ---: | ---: | --- |
| 1 | 0 | 0 | 97338 | silent |
| 37 | 0 | 0 | 97374 | silent |
| 37 | 0 | 0.5 | 97374 | silent |
| 37 | 0 | 37 | 97411 | 97374 /37 |
| 37 | 0 | 1.5 | 97375 | 97374 /1 |
| 37 | 0 | 189528.5 | 286902 | 97374 /189528 |
| 37 | -2 | 37 | 97411 | 97374 /37 |
| 97337 | 0 | 37 | 194711 | 194674 /37 |

The phase eagerly draws once per positive physical defense, including NPC or
neutral owners, before the descending mutable-sector scan. The existing local
sector-3000 garrison must hold on its actual draw; a departing result is refused.
The incoming 97337 fighters at sector2368 then draw their eager movement gate,
clear original force/owner to source859e `00002800`, derive target rejection and
the full directed BFS route from chronological helper-one /48cf TIMER inputs.
The actual first successor must be Gateway Cache at sector3000. Only that prefix
is entered, even when the planned target lies farther away.

Cached entering friendly force is added once before stock. The existing raw
`qbmbf.IntSingle` primitive floors canonical positive SINGLE stock; its whole
numeric amount is added once and its fractional remainder is separately reported.
Stock always clears with source8472 `00008000`, including empty/subunit stock.
Taking is true only for a positive whole amount, with the combined pre-stock
actor. No capture is invented for a sector already physically Mercenary-owned.
Governor, title, ground, all remaining planet fields and all other world bytes
remain untouched. The later incoming arrival cannot reactivate sector3000 after
its scan position has already passed.

## Admission, evidence and verification

Admission keeps default geometry, inactive humans, zero port taxes, the exact
two Mercenary origins, canonical eight joint gateway contexts, mine-free origins,
actual linked/name/zero-bank gateway identity, whole bounded physical NPC forces,
at most10000 Xannor, optional37 neutral force and integer directed graph. Helper
inputs are ordered first-minute family-one /48cf clocks; missing/surplus clocks,
unsupported routes, other owners or contexts and local departure fail atomically.
Historical `ReplayEvolvedNPCTail` admission remains unchanged.

The exporter reuses existing acquisition/native verifiers and complete Python
four-day synthesis. All 24 modeled worlds and receipt sets match Go, including
source RNG continuation, gates, helper reseeds, candidate/route/entered lists,
physical conservation and pickup actor/fraction/stock. Whole-run qualification
remains 144 six-file comparisons /864 native files and1104 child RNG witnesses.
Those native outputs and endpoints audit completed synthesis independently; they
never seed or correct this API. No new DOS run, binary observation or hash change
was needed. Frozen executed acquisition sources remain untouched.

Go tests constrain every changed byte to the five source-owned fields, distinguish
both raw zero residues, cover all positive/silent stock cases, preserve inputs and
output ownership, and exercise early and late atomic errors. A synthetic real-LCG
departure control verifies the hold guard; it is not a new native observation.
Exporter controls reject changed clocks, modeled receipts, worlds and sources,
native output corruption and poisoned witnesses; they enforce complete four-day
synthesis before target reads and accept equivalent gzip recompression by bytes.

```sh
python3 scripts/export_friendly_stock_fixture.py --check
python3 scripts/test_export_friendly_stock_fixture.py
go test ./internal/qbmaint -run TestFriendlyStock
```

Next qualify departed-garrison/local movement and same-scan reactivation through
its separate retained corpus. Full four-day Go composition/report/recipe work
must subsequently reuse these primitives without weakening the held-only guard.

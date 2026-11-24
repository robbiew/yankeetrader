# Bounded Go evolved occupied-combat tail and reports

`ReplayEvolvedOccupiedTail(before, EvolvedTailInputs)` derives the retained
post-mobile Mercenary and inactive lottery phase on child days 307/308. It takes
only modeled bytes/state and the exact source-helper suffix, returning owned
world bytes and `EvolvedOccupiedTailStats`. Unsupported contexts or late failures
return nil world and zero statistics without changing caller storage.

`ReplayEvolvedOccupiedAux(beforeFiles, finalizedWorld, AuxInputs, events, tail)`
emits five owned auxiliary files and physical/casualty/score statistics. It takes
six modeled day-before files, a separately finalized world, Go mobile events and
Go tail receipts. It neither runs a tail nor modifies/finalizes world metadata.
Source news and scoreboard dates/clocks remain separate explicit inputs.

## Retained behavior

All four existing evolved occupied-combat chains are reused. There are 24 modeled
child tail/report sets, 12 Mercenary activations, three instances of the same
qualified unit-victory pattern and 18 conditional lottery helper calls. The
victory starts with 97525 Mercenaries and 182 Xannor defenders at sector 109;
eager branch draw and unit casualty rounds derive 97337 survivors, rather than
assigning an observed force. The defender never exceeds 200, so generic 150-loss
batch combat remains excluded. Original empty-route tail admission is unchanged.

The source eagerly draws once per positive physical sector, scans mutable
Mercenary records descending, and reseeds each target attempt at /48cf. Departure
fields retain `00002800`; defeated defense/owner clear canonically without
repairing stale group caches. Subsequent activations consume the surviving
force. This profile's activation force follows the Python/source post-encounter
stamp, while battle receipts retain the distinct entering force and capped loss.
Mine hits, friendly merging, planet-stock pickup, unqualified defense and fatal
attacker outcomes remain atomic refusals.

The inactive lottery draws exactly once after all movement/combat. Only its
selected >=.5 branch consumes /53b4; no named-player award is admitted. Missing,
surplus or mislabelled helpers fail even after earlier private writes. The
separate existing rank/watermark writer runs after this returned phase.

## Publication ledger

Reports require existing named homes, optional neutral Route Haven and exact
links, child date handoffs, inactive ranks/assets, zero taxes/private stream,
default score path/year and no ordinary planet creation/deletion. Route Haven
fatal events are source ordered with unique dead groups; ground receipt
continuity ends at the modeled final ground. Mercenary battle receipts conserve
unit rounds and actual faction casualties. Final Mercenary sectors/force must
agree with physical records; both factions and unscored neutral force conserve
across the complete day-before/final-world ledger.

News preserves source order, entering-force counts, original spelling/case
(including `fighters beloning to` and `Won!`), CRLF and DOS EOF. Actual surviving
physical force supplies scores; exact bounded percentage rounding preserves the
existing halfway refusal. Names copy unchanged, yesterday news is the exact
previous modeled news, and private output is empty. Historical bootstrap reports
remain strict. No runtime executable, captured output or host clock enters Go.

## Qualification and tests

The exporter brackets existing Python tail, NPC completion and auxiliary writers.
Only original parent files enter before-only synthesis. Replay comparison opens
native targets after the whole three-day prediction; independent native audit
runs separately. Qualification remains **144 six-file comparisons /864 files and
1242 child RNG witnesses**; prefix witnesses are checked without recounting them.
Phase worlds/receipts are modeled oracles, not new native measurements. No
capture bytes, observation hashes or frozen acquisition sources changed.

Tests match all 24 complete tail worlds, draw/state/activation/reseed/battle/
lottery receipts and every byte of the five report files. They join actual Go
mobile output/state into tail, existing metadata and reports. Day-before report
files still come from the independently modeled fixture: this is phase
composition, not a completed original-input three-day Go chain.

Atomic controls reject malformed geometry, humans/hiring/revenge, graph, helper
suffixes, late hazards, batch/foreign defense, report dates/clocks, side files,
physical counts, forged victory/casualty/endpoint stamps and ground-ledger
order/payload/handoff corruption. Inputs and returned buffers remain isolated.
Five exporter controls cover inventories/receipts/clocks/sources, equivalent gzip,
synthesis-before-target reads, corrupt native files and poisoned RNG witnesses.

```sh
python3 scripts/export_evolved_occupied_tail_fixture.py --check
python3 scripts/test_export_evolved_occupied_tail_fixture.py
go test ./internal/qbmaint -run 'TestEvolvedOccupiedTail|TestEvolvedOccupiedReports|TestEvolvedOccupiedGroundReport'
```

Next compose the full three-day Go evolved occupied-combat parent from pinned
original files and explicit clocks, using only its own day outputs as child
inputs. Reuse completed occupied-day306, evolved ports, economy/mobile, tail,
metadata and report APIs without relaxing their gates. A new explicit recipe/CLI
profile follows complete-chain verification. Later stock/gateway children,
production policy, DOS save import/export and native Windows/live BBS acceptance
remain separate.

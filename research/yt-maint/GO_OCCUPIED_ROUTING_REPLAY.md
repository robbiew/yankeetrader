# Bounded Go occupied-world home/mobile routing

`ReplayOccupiedHomeMobile` begins with independently modeled post-economy world
bytes and state, then runs the retained initial occupied-world phase through
Mercenary Base birth. It composes the existing home assignment writers and both
qualified combat primitives. The returned world and statistics are owned; any
early or late error returns nil world/zero statistics without changing caller
worlds or clock recipes. It has no native/file/host-clock input.

Admission is separate from the historical initial and convergence APIs. It covers
default geometry/day306, inactive humans, zero taxes/revenge, one tracked 10000
Xannor HQ, missing mobile groups and homes, no mines and only the retained clean
post-economy ordinary slots 2/3. Ordinary names, dates, ground/rates/stocks, owners,
empty/reserved fields and unique links are checked. Additional physical forces
are limited to the retained sector854 Mercenary 37/100000 or neutral 37 contexts.
Explicit same-day creation clocks and complete source-labelled helper prefixes
are required; malformed/unused/exhausted clocks fail rather than selecting a
different profile or patching a target.

## Source order and composition

The phase restores Wanderer, rejects occupied placement candidates, creates
Xannoron with its initial ground/bank draws and common ground-increment draw,
then chooses the fallback, allocates nineteen groups and follows directed BFS
routes in source order. It maintains shared pursuit and consumes eager candidate
and interception scans only on the actual surviving source branches.

Foreign defense calls `ReplayForeignDefense` with the calculated current state.
Defender defeat clears pursuit before the following group's candidate scan.
Attacker defeat sets pursuit to that sector, stops traversal and suppresses the
fatal-edge player scan. Neutral ground calls `ReplayNeutralGroundAssault` and
similarly stops the dead moving group. Both return state/draw counts for actual
continuation; no observed endpoint or configured draw budget corrects the stream.
Statistics preserve source-order typed events, planned routes and actually
entered prefixes separately.

Group pointer cleanup, source raw cache zeros, reserve/casualty accounting,
group-20 mine placement and physical deposition are calculated before Base
restoration/placement. Neutral physical force is not incorrectly counted as an
allocated Xannor group or erased during deposition. The result ends at the
pre-Mercenary-tail boundary: no downstream tail, final metadata, news or scores
are published by this API.

## Existing evidence and tests

The exporter wraps the existing occupied Python economy and tail boundaries.
All 30 intermediate before/after worlds, states, births, routes, groups, events
and reseeds are calculated. Initial inputs retain the existing reconstructed
baseline/fixture provenance; native case before-worlds and after files do not
seed a phase. The complete Python run precedes native target comparison.

The independent whole-run audit remains **180 six-file comparisons /1080 native
files and 1872 RNG witnesses**, plus existing original-source evidence. Phase
hashes and receipts are model-derived intermediate oracles, not newly captured
phase observations. No native bytes, hashes or acquisition attribution changed.

Go tests match every complete phase world, all 120 combat events, groups, routes,
entered prefixes, eager/skipped scan counts, birth/rejection receipts, helper
old/seeded states and final state. They also compose actual Go capped ports,
ordinary economy and this phase directly in all 30 cases. A dedicated assertion
checks pursuit clearing in the 37-Mercenary scenario. Late helper exhaustion,
unconsumed clocks and unsupported contexts return no partial publication. Input
and recipe isolation, copied output and strict older admission are retained.

Exporter controls reject altered inputs/receipts/source identities, native
outputs and poisoned independent witnesses; they enforce synthesis-before-target
ordering and accept equivalent gzip recompression by complete raw bytes.

```sh
python3 scripts/export_occupied_routing_fixture.py --check
python3 scripts/test_export_occupied_routing_fixture.py
go test ./internal/qbmaint -run TestOccupiedRouting
```

Next qualify casualty-dependent news/faction scores and compose the already
recovered Mercenary/lottery tail, final metadata and all six occupied-world files.
This milestone does not add a research CLI profile, broaden historical APIs or
change modern gameplay/save 35, releases or Windows/live BBS acceptance.

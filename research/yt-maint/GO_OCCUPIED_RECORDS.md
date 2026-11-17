# Bounded Go occupied-world six-file replay

`ReplayOccupiedFiles` takes exactly the three original before files and an
`OccupiedInputs` recipe containing startup RNG state, 1000 capped port clocks,
ordered active-planet clocks, missing-home creation clocks, source-labelled
helper clocks separated at Base birth, final day and independent report clocks.
It accepts no intermediate world, calculated RNG endpoint, combat event or
expected output. The phase boundary separates helper arrays, not RNG states:
the actual calculated state continues through every phase.

Admission pins the ten original occupied before-world hashes and original names
and news bytes. Calendars remain day 306 /2026-11-02, and all existing phase guards
remain in force. Unsupported contexts, missing/surplus helpers and late report
failures return nil files and zero aggregate statistics. Inputs are readonly;
all six output buffers are owned. This is a research API with no filesystem,
host clock, production maintenance selection or modern save integration.

## Composition and receipts

1. Existing capped clean ports emit their complete block.
2. Ordinary economy uses the supplied startup state and ordered planet clocks.
3. Home/mobile routing consumes the calculated economy state and creates ordered
   typed combat receipts, through Mercenary Base placement.
4. Existing `ReplayEvolvedNPCTail` consumes the calculated routing state and only
   the remaining helper clocks. It eagerly draws once for each physical defense,
   scans mutable Mercenary sectors descending, preserves raw departure zero
   residues, derives empty routes and computes the inactive lottery.
5. Existing inactive metadata applies the final watermark and all 50 -1 ranks.
6. The casualty writer receives this Go-finalized world and calculated events,
   producing the remaining five files. Original before news rotates unchanged.

The existing tail already admitted the retained absent/surviving-97525 Mercenary
contexts. No duplicate combat/tail primitive or relaxed historical admission was
needed. The aggregate receipt includes each phase's calculated statistics. It
does not describe modeled intermediate states as newly acquired native evidence.

## Reused qualification

The new exporter instruments existing complete before-only Python synthesis,
capturing remaining tail clocks, calculated tail receipts and six output hashes.
Tests join the existing economy, routing and report fixtures by exact case name;
the new fixture does not duplicate native captures or feed modeled phase worlds
into the public composition. Original before bytes enter once, and every Go
intermediate state/world/event is calculated internally.

All 30 sets match every byte of all six files. Tests compare RNG state handoffs,
lottery raw values/candidates, physical desertion sectors, three Mercenary
activations, mutable descending routes, force conservation, 120 combat receipts,
final watermark/ranks and output ownership. Late exhausted/mismatched helper
clocks and report errors demonstrate atomic failure of the complete operation.

Independent retained qualification remains 180 six-file comparisons /1080 native
files and 1872 RNG witnesses. Exporter corruption controls reject changed native
targets, poisoned RNG witnesses and altered clocks/receipts/source fingerprints,
and enforce complete synthesis before targets are opened. No native bytes,
hashes, frozen source attribution or acquisition observations changed.

```sh
python3 scripts/export_occupied_records_fixture.py --check
python3 scripts/test_export_occupied_records_fixture.py
go test ./internal/qbmaint -run TestOccupiedFiles
```

Next add an occupied research recipe/CLI profile that reuses these fixtures and
retains fresh output publication/source receipts. Full general maintenance,
arbitrary encounters and production integration remain outside this milestone.

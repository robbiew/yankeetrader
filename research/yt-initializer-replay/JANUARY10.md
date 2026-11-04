# January 10 initializer parity — 2026-11-04

Fresh original DOS captures close the January 10 date restriction in `qb36-v1`.
Ten added controls cover January 9, 10 and 11 in each admitted year (2026–2028),
plus an independent January 10, 2027 repeat. Every complete source world matches
Go and Python synthesis: 4,151 records / 568,687 bytes per control. The ten earlier
controls and their fingerprints remain unchanged; portable Go fixtures now cover
**twenty** complete native worlds.

## Observed bytes and bounded rule

On January 10, the pre-maintenance port watermark `day-of-year - 10` is numeric
zero, but its raw four bytes depend on the port trade class:

| Trade class | Preceding coefficient-array index (`7 - class`) | Raw date bytes at record offset 45 | Ports per retained world |
| --- | --- | --- | --- |
| 1 | 6 | `06004000` | 345 |
| 2 | 5 | `05002000` | 345 |
| 3 | 4 | `04000000` | 310 |

All four January 10 controls retain the same class/count mapping. Neighboring
January 9 and January 11 controls serialize canonical -1 (`00008081`) and +1
(`00000081`) respectively. The repeat matches the January 10, 2027 world byte for
byte. Each separate seed probe observes TIMER FAC `00004800` and raw seeded state
`c805`; no seed is inferred from the world hash or assumed to be canonical zero.

The archived initializer listing at code `1c28..1cb9` computes the class,
subtracts it from seven to index the selling coefficient, converts that index to
an integer, and then adds the stored calendar day to -10 before writing the
watermark. The index conversion leaves the FAC low word equal to `7 - class`;
the upper mantissa remains that of the same small integer. The existing retained
BRUN30 cancellation contract clears only the exponent on exact zero. Preserving
those bytes reproduces all observed January 10 records. This is a bounded writer
rule corroborated by runtime outputs, not a general MBF arithmetic emulator.

New pinned original-byte contracts cover the port class/date sequence (file
`0x1e28`, 146 bytes), seven constant (`0x29de`, four bytes), and minus-ten constant
(`0x2f48`, four bytes). Together with the previous conversion/addition ranges,
[native contracts](native-contracts.json) now contain 26 independently checked
ranges. The original binaries and archived listing are unchanged.

## Capture provenance and validation

[Controls](january10-controls/) retain complete compressed pre-maintenance
worlds, independent raw-seed traces, original normal-return markers, exact input/
clock recipes, aliases/newspaper outputs and checksums. The runner executes only
copied original initializer/runtime binaries inside disposable directories. The
maintenance child is the declared five-byte exit stub; no original maintenance
result is claimed. Prior radio sentinels are removed by the original initializer.

The REA service was reachable, but its Ghidra provider still reported a missing
configured JDK. These observations therefore use fresh DOSBox execution and the
pinned archived byte/listing contracts, not new successful REA decompilation.
No REA, emulator or Python dependency is added to the game or portable Go tests.

```sh
python3 scripts/recover_initializer_controls.py --january10 /tmp/yt-jan-new-controls
python3 scripts/verify_january10_controls.py /tmp/yt-jan-new-controls
python3 scripts/test_verify_january10_controls.py
python3 scripts/test_replay_qb_initializer.py
python3 scripts/export_qb_initializer_fixture.py --check
python3 scripts/test_qb_initializer_fixture.py
go test -race ./internal/qbinit ./internal/game -run 'Test(QB|January10)' -count=1
python3 scripts/smoke_qb_profile.py
```

The independent control verifier pins all native whole-world hashes and checks
all 1,000 raw date fields per world, neighboring dates, class frequencies and the
repeat. Corruption tests reject normalized/class-wrong zeros, rehashed date/
return/seed changes and missing neighbor/repeat controls. Source replay and Go
fixtures compare all five record blocks, complete hashes and stream endpoints.
The gameplay regressions create, save/load and reset January 10 recipes through both Genesis and administrative paths in each
admitted year, keeping modern UTC watermarks separate from source dates; CLI
smoke initializes a January 10 world against its native fingerprint.

## Compatibility and limits

The change extends date admission; it does not reroll existing worlds or change
any previously admitted source output. `qb36-v1`, save **35**, default counts and
modern projection/reset adaptations remain unchanged. New January 10 recipes
require this updated build on every node: earlier save-35 binaries reject that
formerly unsupported date. Do not strip the recipe to force an old binary to load
it; use a compatible backup for rollback.

The evidence covers selected source dates, all three trade classes and the
measured midnight state. It does not prove every 24-bit seed/calendar combination,
exact DOS maintenance, arbitrary MBF arithmetic or DOS save interoperability.

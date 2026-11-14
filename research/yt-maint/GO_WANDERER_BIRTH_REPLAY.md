# Bounded Go initial Wanderer creation and placement

`qbmaint.ReplayWandererBirth` ports only the first initial NPC creation step,
before Xannoron/mobile groups/Mercenary Base. It accepts a before-world, explicit
source day, 24-bit modeled RNG state and the actual raw first helper TIMER.
There is no target-world, target sector or correction-table input.

The model restores the source-assigned fields of inherited planet record 4052,
sets its name to The Wanderer and selects one empty sector's planet link.
Unassigned record bytes are preserved. Original raw constants, including stock/
ground zero residue `00001c00`, are taken from the already recovered original
YTMAINT mapping and independently authenticated during fixture export. No new
native acquisition or source query was needed.

The existing `qbrng` primitive preserves the old low seed byte, XOR-mixes the
raw helper TIMER words and advances once. The bounded integer helper uses the
same explicit float32 product/floor step as the independent Python/source model.
It is not a general MBF conversion claim. Day 1..732, state width, TIMER range,
default geometry, inactive players/planets and all-empty sector planet links are
guarded. Rejection/retry and occupied-world behavior remain excluded. Invalid
inputs return no world and zero statistics, preserving the input.

## Reused native targets and provenance

Twenty-nine observed fresh-calendar/clock-matrix runs retain the complete
137-byte birth record and its four-byte sector link undisturbed through final
maintenance. Both match Go and independent Python synthesis byte for byte.
The three declared `matrix/late/observed-*` runs later alter the Wanderer in an
encounter and are explicitly excluded from this final-target birth comparison.
They remain authenticated in the parent corpus; no mismatch is masked or
rehash performed, and encounter handling is not admitted here.

Fixture export reuses the clean-port before-worlds and existing authenticated
raw host observations. It derives initial state/day/TIMER from source-qualified
observations, synthesizes before-only birth bytes, then opens native targets
separately. The original executable and Python/exporter/source fingerprints are
bound in the fixture. Sector and complete record/link bytes are native oracles;
seeded/final RNG endpoint values are independent Python-model expectations,
not newly observed native endpoint witnesses.

Go tests compare whole records/links, every unrelated world byte, modeled RNG
statistics and input/output isolation. Guards cover late occupied/activity
failures, invalid day/state/TIMER/geometry, inherited bytes and raw-zero TIMER
seeding. Three exporter regression tests reject changed source inputs, modeled
state, native record/link bytes, source inventories and capture exclusions.

```
python3 scripts/export_wanderer_birth_fixture.py --check
python3 scripts/test_export_wanderer_birth_fixture.py
go test -race ./internal/qbmaint ./internal/qbrng ./internal/qbmbf ./internal/qbinit
```

Xannoron creation, moving-group allocation/routes/encounters, Mercenary Base,
active-player economy/rankings, auxiliary files, full Go maintenance and playable
integration remain separate. Gameplay, save format 35, original observations,
initializer fingerprints and sysop procedures are unchanged. Audit Xannoron
creation/timestamp/ground/bank inputs next against the retained evidence before
starting the next bounded Go NPC slice.

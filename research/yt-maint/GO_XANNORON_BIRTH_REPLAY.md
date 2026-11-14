# Bounded Go initial Xannoron creation

`qbmaint.ReplayXannoronBirth` models only reserved planet 4151 creation and its
HQ planet link, after Wanderer placement and before mobile group allocation.
The inputs are an independently modeled post-Wanderer world, explicit source
day, modeled 24-bit RNG state and actual raw Xannoron TIMER seconds. No native
target, selected result or correction table enters the API.

## Source and numeric composition

The existing Python NPC replay and original YTMAINT constants supply the source
contract. All source/captures were reused; no new acquisition or query was needed.
The record is inherited, not zero-constructed. It receives the source-assigned
name, date, production/stock constants, owner, ground, bank and timestamp fields.
Unassigned bytes survive, including raw stock-zero residue `00007000`. The HQ
link is set to canonical 100; sector force/owner and every other world byte are
preserved at this prefix stage.

Timestamp calculation composes qualified raw `DivideSingle(TIMER,60)` and
`IntSingle`. Sub-minute results retain their original fractional FAC bytes with
only the exponent cleared. Ground uses the first and third RND values, separately
multiplied by 250/25 then INT-truncated. Bank uses the second RND, multiplied by
10000000 then added to 100000 with separate raw SINGLE rounding. Raw RND encodings
are constructed exactly from the qualified generator's 24-bit state; arbitrary
host floating-point encoding is not used. All three draws continue the modeled
Wanderer endpoint without reseeding.

## Explicit admission

- Default 4151-record geometry; inactive players and no additional active planets.
- A modeled Wanderer predecessor and exactly one Wanderer sector link.
- Configured/tracked HQ 8..3000, its initial 10000 Xannor force/owner, no other
  sector force and an empty HQ planet link.
- Source day 1..732, 24-bit state and nonzero DOS TIMER from the raw encoding
  nearest one centisecond through less than 86400 seconds.
- Positive resulting ground defense (1..273). Exact-zero TIMER policy,
  sub-centisecond inputs, zero-ground births and occupied-HQ cases are excluded
  rather than widening the retained capture admission silently.

Errors return nil world and zero statistics without mutating input. Successful
output has independent storage. Clock/state source authentication remains the
caller's responsibility; the guards are not provenance verification of arbitrary
caller-supplied bytes.

## Reused native validation

All 32 existing observed fresh-calendar/clock-matrix runs retain the complete
137-byte creation record and its four-byte HQ link unchanged through final
maintenance. Every byte matches independent before-only Python synthesis and Go,
including the three late-night cases whose later Wanderer encounter prevents
using their final Wanderer record as a birth oracle. No such exclusion is needed
for these Xannoron record/link targets.

The fixture exporter authenticates the existing native/source manifests first,
extracts clock inputs from qualified raw host observations and constructs the
Wanderer prefix from before inputs. Only after independently synthesizing
Xannoron does it open native target records/links. The Go test constructs its
own prefix with `ReplayWandererBirth`, verifies the modeled RNG handoff, then
compares the whole native Xannoron record/link and every unrelated prefix byte.
This does not claim whole-world equality with final native maintenance output.

Record, timestamp, bank, ground and link bytes are native oracles. Final RNG
states are independent Python-model expectations, not newly observed native
endpoint witnesses. Four exporter regressions reject changed prefix inputs,
clock/state/field identities, native records/links and source/control inventories.
Go tests cover raw residue, inheritance, three-draw state continuation, atomic
admission failures, source isolation and the explicit zero-input exclusions.

```
python3 scripts/export_xannoron_birth_fixture.py --check
python3 scripts/test_export_xannoron_birth_fixture.py
go test -race ./internal/qbmaint ./internal/qbrng ./internal/qbmbf ./internal/qbinit
```

Initial mobile groups, routing/interceptions, Mercenary Base creation, active
player economy/rankings, auxiliary files, full Go maintenance, production
integration and Windows/live-BBS acceptance remain separate. Original captures,
Python replays, gameplay, save format 35, initializer fingerprints and sysop
procedures are unchanged. Audit the initial mobile-group allocation/RNG
continuation against current source/captures before choosing the next Go slice.

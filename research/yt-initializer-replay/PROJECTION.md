# Safe QB source projection and admission

This slice adds the internal `prepareQBWorld` / `projectQBSource` candidate
pipeline in `internal/game/qb_projection.go`, building on the
[pure Go source generator](GO_IMPLEMENTATION.md). It creates no active save and
adds no CLI flag, persisted QB recipe or schema. Save format remains **34**.
Existing constructors do not select this pipeline. The
[compatibility contract](COMPATIBILITY_CONTRACT.md) still governs later integration.

## Admitted candidate

The source generator runs once with explicit options. Its owned raw bytes and
RNG statistics are preserved. The candidate retains a SHA-256 of those complete
source bytes, source options and statistics separately from its modern world.
This fingerprint describes pre-projection source bytes, not the evolving save.

Admission checks bounded record coverage/layout and integer-valued source fields,
HQ/record-pointer consistency, complete graph bounds, unique warp destinations,
port locations/names/classes/economy and all authoritative sector/port links.
MBF exponent-zero residues decode numerically as zero; noninteger/out-of-range
values are rejected before conversion to modern indices or resources.

Only Earth's redundant self-link is omitted, preserving every remaining warp's
relative order. Both forward and reverse Earth connectivity must hold. The
original duplicate-port control at state `a90a05` fails admission rather than
moving/replacing a port or choosing another state. HQ sectors 1–7 are rejected.
No source repair, resampling or fallback generation occurs in projection.

The modern candidate has fresh typed maps and no imported inactive player/planet
records. It uses current UTC creation/maintenance watermarks and ten initial
production days of cargo. Source rates, coefficients, locations and names remain
unchanged. Existing DOS reference pricing is selected by the existing internal
map/economy rule-family fields; these are not a persisted QB generation profile.

The source HQ becomes one 10,000-fighter Xannor defense plus HQ state with zero
reserve. Modern bounded bootstrap creates Mercenary Base, Xannoron and The
Wanderer using its separate supplied modern seed. All required homes and final
world invariants must hold; Xannoron/HQ must remain at the source location.
Bootstrap never consumes the QB stream or changes its source fingerprint.

Every error returns a nil candidate. The source input remains unchanged, and all
intermediate world state stays local. Generation draw-limit errors propagate
without a partial result. The helpers accept no active world/store and perform
no filesystem publication. This is not a DOS save importer.

## Verification

```sh
go test -race ./internal/game -run '^TestQB' -count=1
go test -race ./...
go vet ./...
```

Five test groups cover:

- Three distinct admitted native states, exact baseline Earth production/
  coefficients, ordered Earth warps, native HQ force and required modern homes.
- Historical source date versus current UTC world/port watermarks, ten-day
  initial stock and absence of inactive DOS accounts/planet placeholders.
- Retained duplicate-port rejection, a generated protected HQ, raw-state errors
  and exhausted source budgets, always with a nil candidate.
- Truncated/layout/HQ/warp/name/stock/economy/link corruptions and source immutability
  on rejection; a directed graph reachable from Earth but unable to return
  explicitly exercises reverse connectivity.
- Repeatable complete candidates, independently seeded modern bootstrap with
  unchanged source/map/economy, and no shared mutable candidate storage.

Tests require only portable Go source fixtures and compiled code; this slice adds
no new native recovery or external executable dependency. Existing source goldens
continue to test bit-exact source behavior independently of modern adaptations.

## Next integration slice

Persist a versioned typed recipe and implement CLI admission, old-save/unknown-
profile handling, source provenance round trips, Genesis intent binding and both
reset paths before enabling a playable QB profile. Preserve source recipes and
repeat-layout reset semantics, archive-first guarded admin resets, committed
versus pre-replacement failure handling and current-world immutability on failure.

The internal schema-34 candidate is deliberately not exposed to CLI/store creation:
using existing `dos` rule-family fields alone would lose the source recipe and
would reset using the modern generator. Completing the future schema/recipe and
reset contract is therefore a prerequisite to publishing this profile.

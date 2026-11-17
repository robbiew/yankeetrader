# Bounded Go neutral-owner transfer and mine-before-stock pickup

`ReplayNeutralOwnerStockMercenary` consumes a modeled pre-Mercenary world and
explicit calculated state/source helper clocks. It returns owned phase bytes
and calculated receipts, or nil world/zero statistics on every error. It ends
before lottery, final metadata, news and scores. Existing held/departed APIs and
historical tails retain their original admission; no modern policy is selected.

## Source order and physical ownership

The six retained contexts combine one or 37 neutral fighters, neutral empty/half/
37 stock and the linked one-mine 37-stock branch, plus two/four-second friendly
one-mine controls. Neutral physical defenders take their eager desertion draw
but do not activate in the Mercenary scan. Friendly local fighters may hold or
depart and reactivate later in the descending mutable scan. Calculated helper
clocks, graph paths and actual entered prefixes determine every branch.

At a linked mine the incoming force is 97337. The source helper2 /4aa4 reseeds
once, starts its bound at 10000, and consumes two shrinking integer draws. The
capped loss affects only incoming fighters. The spent mine subtracts to exact
`00000000`; raw pickup/departure zeros are not substitutes for this field.

Surviving incoming force then adds actual entering local physical fighters once,
followed by raw SINGLE INT whole stock. Owner-zero fighters debit neutral inventory
and credit Mercenaries; owner-2 fighters count as a friendly merge rather than
new inventory. The pre-stock actor includes local force only if actually present.
Positive local force suppresses capture, while an empty physical gateway emits
the capture receipt. Empty/subunit stock clears silently with `00008000`.
Governor, name, ground and unrelated planet/world bytes stay unchanged.

| Retained case | Incoming mine loss | Neutral transferred | Gateway final force | Separate local force |
| --- | ---: | ---: | ---: | ---: |
| neutral-one-empty | 0 | 1 | 97338 | 0 |
| neutral-whole | 0 | 37 | 97411 | 0 |
| neutral-half | 0 | 37 | 97374 | 0 |
| neutral-mine-whole | 381 | 37 | 97030 | 0 |
| friendly-mine-second-two | 159 | 0 | 97252 | 0 |
| friendly-mine-second-four | 4374 | 0 | 93000 | 37 at 356 |

These values are comparison receipts from the qualified fixture, not inputs to
the API. The four-second path derives the local group's endpoint at 356, preserving
its 37 fighters separately from the incoming pickup actor and gateway force.

## Bounds and verification

Admission requires the exact linked owner/force/mine/canonical-stock contexts,
neutral zero-bank Gateway Cache identity, default geometry, inactive humans,
zero taxes, bounded whole NPC forces and integer graph. Helpers are ordered
first-minute family 1 /48cf target or family 2 /4aa4 mine clocks. Computed call sites
enforce chronology. A single linked mine, one pickup and at most three Mercenary
activations are supported; other mine, defense, merge or planet contexts fail.

Tests compare all 18 modeled worlds, 27 activation receipts and nine mine receipts
against the existing Python four-day replay. They verify complete RNG continuation,
source gates/reseeds/candidates/routes/entered prefixes, exactly two mine draws,
mine-before-pickup event order, incoming-only losses, separate neutral debit,
friendly merging, physical conservation, pickup actors/fractions and distinct
raw zeros. Changed bytes are constrained to source-owned origins/destinations,
the actual mine field and stock field. Late clock exhaustion or later route errors
publish no partial output; caller bytes/recipes and returned storage are separate.

The exporter completes the original modeled three-day prefix and declared child
before any native targets are opened. Independent retained qualification remains
108 six-file comparisons /648 native files and 855 child RNG witnesses. Original
observation bytes/hashes, frozen acquisition sources and static evidence remain
unchanged. Integrity controls reject altered modeled inputs/receipts/sources,
native corruption and poisoned witnesses, enforce synthesis-before-target reads
and allow equivalent gzip recompression by uncompressed bytes.

```sh
python3 scripts/export_neutral_owner_stock_fixture.py --check
python3 scripts/test_export_neutral_owner_stock_fixture.py
go test ./internal/qbmaint -run TestNeutralOwnerStock
```

Next audit the distinct Mercenary foreign-defense/surviving-stock branch against
its existing corpus and Python rules. Full four-day Go composition and research
recipe publication remain later integration work, not claims of this phase.

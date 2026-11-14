# Bounded Go Mercenary Base creation and placement

`qbmaint.ReplayMercenaryBaseBirth` ports main41c1..4473 as already modeled by
`scripts/replay_maintenance_npcs.py`. Existing native captures and original
executable constants were reused; no new acquisition or binary query was needed.
PR #155's ordinary initial mobile-group slice was merged and verified on main
before opening this separate PR. No open PR duplicated this slice at audit time.

Inputs are an independently modeled post-mobile-group world, explicit source day
1..732, the modeled 24-bit RNG handoff and the next raw helper-one TIMER sample
(ordinal 41 of the initial NPC stream). RANDOMIZE preserves the incoming low
byte; one bounded integer draw chooses sector 1..3000. A nonempty link is
rejected, without trying a new clock or silently assuming a retry policy.

The reserved record 4150 (planet slot 99) is inherited. Name/activity/date,
production, stock, owner, ground, bank and field 125 use the original assigned
bytes, while every unassigned byte remains unchanged. In particular stock zeros
are `0000a000` and field 125 is `00003e00`, not canonicalized zeros. Sector link
99 is the only other world write. It is permissible for the base to share a
sector with a mobile group if its planet link was empty.

Admission requires default geometry, inactive players, two modeled birth planets,
zero pending revenge, all twenty distinct positive Xannor group endpoints,
10000 total force, and the ordinary group-20 mine prefix. Existing bases, foreign
forces, hazards, occupied placement links and noninitial worlds are excluded.
The caller authenticates clock and state provenance; these guards do not prove
arbitrary inputs were acquired natively. Errors return nil output/zero stats and
preserve the input. Success returns independent storage.

## Existing native qualification

The exporter first authenticates the mobile fixture/source/observation chain,
extracts raw helper clocks and independently synthesizes the inherited base
record from before bytes and original constants. It admits placement using the
modeled earlier Wanderer/HQ links, then opens native targets for whole-record
and four-byte placement-link comparison. All 29 ordinary initial runs match.
The three `matrix/late/observed-*` combat runs remain authenticated in parent
research but are outside the Go mobile-prefix composition; no new validation
of those branches is claimed.

Go tests reconstruct Wanderer birth, Xannoron birth and mobile groups before
calling this API, and verify every unrelated prefix byte. Native record/link
oracles are distinct from independent Python seeded/final RNG states. The raw
TIMER and state are inputs, not selected-sector or target-derived corrections.
This is not whole native final-world equality: hiring, desertion, lottery,
rank/report/auxiliary phases and complete maintenance remain separate. Gameplay
and modern save format 35 are unchanged. Original native hashes/bytes and local
unrelated smoke captures are preserved.

## Verification

```
python3 scripts/export_mercenary_base_fixture.py --check
python3 scripts/test_export_mercenary_base_fixture.py
go test -race ./internal/qbmaint ./internal/qbrng ./internal/qbmbf ./internal/qbinit
go vet ./internal/qbmaint ./internal/qbrng ./internal/qbmbf ./internal/qbinit
```

CI checks the portable oracle, source/clock inventory and corruption controls.
Tests cover whole records/links, one-draw continuation, inherited sentinel bytes,
stock/FAC zero residues, atomic admission and output independence. Next audit is
the initial no-hiring desertion/lottery tail and auxiliary writes against existing
source/captures; do not repeat completed initial mobile or base creation.

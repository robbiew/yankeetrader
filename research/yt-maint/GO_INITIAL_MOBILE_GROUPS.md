# Bounded Go initial mobile-group allocation

`qbmaint.ReplayInitialMobileGroups` ports the already recovered initial plain-route
slice in `scripts/replay_maintenance_npcs.py` (top fallback, allocation, routing
and final writeback). No new DOS capture, executable query or observation was
needed. PR #154's birth slice is already merged on main; no open PR duplicated
this work at the initial audit.

## Inputs and phase boundaries

Input is an independently modeled post-Wanderer/post-Xannoron world, a 24-bit
state, 39 raw helper-one TIMER samples (top fallback then fallback/candidate per
missing group), and 19 helper-two samples. There are no target/patch inputs.
The first helper reseeds while preserving the inherited low byte; it draws a
1..2993 fallback plus 7. Each missing group reseeds helper two and successively
draws four shrinking 1..bound values. The force is deducted from HQ before
selection. Fallback/candidate helpers each reseed and draw once. Fifty eager
candidate draws and fifty eager draws per entered plain sector continue the
same stream. Group 20 selects the top fallback and increments its endpoint mine
field. Original column-order directed BFS supplies finite routes; no encounter
handler is implemented.

The default 4151-by-137 layout, all-inactive players (whose cached positions are zero), initial 10000 HQ force,
empty mobile slots and the two modeled birth planets are required. Invalid
warps, unreachable routes, same-HQ fallback retries, candidate rejection,
entered planets/mines, protected targets, zero-bound allocations, zero or merged groups and existing hazards fail without
partial output. The admitted plain routes never change RNG behavior by route
order; only their entered-sector counts matter. This does not implement general
interception, NPC combat, live gameplay or complete maintenance.

## Reused evidence and qualification

The exporter authenticates the existing clean-port before-world/capture chain
and Xannoron birth fixtures, then runs the independent Python NPC reference on
before-worlds and raw measured clocks. Only afterward does it open native final
worlds. Across 29 runs it compares the complete inventory of all 3000 sector
force, owner and mine fields plus all 20 mobile pointers: 9020 four-byte fields
per run, 261580 fields total. Portable fixtures retain a SHA256 of that complete
native projection, not a patch or synthesized expected output.

The three `matrix/late/observed-a`, `-b`, `-c` runs enter Wanderer combat; they
remain authenticated in parent evidence and are explicitly excluded here.
There are no new native RNG-state measurements. Group results, draw counts and
the state immediately before helper-one ordinal 41 (Mercenary Base placement)
are independent Python-model endpoints; they are labeled separately from native
field oracles. Go tests reconstruct both preceding births rather than loading
an after-world as the replay input.

Only group writeback fields and the group-20 endpoint mine field change relative
to that modeled prefix. All other bytes stay inherited. Full native final-world
parity is deliberately not claimed: later Mercenary Base, desertion, lottery,
rank and report phases remain separate. Modern save format 35 is unchanged.

## Verification

- `python3 scripts/export_mobile_groups_fixture.py --check`
- `python3 scripts/test_export_mobile_groups_fixture.py`
- `go test -race ./internal/qbmaint ./internal/qbrng ./internal/qbmbf ./internal/qbinit`
- `go vet ./internal/qbmaint ./internal/qbrng ./internal/qbmbf ./internal/qbinit`

CI regenerates and checks source/observation provenance and corruption controls.
Tests compare every projected native field via its digest, conserve force,
validate helper/state handoffs, preserve input/unrelated bytes and reject
unsupported profiles atomically. Next audit is Mercenary Base creation and
placement against existing captures; do not repeat completed mobile allocation.

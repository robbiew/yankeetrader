# Next bounded slice: physical owner, mine damage and stock pickup

Planning audit, 2026-11-07. The proposed acquisition matrix is now executed in
[separate native controls](NEUTRAL_OWNER_STOCK_CONTROLS.md). This document preserves
the pre-acquisition questions; outcomes do not widen replay admission. Departed-garrison research PR #109
and replay PR #110 already cover local Mercenary hold/departure without mines;
PR #108 owns the included held-garrison replay dependency. Keep their heads fixed.

## What is already complete

- [Gateway hazards](GATEWAY_HAZARD_REPLAY.md): zero local defense or a positive
  Xannor defense, linked stock, one-mine damage, three-mine fatal incoming force,
  and the two-day continuation. `recover_maintenance_gateway_hazards.py` assigns
  owner -1 whenever its local defense is positive. It does not capture positive
  owner-zero or owner--2 defense together with the mine/stock composition.
- [Friendly stock](FRIENDLY_STOCK_REPLAY.md): held positive owner--2 garrison,
  whole/fractional/empty stock, neutral/Mercenary planetary governors, no mines.
- [Departed stock](DEPARTED_STOCK_REPLAY.md): the local 37 can depart, then
  reactivate lower in the same descending scan; held counter-controls remain.
  Its eight fixture admissions all require a mine-free gateway.

## Smallest useful new matrix

Use the existing per-mode November 4 evolved parent and forced 2368-to-3000 hop,
with Gateway Cache at slot 3, ground 500000, neutral planetary governor, zero
rates/bank, and incoming force 97337. Preserve every other parent byte and declare
all edits independently. Six *new* fixture proposals follow:

| Fixture | Local physical force | Sector owner | Stock | Mines | Requested clock |
| --- | ---: | ---: | ---: | ---: | --- |
| neutral-one-empty | 1 | 0 | 0 | 0 | 00:00:02 |
| neutral-whole | 37 | 0 | 37 | 0 | 00:00:02 |
| neutral-half | 37 | 0 | 1/2 | 0 | 00:00:02 |
| neutral-mine-whole | 37 | 0 | 37 | 1 | 00:00:02 |
| friendly-mine-second-two | 37 | -2 | 37 | 1 | 00:00:02 |
| friendly-mine-second-four | 37 | -2 | 37 | 1 | 00:00:04 |

The clocks are interventions, not promises of hold/departure after adding a mine.
Existing mine-free two/four-second and empty-defense mine fixtures are comparison
controls already retained; do not reacquire them just to fill a table. Start with
one complete day in six established observation modes: 36 runs / 216 output files
if all complete. Freeze this recipe and actual executed sources before launch.
Any later supplement must have its own predeclared recipe and retain all outcomes.

## Questions to measure, without assumed answers

1. Does positive owner-zero physical force enter the source cached-force sum
   before stock, without a foreign-defense event? Does positive entering force
   suppress capture text independently of the neutral planetary governor?
2. Does any such faction transfer debit the neutral inventory and credit the
   Mercenary inventory once? Inventory accounting must allow a *measured* owner
   transfer rather than forcing the existing no-transfer conservation equation.
3. With a mine, which incoming count appears in capture/taking text, and does
   local entering force join before or after the mine loss? Bind helper2/4aa4
   calls and RNG witnesses independently; never infer missing draws from totals.
4. For owner -2, does the local group hold or depart under the actual full scan,
   and does departure leave mines untouched until the incoming route reaches them?
   Record all later activations and physical endpoints, even if outcomes differ
   from the mine-free controls.

## Evidence and acceptance boundaries

The existing immutable source audit (`verify_maintenance_friendly_stock_native.py`)
binds the cached owner/link pickup gate, actor-plus-entering-force arithmetic and
capture gate to original bytes. Gateway recovery separately binds mine helper
semantics. These conditional source contracts motivate this experiment; they do
not establish the combined outcomes. No new REA packet is needed merely to repeat
those exact byte ranges; obtain a new bounded native read if a different source
path must be explained.

Retain exact six-file before/after bytes, full console/public receipts, all
physical owner inventories, raw stock clears, raw date/time, original guests and
CPU, natural exit, loaded observer, paired frames and persisted flush receipts.
Verify all modes and provenance independently of the writer. Preserve mismatches
and failures; no retries, altered observation hashes, normalization or hand-edited
parent saves to make the outcome fit. If added contexts perturb earlier Xannor
activity, retain and account for it before qualifying any loss-free rule.

Only after native qualification should a separate before-only replay derive the
modeled parent, pure edits, owner transfer, mines, repeated activations and all
writers. Require coherent faction-transfer/double-count corruption controls and
retain the strict historical admission guards. Human owners, negative/overflow
stock, general MBF behavior, production integration and live BBS acceptance are
outside this proposed slice.

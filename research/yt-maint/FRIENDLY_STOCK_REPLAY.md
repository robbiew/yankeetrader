# Before-only held-friendly-force and planet-stock replay

Implemented 2026-11-07 after checking acquisition-only PR #107 at
`d9bfdbfcf1267fd7a60a8106990c55d755ddef99`. Its eight-case corpus, frozen executed
sources, native packet, manifests and every observation remain unchanged. This
milestone implements the missing composition; it does not recapture that work.
Production Go, dependencies, generation fingerprints and save 35 are unchanged.

## Inputs and complete modeled handoff

The new explicit `replay_maintenance_friendly_stock_records.py` profile accepts
only the original three-file `route-mercenary-100000` input, four frozen typed
source-day inputs, and one of eight declared joint fixture names. The existing
combat replay computes the complete November 2–4 prefix. A pure fifteen-edit
transformation receives the actual modeled November 4 six-file object, redirects
the gateway edges, creates Gateway Cache and installs the declared friendly
force/governor/stock. All five side-file objects remain the modeled parent bytes.
The child then runs November 5 port economy, planets, Xannor actions, Mercenary
composition and all five public/private auxiliary writers.

No native November 4 after-world is loaded as a synthesis handoff. Core reads are
limited to immutable original maintenance constants/literals. After-targets,
capture metadata, expected hashes and observed old RNG states are excluded.
Comparison code opens outputs only after the entire four-day modeled chain is
complete. Actual before/after fixture comparisons and observed RNG states remain
independent verification witnesses rather than model seeds.

## Derived composition

The earlier physical garrison at sector 3000 activates first in the descending
mutable scan and holds on its eager movement draw. The modeled force 97337 then
departs sector 2368, consumes source-labelled helper TIMER inputs, computes its
route and stops at Gateway Cache on the forced first hop. Pickup precedes ordinary
nonplanet merge, exactly as qualified by the existing original-byte audit.

| Case | Friendly force | Governor | Stock | Saved force | Taking actor / amount |
| --- | ---: | ---: | ---: | ---: | --- |
| friendly-one-empty | 1 | 0 | 0 | 97338 | None |
| friendly-empty | 37 | 0 | 0 | 97374 | None |
| friendly-half | 37 | 0 | 0.5 | 97374 | None |
| friendly-whole | 37 | 0 | 37 | 97411 | 97374 / 37 |
| friendly-odd-half | 37 | 0 | 1.5 | 97375 | 97374 / 1 |
| friendly-large | 37 | 0 | 189528.5 | 286902 | 97374 / 189528 |
| friendly-owned-whole | 37 | -2 | 37 | 97411 | 97374 / 37 |
| friendly-large-force | 97337 | 0 | 37 | 194711 | 194674 / 37 |

The model computes `incoming + entering friendly + INT(stock)` once. It does not
apply a second plain-merge event. The original positive-SINGLE floor routine is
reused for positive stocks; exact admitted zero is handled explicitly. The whole
stock clears to source `8472` raw `00008000`, including discarded subunit stock.
Capture text is suppressed by entering friendly force, independent of governor.
Positive taking text stamps the combined pre-stock actor. Zero converted stock
prints no taking-zero receipt. Both neutral and Mercenary planet governors,
planet titles/ground and unrelated record bytes remain unchanged by pickup.

Public ledger admission independently binds the initial two physical forces, the
held-garrison activation, the incoming activation, combined receipt actor, pickup,
raw clear, final physical force and exact faction score. Coherent overwrite or
double-count totals, changed governors and falsely captured/merged actors fail.
The public news clock is 00:00:00 and the distinct source score clock is 00:00:01;
they remain explicit immutable clock inputs rather than one substituted clock.

## Historical boundaries remain strict

The new record/NPC/planet/public-writer modules form an explicit bounded profile.
The old stock pickup still rejects an occupied gateway and its public wrapper
still admits only its previous single-force context. Its private descending-scan
kernel gains a pickup-action parameter so the new wrapper can reuse the exact
scan/RNG/combat logic. The default path is unchanged; no global monkeypatch or
mutable profile switch is used.

The new admission accepts only the eight **jointly measured** force/governor/stock
combinations, not their arbitrary Cartesian product. It requires the actual linked,
mine-free Gateway Cache, canonical exact initial stock bytes, fixed incoming
force, no hiring/human actions, the observed one-day date/clock range and full
helper-clock consumption. A garrison departure, unrelated combat, unknown stock,
negative/nonfinite/overflow conversion or arbitrary world fails explicitly.

## Complete comparison and validation

All **144 complete comparisons / 864 files** are byte-identical. For each case,
three independently modeled source-clock chains are checked against both
unobserved outputs, attach-only and all three observed targets. The 24 direct
observed-source comparisons are included. All **1104 new-stage RNG-state
witnesses** agree; the three prefix stages are also audited without counting
reused prefix observations as new targets. No normalized byte or skipped output
is admitted by the report-inventory validator.

All **28 new tests** pass: 11 complete-chain/read-boundary tests, 11 auxiliary
publisher/adversarial-ledger tests and six atomic pickup/historical-guard tests.
They verify modeled object and marker handoffs, original-source-only reads,
fifteen exact fixture edits against the independent recipe, output-read ordering,
poisoned observed RNG independence, typed chronology, coherent double-count and
overwrite rejection, governors, combined receipt actors, zero-receipt suppression,
source-specific raw clears and no-write failures. All 54 historical stock tests,
24 acquisition/provenance tests and nine native-audit tests also pass.

```sh
python3 scripts/replay_maintenance_friendly_stock_records.py --output /tmp/friendly-stock-replay.json
python3 scripts/test_replay_maintenance_friendly_stock_records.py
python3 scripts/test_replay_maintenance_friendly_stock_mercenary.py
python3 scripts/test_replay_maintenance_friendly_stock_aux.py
python3 scripts/verify_maintenance_friendly_stock.py
python3 scripts/verify_maintenance_friendly_stock_native.py
```

These portable checks run in CI without DOSBox, Frida or a new native query.
All 4682 archived original hashes remain unchanged. No new live BBS, full Go
runtime or native Windows durability acceptance is claimed.

## Remaining scope

The measured held-friendly-force-plus-planet-stock composition is now integrated,
not missing replay work. Further bounded state work includes a garrison that
actually departs before incoming pickup and unmeasured owner/hazard/stock or
surviving-combat compositions. Do not infer those paths from this held-garrison
corpus. General MBF, negative/overflow conversion and arbitrary-world/native-save
compatibility remain separate. Existing modern safeguards remain intentional.

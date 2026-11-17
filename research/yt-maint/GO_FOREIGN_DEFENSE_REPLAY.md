# Bounded Go foreign-defense combat

`ReplayForeignDefense` ports the existing occupied Python `defense` rule into a
separate Go primitive. Inputs are an independently modeled complete default
world, moving group 2–20, sector 854, whole attacker force 1–10000 and a 24-bit
modeled RNG state. Only Mercenary owner -2 with 1–100000 whole defenders and no
mine or planet hazard is admitted. Other owners, mixed hazards, malformed
geometry and out-of-range inputs fail before any output or state publication.

The source uses a 5000 batch only when both remaining forces strictly exceed
5000, otherwise 500, switching to 1 when either is below 500. Each round consumes
one actual recovered RND draw: values above .5 damage attackers; equality belongs
to defender damage. Raw source counters remain distinct from capped survivors.
Only physical defense force is written; defeat also clears its owner, both with
canonical zero. Other world bytes, including pointers and raw hazard-zero aliases,
are preserved. Caller storage is readonly and the returned world is owned.

Statistics contain initial/capped forces, raw damage counters, draw count and
modeled initial/final states. `PreferredCleared` reports defender defeat for the
future routing caller. It does not itself update shared pursuit, moving group
pointers, deposited fighters, public events, scores or the downstream tail.

## Evidence reused

`export_foreign_defense_fixture.py` instruments the existing ten-case occupied
Python replay. It captures 63 calculated encounter before/after worlds and RNG
receipts across the 37/100000-defender controls and three observed clock streams.
Worlds and states come from synthesis, not retained native encounter endpoints.
The complete modeled run exists before native targets open; native case before
files, after files, traces and captured RNG fields do not enter the primitive.

The separate whole-run audit verifies **180 complete six-file comparisons /1080
native files and 1872 helper/final RNG witnesses**, plus the existing original
native source packet. Encounter oracles are model-derived intermediate receipts;
this adds no native observations, acquisition, output corrections or changed
observation hashes. Frozen acquisition attribution remains unchanged.

Twenty-four additional synthetic controls use the same Python rules and actual
recovered LCG, with explicit inverse seeds selecting .5 and its next 24-bit
fraction. Force pairs straddle 499/500/501 and 5000/5001 thresholds, including
asymmetric sides and the 100000-defense bound. These are mathematical/source
boundary checks, not new DOS executions.

Go tests match all complete encounter/synthetic world hashes, raw counters,
survivors, draws, final state and pursuit-clear outcomes. They verify both native-
qualified winners, canonical defeated fields, unchanged surviving owners,
exact write bounds, owned output, atomic refusals and raw hazard-zero retention.
Exporter tests reject changed inputs/receipts/source identities, altered native
targets and poisoned independent witnesses, enforce synthesis-before-target
ordering and accept equivalent gzip recompression by full decompressed bytes.

```sh
python3 scripts/export_foreign_defense_fixture.py --check
python3 scripts/test_export_foreign_defense_fixture.py
go test ./internal/qbmaint -run TestForeignDefense
```

[Strong neutral-planet ground assault](GO_NEUTRAL_GROUND_ASSAULT.md) is now
qualified separately. Next integrate
combat with routing, shared pursuit, scan suppression, group writes, casualties,
news and scores before claiming complete occupied-world Go maintenance. Existing
ordinary/convergence APIs, CLI profiles, modern gameplay, save 35, release
packages and native Windows/live BBS acceptance are unchanged.

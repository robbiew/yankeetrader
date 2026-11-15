# Bounded Go day-one convergence admission

`qbmaint.ReplayConvergenceDayOneHomes` admits the retained post-economy day-one
world with active Convergence Haven and three missing NPC homes. It takes the
modeled RNG state, three explicit creation DATE observations (all day 306), the
raw Xannoron creation TIMER and a chronological source-labelled helper prefix.
It returns the complete modeled world at the pre-tail boundary and receipts.

This is a separate explicit API. Existing Wanderer/Xannoron/Base birth and
existing-home continuation APIs retain their strict admission. The shared mobile
engine has separate missing-home and existing-home admission gates; the existing
API always chooses its original gate. Convergence Haven is never hidden, removed
or patched back to bypass a validator. Its complete post-economy record remains
unchanged through the birth/mobile phase.

The admitted day-one context requires default geometry, inactive humans, zero
taxes, no pending revenge, the named Xannor-owned Haven with a current economy
date and one slot-2 link, absent homes, a tracked 10,000-force HQ, no prior mines
and a normalized HQ-only group cache. Existing homes, other active planets,
non-HQ deployments and mismatched source calendars fail. Creation TIMER is zero
or within the bounded nonzero DOS range; unqualified zero final Xannoron ground
is rejected. Broader birth, combat and calendar profiles remain separate.

## Writers and state continuation

The recovered assignment lists preserve unassigned reserved-slot bytes and their
distinct raw zeros. Wanderer restoration and placement precede Xannoron creation;
its initial ground/bank draws precede the common ground increment. Creation uses
qualified SINGLE multiply/divide/add/INT primitives. Zero TIMER aliases preserve
the original raw exponent-zero residue, rather than inventing a canonical clock.

The same before-only physical cache normalization, sticky-preference routing,
helper caller checks, directed BFS, eager/interception draws and additive group
writeback used by the existing-home phase now run under the explicit day-one
gate. All 19 missing groups allocate from remaining HQ force. Base restoration
and its caller `437a` placement/retry loop run after mobile writeback. The helper
prefix must end there; tail clocks are not consumed. Model creation flags are
returned explicitly for later auxiliary output.

The phase calculates 26,670 draws, 60 helper reseeds and 19 mobile activities in
each of the three retained observed day-one runs. The results include 20 group
outcomes but only three physical positive-force sectors, preserving convergence
and later physical-sector desertion semantics. Existing-home days still perform
17/0 allocations and consume no creation clocks; their complete six phase-world
regressions remain unchanged.

## Existing evidence and tests

No new native acquisitions or changed observation hashes were needed. The
exporter authenticates the existing convergence/source packets and instruments
the recovered Python chain. Each phase input is its modeled post-economy world,
and its output is taken before the Mercenary tail. Source creation dates/TIMER
are extracted from the authenticated clock inventory. All three modeled days
exist before native after-files or cache probes are opened; no native child,
captured RNG endpoint or cache payload seeds or corrects synthesis.

The separate full Python audit retains **54 complete native six-file comparisons
/324 files, 501 RNG witnesses and 1,440 cache-field comparisons**. The three new
phase-world hashes and birth/helper/route receipts are **modeled intermediate
oracles**, not new native phase observations. Native outputs remain byte-exact.

Go tests compare all three complete phase worlds, creation flags, bank/timestamp,
ground, helper old/seeded states, caches, groups, routes and final RNG state. They
also compose actual Go port output into planet economy, this birth/mobile phase
and the evolved tail in all three cases, carrying each returned world/state to
the next phase without substituting a Python world. Auxiliary output and final
metadata are still separate, so this is not yet complete six-file Go chaining.

Tests preserve the Haven and unassigned home fields, enforce strict older APIs,
check immutable inputs and owned outputs, and reject malformed/late incomplete
recipes without partial publication. Synthetic tests cover raw zero TIMER
aliases and the unqualified zero-ground refusal boundary; they are not new native
runs. Exporter controls reject altered source dates/clocks, inputs, model seeds,
outputs, native files, RNG witnesses and cache probes while accepting portable
gzip recompression by complete decompressed bytes.

```sh
python3 scripts/export_convergence_day_one_fixture.py --check
python3 scripts/test_export_convergence_day_one_fixture.py
go test ./internal/qbmaint -run 'TestQualifiedConvergenceDayOne|TestGoConvergenceDayOne|TestConvergenceDayOne'
```

[Evolved auxiliary output and final metadata](GO_EVOLVED_AUXILIARY.md) are now
implemented separately. Next qualify complete Go three-day six-file chaining. Reuse existing captures and the [Python chain](EVOLVED_CHAIN_REPLAY.md).
Do not repeat completed port, planet, birth/mobile or tail recovery. Initial-only
research CLI v1, modern gameplay/save 35, general DOS interoperability and native
Windows/live BBS acceptance remain separate.

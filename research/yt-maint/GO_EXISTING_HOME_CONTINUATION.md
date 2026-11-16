# Bounded Go existing-home and mobile continuation

`qbmaint.ReplayExistingHomeContinuation` accepts a complete post-economy world,
a modeled 24-bit RNG state and a chronological helper TIMER prefix. Each helper
carries family 1/2, original caller address and all four raw TIMER bytes. The API
computes the required calls from the world; it does not select branches from an
observed call count, cache dump, expected endpoint or correction table.

The phase starts after ordinary planet economy on convergence days **307/308**
and stops before the Mercenary/desertion/lottery tail. Its admission requires all
four existing named planets, current economy dates and ownership, unique home
links, tracked HQ, inactive human players, zero port taxes, no pending revenge,
integer graph/pointers/mines and conserved 10,000-fighter Xannor physical force.
Missing homes, creation recipes, human/foreign force and encountered mines or
non-Xannor planetary combat are excluded. Existing initial-only and explicit
late-clock combat APIs remain strict and unchanged.

The existing-home paths preserve the evolved records. Wanderer unlinks its old
physical location before selecting a new empty location, retains its economy
bytes and applies only common ownership/bank aftermath. Its zero bank defaults
to 250,000. Existing Xannoron consumes no creation clocks or birth draws, but its
common ground-increment draw still runs; its zero bank defaults to 1,000,000.
Existing Base lookup consumes no creation clocks and writes no Base record.

Cache normalization reads only the before-world. A physical Xannor deployment
is consumed once, before duplicate pointers are combined and emptied entries
are cleared. Source-specific `00008000` cache-clear residues are retained.
Missing groups allocate through four nested helper-two draws from the remaining
HQ cache force. Existing groups keep their strengths and origins. The retained
profiles produce **17 allocations on day two and none on day three**.

Mobile continuation preserves column-order directed BFS, same-origin fallback
rejections, source-labelled helper reseeds, sticky preferred candidates,
conditional eager candidate scans, 50 draws per ordinary entered sector,
protected-sector activity retries, group-20 targeting/mine increment, additive
physical writeback and force conservation. Source-clock exhaustion, wrong
family/caller, unconsumed tail clocks, unsupported encounters or finite research
guards return no world or statistics. All calculation uses private world/RNG
state, so even late refusals cannot mutate caller data or publish partial state.

## Existing evidence and validation

No captures or native hashes changed. The exporter reuses the existing Python
three-day replay and authenticates its original convergence/source evidence.
It derives each phase's input after Python planet economy and its output at the
pre-Mercenary boundary. All initial inputs and subsequent day handoffs are
modeled; no native child world, captured RNG endpoint or cache probe feeds
synthesis. Intermediate phase worlds, helper seeds and route receipts are
**modeled results**, not additional native phase observations.

The Python chain separately validates **54 complete native six-file comparisons
/324 files, 501 RNG witnesses and 1,440 source cache fields**. Native targets and
cache probes open only after all three modeled days exist. The portable fixture
contains six modeled phase input worlds, raw helper prefixes, complete output
hashes, normalized caches, groups, routes, draw counts and calculated reseeds.
No native after-world is embedded as a phase input or used to repair a result.

Go tests match all **six complete phase worlds**, caches, 120 group outcomes,
114 route activities and every helper old/seeded state. Phase draw counts are
25,659/26,942; the common Xannoron ground increments are 4/3. They also feed the
existing Go planet API's actual output world and final state directly into this
API in all six cases, without substituting a Python world between the two phases.
This establishes two-phase composition, not a complete Go multi-day chain.

Tests cover Base preservation, raw/unwritten bytes, input/output independence,
conditional bank defaults, protected source chronology, skipped creation clocks,
missing homes, unsupported hazards and atomic late refusal. Exporter controls
reject altered phase inputs/outcomes, clocks, model reseeds, native files,
RNG witnesses and cache probes, enforce read boundaries and accept portable gzip
recompression by comparing complete decompressed bytes.

```sh
python3 scripts/export_evolved_continuation_fixture.py --check
python3 scripts/test_export_evolved_continuation_fixture.py
go test ./internal/qbmaint -run 'TestExistingHome|TestGoPlanetEconomyFeeds'
```

The [evolved Mercenary/desertion and lottery tail](GO_EVOLVED_TAIL_REPLAY.md)
now has its own bounded Go API and composes directly with this phase. Next are
evolved auxiliary/final metadata and complete Go chaining. The explicit
[day-one convergence API](GO_CONVERGENCE_DAY_ONE.md) now shares this mobile engine
under a separate missing-home gate; this existing-home API remains strict.
Reuse the [existing Python chain](EVOLVED_CHAIN_REPLAY.md); its recovery is already
done. The research CLI's initial-only v1 recipes, modern gameplay and save 35 are
unchanged. This does not establish arbitrary worlds, general DOS loading,
selected combat, native Windows durability or live BBS acceptance.

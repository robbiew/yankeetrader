# Research-only bounded initial maintenance API

`qbmaint.ReplayInitialMaintenance(before, recipe)` is the exported programmatic
entry point for the already qualified ordinary initial profile. It returns six
file byte slices and `InitialStats`. It performs no filesystem I/O and reads no
host clock, native target, executable, correction table or modern gameplay save.

`before` must contain exactly YTDATA.DAT, YTNAME.DAT and YTNEWS.DAT. The caller
supplies and authenticates `InitialRecipe`:

- `Ports`: the existing 1000-item source day/TIMER-minute schedule and cap mode.
- `WandererDay`, `XannoronDay`, `BaseDay`, `FinalDay`: separately sampled source
  phase days, bounded by the qualified components.
- `InitialState`: the source-qualified 24-bit startup RNG state.
- `HelperOne`: exactly 41 or 42 raw helper-one TIMER samples in source order.
- `HelperTwo`: exactly 19 raw helper-two TIMER samples.
- `XannoronTimer`: the raw creation TIMER sample, not a saved minute field.
- `Aux`: independent sampled news/score dates and exact native clocks.

The recipe is not a modern initializer/save recipe. Calendar and source
provenance are not inferred from an after-file or host date. No broad promise is
made for arbitrary combinations of otherwise individually valid inputs.

The entry point invokes Go clean ports, Wanderer birth, Xannoron creation,
ordinary initial mobile groups, Mercenary Base birth, no-hiring NPC tail,
inactive ranks and bootstrap auxiliary writers. RNG states are passed directly
between components. The optional 42nd helper belongs solely to the selected
inactive lottery branch; mismatched helper inventory fails. Stats retain each
phase's results, total draws and final modeled state.

All before files and recipe slices are readonly. Each component retains its
existing bounds; any failure returns nil files and zero aggregate statistics,
including a late invalid auxiliary clock after world synthesis. Successful
outputs own their storage. This transactional return contract does not write,
import or publish a save, and does not replace modern maintenance behavior.

## Existing native validation

Tests assemble recipes from the existing independently authenticated portable
clock/input fixtures, not from native after files. The API's complete six-file
output matches every native byte through per-file SHA256 oracles in all 29
ordinary initial runs. No new observations, captures, fingerprints or native
endpoint measurements were needed. Final RNG expectations remain independent
Python-model results, distinct from native file oracles.

Tests cover all six files, statistics/phase handoff, input and output isolation,
missing/extra files, helper inventories and early/late phase admission failures.
The existing CI race/vet jobs and portable fixture provenance checks cover the
entry point without duplicating native artifacts or adding another exporter.

The three late-clock Wanderer-combat prefixes remain excluded. Active players,
existing NPC worlds, arbitrary production, hiring/desertion, general lottery,
message compression, DOS save loading, a public CLI and playable integration
remain outside this API. Modern save format 35 is unchanged. Next audit is the
existing late-clock combat recovery/captures before expanding Go admission.

```
go test -race ./internal/qbmaint ./internal/qbrng ./internal/qbmbf ./internal/qbinit
go vet ./internal/qbmaint ./internal/qbrng ./internal/qbmbf ./internal/qbinit
```

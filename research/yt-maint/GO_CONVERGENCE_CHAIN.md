# Bounded Go three-day convergence chain

`ReplayConvergenceChain` composes the existing qualified Go phase APIs across
November 2–4, 2026 (source days 306–308). Only the exact three measured original
before files are accepted, with their existing Python chain hashes checked at
entry. It returns three complete owned six-file results and calculated phase
receipts, or nil on any error, including failures on day two or three.

Each day runs evolved ports, planet economy, day-one creation or existing-home
cache/mobile continuation, Mercenary/lottery tail, then auxiliary output and final
metadata. The next day receives only the preceding Go result. No caller-supplied
child world or phase correction can enter this API. Journal rotation therefore
uses the previous Go-generated news; names remain unchanged across the chain.

Recipes contain one explicit startup RNG state per DOS run, port and planet
clocks, source-labelled home/tail helper clocks, optional first-day creation
clocks and separate report dates/clocks. State continues from planet economy
through home/mobile and tail. Each new DOS process starts from its own
source-derived seed, rather than the previous process's final state. The chain
enforces consecutive days and cross-phase calendar identity; each existing phase
retains its detailed admission and exact clock-consumption checks. Creation
clocks appear only on day one; creation news flags come from calculated outcomes.

Tests reuse the existing qualified fixtures directly. Only original day-one
before files are decompressed as synthesis inputs; later before worlds, expected
phase worlds and observed endpoints are never passed to the chain. Three source
clock sequences produce nine complete six-file results matching retained
native-qualified hashes. Within-day RNG handoffs and calculated final states are
checked separately from file hashes. Tests also verify owned per-day outputs,
immutable original files/recipes, exact previous-news rotation, and atomic refusal
for malformed initial files, missing/reordered days, mixed calendars, invalid
creation contexts and exhausted or malformed late helper/report clocks.

No exporter or capture is duplicated. Existing fixture exporters authenticate
their source fingerprints and the independent Python chain, which computes all
three children before opening native targets or cache probes. The auxiliary
exporter separately verifies 54 complete six-file comparisons (324 files), 501
RNG witnesses and 1,440 cache fields. Its corruption controls remain in CI.
Intermediate phase/state receipts remain modeled; this milestone adds Go
composition, not new native observations or broader admission.

```sh
go test ./internal/qbmaint -run TestConvergenceChain
python3 scripts/export_evolved_aux_fixture.py --check
python3 scripts/test_export_evolved_aux_fixture.py
```

CI's existing race-enabled package tests run the new chain tests, and existing
fixture checks retain provenance qualification. Next add an explicit research
recipe/CLI adapter for the bounded chain. Current CLI v1 remains initial-only;
modern gameplay/save 35, general production maintenance, DOS save interoperability
and native Windows/live BBS acceptance are unchanged.

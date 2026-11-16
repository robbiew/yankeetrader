# Bounded Go evolved auxiliary output and final metadata

`ReplayEvolvedAux` takes original/model-derived before files, an independently
modeled pre-final world, explicit final day, source-ordered creation flags and
separate news/score text dates and clocks. It returns owned copies of all six
files or an error without partial publication. It performs no filesystem or
host-clock reads and accepts no target outputs.

Admission is limited to the retained convergence days 306–308, default geometry,
inactive human accounts, zero port taxes, empty private messages, conserved
10,000 physical Xannor defenses, the three named NPC homes and Convergence Haven.
Creation requires all three homes on day one and the original three-file input;
later days require existing homes and six before files. Additional active planets,
broken references, modified human records, stale metadata and unsupported paths
are refused. This is a bounded research API, not general maintenance.

The existing inactive-rank writer sets the final watermark and fifty ranks.
The shared initial/evolved report formatter preserves DOS CRLF and final EOF,
separate text clocks (including `24:00:00`), comma formatting and fixed widths.
Creation news appears only when homes were created. Names copy unchanged, current
news rotates byte-for-byte to yesterday's news, and private messages remain empty.
The scoreboard counts physical defenses rather than duplicated group caches.
The older strict initial API retains its original admission and regressions.

`export_evolved_aux_fixture.py` reuses the existing Python chain and captures.
It captures modeled pre-final worlds before rank finalization and original/model
before files; no native child before file, after-file, RNG witness or cache probe
enters synthesis. All three modeled days precede native comparisons. The separate
audit checks 54 complete six-file comparisons (324 native files), 501 RNG witnesses
and 1,440 cache fields. Frozen native hashes and bytes are unchanged; no captures
were added. Nine fixture cases store complete inputs and six calculated output
hashes with source fingerprints and portable compressed blobs.

Go tests match all nine six-file results and compose actual Go port, planet,
home/mobile and tail results into this API for each day. These tests begin each
day from independently modeled before inputs: they do not yet qualify chaining
the previous day's complete Go result into the next day. Tests cover independent
clocks, raw binary journal rotation, owned outputs, exact metadata write bounds,
creation flags and atomic refusals. Exporter controls reject altered inputs,
outputs, source fingerprints, native files, RNG witnesses and cache probes while
allowing equivalent gzip recompression.

```sh
python3 scripts/export_evolved_aux_fixture.py --check
python3 scripts/test_export_evolved_aux_fixture.py
go test ./internal/qbmaint -run 'TestEvolvedAux'
```

[Complete Go three-day six-file chaining](GO_CONVERGENCE_CHAIN.md) now qualifies
actual cross-day handoffs separately using these existing phases.
Research CLI v1 profiles, playable gameplay, save 35, general DOS interoperability
and native Windows/live BBS acceptance remain separate.

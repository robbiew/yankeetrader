# Bounded Go evolved-port economy

`qbmaint.ReplayEvolvedPorts` migrates the existing Python port writer for the
retained convergence chain: initial day 306, then full-stock days 307 and 308.
The API takes the complete before-world and 1,000 raw source TIMER minutes and
calendar days. It returns only the 137,000-byte port block and draw-free stats.
It does not open an oracle, consume RNG, write files or update other records.

The product of rate and elapsed time uses the qualified raw SINGLE primitives.
Cargo addition retains its wider value until each record assignment; a rational
sum preserves low bits before nearest-even SINGLE stock/rate conversion within
this finite bounded profile. Maximum selection compares that wider cargo value
against the source's stored SINGLE maximum. A synthetic rounding regression
checks why equal wider cargo values can select the last commodity when the
stored maximum rounds down. This is a model boundary test, not a native capture.

The admission gate requires default geometry, a complete nondecreasing midnight
clock schedule, zero treasury/asking price, original bounded coefficients and
rates, and either clean initial stocks or consecutive-day full stocks. Other
elapsed intervals, prices, economies and selected-plague branches are excluded.
Errors return no partial block or statistics. Existing initial-only APIs stay
strict; the research CLI's v1 profiles are unchanged.

## Existing evidence and tests

No native captures were added. `export_evolved_port_fixture.py` authenticates the
existing convergence and evolved native evidence, then synthesizes all three days
of each observed chain before opening any native after-world oracle. Its next
before-world receives only its own modeled port block. All nine predictions
match each stage's six native modes: **54 complete native port-block comparisons**.
The portable fixture stores one initial world, nine source clock schedules and
complete block hashes; it does not embed native child worlds as replay inputs.
Compressed fixture containers are compared by decompressed bytes.

Go tests independently carry their own modeled blocks through the three observer
chains and compare all nine complete port-block hashes (9,000 records), elapsed
bounds, classes, promotions and zero draws. Promotions are 0/3,000/3,000 per chain.
Tests also check unwritten bytes, input immutability, output independence,
unsupported-profile refusals and source maximum rounding. Exporter regressions
reject altered schedules, oracles, source inventory and before bytes while
accepting portable recompression. CI checks the exporter against authenticated
native evidence and runs the Go tests.

```sh
python3 scripts/export_evolved_port_fixture.py --check
python3 scripts/test_export_evolved_port_fixture.py
go test ./internal/qbmaint -run TestEvolved
```

This establishes port-only Go handoff. The existing
[Python evolved-chain replay](EVOLVED_CHAIN_REPLAY.md) already covers complete
three-day files, NPCs, economy and auxiliary output. Full Go evolved maintenance,
evolved NPCs, general DOS loading and playable integration remain separate;
modern saves and gameplay are unchanged. The [bounded Go evolved-planet phase](GO_EVOLVED_PLANET_REPLAY.md) now has its
own qualified API, as does [existing-home continuation](GO_EXISTING_HOME_CONTINUATION.md).
The [evolved tail](GO_EVOLVED_TAIL_REPLAY.md) is now migrated too; next audit
evolved auxiliary/final metadata output before adding controls. Explicit
[day-one convergence admission](GO_CONVERGENCE_DAY_ONE.md) is now migrated.

# Bounded pure Go clean-port maintenance replay

`internal/qbmaint.ReplayCleanPorts` now synthesizes the complete 137000-byte
non-Earth port block from a before-world and explicit calendar/raw TIMER inputs.
It accepts no after-world, correction table, modern save or gameplay policy.
The independent Python `replay_maintenance_ports.py` remains unchanged.

## Reused native evidence

No new DOS acquisition was needed. The four existing fresh-calendar profiles
supply eight observed runs; the eight saved-base-year clock-matrix profiles
supply twenty-four observed runs. All 32 port blocks / 32,000 complete 137-byte
records match both the existing Python synthesis and the new Go implementation.
This includes next-day, New Year, leap-day, noon, capped elapsed days and the
matrix's independently observed midnight date/TIMER boundary. Date and TIMER
are separate observations; the replay does not synchronize them artificially.

The fixture exporter first authenticates the original calendar/clock manifests,
frozen acquisition sources, raw observations and observation neutrality through
their existing verifiers. It extracts schedule inputs from the source-qualified
host observations. Python synthesis receives before bytes and schedules only;
after-world port blocks are loaded separately as validation oracles. Every
native port byte is compared without masking. The portable fixture deduplicates
before-worlds by SHA256 and retains complete compressed native output blocks,
raw timers, per-port days, class counts and source/manifest fingerprints.
Compressed fixture containers are derived portable data; checks compare complete
uncompressed bytes rather than requiring platform-specific zlib headers. Original
capture bytes, manifests and source attribution remain unchanged.

## Admitted behavior

- Default 4151-record geometry; the returned block starts at zero-based world
  byte `3051*137` and contains 1000 records. Earth and all other phases are excluded.
- Strict mode uses one Gregorian day (1..366), exactly ten elapsed days and
  monotonically nondecreasing raw timer values.
- Capped mode uses per-port base-year days (1..732), nondecreasing dates spanning
  at most one day and at least ten elapsed days. One timer rollback is admitted
  only from above 1439 minutes to below one minute.
- Clean stock/event/timestamp fields must be numeric zero, including raw aliases.
  Rates are integral 1000..32766; nonzero coefficients have integral magnitudes
  1..100. Old day values must be integral within the initial-profile bound -9..722.
- Stock is exactly rate times ten. Only strict greater-than changes the maximum;
  the first equal maximum wins. Class and coefficient signs follow that choice.
- The exact raw timer bytes are copied to the timestamp field. Unwritten record
  bytes are preserved, including noncanonical zero residues. Bounded integer
  decoding/encoding uses bits; timer order/range checks reuse qualified raw
  comparison/sign-zero primitives. No host floating-point conversion is used.

Invalid inputs return an error, nil block and zero statistics. All input slices
remain unchanged on success and failure; output storage is independent. These
are value/order guards, not authentication of caller-provided clock observations.
The caller remains responsible for source qualification.

## Verification and exclusions

Go tests compare all native bytes and statistics, assert input/output isolation,
reject unsupported geometry/counts/dates/timers/rates/stocks/coefficients, check
multiple rollbacks and verify tie/residue/narrow-write behavior. Eight exporter
regression tests reject altered before inputs, clocks, calendars, native oracles,
source identities and dropped/duplicated controls, and enforce separate synthesis
and target loading. Existing whole-world replay and initializer checks remain
required independently; this milestone claims port-block equality only.

```
python3 scripts/export_clean_port_fixture.py --check
python3 scripts/test_export_clean_port_fixture.py
go test -race ./internal/qbmaint ./internal/qbmbf ./internal/qbinit
```

Populated-port economies, fractional rates, arbitrary elapsed production, events,
other NPC/planet/player phases, full Go maintenance, production integration, DOS
save interoperability and native Windows/live-BBS acceptance remain separate.
Gameplay, save format 35, initializer fingerprints and sysop procedures are
unchanged. Audit the next recovered maintenance phase and its existing replays
before selecting another Go migration; do not repeat these clean-port controls.

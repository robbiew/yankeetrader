# Sector mine placement and recovery research — 2026-10-28

This report records eight controlled DOS mine-placement sessions plus four
home-sector boundary sessions. The immutable original `YT.EXE` SHA-256 is
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
The tests used copied fixtures, a copied `KEYFEED.COM`, explicit `KEYS.TXT`
inputs, and full before/after `YTDATA.DAT` snapshots. The archive itself was not
mounted or modified. Run `python3 scripts/recover_mine_placement.py <new-dir>`
to reproduce the suite; `python3 scripts/verify_mine_placement.py` validates the
committed snapshots and transcripts.

## DOS observations

| Case | Saved result |
|---|---|
| `D;5` with 10 carried mines in sector 100 | Player stock 10 → 5; sector stock 0 → 5; turns remain 500. The game reports “Sector 100 is now mined!” |
| Blank amount or `D;0` | Default is zero; no stock or sector change. |
| `D;11` with 10 carried mines | No drop; stock and sector remain unchanged. |
| `D;-1` | No drop; stock and sector remain unchanged. |
| `D;5` with 3 existing sector mines | Player stock 10 → 5; sector stock 3 → 5. DOS replaces the aggregate field count with the entered amount; it does not add the amount. |
| `D;5` with no carried mines | Reports “You don't HAVE any!”; state remains unchanged. |
| `D;5` from sectors 1, 2, or 7 | Refused with “The Union doesnt like the home 7 sectors mined!”; stock, field and turns remain unchanged. |
| `D;5` from sector 8 | Accepted; stock 10 → 5, sector stock 0 → 5, turns remain 500. |

These runs establish the command's stock validation, zero default, lack of turn
cost, overwrite behavior for an existing field, and the home-sector boundary.
They do not establish every invalid numeric input or every account/planet
combination. `D` is the only sector-field operation named in the recovered
instruction manual. It describes dropping mines but no field pickup/withdrawal;
an equivalent DOS recovery operation was not found or tested. Taking carried
mines from a planet is separately documented under planetary transfers.

## Implementation boundary

The modern world represents mine sources and preserves source attribution,
whereas DOS stores one aggregate count. Its additive same-owner mine-layer
representation therefore deliberately differs from DOS's overwrite result for
`D` on an already mined sector. Keep that policy explicit and covered by tests.
The recovered home-sector protection should include every source of field
creation, including voluntary placement, wrecks and combat aftermath. Placement
also needs fresh confirmation, unchanged-state revalidation and atomic stock
transfer. Sector-field withdrawal remains a separate design question because
the DOS recovery path is not established; do not present a new recovery command
as recovered behavior.

## Evidence

- Standard probes: [`mine-placement-dos/results.json`](mine-placement-dos/results.json)
- Home-sector boundary probes: [`mine-placement-home-boundaries/results.json`](mine-placement-home-boundaries/results.json)
- Raw compressed save pairs, transcripts, input streams and emulator logs are
  retained per scenario below those directories.
- `scripts/verify_mine_placement.py` checks the expected field and stock deltas,
  turn invariance, transcript markers, and snapshot hashes.

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
| `D;5` with 3 existing sector mines | All three initial mines explode before `D;5`. Player stock then changes 10 → 5 and the empty sector gains five mines. This does not distinguish addition from replacement of a still-nonempty field. |
| `D;5` with no carried mines | Reports “You don't HAVE any!”; state remains unchanged. |
| `D;5` from sectors 1, 2, or 7 | Refused with “The Union doesnt like the home 7 sectors mined!”; stock, field and turns remain unchanged. |
| `D;5` from sector 8 | Accepted; stock 10 → 5, sector stock 0 → 5, turns remain 500. |

These runs establish the command's stock validation, zero default, lack of turn
cost and the home-sector boundary. Placement onto a still-nonempty field is
unverified: the existing-field probe exhausts its starting field before the
drop prompt.
They do not establish every invalid numeric input or every account/planet
combination. `D` is the only sector-field operation named in the recovered
instruction manual. It describes dropping mines but no field pickup/withdrawal;
an equivalent DOS recovery operation was not found or tested. Taking carried
mines from a planet is separately documented under planetary transfers.

## Implementation boundary

The modern world represents mine sources and preserves source attribution,
whereas DOS stores one aggregate count. Its additive same-owner mine-layer
representation is an explicit modern policy. DOS placement onto a still-nonempty
field has not been established by these probes; no additive/replacement
divergence is claimed. The placement command requires fresh
confirmation, unchanged-state revalidation and atomic stock transfer. Sectors
1–7 are protected for voluntary placement; other mine sources retain their
existing behavior until separately researched. Sector-field withdrawal remains
a separate design question because the DOS recovery path is not established; do
not present a new recovery command as recovered behavior.

`D`/`DROP [quantity]` is implemented. It merges a new amount into the caller's
attributed layer, spends no turn, protects sectors 1–7, and requires a fresh
confirmation after pending input is discarded. The committed research precedes
this gameplay change in the local branch history.

Version 10 adds persistent departure grace for living occupants who had no
unresolved mine encounter before a voluntary drop. This is an explicit modern
entry/aftermath policy: deploying does not immediately detonate the new field
against ships already there, including after reconnect. Movement, emergency
escape and death clear the grace. New wreck mines revoke it and retain their
existing immediate aftermath behavior; reentry, including by the original owner,
triggers normal mine resolution. Version-nine saves upgrade with no grace, so
pre-existing pending encounters are not waived. The isolated placement probes
above do not establish all multi-occupant/aftermath boundaries in DOS.

Game, store and door regressions cover preserved fields, other entrants, owner
reentry, wreck hazards, rollback, concurrent placement, legacy upgrade and death.
The real terminal `smoke_mines.py` includes deployment, reconnect, departure and
reentry. The original embedded DOS manual remains byte-for-byte preserved;
current Go rules are documented in the README and this report.

## Evidence

- Standard probes: [`mine-placement-dos/results.json`](mine-placement-dos/results.json)
- Home-sector boundary probes: [`mine-placement-home-boundaries/results.json`](mine-placement-home-boundaries/results.json)
- Raw compressed save pairs, transcripts, input streams and emulator logs are
  retained per scenario below those directories.
- `scripts/verify_mine_placement.py` checks the expected field and stock deltas,
  turn invariance, transcript markers, and snapshot hashes.

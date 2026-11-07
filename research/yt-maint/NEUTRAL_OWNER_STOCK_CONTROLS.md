# Neutral physical owner and mine-stock controls

The [predeclared six-fixture plan](NEXT_OWNER_STOCK_CONTROLS.md) is now captured
as 36 original-DOS runs, six modes per fixture, with 216 complete output files.
All six modes agree byte-for-byte within every case. This acquisition extends
PRs #109/#110 without changing their captures or widening historical replay.

Each case starts from its own mode's pinned November 4 evolved-combat world,
applies fifteen declared edits and runs one full November 5 maintenance day.
Five side-file inputs are unchanged (180 unchanged links); 36 YTDATA links are
independently explained by the exact edit ledger. Sector 2368 has the same forced
first hop to 3000, with Gateway Cache in slot 3, ground 500000, neutral governor,
zero bank/rates, incoming 97337, and the declared local force/owner/stock/mines.
Two unobserved, three observed and one attach-only execution are retained.

## Measured outcomes

| Case | Neutral fighters transferred | Incoming mine loss | Taking actor | Stock added | Final Mercenary physical inventory |
| --- | ---: | ---: | ---: | ---: | --- |
| neutral-one-empty | 1 | 0 | silent | 0 | 97338 at 3000 |
| neutral-whole | 37 | 0 | 97374 | 37 | 97411 at 3000 |
| neutral-half | 37 | 0 | silent | 0 | 97374 at 3000 |
| neutral-mine-whole | 37 | 381 | 96993 | 37 | 97030 at 3000 |
| friendly-mine-second-two | 0 | 159 | 97215 | 37 | 97252 at 3000 |
| friendly-mine-second-four | 0 | 4374 | 92963 | 37 | 93000 at 3000 plus 37 at 356 |

Positive physical neutral fighters join the arriving Mercenaries once; their
neutral inventory falls by the same amount. This is an actual faction transfer,
not a no-transfer conservation assumption. Positive entering force suppresses
capture text. The incoming force alone takes mine damage, then entering force
joins it, then whole stock adds. Taking text stamps the combined pre-stock force.

The four-second friendly group departs 3000 before the incoming force reaches
the mine, and later activates again at 13. It ends at 356, separately from the
arriving group. The surviving incoming 92963 emits capture text and then takes
37 stock. Earlier Xannor activity also differs: seventeen fatal Wanderer assaults
lose 3673 Xannor, leaving 1293. The verifier retains those complete receipts and
actual physical totals; it does not force the mine-free path's earlier outcomes
or local endpoint onto this fixture.

All three one-mine cases spend their mine and retain one authenticated original
helper2/4aa4 callback. Full event frames bind old state, TIMER and source identity;
this acquisition does not claim a before-only derivation of those loss values.
Whole, half and empty stock clear with original source8472 raw `00008000`.
The incoming origin retains source859e raw `00002800` force/owner zeros.
Planet title/link, governor and bank remain intact; ground/rates follow the
independently checked source economy. News/console order and scores bind the
actual resulting faction inventories.

## Provenance, failure disclosure and validation

The primary recipe and actual executed sources were frozen before native launch.
An initial preflight failed on an inherited fixture assertion that still expected
owner -2 and zero mines. It failed in fixture construction, before any DOS process
started. Its original frozen sources, recipe and traceback are retained under
`preflight/`. The assertion was corrected to check the declared owner/mines;
a fresh destination froze the corrected writer before all 36 native runs.
No native observation was retried, altered or rehashed to redefine an outcome.

The independent verifier imports neither acquisition writer nor replay model.
It pins the complete corpus and sources, independently reconstructs all fixture
bytes, checks exact launches/CPU/date/time, original guests, raw outputs and DOS
return, bounded owned-process controller, loaded observer and flush receipts,
source clocks/helper counts, stock clears, public events, faction transfers,
physical sector distribution and all six-mode output equality.

Twenty new tests cover missing inventory, immutable manifests, rehashed command,
clock, host-log, observer, error and owner-input substitutions; duplicated/ignored
neutral force, wrong mine/receipt actor, capture gate, receipt order, source clear
and missing later activation. The existing native byte audit is reused without
a new native read or changed original packet. CI runs:

```sh
python3 scripts/verify_maintenance_neutral_owner_stock.py
python3 scripts/test_verify_maintenance_neutral_owner_stock.py
```

Next: a separate before-only integration must derive the modeled parent, edits,
owner transfer, mine helper inputs, earlier Xannor actions, repeated local moves
and all six writers before opening any target. Existing replay admission remains
strict. General MBF, arbitrary owners/hazards, active-player maintenance,
production DOS maintenance and live BBS acceptance are not established. Production
Go, dependencies, generation fingerprints and save format 35 are unchanged.

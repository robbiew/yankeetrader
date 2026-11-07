# Departed garrison and planet stock: bounded original-DOS controls

This acquisition milestone extends the held-garrison controls in PR #107;
PR #108 independently covers held-garrison replay. It does not implement a
before-only departure replay or change production gameplay/save format 35.

The primary predeclared matrix has six fixtures and six observation modes each.
A separate, subsequently declared supplement has two fixtures and the same six
modes. Every first-attempt outcome is retained, including held counter-controls.
There are 48 completed original-DOS runs and 288 complete six-file outputs.
All six modes agree byte-for-byte within each fixture. No observation was
modified or retried to select an outcome.

| Clock/stock/governor | Local 37 | Later local departure origins | Final local sector | Taking actor/amount |
| --- | --- | --- | --- | --- |
| 2s / 37 / neutral | holds | none | merged at 3000 | 97374 / 37 |
| 4s / 37 / neutral | leaves 3000 | 13 | 1810 | 97337 / 37 |
| 6s / 37 / neutral | holds | none | merged at 3000 | 97374 / 37 |
| 8s / 37 / neutral | leaves 3000 | 2082, 1622 | 2862 | 97337 / 37 |
| 2s / half / neutral | holds | none | merged at 3000 | silent |
| 4s / 37 / Mercenary | leaves 3000 | 13 | 1810 | 97337 / 37 |
| 4s / empty / neutral (supplement) | leaves 3000 | 13 | 1810 | silent |
| 4s / half / neutral (supplement) | leaves 3000 | 13 | 1810 | silent |

The incoming 97337 force moves from sector 2368 to 3000. Departed controls
emit capture text for that force even with a Mercenary planetary governor;
governor bytes remain unchanged. Stock clears with original raw `00008000`,
including empty/subunit values. Positive taking text excludes the departed 37.
The arriving group ends with 97374 on whole-stock departure controls; the
separate 37 survives. Held controls instead end with 97411 at 3000. These are
measured contexts, not a general claim about arbitrary clock values or combat.

Each fixture applies the same fifteen declared data edits to its own mode's
pinned evolved-world parent. The five side files are unchanged. Six modes cover
two unobserved, three observed and one attach-only execution. Original guest
binaries, fixed CPU, raw DOS commands/date/time, natural exits, loaded observer,
paired runtime frames and persisted flush receipts remain independently checked.
The existing source audit explains descending scan and capture/pickup gates;
these captures newly establish the departure/tail outcomes.

Both corpus roots contain a recipe frozen before their first run, exact executed
sources and an immutable manifest. The independent verifier imports neither
acquisition writer nor replay model. It verifies fixture lineage, raw outputs,
observer provenance, complete inventories, receipts, physical sector distribution
and six-mode equality. Source callbacks authenticate clocks; the reused historical
`pickup` selector supplies only the identical November 5 calendar context.

Run:

```sh
python3 scripts/verify_maintenance_departed_stock.py
python3 scripts/test_verify_maintenance_departed_stock.py
```

Next is before-only derivation of these routes and repeated activations, with
independent corruption controls. No target-derived decisions or generalized
maintenance compatibility are admitted by this acquisition milestone.

# Active-planet placement and foreign-route controls

Ten declared fixtures now retain **60 complete original-DOS maintenance runs**:
two unobserved, one attach-only and three host-clock-observed runs per fixture.
All six output files agree across the six modes for each fixture: **360 retained
output files**, with no masks or repaired timestamps. These are new controlled
observations, not complete before-only record synthesis for populated worlds.

This extends [the completed twelve-fixture replay](COLLISION_RECORD_REPLAY.md).
It changes no Go gameplay, dependencies, `qb36-v1` fingerprint or save **35**.
Bounded planetary and sector combat already exist in the modern engine; the
remaining task concerns exact original maintenance streams and output bytes.

## Inputs and questions

The same immutable 4151-record baseline supplies three before files. New planets
occupy ordinary slots 2/3, with padded names, matching positive sector links,
active name lengths, owner -1 or 0, ground 500000, each cargo rate 1000, prior-day
stamp 305 and zero remaining numeric fields. Reserved Wanderer, Base and Xannoron
slots are not substituted. There are no named players, new mines or port taxes.
Foreign/neutral forces use actual sector 854, on the established HQ departure
route, with distinct force and owner fields. The runner reconstructs every input;
the independent verifier declares the recipes separately and compares full hashes.

| Fixture | Changed before context | Observed Wanderer / Base sectors |
|---|---|---:|
| `wanderer-occupied` | Named Xannor planet at old candidate 1095 | 2787 / 20 |
| `wanderer-two-occupied` | Named Xannor planets at old candidates 1095, 1792 | 836 / 2537 |
| `base-occupied` | Named Xannor planet at old candidate 2598 | 2787 / 20 |
| `route-planet-friendly` | Xannor planet at 854 | 2787 / 20 |
| `route-planet-neutral` | Neutral planet at 854 | 2787 / 1630 |
| `route-mercenary-37` | 37 Mercenary fighters at 854 | 1095 / 1987 |
| `route-mercenary-100000` | 100000 Mercenary fighters at 854 | 1095 / 1434 |
| `route-neutral-37` | 37 owner-zero fighters at 854 | 1095 / 2598 |
| `wanderer-active-rejection` | Named Xannor planet at actual candidate 2787 | 1310 / 2689 |
| `base-active-rejection` | Named Xannor planet at actual candidate 20 | 2787 / 2308 |

The first three names identify **reference-site controls**, not successful
collisions with those old candidates. The two explicit rejection fixtures were
declared separately after that distinction became observable. No observation is
silently relabeled as a before-only prediction.

## Active economy precedes placement

A live planet changes the stream even if no group attacks it. Starting from the
observed startup state `00c805`, three ordinary LCG advances reach `d61ece`; six
reach `48839b`. These equal the first placement-helper entry witnesses for one
and two active planets respectively. The new native source window includes the
three event-selection RND instructions at main offsets `16a9`, `16bb`, `16e5`.
The bounded recurrence and source order agree; this is not a newly captured
literal-site execution-count trace or a complete active-economy replay.

Consequently, adding an active planet at old candidate 1095 does **not** make
Wanderer reject 1095. Its first candidate is now 2787. The new active-rejection
fixture actually rejects 2787 and accepts 1310. Base's corresponding occupied
20 is rejected in favor of 2308. The independent placement audit uses authentic
source-labelled TIMER and raw helper-state witnesses, checks retry progression,
and verifies the saved link and optimistic per-attempt console receipts. It does
not supply those witnesses to the historical synthesis models.

The actual daily writer advances the planet timestamp to 306. Rates become
1010 and ground becomes 505000 before route combat. Friendly planets retain that
ground. The neutral route planet ends at **504975**, spending 25 ground units
across the subsequent attacks. Owner and name/link survive. Inactive-slot fake
links from earlier research could not establish any of these economy effects.

## Route outcomes and accurate interpretation of receipts

| Context | Saved Xannor | Saved Mercenary | Saved neutral | Verified public losses |
|---|---:|---:|---:|---|
| Friendly active planet | 10000 | 0 | 0 | None |
| Neutral active planet | 4022 | 0 | 0 | 5978 Xannor in 19 attack/death pairs |
| 37 Mercenary fighters | 9963 | 0 | 0 | 37 Xannor and 37 Mercenaries |
| 100000 Mercenary fighters | 5148 | 97525 | 0 | 4852 Xannor and 2475 Mercenaries |
| 37 owner-zero fighters | 10000 | 0 | 37 | None |

The neutral planet kills each attacking mobile group in this sample while
retaining positive ground; friendly ownership bypasses the attack. Owner-zero
sector force is skipped and remains 37. Those selected observations corroborate
the [already recovered per-hop ordering and defense rules](../yt-xannor-mobile/RECOVERY.md#directed-routing-and-per-hop-actions);
they do not recover arbitrary planet production, mines or ship battles anew.

The original foreign-force summary is misleading. In the 100000-force control,
its nineteen `Mercenaries: lost N, dstrd M` lines sum to **4852 in the `lost`
column and 2475 in `dstrd`**. Actual before/after ownership proves these are
Xannor and Mercenary losses respectively, opposite to an intuitive reading of
the text. The 37-force control also emits one `(Xannor ftrs dstrd)` line and one
`(Plyr ftrs dstrd)` line despite having no active human player. The verifier keeps
the literal labels and reconciles actual saved forces instead of inventing a
human casualty or correcting original news. Modern receipts are not changed.

The surviving large Mercenary force subsequently leaves sector 854 during its
own phase. Its total 97525 is counted across physical sectors, not assumed to
remain at the battle origin. Both NPC scoreboard columns equal saved faction
force times 100. All private `YTRMSG.DAT` outputs remain empty; console movement
does not become invented private or public mail.

## Acquisition and native evidence

[The frozen corpus](occupied-route-controls/) includes raw clock/emulator logs,
complete outputs, lifecycle controllers, exact loaded observer scripts, recipe,
seven acquisition source files and immutable pins. It contains **1290 files**.
Manifest SHA-256:
`7c01a0ef401f3df96f413e4aefd046c7f8a57499a1dfa537c83ea950d0dc7a3a`.
Original guests are copied into new disposable mounts and remain unchanged:
YTMAINT `8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6`,
BRUN30 `3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8`.
The installed DOSBox/Frida identities, fixed 200000 cycles, actual date/time,
entry/leave frames and natural status-0 return are independently authenticated.

One complete REA/Ghidra 12.1.4 original-byte read covers `0x11660`, length 720,
through `0x11930` exclusive. Evidence:
`ev_f1fd0d7769669ef1ccc19c210d5300d23dfc87acf511609ab037f4761808e6ae`.
The verifier compares every relocated byte and the three RND sites. Static bytes
are code evidence, not a runtime trace. The REA CLI used an existing JDK via
per-process environment after detecting stale MCP JAVA_HOME; no installation or
configuration was changed, and its private analysis session closed on completion.

The earlier forward-dated pilot inputs (315) invoked ten-day rollback catch-up;
they remain external diagnostics and are **not** these accepted prior-day controls.
A later observed run had natural status 0 but lacked the required Frida flush
notification. That partial case remains external and rejected. A fresh complete
six-mode set was separately acquired; no controller requirement was relaxed and
no automatic retry was added. Accepted captures come from completed case sets in
`/private/tmp/yt-occupied-final`, `/private/tmp/yt-occupied-final-followup` and
`/private/tmp/yt-occupied-rejections-final`; immutable launch metadata records the
actual mounts. Rejected artifacts are not counted among the 60 accepted runs.

## Reproduction and remaining work

```sh
python3 scripts/verify_maintenance_occupied.py
python3 scripts/test_verify_maintenance_occupied.py
# Actual acquisition requires the pinned installed DOSBox and Frida17.23.2:
python3 scripts/recover_maintenance_occupied.py /tmp/new-occupied \
  --scratch /private/tmp/new-occupied-mounts --frida-module /absolute/path/to/frida.js
python3 scripts/recover_maintenance_occupied_rejections.py /tmp/new-rejections \
  --scratch /private/tmp/new-rejection-mounts --frida-module /absolute/path/to/frida.js
```

Both destinations must be fresh; the runners preserve failures and stop. Portable
verification launches no emulator, Frida, Go application or network operation.
All prior corpus pins and historical strict replay APIs remain unchanged.

**Next integrate these measured active-economy, ground-defense and foreign-force
branches into a separate before-only full-stream/six-file profile.** The new
fixtures remain deliberately rejected by the earlier collision-record profile.
Final-pointer convergence and an exact evolved-world chain are still separate;
none of these ten final worlds has duplicate positive mobile pointers. General
MBF, arbitrary maintenance compatibility, DOS save import, live BBS acceptance
and native Windows durability remain unverified.

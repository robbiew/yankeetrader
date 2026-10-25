# DOS initializer validation — Yankee Trader 3.6

Run on 2026-10-24 using DOSBox Staging 0.83.0. Only the copied distribution under `run/` was mounted as DOS C:. The original distribution files are unchanged, verified by SHA-256.

## Genesis: confirmed configured default of 300

Three independent views agree about the discrepancy:

1. The running initializer prints `Ports needed to initiate Genesis: 450` (`evidence/INIT.LOG`).
2. The generated `YTDATA.DAT` contains `00 00 16 89` at zero-based file offset 105, in configuration record 1. Decoded as an MBF single, that is **300**.
3. Running the original `YTCONFIG.EXE` against the generated file displays `<L> Ports needed to initiate Genesis: 300` (`evidence/CONFIG.LOG`). Exiting with X leaves the data file byte-for-byte unchanged.

Thus **300 is the stored and sysop-visible default**; 450 is a stale initialization message. A player actually invoking Genesis at the ownership boundary was not tested, so this does not independently prove the gameplay comparison or its off-by-one behavior.

## Initialization and maintenance

The initializer accepted redirected input: `Y` to confirm and a blank scoreboard path to use `YTSCORE.ASC`. It generated the universe, ports, and auxiliary files and reported normal termination. It then invoked the bundled `YTMAINT.EXE`. DOSBox exited normally after the program chain completed.

Evidence was copied after completion. The scoreboard timestamp is `10-24-2026 13:39:51`; the configuration utility reports that maintenance has already run today. These files represent **post-maintenance state**, not the pristine state immediately before maintenance. Defense counts and automatic planets may already have changed.

## Comparison with static recovery

| Item | Predicted | Observed | Result |
|---|---|---|---|
| Record length | 137 bytes | 137 bytes | Match |
| Record count | 4,151 | 4,151 | Match |
| YTDATA.DAT length | 568,687 bytes | 568,687 bytes | Match |
| Scoreboard text | 41-byte field | Space-padded `YTSCORE.ASC` | Match |
| Numeric encoding | MBF singles | Expected values decode correctly | Match |
| Player slots | 50 | Record base 51 = config + 50 | Match |
| Sectors | 3,000 | Sector end record 3,051 | Match |
| Ports | 1,000 | Port end record 4,051; 1,000 nonempty names | Match |
| Planet slots | 100 | Planet end record 4,151 | Match |
| Starting fighters | 25 | 25 | Match |
| Starting credits | 1,005 | 1,005 | Match |
| Starting holds | 10 | 10 | Match |
| Dead-player deletion delay | 14 | 14 | Match |
| Daily turns | 500 | 500 | Match |
| Lottery plays/day | 5 | 5 | Match |
| Maximum holds | 1,000 | 1,000 | Match |
| Genesis setting | 300 despite printed 450 | Stored 300; YTCONFIG shows 300 | Confirmed |
| Six warp slots per sector | Offsets 41..61 | All 18,000 slots are integral values in 0..3000 | Match |
| Generated graph connectivity | Universe repaired | All 3,000 sectors reachable from sector 1 | Confirmed |
| Unmapped final four bytes | Unknown | Zero in all 4,151 records | Observed; purpose still unknown |

Additional recovered detail: configuration offset 41 is probably the scoreboard-path length, not date/time bookkeeping. It is 11 for `YTSCORE.ASC`; the initializer computes a string length at code 1000:0A99 before writing this field. The starting year field at offset 45 is 26 on the emulated 2026 date.

The initialized Xannor HQ is sector 1114 in this particular randomly generated universe. Its defense-owner field is -1. The post-maintenance defense count is 3,418, so it should not be used as a direct measurement of the initializer's 10,000-fighter assignment.

Unused record fields can contain reused buffer contents: for example, an unused planet slot still contains configuration-like values and text. Readers must identify active records from their actual type-specific flags rather than assuming all unused bytes are zero.

## Generated files

| File | Bytes |
|---|---:|
| YTDATA.DAT | 568,687 |
| YTNAME.DAT | 26 |
| YTNEWS.DAT | 434 |
| YTYNEWS.DAT | 309 |
| YTRMSG.DAT | 0 |
| YTSCORE.ASC | 603 |

`evidence/decoded-data.json` contains field values, representative records, file hashes, and validation results. `validate_data.py` rechecks the preserved files, expected defaults, graph reachability, original file hashes, and the two captured Genesis displays.

## Reproduction

DOSBox was run with dummy video/audio drivers, without loading or creating a primary configuration, with CPU cycles set to 20,000 and sound disabled. The mounted path was `/Users/robbie/Downloads/YT36/analysis/dos-validation/run`.

DOS commands for the initializer:

```
mount c /Users/robbie/Downloads/YT36/analysis/dos-validation/run
c:
yt-init < answers.txt > init.log
exit
```

`ANSWERS.TXT` contains `Y\r\n\r\n`. Running this again resets only the isolated copied universe. The second emulator invocation used `ytconfig < cfgread.txt > config.log`, with `CFGREAD.TXT` containing `X\r\n`.

To rerun the validation without changing the preserved universe:

```
python3 /Users/robbie/Downloads/YT36/analysis/dos-validation/validate_data.py
```

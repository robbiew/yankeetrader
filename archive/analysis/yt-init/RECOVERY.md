# Yankee Trader 3.6 initializer: first recovery pass

Analyzed 2026-10-24 with Homebrew Ghidra 12.2 and OpenJDK 25. The DOS programs were not executed. Original executables were not modified.

## Evidence and limits

Target: `YT-INIT.EXE`, 20,385 bytes, SHA-256 `601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2`.

Ghidra imported the DOS MZ executable as `x86:LE:16:Real Mode`. Import, analysis, export, and project save succeeded. Its loader reported a defined segment without file data. Automatic C decompilation fails on several application functions and misinterprets inline QuickBASIC runtime selectors as x86 instructions. `decompiled.c` is raw diagnostic output, not recovered source.

`qb-annotated.txt` is the more useful first-pass listing. `DecodeQB.java` recognizes INT 3D/3E/3F runtime sequences and selected inline arguments. This is an experimental decoder for this executable, not a complete QuickBASIC decoder. Runtime operation names remain inferred from repeated use. Far-call formatting and other unrecognized inline payloads still require verification.

Numeric constants decode coherently as four-byte Microsoft Binary Format (MBF) singles. The initializer's constant/string area begins at file offset 0x2990, corresponding to logical DS offset 0xA650 after runtime setup. A logical constant address maps to file offset `address - 0xA650 + 0x2990`. These logical DS addresses must not be confused with Ghidra's initial loader segment addresses.

This report preserves the initial static recovery. A subsequent DOS run confirmed the main layout and defaults; see [DOS validation results](../dos-validation/RESULTS.md). In particular, the stored and YTCONFIG-displayed Genesis default is 300, and YTDATA.DAT is exactly 568,687 bytes. The static-only qualifications below describe the original state of this investigation.

## Recovered defaults

| Setting | Value | Main-code evidence (Ghidra CS 1000) | Constant evidence |
|---|---:|---|---|
| Sectors | 3,000 | 0083–0089 | DS A666, file 29A6 |
| Ports | 1,000 | 0078–007E and 199E–19A4 | DS A662, file 29A2 |
| Maximum planets | 100 | 008E–0094 and 1F0C–1F26 | DS A66A, file 29AA |
| Player slots | 50 | 0AC5–0AF2 and player initialization loop | DS AB5C, file 2E9C |
| Starting fighters | 25 | 07A3–07D6 | DS A8B6, file 2BF6 |
| Starting credits | 1,005 | 07DB–080B | DS A8D8, file 2C18 |
| Starting cargo holds | 10 | 0810–0840 | DS A6B6, file 29F6 |
| Dead-player inactivity deletion | 14 days | 0845–0875 | DS A918, file 2C58 |
| Daily turns | 500 | 08B7–08E7 | DS A982, file 2CC2 |
| Daily lottery plays | 5 | 08EC–091C | DS A68E, file 29CE |
| Maximum cargo holds | 1,000 | 09AA–09D8 | DS A662, file 29A2 |
| Scoreboard path | YTSCORE.ASC on blank input | 0A69–0A94 | DS AB4C |
| Remote local-screen display | On | 09DD–0A0B | Printed label plus flag write |

Last-maintenance bookkeeping is initialized to yesterday (087A–08B2). Port initialization explicitly backdates production by ten days (printed label and 1C9F–1CB5).

### Possible original display bug: Genesis threshold

At 098D the program prints `Ports needed to initiate Genesis: 450`. Immediately afterward, 099A–09A5 converts the MBF constant at DS AA32 (file 2D72) and writes it to the shared field descriptor A57A. Its bytes are `00 00 16 89`, decoding to **300**, not 450.

The most likely interpretation is a stale display string and an actual configured threshold of 300. Confirm through YTCONFIG, the generated configuration record, and YT.EXE's Genesis check before adopting it as gameplay behavior.

## Shared YTDATA.DAT record layout

The opening routine at 03C9–04A9 supplies random-access mode `R`, file number 1, filename `YTDATA.DAT`, and record length **0x89 = 137 bytes**. Its FIELD-like setup maps one 41-byte string and 23 four-byte fields:

| Byte offset within record | Width | Descriptor / interpretation |
|---|---:|---|
| 0 | 41 | A536, text/name/path field |
| 41 + 4*n, n=0..22 | 4 each | A53A through A592 |
| 133 | 4 | Unmapped by this FIELD setup; purpose unknown |

The declared record length is 137, while mapped fields sum to 133. Do not silently remove the remaining four bytes. Also do not assume every four-byte field is a modern integer or IEEE float: conversion calls suggest BASIC packed numeric strings, likely MBF singles, to be verified against actual files.

The same descriptors are reused for configuration, players, sectors, ports, and planets. A field's meaning changes with record type.

### Configuration record (record 1): partial map

Offsets are zero-based within the record. Names are reconstructed; original variable names were not recovered.

| Offset | Descriptor | Recovered interpretation | Initial value / status |
|---:|---|---|---|
| 0 | A536 | Scoreboard path | User input or YTSCORE.ASC |
| 41 | A53A | Likely scoreboard-path length | DOS run: 11 for YTSCORE.ASC; string-length call at 0A99 |
| 45 | A53E | Starting-year/date component | Derived from DATE$; needs full date tracing |
| 49 | A542 | Daily turns | 500 |
| 53 | A546 | Last player record / sector base | Inferred 51 = 1 + 50 |
| 57 | A54A | Last sector record / port base | Inferred 3,051 |
| 61 | A54E | Last port record / planet base | Inferred 4,051 |
| 65 | A552 | Starting fighters | 25 |
| 69 | A556 | Starting credits | 1,005 |
| 73 | A55A | Starting holds | 10 |
| 77 | A55E | Dead-player deletion delay | 14 |
| 81 | A562 | Last maintenance day | Yesterday |
| 85 | A566 | Local display flag | On |
| 89 | A56A | Unknown | Not assigned a semantic name yet |
| 93 | A56E | Last planet record | Inferred 4,151 |
| 97 | A572 | Unknown | Unresolved |
| 101 | A576 | Lottery plays/day | 5 |
| 105 | A57A | Likely Genesis threshold | 300 despite printed 450 |
| 109 | A57E | Unknown | Unresolved |
| 113 | A582 | Unknown | Unresolved |
| 117 | A586 | Xannor HQ sector | Randomly selected |
| 121 | A58A | Maximum cargo holds | 1,000 |
| 125 | A58E | Year-related constant | 6,324; role unresolved |
| 129 | A592 | Unknown | Unresolved |
| 133 | none | Unmapped tail | Unresolved |

### Likely default record allocation

Derived from the record-base arithmetic and loops; verify against actual output:

| Records (BASIC uses 1-based numbering) | Purpose | Count |
|---|---|---:|
| 1 | Configuration | 1 |
| 2–51 | Player slots | 50 |
| 52–3,051 | Sectors | 3,000 |
| 3,052–4,051 | Ports | 1,000 |
| 4,052–4,151 | Planets | 100 |

This predicts a base file length of 4,151 * 137 = **568,687 bytes**, provided initialization/maintenance does not append other records. This is a prediction, not a measured file size.

### Sector records: partial map

The writer at 16A9–1787 copies six integer-array entries to descriptors A53A through A54E. The array indices are separated by **0xBB9 = 3,001**, corresponding to six warp columns with indices 0..3000.

| Record offsets | Likely meaning |
|---|---|
| 41, 45, 49, 53, 57, 61 | Six outgoing warp destinations |
| 81 | Defense strength: HQ initialization writes 10,000 here (2016–2021) |
| 85 | Defense ownership/faction: HQ initialization writes -1 here (2026–2031) |

The last two meanings are inferred from the Xannor setup; exact distinctions such as fighters versus another force type require YT.EXE cross-checks.

## Recovered initialization sequence

1. Ask permission to reset the game; create/open the main data file.
2. Set configuration defaults and request the scoreboard path.
3. Clear 50 player slots.
4. Clear a six-column sector graph, generate warps and long warps, repair isolated sectors, and build shortcuts toward sector 1.
5. Write 3,000 sector records.
6. Create 1,000 ports; port 1 is named Earth, others use syllable-generated names. Production is backdated ten days.
7. Reserve 100 planet slots.
8. Set up the Xannor headquarters sector and its initial defenses.
9. Create the newspaper, initialize the real-name/alias mapping, and clear radio messages.
10. Launch YTMAINT.EXE for initial maintenance.

Auxiliary filenames recovered directly: `YTNEWS.DAT`, `YTNAME.DAT`, `YTRMSG.DAT`.

## Files and reproduction

- `../ghidra-projects/YankeeTrader.gpr`: saved Ghidra project.
- `decompiled.c`: uncorrected automatic C output, retained for diagnosis.
- `listing.txt`: original Ghidra listing.
- `qb-listing.txt`: experimental runtime-aware linear listing.
- `qb-annotated.txt`: listing annotated with string descriptors and MBF constant candidates. Untyped data can produce meaningless MBF interpretations; only contextual interpretations above have been reviewed.
- `../ghidra-scripts/ExportYT.java`: initial listing/decompiler export.
- `../ghidra-scripts/DecodeQB.java`: runtime-aware listing export.
- `annotate.py`: associates logical DS references with constants/strings.
- `recovered-init.bas`: manually reconstructed outline, not original source.
- `headless.log`, `analysis.log`, `decode.log`: tool evidence and limitations.

## Next investigation

Run YT-INIT and its initial maintenance in an isolated DOS working directory, capture the displayed values and generated files, and compare the predicted record count/length. Decode the configuration record, check the unexplained four-byte tail, and inspect YTCONFIG and YT.EXE to confirm field semantics, MBF storage, and the Genesis discrepancy. Trace all runtime selectors before treating the automatic decompiler output as trustworthy application logic.

## DOS validation follow-up

The initializer and its automatic initial maintenance completed under DOSBox Staging. The generated file has 4,151 records of 137 bytes, matching the prediction. All recovered configuration defaults matched; YTCONFIG independently displays Genesis = 300, confirming the initializer's printed 450 is stale. All record tails were zero in this run. Full evidence and remaining limits: [DOS validation results](../dos-validation/RESULTS.md).

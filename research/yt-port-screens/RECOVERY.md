# DOS port screen comparison

Ten isolated DOSBox Staging sessions captured **35 original 80×25 text screens** directly from B800 video memory. The capture format is 16 bytes of BIOS metadata followed by 4,000 interleaved character/attribute bytes. BIOS cursor positions are retained. `CAPTURE.COM` and `DUMP.COM` are the preserved research utilities; `@` snapshots without sending a keystroke and `~` waits 36 BIOS ticks. Original binaries and archived saves were never mounted or modified.

Reproduce with `python3 scripts/recover_ports.py /absolute/new/directory` (requires DOSBox Staging). The runner fixes the DOS date to October 24, 2026, time to midnight, and CPU cycles to 200,000. Each scenario starts from the named archived trade fixture's `before.dat`. Only `holds-buy` changes its disposable input: player record 2, MBF32 offset 65, is set to ten holds. Its original fixture hash, patch declaration, and resulting input hash are retained separately.

| Scenario | Captured stages |
| --- | --- |
| earth | Earth shop, fighter quantity, purchase redraw, departure |
| holds | Earth shop, full-holds notice/redraw, departure and following main screen |
| holds-buy | Earth shop, capacity/quantity prompt, purchase redraw, departure |
| forces | Earth shop, ground-force quantity, purchase redraw, departure |
| shields | Earth shop, shield quantity, purchase redraw, departure |
| buy | Cargo quantity, agreement, completed purchase |
| sell | Cargo quantity, agreement, completed sale |
| owned | Another player's ownership report, agreement, completed purchase |
| self | Own-port treasury report, agreement, completed purchase |
| decline | Cargo quantity, agreement, declined purchase |

Each directory includes raw `SCREENS.BIN`, exact keystrokes, compressed original game/emulator logs, and provenance with executable, input fixture, capture utilities, screen and transcript hashes. `python3 scripts/verify_port_screens.py` checks those identities, patches, 80-column BIOS metadata, frame counts, cursor bounds, logout and scenario-specific prompts.

## Observed rendering

- DOS foreground 6 (brown) on black: docking notice, commerce report, Earth table, cargo header, buying rows, balances and prompts.
- Foreground 2 (green) on black: `<Port>` and cargo rows that sell to the player.
- Foreground 14 (bright yellow): cargo separator and the full-holds warning.
- Foreground 7 (gray): typed answers.
- Earth table separators are columns 23 and 32; prices begin at column 25, affordability at 34. Blank lines separate the table, `I`/`0` choices and credit prompt. A successful purchase redraws the commerce report and table without an extra receipt line.
- Cargo labels occupy 13 columns, padded with dots; status begins at column 16, supply ends at 34, holdings at 45 and price at 52. The separator retains its original 53-character layout.
- Holds use a separate capacity message; ground forces and shields have their original distinct quantity wording. Owned cargo ports show the actual owner's alias, or `YOU, Credits:` with the actual treasury.

## Automated comparison and boundaries

`python3 scripts/smoke_port_parity.py` runs the native Go game over real PTYs using the existing ANSI screen emulator. It compares **29 port stages** against these independent DOS captures: every character position, every visible character's foreground, and all backgrounds within the compared port body. Every input prompt remains at its captured row/column. Differences raise errors with exact cell coordinates. Blank cells retain background checks; their invisible foreground attributes can differ because DOS leaves previous attributes behind while scrolling.

The native fixtures use real saved-world fields and transactions. Their coefficients are chosen to reproduce the recorded 10/44/62-credit quotes while retaining the documented Go fixed reference prices. They do not claim recovery of the DOS reference-price RNG. Saved credits, cargo, equipment, turns and owner commissions are checked after each session.

Only live commerce timestamps and the five unsupported Earth affordability values are allowed to differ in the compared body; their colors/backgrounds are still checked. Those Earth items retain the original labels and historical prices but show `N/A`, and cannot be purchased. Caller identity, time remaining, preceding startup/sector history and the status bar remain live and are outside this port-body comparison. Error wording for invalid quantities, timing, terminal font metrics, unimplemented features and a real BBS deployment are not asserted to match.

`evidence/port-parity` contains native recordings/cell snapshots and paired DOS/Go renderings. `--render` optionally regenerates PNGs with the startup renderer (Pillow and Menlo required); CI runs all cell comparisons without image dependencies. The separate `smoke_ports.py` exercises ANSI/UTF-8 and ASCII fallback with the ordinary beginner world, including a declined trade and persistence. `-compact` is unchanged.

REA identified the original `YT.EXE` as DOS MZ, SHA-256 `c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`. The retained `rea-evidence.json` records a static byte observation (`ev_afc5c96613017255f2d7b31c06884c2eba0845afc9afb2a6919e18b2810c43a9`); it is not runtime evidence for these colors. The B800 captures establish the rendering observations. The native REA session was closed after export.

# DOS planet renaming

Fourteen isolated DOSBox Staging sessions captured **45 original B800 screens** plus the persisted DOS saves. The observed rename path is main `1000:5464..55d3`; its name cleaner is sub `1f42:1866..1a92` in the preserved annotated listings. Screens and before/after records establish the behavior below; static code supplies the broader normalization/control-flow context.

## Observed rules and flow

While landed, `N` asks `What do you want to name this planet? -=>`. Blank input returns to the planet menu without renaming. Otherwise DOS cleans the name, truncates it to 41 characters, and asks `"New Name" Is this OK? (Y/n) [Y] ?`. `N` restarts the naming prompt; Enter accepts. A successful rename has no extra receipt, charge or turn cost, and does not change the governor, garrison or carried goods. `D`, the sector display and subsequent saves use the new name.

The cleaner removes leading/trailing spaces, collapses repeated spaces and applies word casing. Captures verify `mIxEd nAME` → `Mixed Name`, `   Test  Name   ` → `Test Name`, and `o'brien alpha-beta x_Y 42base` → `O'brien Alpha-Beta X_Y 42Base`. Apostrophes remain inside a word; other punctuation/digits start a new word. The 50-digit probe confirms truncation to the first 41 digits before confirmation and persistence.

`The Wanderer`, `Xannoron` and `Mercenary Base` are rejected after cleaning, including lower/mixed-case spellings and repeated spaces. The warning is `I Don't think so!`. The original permission guard protects special slots rather than requiring the caller to be governor: the governor, a teammate, an unrelated visitor on an unguarded planet, and a caller on an ungoverned planet all successfully rename an ordinary planet. A disposable copy of an ordinary planet in final slot 100 is rejected before the name prompt with `You can't re-name this planet!`. The static guard also excludes the first/synthetic special slots; the current Go world does not model the synthetic negative planet ID and excludes slot 1 from ordinary allocation.

Both prompts, the returned free-holds text and planet-command prompt use DOS cyan (3) on black. Typed answers use gray (7). Both rejection messages use bright cyan with blink (`8b`), then restore cyan. Blank lines and the original punctuation are retained.

## Capture provenance

Run `python3 scripts/recover_planet_rename.py /absolute/new/directory` to reproduce. It copies known archived planet fixtures, fixes the DOS date/time to October 24, 2026 at midnight, uses 200,000 CPU cycles and the preserved B800 capture tools, and never mounts or changes the archive. Each frame has 16 bytes of BIOS metadata followed by 4,000 character/attribute bytes. `@` captures without a key and `~` waits 36 ticks. `--only` selects individual scenarios.

The `unowned` fixture sets planet record 4053's governor/garrison to zero. `last-slot` copies record 4053 to record 4151 and points sector record 151 at planet slot 100. Provenance retains the original fixture hash, explicit patches and resulting input hash separately. The other twelve inputs are byte-for-byte copies of their archived `before.dat`. Executable, capture/dump tool, screen, transcript and final-save hashes accompany each session. All original executable hashes remain unchanged.

`verify_planet_rename.py` checks those identities, exact patches, geometry/cursor metadata, all 45 frames and the persisted name bytes/activity lengths. It also confirms unchanged player credits, turns, cargo, weapons and ground forces, plus unchanged governor/garrison. Case outcomes:

| Cases | Persisted result |
| --- | --- |
| owner, team, foreign, unowned | New Eden |
| blank, reserved, lowercase, other-reserved, last-slot | Test Planet unchanged |
| retry | Second Name, accepted with Enter |
| long | First 41 digits |
| spaces | Test Name |
| case | Mixed Name |
| punctuation | O'brien Alpha-Beta X_Y 42Base |

## Native implementation and boundaries

`smoke_planet_rename.py` drives actual native PTYs and compares **42 rename stages** against independent original DOS captures. It checks each character position, visible foreground and all backgrounds in the selected rename body/prompt region. Only time-left digits are dynamic there. Native saves verify the chosen name and unchanged player assets/governorship. Every case also runs in ASCII fallback; rejection blink sequences are checked separately. `--render` optionally creates paired screenshots using the existing Pillow/Menlo renderer.

Three DOS frames contain irrelevant invalid commands sent after a rejection while probing permission/case behavior; they remain preserved but are not claimed as rename comparisons. The long-name DOS input line wraps by overwriting the beginning of the old prompt. Native input wraps normally; the comparison therefore checks its current confirmation line and subsequent returned menu, not that corrupt historical input line. Raw captures preserve the difference. Caller/status labels, preceding startup/sector history, font metrics, timing and blink animation are outside the body comparison.

The Go backend rechecks the landing token, planet location and current landing permission under the store lock before changing the name. Failed/abandoned confirmation cannot commit; stale sessions and lost access cannot rename another planet. Tests cover cancellation/retry, disconnect before/after commit, replacement sessions, movement, changed defenses, shared access, slot 100, invalid controls/non-ASCII, and truncation at a trailing-space boundary. The UI passes the original candidate to the backend so cleaning/truncation happens exactly once on the committed name.

Existing ASCII save/name safety limits remain; no new charge, ownership restriction or money/production rule is introduced. Synthetic NPC planets, thrusters, forced landing and complete game/real BBS deployment parity are outside this change. `-compact` is unchanged; the new action is `N` in the default DOS planet menu.

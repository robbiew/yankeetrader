# Remaining newspaper events: inventory, evidence and implementation

Target: original DOS 3.6 YT.EXE, SHA-256
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
This follow-up first audited current Go producers rather than treating historical
research checklists as the current feature backlog.

## Already implemented

The starting game published fourteen kinds: login, team creation, planet creation,
public radio broadcasts, player planetary ground actions, paid lottery prizes,
Xannor HQ victory, Xannor-caused player deaths, Xannor planetary assaults, port
plague, planetary plague, civil war, super-planet awards and inactive-account
retirement. Private former-owner port-sale notices deliberately remain private.

## Native caller inventory

The REA Ghidra search in `rea.json` covers initialized loaded addresses
`0x10000..0x2bfff` inclusive: 114,688 bytes in main/sub code blocks, with no skipped
bytes or continuation. Its **61 direct shared-writer byte encodings** match the
archived QuickBASIC annotated main/sub listings. The independently relocated MZ
image reproduces every returned call and eight selected native byte reads.
This is a bounded direct-call inventory, not proof about indirect logging or
another executable such as YTMAINT.EXE. Static bytes do not observe execution.

Main segment is `1000`; sub segment is `1f42`. Offsets below are segment-relative.
The writer itself is `1f42:1a9b`; REA uses linear loaded addresses with load 1000.

| Caller offsets | Classification and disposition |
| --- | --- |
| main 06b4 | New registration; added |
| main 5be7 | Successful team join; added |
| main 0e3c / 109a | Fighters surrender / defender casualties; added |
| main 2f5d | Fighter casualty's residual carried mines explode; added only to the confirmed fighter-kill branch |
| sub 2d5e / 2d97 / 2dcf | General death, killer/victim, actual captured ports; added |
| sub 2e85, 2fb4..3540 | Salvage header, positive resources, empty holds/cargo or NOTHING; added |
| sub 6468 / 6c79 | Mine encounter and final shields; added |
| sub 7273 / 73fd / 778c / 77e5 | Missile defense casualties, mines, ship target and damage; added |
| sub 7bfb / 7cf5 / 7ef7 / 8083 | Missile planetary attack, ground, production and destruction; added |
| sub 9f3a | Retaliatory missiles; added |
| sub b009 / b110 / b209 / b48b / b4db / b834 / ba3f / bc05 / bc5c | Plasma defense, mines, ships and planets; added |
| sub 82d6 / 8396 | Thruster transport explosion and positive fighter losses; added |
| main 394d / 58e6 / 9a93 / 9b1c | Planet creation, team creation, public broadcast header/body; already implemented |
| sub 166d / 52ba / 9024 / 91af / 9229 / 930e / a8f8 / a901 / a90a | Login, lottery, ground assault and HQ reports/separators; already implemented as typed records |
| main 11a1 | Original Xannor turn-bonus collection; no corresponding modern turn-bonus mechanic is added by this newspaper work |
| main 05e8 / a6d8; sub 465a / 47ed / 47ff / 4811 | Full-game rejection, missing files and runtime diagnostics; intentionally excluded from public gameplay events |

## Runtime corroboration

Four new normally returned copied-world DOS controls are retained in `dos/`, with
before/after complete worlds, exact auxiliary files, raw logs, input keys, binary
identities, clock files and shell return markers. The capture runner mounts only
disposable copies. Archived executables and source worlds are unchanged.

- Registration accepts the default real-name alias Newsnew, and appends one
  `New Player Entered` line. It does **not** append `Logged on` as well.
- Team join appends `Q  Joined Team 1` after valid ABCD consent and saves team 1.
- Wrong password and cancellation append the ordinary existing-account login
  only; neither publishes a join or changes membership. Passwords stay absent
  from the public suffix.

Eleven selected **existing retained newspaper files** corroborate sector
surrender/casualties, fighter death/loot/wreck mines, missile fighters/mines,
plasma fighters/ships/self-death/planet damage/destruction, thruster explosion
and mine shields. `sources.json` binds the original artifact and extracted news
bytes by hash, plus required report fragments. No new replay is claimed for
these older captures. Archive fixtures can contain earlier events; their entire
contents are not attributed to the last action. The fresh membership controls
instead verify the exact new news suffix and relevant saved membership.

The native inventory/annotated control flow supports the broader event mapping;
the eleven runtime sources do not independently prove every numeric edge,
retaliation variant or salvage resource. Existing subsystem research remains
applicable. Exact RNG, MBF rounding, colors and every original line break remain
outside the claim.

## Modern implementation

Save **31** introduces registration, team-join and structured combat payloads.
Schemas 1–30 upgrade without backfilling historical events; legacy saves claiming
these new fields/kinds are rejected. New-account registration replaces its first
login line. Existing logins, replacement ships and reconnects retain login news.

Combat records store only whitelisted public alias/name snapshots, sector and
outcome quantities. They do not include BBS identities, team credentials, private
radio, bank balances or command tokens. General deaths preserve real attribution;
the existing dedicated Xannor death report is not duplicated. Actual transferred
ports and sampled loot are reported, not cached ownership or unsampled stock.
Only unsalvaged fighter-casualty mines actually deployed outside Earth get the
explicit wreck-explosion event.

One structured record may summarize several original DOS lines. Weapon defense
casualty news retains the original strictly-more-than-nine threshold. Planetary
summaries report actual production/ground loss and remaining quantities; lazy
production is applied before measuring damage. A destroyed planet's accepted
name survives removal. Transport may summarize a zero-fighter explosion in one
record. These are formatting/storage adaptations, not claims of byte parity.

Journal append and action share the authoritative world transaction. Cancelled,
rejected, stale and rolled-back operations publish no committed success reports.
Public snapshots are validated on load. The existing 1,024-row/today-and-yesterday
retention and UTC selection remain. Appends reserve enough monotonic journal IDs
before mutation; conservative bounded combat reservations can refuse a launch or
hazard near uint64 sequence exhaustion even if a particular outcome would use
fewer IDs. Export does not reset the sequence. No new arbitrary public-message
writer is exposed.

## Validation and remaining boundaries

```sh
python3 scripts/verify_remaining_news.py
python3 scripts/test_remaining_news_verifier.py
```

The independent verifier reconstructs relocated native bytes, checks all 61 direct
calls, verifies the eleven retained news artifacts, and verifies fresh normally
returned membership controls and their exact new suffixes. Corruption controls
reject false registration and team-state files even after hashes are recomputed,
as well as changed native bytes and source hashes. CI runs both commands.

Go coverage exercises attribution, snapshots, positive/empty salvage, actual wreck
remainders, rejection before mutation, near-exhausted journals, malformed payloads,
legacy-field rejection, and lazy production versus battle damage. Existing store
rollback/concurrency tests and terminal newspaper/weapon flows cover integration.
Native Windows crash durability, live BBS acceptance, unimplemented random-event
mechanics, the original turn-bonus branch and exact DOS numeric parity remain
separate. Routine maintenance headings/runtime diagnostics are not new public
journal event types.

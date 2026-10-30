# Danger scanner and manual emergency warp — integration research

Historical research slice, 2026-10-30. The later bounded danger-scanner and
manual-warp [implementation](IMPLEMENTATION.md) now follows these controls.
Existing combat/mine escape remains playable. This slice closes specific purchase, command-queue and arrival gaps in
the [earlier encounter research](../yt-navigation/ENCOUNTERS.md); it does not
claim complete DOS RNG or operational parity.

## Evidence and scope

[Forty-one completed ordinary DOS sessions](dos/results.json) retain 82 complete
before/after world snapshots, exact key streams, readable transcripts, emulator
logs, actual DOS date/time output and existing DAT/ASC sidefile payloads. Four
follow-ups inherit their parent's exact committed world and all recorded sidefiles.
The [frozen recipe](dos/recipe.json) declares every world modification and command.
No executable was patched to force an outcome. Disposable mounts use original
YT.EXE, BRUN30.EXE, LOCAL.EXE and the archived keyboard feeder; no archive is mounted
for execution or changed.

The source is `archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT`,
SHA-256 `04eaf42c54d4f35c3412737e27fa968b5abcd22eb295cb5d8b45ab8045fcd0ec`.
YT.EXE is `c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
Recipe SHA-256 is `da66c10029fbe63a30c302acee6ec520bb4819d833c5bed42ba9ebef4c4fbc7d`.
The 3,000-sector fixture deliberately contains a closed navigation subgraph at
100–110 and isolated hazard patches elsewhere. The two-sector disruption control
is separately declared; it forces the existing session disruption formula without
patching code. These fixtures are research setups, not generated Go worlds.

All sessions request 10/24/2026. The meltdown cases request 02:00:00; their raw DOS
clock reads 01:59:59.95, a timer-quantization boundary retained in the evidence.
Other cases log 00:00:00.00. These are selected branch controls, not a probability
sample. Failed pilot timing runs are not included in the 41 completed controls.

## Earth purchase and persistence — observed

| Control | Saved result |
|---|---|
| `shop-exact` | Item 5 spends exactly 250,000 credits; balance 0, scanner installed |
| `shop-above` | 250,001 becomes 1; scanner installed |
| `shop-below` | 249,999 and absent scanner unchanged; affordability refusal |
| `shop-repeat` | One installation/250,000 charge; second selection refused |
| `shop-installed-poor` | Installed scanner and zero credits: duplicate refusal takes precedence |
| `shop-leave`, `shop-blank` | No purchase or inventory change |
| `shop-reconnect` | Exact parent save reloads installed scanner; repeat purchase refused |
| `shop-installed-use` | Exact purchase follow-up uses the installed scanner to warn about a mine |

Earth's shop labels the scanner as **item 5, price 250,000**. Selecting it installs
immediately: no quantity prompt or second purchase confirmation. The captured refusal
cases use fresh input to leave the shop. Each
Earth docking costs one turn, including cancelled or refused purchases; additional
shop selections do not cost extra turns. The reconnect's new docking spends one
more turn, while its duplicate refusal spends no credits.

The scanner is player-record offset 93, a four-byte MBF single: canonical absent
0 and installed −1. Noncanonical 1 and −2 also activate warnings in two declared
robustness controls; this does not recommend nonboolean modern save state.

The retained post-logout scores also establish the scanner asset value:
`shop-exact` (cash 0, installed) and `shop-leave` (cash 250,000, absent) both
store score 10,140,250. `shop-above` stores 10,140,251. This corroborates counting
an installed scanner as 250,000 points; it does not change score-cache timing.

## Warnings and queued travel — observed

A warning costs no turn. Fresh decline preserves position, hazards, shields and
inventory. The invalid/nonadjacent movement control rejects the jump without
scanning the unreachable destination.

- Xannor, Mercenary and human forces use their real owner labels. The combined
  controls print one header, then disruption (when present), mines, fighters,
  one drive-deactivation line and one fresh confirmation. Quantities are exact.
- `scanner-autopilot-first-yes` accepts a mine warning and stops at 101, spending
  one turn and resolving the mine. It does not continue the discarded course.
- `scanner-autopilot-second-no` completes the clear first hop, then declines a
  warning at 107. It remains at 101 with 499 turns and the mine in 107 intact.
- `scanner-autopilot-second-yes` accepts that second hop, resolves its mine and
  stops at 107 with 498 turns. Later course commands remain discarded.
- `scanner-stacked-no-fresh-yes` discards the queued N and obeys the fresh Y.
  The earlier evidence separately proves queued Y cannot approve a warning.
- `scanner-decline-then-warp` declines the mine warning and successfully engages
  manual W afterward. “WARP DRIVE DEACTIVATED” clears queued travel; it does not
  permanently disable manual emergency warp.

Own-force and valid same-team exemptions, different-team warnings and persisted
scanner damage already have controlled evidence in the earlier
[encounter](../yt-navigation/ENCOUNTERS.md) and [hazard](../yt-navigation/HAZARDS.md)
packages. They are not newly inferred from these hostile-owner controls.

## Manual warp and arrival — observed

Manual W needs positive turns, but no purchased scanner, cloak energy or credit
payment. The original accepts the stacked `W;Y` command; fresh modern confirmation
is a proposed safety policy, not a recovered original restriction.

| Control | Observed result |
|---|---|
| `warp-clear` | 100→60, 500→445 turns; exits the fixture's closed route graph |
| `warp-one-turn` | Same destination, final turn consumed; no negative turn balance |
| `warp-zero-turns` | No engagement, movement or resource change |
| `warp-same-sector` | 2665→2665 still costs 58 turns |
| `warp-avoided-landing` | Locks out 881 in the same login, then lands in 881 for 65 turns |
| `warp-empty-exits` | Lands in sector 60 with all six outgoing links empty |
| `warp-from-earth` | 1→2665 for 58 turns; no credit/equipment requirement |
| `warp-repeat-same-day` | Linked second warp spends another 58 turns without a new equipment cooldown |
| `warp-meltdown` | 100→219, all 500 turns consumed; no equipment or death-field change |
| `warp-reconnect-meltdown` | Same-date reconnect retains sector 219 and zero turns |

The earlier attempt named `warp-current-sector` starts at 60 and selects 2665;
it does not establish same-sector landing. Likewise, `warp-avoid-destination`
locks out 60 but selects 881. The specifically named successful controls above
close those gaps. DOS avoid lists reset on reconnect, so the avoided-landing
control must set the list and warp within one login.

Mined arrival resolves mine damage without charging a separate normal movement
turn. Three mines reduce shields from 10,000 to 8,088 in the retained normal run.
With a scanner installed, one mine reduces shields to 9,134 and no pre-arrival
scanner confirmation appears. Scanner installation remains intact in that case.

Hostile fighter arrival leaves all 100 Xannor fighters in place and enters their
encounter menu, blocking ordinary commands. The controls quit from that unresolved
encounter; they do not defeat, surrender to or escape it. Own fighters remain
unchanged and permit the normal command prompt. Combined mines and fighters
resolve mines before the hostile fighter encounter.

A natural meltdown with an installed scanner still lands in mined sector 219,
spends every turn and resolves its mine: shields become 9,915. Meltdown therefore
does not suppress arrival hazards. It prints disabled-engine/one-solar-day text,
but these captures establish only the all-turn debit and same-date persistence,
not next-day engine repair or a separate persistent engine-damage flag.

## Static corroboration and numerical limits

Ten complete [REA byte observations](rea/yt.json) cover the relevant original
call sites. They are static shipped-artifact observations, not execution traces.
Ghidra 12.1.4 uses MZ load segment 0x1000 and linear byte addresses. The verifier
independently maps the original MZ payload and applies relocation words before
comparing every retained byte. The session was closed after export.

| Observation | Linear start | Bytes |
|---|---|---:|
| Manual command gate | `0x11594` | 134 |
| Movement scanner gate/queue clearing | `0x11c3e` | 113 |
| Earth price assignment | `0x16d3f` | 40 |
| Scanner purchase | `0x17820` | 143 |
| Shared billing | `0x17c2e` | 143 |
| Saved scanner load | `0x1a470` | 19 |
| Scanner hazard order and owner labels | `0x300de` | 998 |
| Emergency-warp helper | `0x293e4` | 1084 |
| Random destination helper | `0x20ef9` | 34 |
| Main arrival/disruption loop | `0x1081f` | 98 |

Evidence IDs and profile digest are retained in that bundle. For example, purchase
is `ev_f0c81e9a00b5263222bde8f815de66e75e0e5dfad137b9c977712095e817b1cf`
and warp is `ev_724b6d3c98f42409e2009dcd038214d6304acde2d8d6e9a689aaeed0d4335971`.

The [existing mathematical model](../yt-navigation/encounter_rules.py) interprets
loop budget `70*(RND+RND)`, heat increments on strict `RND>.75`, a stop at 31 marks,
and destination `INT(RND*sector_count)+1`. Normal debit is
`min(turns, 4*heat + INT(4*RND))`; 31 marks spends all remaining turns. The extra
post-destination draw writes a temporary that recharge later overwrites. The
model retains this draw without inventing a destination override.

Captured normal receipts satisfy the exact capped interval
`min(turns,4*heat) <= debit <= min(turns,4*heat+3)`. Mathematical zero-debit and
meltdown branches are checked with injected draws; a natural zero-debit warp was
not observed. Original RNG state, MBF loop-bound conversion and rounding at every
fractional boundary remain unverified.

## Proposed bounded implementation contract — not shipped here

- Add an explicit persisted scanner flag and an Earth item-5 purchase using exact
  integer debit and existing docking/session validation. Reject duplicate or
  unaffordable purchases without charging. Preserve old saves without granting
  free equipment, and persist any supported scanner destruction with mine damage.
- Warn only from real current hazard state. Preserve own/team exemptions, actual
  owner labels, one fresh post-warning decision and free cancellation. Invalidate
  queued commands and stop autopilot after a warning, retaining completed hops.
  Revalidate position, generation, hazards, ownership/team and turn budget under
  the store lock before accepting a decision. Do not fabricate disruption data
  where the modern world has no corresponding model.
- Expose manual warp through a fresh risk confirmation in both interfaces. Use
  bounded draws/work, exact capped whole-turn accounting, real destination and
  actual debit receipts. Preserve the established random-destination rules;
  avoid lists are route preferences, not a safe-warp guarantee. Do not add an
  equipment purchase requirement or a credit charge unsupported by the evidence.
- Persist destination, recharge/meltdown, landing-token invalidation, mines,
  scanner loss and any death/estate consequences atomically. Hostile destination
  fighters must remain an encounter gate. Reuse protected-Earth, attribution and
  ship-generation rules; no extra movement debit or cross-generation action.
- Validate cancellation, stale warnings, concurrent actions, rollback, committed
  durability, same-sector/avoided/hostile destinations, full/short turn budgets,
  repeated warps, scanner purchase/loss/reload and migration. A saved failure
  cannot be replayed as a free teleport or double payment. Update README in the
  implementation commit.

These are modern implementation policies informed by the original controls, not
claims that DOS uses atomic transactions, modern bounds or fresh W confirmation.
The research milestone left schema version 20 unchanged. The later
[implementation](IMPLEMENTATION.md) adds version 21 and the supported gameplay.

## Reproduction and verification

```sh
python3 scripts/verify_scanner_manual_warp.py
python3 scripts/test_scanner_manual_warp_verifier.py
python3 scripts/verify_encounter_evidence.py
python3 scripts/verify_encounter_followup.py
python3 scripts/verify_hazard_evidence.py
python3 scripts/verify_archive.py
# Existing DOSBox Staging required; the destination must not exist:
python3 scripts/recover_scanner_manual_warp.py /private/tmp/yt-scanner-warp-new
```

The independent verifier freezes declarations, reconstructs every setup and
parent chain, checks all recorded sidefiles/keys/clocks and asserts real purchases,
exact warnings, partial autopilot progress, recharge/cap/heat relationships,
meltdown, hazardous arrival, private assets and native bytes. Twenty-three
rehashed corruption controls prove that changed quantities, duplicated warnings,
broken chains, incorrect debits, forged caps/receipts and altered bytes are rejected.
Earlier encounter/follow-up/hazard verifiers and all 4,682 archive hashes pass.

Remaining limits: next-day repair behavior, lethal warp arrival, complete session
disruption/black-hole chains, fractional/large-balance scanner purchases, all
faction/team combinations and exact RNG/MBF parity. Existing sidefile retention
covers DAT/ASC files present before each launch; it is not a general filesystem
write trace. No modern runtime, live BBS or native Windows acceptance is claimed
by this research-only milestone.

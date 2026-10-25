# YT.EXE missiles and planetary assault

## Result and validation

Recovered the main damage loops from the previously imported YT.EXE and ran **10 additional DOS sessions** through the original local interface. `verify_evidence.py` passes **80 checks**, including four explicitly separate model checks. These check binary hashes, normal session completion, ammunition/turn accounting, printed damage against saved data, assault traces, ownership, and surviving forces. They are not 80 independent DOS runs.

The spreadsheet is a useful estimate for sector fighter damage and planetary ground bombardment, and its one-missile-per-sector-mine rule matches. Its fighter range is not a hard range; its shield coefficient does not match the recovered original ship loop. There is **no planetary assault formula in the workbook** to validate: the missile ground-force cell describes bombardment, not landing combat. Xannor's F13 attack-size helper is a separate NPC rule and was not validated here.

Original YT.EXE SHA256: `c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`. Original and experimental copies are unchanged. Ghidra project and decoded listings remain under `../ghidra-projects` and `../yt-combat/{main,sub,sub2}`. Branch target annotations normalize Ghidra segment aliases.

## DOS comparisons

All missile volleys below launch **20 missiles** against isolated adjacent-sector targets, starting with 100 missiles aboard. The game saves 80 missiles and deducts one turn per launch. Data and GAME.LOG files are under `../yt-combat/experiments/<case>/`; before.dat preserves each initial fixture. Results and hashes are in `evidence.json`.

| Case | Spreadsheet | DOS result |
|---|---:|---|
| missile-fighters: 1,000,000 sector fighters | 49,000–51,000 destroyed | **39,262 destroyed**, persisted as 960,738 remaining |
| missile-mines: 10,000 sector mines | 20 destroyed | **20 destroyed**, 9,980 remaining |
| missile-shields: fully cloaked ship, zero fighters, 1,000,000 shields | 23,000 shield damage; no cloak input | Target skipped, no shield damage |
| missile-uncloaked: same ship with cloak set to zero | 23,000 shield damage | **9,211 shield damage**, zero fighter damage |
| missile-shipfighters: uncloaked ship, 1,000,000 fighters and shields | 49,000–51,000 fighter damage; 23,000 shield damage | **35,579 fighters and 228 shields** lost |
| missile-ground-fixed: planet, 5,000 initial ground forces | 250 ground damage | **4,766 remaining** after the attack |
| missile-planet: same ground-force setup at afternoon game time | 250 ground damage | 4,781 remaining, including pre-impact lazy growth; not a clean 5,000-minus-final damage comparison |
| missile-production: zero ground defense, 100,000 starting production per category | 20,000–60,000 total production loss | **59,613.78 total production loss reported** |

The fixed-clock ground case sets DOS date 10/24/2026 and time 00:00:00 before starting, matching the fixture's update day and midnight timestamp. Only seconds of natural growth occur before impact. The initial 5,000 becomes 4,766, consistent with a random total near the helper's mean of 250. Do not read a single result as proof of a distribution or an exact 12.5 damage constant.

The uncloaked ship cases also triggered a **one-missile retaliation** from Enemy. The game separately reported 2,456 and 169 fighters destroyed aboard the attacker's ship in those two retaliations. Verification distinguishes outgoing target damage from the return fire. Cloaking is not blanket immunity: explicitly targeted retaliation hit the fully cloaked attacker.

| Assault case | Setup and DOS result |
|---|---|
| assault-win | Commit 1,000 out of 10,000 aboard against 10 defenders. Attacker sequence: 991, 990, 986, 983, 973; defenders then fall to zero. Ownership changes from player record 3 to record 2. **973 surviving attackers become the garrison; 9,000 uncommitted forces remain aboard.** |
| assault-loss | Commit 100 out of 10,000 aboard. Sensors report 100,610 defenders after lazy growth. Attackers fall to zero on the first exchange. **Ownership remains record 3, defenders remain 100,610, and 9,900 forces remain aboard.** |

Both assault sessions retain 500 turns. Thus these force-land assaults do not themselves deduct a turn in the supplied release. This is an observed rule, not classified here as a defect or a proposed balance change.

## Missile algorithms

Main launch command `1000:2059..233e`; missile routine `1f42:6c95..80b9` (module bmYT-SUB). Sector fighter calculation `7194..71f4`; mine calculation `740b..74df`; ship loop `7624..76f2`; planetary ground `7c20..7cb4`; production `7d36..7de5`.

For positive, unsaturated targets, the recovered operations are:

### Sector fighters

```
killed = 0
for each available missile:
    killed = floor(killed + RND * 5000)
    consume one missile
    if killed >= defenders:
        killed = defenders
        stop attacking this group
```

Average damage is roughly 2,499.5 per missile before caps and MBF rounding. The sheet's 2,450–2,550 coefficients bracket an average, not every possible volley. A single missile can roll near zero or near 5,000. The DOS 39,262 result directly disproves a guaranteed 49,000 minimum for 20 missiles.

### Sector mines

Destroy `min(remaining missiles, sector mines)` and consume that many missiles. This confirms I9's one-to-one rule for isolated sector mines. Surviving missiles can continue into later targets. A cell that multiplies the initial volley by every damage coefficient independently will overcount the available missiles.

### Ship fighters and shields

A normally untargeted cloaked ship is skipped; the branch also admits an explicitly selected target. The two cloak fixtures establish this distinction for the tested states, without establishing all anti-cloak/scanner interactions.

Within an eligible ship encounter, maintain cumulative fighter kills K and shield damage S. For each missile:

```
consume one missile
perform the ship mine-dropping check
K = floor(K + RND * 4001)
if RND * original_ship_fighters < K:
    S += floor(RND * 1001)
stop if both defenses have been exhausted
```

Then cap K at the original fighters and S at the original shields and save the remaining defenses. Note that the comparison uses the original fighter count and cumulative kills; it is not an unconditional fixed shield strike. With no fighters, essentially every positive fighter roll allows a shield hit, averaging about 500 shields per missile. With many fighters, shields are hit much less often initially. There is no 1,150 shield constant in this loop.

Ship fighters average about 2,000 per missile before caps, unlike sector fighters. The spreadsheet's common fighter coefficient omits that distinction. The mine-dropping side effect and retaliation were identified but their full decision rules, protected-sector behavior, and exploit chain remain separate work.

### Planet ground defenses and production

Planet loading applies lazy updates before damage. Remaining missiles first attack ground forces:

```
while ground > 0 and missiles > 0:
    ground -= RND * 25
    consume one missile
floor and clamp ground to zero
```

This supports J9's **12.5 average** before final integer conversion and caps. It is not 12.5 guaranteed damage per missile.

Only missiles left after ground defense proceed to production. Per remaining missile, each of the three production categories loses an independent `RND * 2000`. Average loss is about 1,000 per positive category, up to about 3,000 total average with all three categories still positive. Individual random outcomes are wider than the sheet's nominal 1,000–3,000 range. Production is clamped, stocks are constrained, and destruction handling follows. A 20-missile volley used entirely on ground forces does not simultaneously cause the sheet's production estimate.

As with plasma, the production loop's entry condition appears to omit ore-only production when organics, equipment, and the referenced ground-production variable are zero. That unusual case remains a static lead requiring its own DOS reproduction.

## Planetary assault

Main hostile landing dispatch: `1000:35a0..369d`. Ground battle: `1f42:8f35..932a`.

The game reloads/updates the planet, takes the integer ground-defense count, and removes the entire committed force from the player's ship **before combat**. While both sides remain positive:

```
if RND > 0.4:
    attackers = max(0, floor(attackers - RND * defenders))
else:
    defenders = max(0, floor(defenders - RND * attackers))
```

Each exchange uses a fresh draw to choose the damaged side and another draw for the damage magnitude. Approximately 60% of exchanges damage attackers and 40% damage defenders. Damage scales with the opposing surviving force. This is different from fighter combat's 5% batches, cloak modifier, and surrender threshold. No cloak modifier or surrender check appears in this ground loop.

If defenders reach zero and attackers survive, ownership changes to the attacker and surviving troops remain on the planet as its garrison. They are not refunded to the ship. If attackers die first, the original owner and surviving defense remain. The losing case does not return committed troops. The printed per-exchange trace in the two DOS cases obeys the recovered casualty bounds, and the final ownership/garrison/ship-force records match the transcript.

The captured planet still has its production and stock systems; this is capture rather than missile-style production bombardment. Broader edge cases—simultaneous exhaustion, tiny/fractional forces, maximum numeric values, interrupted combat, and concurrent ownership changes—remain untested.

## Artifacts and limits

- `fixtures.py`: builds initial missile and assault fixtures from the existing combat fixtures; requires new destination directories.
- `../yt-combat/run_session.py`: normal local sessions using the BIOS keyboard feeder. `run_clock_session.py` additionally sets the DOS date/time for the controlled ground case.
- `recovered_rules.py`: readable selected algorithms with an injected RNG. Positive, uncapped production case only; not a complete combat implementation.
- `verify_evidence.py`, `evidence.json`: repeatable inspection of the captured DOS evidence. Run from the distribution root with `python3 analysis/yt-missiles/verify_evidence.py`.
- `../ytcalc/extracted.json`: prior read-only spreadsheet extraction, source hash `f548b8f47268d9ad9276b58849bf81240fc75bbd89ca414d0d822195a16dae7c`. Relevant cells F9:L9 and E10. Workbook unchanged.

Original RNG seeding/state and exact MBF intermediate rounding have not been reproduced. Injected-RNG model checks establish readable arithmetic examples, not byte-for-byte equivalence with a DOS random sequence. The reverse engineering is partial; normal route interception, friendly/team exclusions, black-hole handling, NPC decisions, and retaliation require additional tests before a complete combat implementation.

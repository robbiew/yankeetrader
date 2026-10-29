# Yankee Trader 3.6 daily maintenance — recovered rules and DOS validation

Analyzed 2026-10-24. Target `YTMAINT.EXE`, revision 03/14/94, SHA-256 `8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6`. The original distribution and the earlier preserved initialized universe are unchanged.

## What is established

The economic rules below were traced in the binary and checked against unmodified DOS maintenance runs with controlled data fixtures. Xannor regeneration, revenge activation, HQ recovery/relocation, and planet recreation were also exercised. Plague and civil-war effects were observed with separate production-heavy and ground-force-heavy fixtures.

This is a usable first specification for the core economy and NPC lifecycle, **not a complete recovery of every random combat and targeting formula**. Those gaps are listed explicitly at the end.

## Method and evidence

- Imported and analyzed the executable in the existing Ghidra `YankeeTrader` project using `x86:LE:16:Real Mode`.
- Exported automatic C, disassembly, and a runtime-aware annotated listing. Automatic C remains unreliable around QuickBASIC's INT 3D/3E/3F dispatch and inline arguments. The manually interpreted listing is the primary static evidence.
- Extended the runtime decoder to recognize additional floating-stack and array argument bytes. `qb-annotated.txt` includes string descriptors and candidate MBF32 constants. Some constants are MBF64 or other data; an annotation by itself does not establish type or meaning.
- Created separate scenario directories under `experiments/`, copied original EXEs and baseline data, and modified **only copied DAT records** to establish known balances, rates, dates, defenses, and stored scores.
- Ran DOSBox Staging 0.83.0 with dummy video/audio and 200,000 CPU cycles. The emulator mounted only each scenario directory. Executables were unmodified in every run.
- Set the DOS date with `date 10/25/2026` and time with `time 00:00:00`. Captured the actual DOS date/time and program output. A preliminary hyphenated-date probe was rejected because DOS ignored the date; it is retained but excluded from conclusions.
- Preserved `BEFORE.DAT`, final `YTDATA.DAT`, logs, decoded results, and, for the repeated tax experiment, `FIRST.DAT`.
- `validate_recovery.py` passes **221 evidence checks**, including all original distribution hashes and hashes of the copied maintenance executables. The count includes individual field comparisons and integrity checks; it is not 221 independent DOS runs.

## Planet record map

All offsets are zero-based within a 137-byte record; numeric fields are four-byte MBF singles. Planet slots begin at record 4052 in the default universe.

| Offset | Meaning | Evidence |
|---:|---|---|
| 0..40 | Name, space padded | Generated records and name display |
| 41 | Last production update day | Advances to current game day |
| 45, 49, 53 | Daily ore, organics, equipment production | Independently controlled fixtures |
| 57, 61, 65 | Stored ore, organics, equipment | Measured production deltas |
| 69 | Missiles | Rate and elapsed-time tests |
| 73 | Owner/faction | Xannoron recreated with -1 |
| 77 | Ground forces | Growth and civil-war tests |
| 85 | Name length / active-name indicator | The Wanderer = 12, Xannoron = 8; controlled names |
| 89 | Last update time in minutes after midnight | Fractional minutes, from TIMER/60 |
| 113 | Plasma bolts | Large-production and rich-bank tests |
| 117 | Planet bank balance | Interest and bank-bonus tests |
| 125 | Mines | Rate and elapsed-time tests |
| 129 | Fighters | Rate and elapsed-time tests |
| 133..136 | Unmapped tail | Previously observed zero; purpose unresolved |

The planet's sector association is maintained through sector records: sector offset 93 contains a planet-slot reference. **Offset 85 in a planet is not a sector number**; its meaning differs from the same offset in a sector, where it is defense ownership.

## Planet update rules

Static evidence: main-code segment `1000`, principally 100A–1CBC. These equations describe the ordinary update before plague/civil-war damage and later NPC combat. They use real-valued arithmetic for readability; a faithful port will also need to reproduce original MBF rounding.

Let `P1,P2,P3` be the old daily cargo production, `B` the old bank balance, `G` the old ground forces, and `S=P1+P2+P3`.

### Elapsed time and the ten-day limit

```
elapsed = current_day - last_day + (current_minutes - last_minutes) / 1440
D = elapsed
if elapsed < 0 or elapsed > 10:
    D = 10
```

The upper limit is ten days of catch-up, with the record's timestamp then advanced to now. **Negative elapsed time also becomes ten days**, rather than zero. The clock-rollback fixture confirmed this behavior.

There is no forced whole-minute or whole-day rounding. The controlled runs advanced about 0.05 emulated seconds before this update, producing small fractional inventory amounts. Validation uses the saved update timestamp to calculate the actual interval.

Evidence: 124B–12D2; half-day, two-day, twenty-day, and future-clock fixtures.

### Ordinary production and bank bonuses

Daily rates are derived from the **old**, pre-growth cargo rates and bank balance:

| Resource | Base daily rate | Additional daily rate from old bank B |
|---|---:|---:|
| Ore | P1 | B / 10,000 |
| Organics | P2 | B / 20,000 |
| Equipment | P3 | B / 30,000 |
| Fighters | S | B / 500 |
| Missiles | floor(S / 2,500) | B / 100,000 |
| Mines | floor(S / 25,000) | B / 250,000 |
| Plasma bolts | floor(S / 100,000) | B / 25,000,000 |

For each resource, `new_stock = old_stock + (base_rate + bank_bonus) * D`.

The base daily weapons rates are truncated **before** multiplication by elapsed time. Stocks themselves may remain fractional. A half-day fixture with S=6,500 produced about one missile: `floor(6500/2500) * 0.5 = 1`, not 1.3. A large-production fixture with S=150,000 produced about 150,000 fighters, 60 missiles, six mines, and one plasma bolt in one day.

Evidence: 104E–1246 (read stocks and construct base rates), 12E4–13C7 (bank bonuses), 1464–1571 (stock increases).

### Interest and ground-force growth

```
new_bank = floor(B + B * 0.01 * D)
new_ground = floor(G + G * 0.01 * D + (B / 10000) * D)
```

Bank bonuses use B **before interest**. The bank and ground-force values are truncated; ordinary resource stocks are not truncated at this stage.

Interest is linear within an elapsed-time update. Separate updates compound because the next update starts with the new bank balance:

| Starting balance | Update pattern | Result |
|---:|---|---:|
| 1,000,000 | One one-day update | 1,010,000 |
| 1,000,000 | One two-day catch-up | 1,020,000 |
| 1,000,000 | Two successive one-day updates | 1,020,100 |
| 1,000,000 | Twenty days missed | 1,100,000 because D is capped at 10 |

This is more precise than the manual's claim of interest “compounded by the minute.” It does not internally simulate a separate compounding step for every missed minute.

Ground-force control: G=100, B=1,000,000 became 201 after one day and 302 after two days, before any NPC damage. The zero-bank test planet was attacked later by Xannor, so its final ground count was explicitly excluded from the production comparison.

Evidence: 13CC–1454; bank bonus preparation at 1391–13A3.

### Surplus and natural cargo-production growth

After adding this update's goods, for each cargo type:

```
if new_stock > 10 * old_daily_rate:
    daily_rate = new_stock / 10
else:
    daily_rate = old_daily_rate
new_daily_rate = daily_rate * (1 + 0.01 * D)
```

A minimum cargo rate of one appears in the static code at 15E2–1649; the zero-rate boundary was not separately tested.

The surplus boost can be large. With old rates 1,000 / 2,000 / 3,000 and 20,000 units of each cargo already stored, a one-day run produced new rates of approximately **2,121 / 2,222 / 3,030**. These are based on the newly replenished stocks, then the 1% natural growth factor.

A two-day catch-up applies a 2% linear increase, not two compounded 1% steps. Bank bonuses influence future rates indirectly when they raise stocks past the surplus threshold; they are not simply added permanently to the displayed base rates.

Evidence: 14B9–1510 and 1576–15E0.

## Overcrowding: plague and civil war

Static event selection is at 164E–170A; damage and reporting are at 1719–1B24.

The listing indicates two separate tests, using post-growth production and ground forces:

- Plague candidate: compare a random fraction of total production against another random value scaled by 1,000,000 plus 100,000.
- Civil-war candidate: a random fraction of ground forces exceeds 1,000,000. This can override the plague candidate.

These draw/comparison interpretations are static findings. Exact event probabilities have **not** been statistically or instruction-by-instruction validated.

DOS event controls confirmed:

| Fixture | Observed result |
|---|---|
| 1,000/day per cargo, 100 ground forces | No event on the test planet |
| 100,000,000/day per cargo, 100 ground forces | Plague |
| 1,000/day per cargo, 100,000,000 ground forces | Civil war |
| Same large ground force plus 1,000,000,000 credits | Civil war and a large bank debit |

Both plague and civil war randomly reduce cargo production and ground forces. Civil war can also spend bank credits. Excess cargo stocks are reduced when they exceed ten times the reduced production rate.

For example, the plague fixture's post-growth total production of 303,000,000 fell to approximately 158,411,800; its ground forces fell from 101 to about 27.47. The rich civil-war fixture spent 779,226,240 credits from the post-interest bank. These are captured outcomes, **not fixed penalties or averages**.

The civil-rich log repeated the same insurrection expenditure in another planet's report; do not interpret repeated log text as an independently verified debit. The data-file comparisons are authoritative.

## Port taxes and the repeat-run bug

Static tax loop: 3F73–40D6. Port treasury is at offset 89.

For nonnegative treasury balances, ports **2 through 1000** pay:

```
tax = floor(treasury / 10)
new_treasury = treasury - tax
```

**Earth, port 1, is excluded from this loop.** There is no elapsed-day multiplication in this tax calculation.

| Port | Starting treasury | After first maintenance | Same-day rerun |
|---:|---:|---:|---:|
| 1 (Earth) | 1,005 | 1,005 | 1,005 |
| 3 | 9 | 9 | 9 |
| 4 | 10 | 9 | 9 |
| 5 | 19 | 18 | 17 |
| 6 | 101 | 91 | 82 |
| 7 | 1,005 | 905 | 815 |
| 8 | 1,000,000 | 900,000 | 810,000 |

The first run reported 100,112 credits in taxes and 10,010 hired mercenaries. The second reported 90,100 in taxes and 9,010 mercenaries. The later [Mercenary maintenance recovery](../yt-mercenary-maintenance/RECOVERY.md) establishes the two rounding stages and group allocation with isolated and chained runs; final force counts also reflect later combat and merging.

### Maintenance is not idempotent

At 0351–0384, the program checks the saved maintenance day and prints `Maintenance not needed!` when it matches today. **It then falls through into the rest of maintenance.**

The same-day tax rerun confirmed that it still taxes, moves/attacks with NPCs, and generates a scoreboard. This contradicts the old change-history claim that maintenance only runs once per day.

A modern version needs an explicit decision about reproducing or fixing this behavior. A daily execution guard should not be assumed to exist in the DOS version.

## Xannor rules

### Groups, stored pointers, and regeneration

There are 20 group slots: one headquarters group and 19 mobile groups. Sector records 1..20 use offset 105 as group-location pointers. The maintenance phase caches, merges/clears duplicate or invalid group entries, operates on the groups, and writes the updated state back.

The strongest active player's **stored score at the start of maintenance** controls regeneration. The fixtures deliberately supplied this field; the scoreboard later recalculates scores and is not the value used for this test.

Let `T` be that top stored score and `X` the cached aggregate group strength:

```
regen = floor(T / 500)
if X > floor(T / 100):
    regen = 0
```

Regeneration is added to the headquarters group. The comparison is strict `>`; this is a regeneration cutoff, not a hard force ceiling. A permitted regeneration step can take the total above the cutoff.

Five controlled score fixtures began with total Xannor strength 10,000:

| Top stored score | Cutoff floor(T/100) | Reported regeneration | HQ strength change |
|---:|---:|---:|---:|
| 100,000 | 1,000 | 0 | 0 |
| 999,999 | 9,999 | 0 | 0 |
| 1,000,000 | 10,000 | 2,000 | +2,000 |
| 1,000,500 | 10,005 | 2,001 | +2,001 |
| 10,000,000 | 100,000 | 20,000 | +20,000 |

Final **total** force counts include later combat losses and cannot be used alone to measure regeneration. In the matched runs a 252-fighter mobile group was lost in later action; the direct HQ deltas above separate that loss from regeneration.

Evidence: 2436–24EE (top score and base regeneration), 26C9–29AF (group loading/normalization), 29B1–2A3A (total and cutoff), 2AA6–2ABF (HQ addition).

### Targeting, revenge, and HQ recovery

Confirmed behaviors:

- Maintenance selects a top player for special targeting. With an uncloaked `Test Captain` fixture, the log explicitly reported `Group 20 will hunt for Test Captain`.
- A revenge victim pointer is stored in sector 21, offset 105. Setting it to an active player in sector 8 activated `Xannor REVENGE!`; maintenance cleared the pointer afterward.
- Static code sets the random search-loop bound to **25 in revenge mode versus 1 normally** at 3234–3262. This differs from the change history's “50 times” description. Activation and pointer consumption were dynamically verified; the precise number of RNG/search calls was not instrumented.
- The code contains additional target preferences for groups 16–20, plus special behavior for weak groups; their full decision tree has not yet been independently validated.
- If another faction holds HQ, the Xannor attempt to reclaim it and can relocate. Replacing HQ ownership with mercenaries and 100 defenders produced an explicit successful reclaim report and moved HQ from sector 1114 to sector 818 in the test universe.
- Xannor move between sectors, hit mines, and attack defenses, players, and planets. Their attacks occurred during the economy fixtures, so final ground-force counts were checked for interference rather than assumed to represent production alone.

Static evidence: 2AC4–2F3F (HQ handling), 2FAB–30EA (revenge pointer), 311E–3E2D (mobile-group targeting/actions).

### Recreating Xannoron

Clearing both the HQ sector's planet reference and the old planet's active-name field caused the original program to report that the Xannor had made a planet and to recreate Xannoron.

Observed initial values for the rebuilt planet:

- Name `Xannoron`, name length 8, owner -1.
- Daily ore, organics, equipment production **100,000 each**.
- Zero cargo stocks, missiles, mines, and fighters in the measured recreated record.
- Randomized ground forces and bank balance: 175 ground forces and 3,980,002.5 credits in this run.

The static creation code indicates ground forces from `floor(RND * 250)` and bank balance from `RND * 10,000,000 + 100,000`, with BASIC rounding/conversion. The observed sample fits those ranges; their full distributions have not been measured.

A first missing-planet probe only cleared its name length while leaving the sector reference alive; it did not recreate the planet and is excluded as an invalid deletion fixture. The corrected experiment is `missing-xannoron-v2`.

Evidence: 20AD–2331, especially 21AB–228C.

## Maintenance order

The main path runs approximately:

1. Check/report maintenance day, open data, and prepare/protect bookkeeping.
2. Compress/rotate messages and newspaper data.
3. Load players, delete qualifying inactive entries, and reduce cloak charge.
4. Update ports, handle port overcrowding, and switch selling commodity toward the greatest stock.
5. Update all active planets, then apply overcrowding events.
6. Move/regenerate The Wanderer and recreate Xannoron if needed.
7. Select the top player, process Xannor regeneration, HQ recovery, revenge, movement, and attacks.
8. Collect port taxes.
9. Maintain mercenaries, rebuild their planet if missing, hire groups, and perform their actions.
10. Run the super-planet lottery, regenerate scoreboard, and finish.

Only the selected economic and Xannor rules above have been validated in detail. Player deletion, cloak decay, port growth/plague probabilities, Wanderer behavior, the full mercenary algorithm, and the lottery need their own focused recovery passes before claiming complete parity.

## Reproduction and files

- `../ghidra-projects/YankeeTrader.gpr`: saved project containing the initializer and maintenance executable.
- `qb-annotated.txt`: runtime-aware annotated listing; primary static evidence.
- `decompiled.c`: raw automatic C, with known dispatch/decode limitations.
- `recovered_rules.py`: readable reconstructed ordinary planet/tax/regeneration equations; excludes random events, NPC combat, and bit-exact MBF arithmetic.
- `validate_recovery.py`: checks preserved DOS evidence without rerunning/mutating scenarios.
- `experiments.py`, `more_experiments.py`, `event_experiments.py`, `xannor_events.py`: controlled scenario setup/runners.
- `experiments/*/BEFORE.DAT`, `YTDATA.DAT`, `MAINT.LOG`, `results.json`: per-scenario evidence. DOS truncates the date/time log names to `MAINTDAT.LOG` and `MAINTTIM.LOG`.
- `validation-results.json`: all checks and qualifications.

Safe evidence revalidation (first prepare the disposable workspace described in [the recovery README](../README.md)):

```
python3 /tmp/yankeetrader-recovery/analysis/yt-maint/validate_recovery.py
```

Scenario creation intentionally refuses existing directory names, preserving the collected evidence. Use a fresh name when rerunning an experiment.

## Remaining precision work

1. Recover/instrument the QuickBASIC RNG and exact MBF32/MBF64 operation order for bit-for-bit results.
2. Validate the exact plague/civil-war probability comparisons and damage distributions.
3. Recover each Xannor targeting/combat branch, cloak detection, mine damage, and HQ relocation criteria beyond the demonstrated path.
4. Implement the separately recovered [Mercenary hiring and route rules](../yt-mercenary-maintenance/RECOVERY.md), retaining the documented RNG/lifecycle boundaries; recover the other maintenance phases listed above.
5. Decide which original defects to preserve behind a compatibility option: same-day reprocessing and ten-day rewards after clock rollback are now demonstrated behaviors, not assumptions.

## Project decision: fixes in the modern version

The user subsequently specified that known defects and exploits should be fixed. This supersedes the compatibility-option suggestion above. Preserve original behavior for research, and track deliberate corrections in [Issues and exploits](../ISSUES_AND_EXPLOITS.md) and the [working plan](../RECONSTRUCTION_PLAN.md).

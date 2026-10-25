# Planet management and economy

Recovered from the original Yankee Trader 3.6 YT.EXE, with controlled DOSBox sessions. This completes the first pass through planet creation, cargo/equipment transfers, production investment, banking, ordinary landing permissions, garrison management, and relocation. It builds on the earlier [maintenance recovery](../yt-maint/RECOVERY.md) and [planetary assault recovery](../yt-missiles/RECOVERY.md).

Validation: **190 checks pass across 24 original DOS sessions**. These are field, action, model and integrity checks, not 190 independent playthroughs. Original executable hashes still match the archived inventory.

## Model and storage

There is no independently stored colonist population in these recovered paths. The planet owns three daily cargo-production rates directly. Planet records use the existing 137-byte layout:

| Offset | Value |
|---:|---|
| 41 / 89 | Last update day / minutes since midnight |
| 45 / 49 / 53 | Ore / organics / equipment production |
| 57 / 61 / 65 | Corresponding cargo stocks |
| 69 / 113 / 125 / 129 | Missiles / plasma bolts / mines / fighters |
| 73 / 77 | Governor player/faction / ground forces |
| 85 | Active name length |
| 117 | Bank balance |

Sector offset 93 references the planet slot. Human governor values refer to player records; owner 0 is ungoverned. Unused fields can retain earlier buffer contents: a newly created planet is not an all-zero record with just a few populated fields.

## Planet creation

Main `1000:3515..39ae` implements `L`. Without an existing planet, it quotes **25,000 credits**, checks affordability, asks Yes/No, searches for a free planet record, and obtains a confirmed name before committing. Activity is tested by name-length field 85. In the default layout its search starts at planet slot 2, leaving The Wanderer's slot 1 outside the ordinary search.

The successful `planet-create` fixture allocates slot 3 because slot 2 is occupied, names it New Eden, charges exactly 25,000, and links it to sector 100. Initial base production is **1 ore, 1 organics, 1 equipment per day**; initial warehouses contain **10 of each** and **30 fighters**. It starts with **one ground force**, its creator as governor, zero bank, missiles, mines, and plasma bolts. Later lazy updates introduce small fractional changes in saved snapshots. The ship's 500 turns remain 500. There is no separate carried Genesis Device consumed by this purchase path.

`planet-poor` rejects 24,999 credits. `planet-full` fills all eligible activity markers and confirms that no planet is allocated or money charged when all slots are taken. Creation returns to the sector interface rather than automatically landing on the new planet.

## Landing, ownership, and shared access

The landing handler calls permission routine `1f42:8c7f..8f32`, which also updates the planet. In controlled tests:

- The governor can land on a defended planet.
- Another player with the same nonzero team can land and use its bank.
- A foreign non-team player is denied by positive ground forces and offered a separate force-landing assault.
- A planet with zero ground forces admits a foreign player, who can withdraw its entire bank without becoming governor.

The bank and cargo operations are therefore shared facilities protected by landing permission, not private accounts restricted to the governor. The last case is an explicitly documented game rule, not itself an exploit. `planet-foreign` uses two team-zero players and is denied: two players having no team does not make them teammates. NPC and invalid/dead-governor branches remain in the static listing; their complete adoption/revolt rules are not asserted by these ordinary access tests.

`F` misleadingly asks how many ground forces to “drop,” but accepts a **target planetary garrison**, not a signed transfer amount. Starting with 100 on the planet and 15 aboard, target 90 yields 90 on the planet and 25 aboard. Target zero takes all 115 aboard and clears the governor. Negative target -10 is rejected without changing forces. Positive garrison writes the acting player as governor (`1000:3389..3512`).

## Taking and depositing resources

`A`, also the empty planet-command default, takes whole available fighters, missiles, mines, and plasma bolts separately from cargo capacity. It fills remaining cargo holds with **equipment first, then organics, then ore** (`1000:4551..4955`). In `planet-takeall`, 100 holds already contain 10 ore, 20 organics, 30 equipment: the 40 free holds receive equipment, while the ship also collects 600 fighters, 70 missiles, 80 mines, and 90 plasma bolts. A fractional fighter remainder stays on the planet.

The transfer submenu (`1000:4958..4eec`) supports cargo, fighters, missiles, mines, and plasma bolts:

- `T;C` transfers all three cargo inventories and empties the ship's holds.
- `T;B`, `T;S`, and `T;M` transfer all carried plasma, missiles, and mines.
- `T;F` asks for a fighter quantity. Sending 123 moves exactly 123.

Cargo deposit can immediately raise productivity. For a cargo type, if the combined warehouse stock plus incoming cargo exceeds ten times its current base rate, the code assigns **floor(combined stock)/10 + 1** as the new base rate. This is distinct from ordinary time-based growth. Depositing 10/20/30 into warehouses initially holding 100/200/300 changes rates from 10/20/30 to **12/23/34**, with all cargo conserved apart from separately measured elapsed production. The surplus is not consumed by this rate adjustment.

Tests exercise cargo conservation, each weapon inventory, shared landing access, and hold priority. They do not establish safety under simultaneous sessions; multi-record transfers need atomic writes in Go.

## Spending to improve productivity

`$` (`1000:50ec..5461`) floors the requested credit expenditure, requires at least one credit and sufficient funds, divides it by 250, and adds the quotient to **each** cargo rate. It then deducts the original expenditure.

```
spend = floor(input)
increase_per_cargo_type = spend / 250
ore_rate += increase_per_cargo_type
organics_rate += increase_per_cargo_type
equipment_rate += increase_per_cargo_type
ship_credits -= spend
```

There is no requirement to buy whole 250-credit blocks: **one credit adds 0.004 to each rate**, and 251 credits add 1.004. These are persisted fractional rates, not merely display estimates. Printed fighter/weapon increases describe changes in derived daily production; buying a rate increase does not immediately grant those weapons.

## Bank transfers and interest

`B` (`1000:4f53..50e9`) asks for the **desired final account balance**. With cash C, bank B, and requested integer target T:

```
require 0 <= T <= C+B
bank = T
cash = C+B-T
```

Blank input cancels. Target zero withdraws everything. Starting with 100,000 aboard and 10,000 in the bank, target 15,000 leaves 95,000 aboard; target zero leaves 110,000. Negative and excessive targets are rejected. Teammate and unguarded-foreign withdrawal fixtures each recover the full 10,000 while leaving governor 3 unchanged.

Planet updates occur lazily during landing, menu processing, and economic operations (`2e79:0a97..0fd2`). The bank accrues `floor(B + .01*B*D)` for elapsed days D; time rollback or more than ten days becomes ten days. Interest is linear within one update and compounds across separate updates, rather than simulating every missed minute. A half-day fixture with 1,000,000 in the bank pays **5,001 credits of interest** before withdrawal: the additional credit comes from the roughly fourteen seconds elapsed before the command. Banking also grants the production bonuses recovered in the maintenance report.

The in-game update and YTMAINT have separate implementations. The in-game routine grows base cargo rates before adding new production and applies its surplus adjustment afterward; maintenance's previously recovered order differs. Use the `planet-lazy-production` fixture to distinguish the two rather than assuming one routine can be substituted for both. Exact MBF rounding and every multi-update boundary are still compatibility concerns.

## Confirmed money-rounding exploit

`planet-bank-large` starts with exactly **100,000,000 credits** aboard and an empty bank. Setting the bank to one credit and logging out leaves **100,000,000 aboard plus one in the bank**. Player cash is computed with higher precision during play, then rounded to MBF single precision when persisted; at this magnitude the one-credit debit disappears.

`planet-bank-large-relogin` starts from the **exact, unmodified persisted world** of that first session, advances DOS time to 00:01:00, and sets the target bank balance to two. It leaves **100,000,000 aboard plus two in the bank**. The small bank balance earns zero whole interest credits across this interval, so the additional money is not interest. Both sessions perform normal quit/save. This demonstrates a repeatable way to increase saved total money across logins. It does not establish the maximum farming rate or behavior at every balance.

Use exact integer/fixed-point money and one atomic debit/credit operation in Go. Do not retain MBF single storage for spendable balances. This is separate from the negative-time defect: an earlier probe resetting DOS time to midnight was excluded because that caused a clock rollback; the validated second session uses a later clock.

## Relocation

Planet `!` traces a shortest route and quotes **10 turns per hop**, then asks for confirmation (`1000:2fb4..3386`). `planet-move-yes` moves the planet and ship from sector 100 to 101, clears the old sector link, sets the new link, preserves stocks/ownership, and reduces turns 500→490.

The step helper `1f42:80c2..8568` tests a random stress threshold of 0.995, suggesting approximately **0.5% explosion risk per step**; that probability is static recovery, not an empirical distribution test. Collision with an occupied destination forces the explosion branch. `planet-move-collision` destroys the moving planet, leaves the destination planet intact, leaves the ship in sector 100, and destroys **326 ship fighters** in the recorded roll. The failed step leaves turns at 500. This is destructive movement behavior described by the original manual, not evidence that both planets must be destroyed.

Intermediate hostile sectors, NPC special cases, random explosion frequency, and exact fighter-loss RNG remain to be tested. The exploratory `planet-move` run never supplied a valid confirmation and is excluded from completed-action assertions.

## Evidence and implementation

`fixtures.py` builds only isolated copied saves and refuses to overwrite existing directories. `scenarios.json` records exact key streams, source fixtures, snapshot hashes, date/time, and evidence status. `validate.py` checks the saved data and logs from the counted scenarios. Experiments are under `../yt-combat/experiments/planet-*`; six preliminary menu/access/clock probes are excluded from the main validation set. Some sessions terminate at the emulator deadline after actions have persisted; the validator checks concrete completed actions rather than equating timeout with a successful logout.

Use integer or fixed-point money in Go, fractional production rates, explicit target-balance/target-garrison prompts, and atomic conservation across ship/planet changes. Keep routine access and intended collision consequences distinct from defects. The modern rules must also reject negative elapsed time rather than awarding ten days of production, and check current landing permission during each mutation so a stale session cannot retain access after a capture.

### Reproducing the controlled runs

Run `fixtures.py` from the YT36 root only when its destination fixture directories do not already exist. Preserve existing evidence. Use the existing `run_clock_session.py` with a fresh destination, source fixture, recorded keys and a 45-second deadline (50 for creation/movement). DOS date is 10/24/2026; default time is midnight. After `planet-bank-large` completes, `prepare_relogin.py` creates the second fixture from its exact save. Set `YT_DOS_TIME=00:01:00` for `planet-bank-large-relogin`. The runner now supports that time override; existing experiments retain the midnight default.

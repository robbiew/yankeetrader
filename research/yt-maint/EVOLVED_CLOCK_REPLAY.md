# Before-only replay of evolved clock/date children

The four [clock/date control profiles](EVOLVED_CLOCK_CONTROLS.md) now have a
separate before-only replay. All **144 complete comparisons / 864 files** match
byte-for-byte, with **1278 independent helper/final RNG-state checks** for the
new children. No field, timestamp, raw numeric-zero residue or public/private
side file is masked. This extends the [three-day midnight replay](EVOLVED_CHAIN_REPLAY.md)
without changing its API or admission guards.

## Inputs and modeled handoffs

The public API accepts the original November 2 three-file before-world and three
immutable day-input structures. The first day is computed by the existing
convergence profile. Each child then receives that prior model's complete six-file
object: data, names, public/yesterday/private journals and scores. No captured
child-before or child-after file is opened during synthesis.

Inputs extracted from source-qualified observations retain calendar returns,
raw TIMER values, helper caller order and independent publication text clocks.
The startup seed field is derived from the actual startup TIMER, not an observed
RNG state. All observed `rng_raw` values are discarded by extraction; changing
those witnesses cannot change inputs or modeled output. Witnesses are checked
only after the complete three-stage prediction exists.

Three independently observed clock streams per profile are replayed. Both new
children are compared against all six native modes only after their entire chain
has been calculated: four profiles × three streams × two children × six targets.
The existing original prefix is also audited, without counting it again in the
864-file new-child inventory. No new cache probe is claimed for these captures.

## Economy, calendar and exact source clocks

The separate port/planet modules admit only measured date handoffs and named,
bounded before contexts. They retain the source arithmetic order: single rate
products, wider cargo sums, stock-derived rate promotion, rounded source floors,
fractional elapsed minutes and the ten-day cap. The noon first child advances
about 1.5 days; its next midnight advances about half a day. Second-two keeps the
BIOS-quantized fractional time. Eleven-day and sixty-day gaps both cap economy
at ten days while keeping their distinct actual helper clocks and RNG streams.

The original saved base year remains 2026. January 1/2, 2027 publish serial days
366/367, with actual Gregorian dates in the separate news/score writers. Rates
above the old profile's 40000 ceiling are bounded explicitly; the native 65528
long-gap rate is admitted. Selected plague/civil-war damage, unknown resources,
extra active slots and arbitrary-world economies still fail closed.

## Composed combat and publication

| Profile | Child 1 physical Xannor | Child 2 physical Xannor | Child 2 score |
|---|---:|---:|---:|
| Second two | 10000 | 9994 | 999400 |
| Noon | 8300 | 8300 | 830000 |
| Eleven-day catch-up | 10000 | 10000 | 1000000 |
| New Year | 10000 | 9638 | 963800 |

Source-ordered route actions select the attacks; target saves/public summaries
never choose their branches. Fourteen fatal Wanderer attacks consume nineteen
of 250 post-economy ground and 1700 Xannor fighters. Four fatal Base attacks
consume five of 194650 ground and 362 fighters. Each actual positive-ground loop
advances the independently modeled RNG. Fatal ground combat updates shared
pursuit, clears the group, and skips later route processing. Neither defending
planet exhausts ground or loses its title.

The six-fighter mine encounter derives helper roll 223, caps the hit at remaining
force and consumes one mine. The public header prints the original force six,
not the uncapped roll. Mine death clears the group without inventing a shared
pursuit update. The source initial-mine loop still determines how many helper
calls occur; only positive effective hits consume mines.

The consumed mine's numeric zero is also byte-exact. Immediately before the
`1 + (-1)` decrement, the source evaluates physical record `51 + sector` for
random-file I/O. The recovered BRUN single-add cancellation clears only the FAC
exponent, retaining that preceding mantissa. For sector 980 the replay computes
`mbf(1031)` and clears its exponent, rather than injecting the captured zero.
A second-sector regression distinguishes the operation rule from a fitted literal.

The New Year child also exercises a repeated group-20 endpoint at sector 439.
Its no-hop path skips the original movement/deposition block; the prior mine
remains one. A genuine arrival still increments the previous mine count. This
new source branch is confined to the new profile; earlier published profiles
remain unchanged.

Auxiliary writers check that fatal public losses reconcile with physical force,
then derive scores from surviving deployments. Actual surviving home names,
links and ownership are checked. Names stay unchanged, private output stays
empty and yesterday news is the prior modeled public journal. Independent news
and scoreboard clocks are retained. Previously lost fighters are not restored
or announced again on the next day.

## Evidence and verification

The frozen 48-run corpus and its manifest are unchanged. Original code and
retained evidence are authoritative, including:

- [Mobile route/mine evidence](../yt-xannor-mobile/RECOVERY.md), including source
  mine helper `71af`, its `7312` random caller and fatal return guards. The
  [retained phase read](../yt-xannor-mobile/rea/phase-paths.json) at `0x172f6`,
  length 245, covers the FAC/decrement ordering (Evidence
  `ev_2cb47e5200f5cbb70fcc3fa1384a65e4ccfd9ae452e788386014b1dd57b4fe11`).
- [Retained chronology read](chronology-native/rea.json) at `0x139d4`, length
  1116, covers the no-successor guard and endpoint mine increment (Evidence
  `ev_658ad14a8bd6dcde639d4f4ed3d0b1d6a29c37ce681e7e947b659598d786bae5`).
- [Positive-ground assault evidence](../yt-xannor-planets/RECOVERY.md) and the
  complete retained [Wanderer battle read](wanderer-encounter/native/rea.json).
- [Initializer native byte contracts](../yt-initializer-replay/native-contracts.json),
  including the original BRUN single-add exact-cancellation path. These contracts
  are archived byte/disassembly evidence, not a new execution trace.
- [Existing evolved-home source read](evolved-replay-native/rea.json).

Portable tests cover complete comparisons, precise target-read ordering, actual
modeled object handoffs and synthetic marker propagation, all helper/final RNG
witnesses, poisoned observed states, malformed clocks/callers, unknown worlds,
source-calendar order, casualty/news/score conservation and raw zero derivation.
The independent capture verifier still authenticates all 48 launches and all
288 before-file inheritance links. Historical three-day replay guards/tests
remain unchanged.

```sh
python3 scripts/verify_maintenance_evolved_clocks.py
python3 scripts/replay_maintenance_evolved_clock_records.py
python3 scripts/test_replay_maintenance_evolved_clock_ports.py
python3 scripts/test_replay_maintenance_evolved_clock_planets.py
python3 scripts/test_replay_maintenance_evolved_clock_aux.py
python3 scripts/test_replay_maintenance_evolved_clock_npcs.py
python3 scripts/test_replay_maintenance_evolved_clock_records.py
```

README, plan, validation ledger and CI are updated in this milestone. Production
Go, dependencies, save 35 and `qb36-v1` generation fingerprints do not change.
These are bounded research comparisons; they do not establish arbitrary-world
maintenance, a general MBF emulator, live BBS acceptance or native Windows
crash durability. The next expansion should first acquire evolved foreign-force
and surviving-combat handoffs, rather than repeat the completed clock matrix.

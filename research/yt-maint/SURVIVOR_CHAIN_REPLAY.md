# Before-only replay through both added survivor days

The four [longer survivor control chains](SURVIVOR_CHAIN_CONTROLS.md) now replay
from one original before-world through **all five days, November 2–6, 2026**.
The two added children match **144 complete comparisons / 864 files**, with
**1182 independent new-stage RNG-state audits**. All **63 new tests** pass.
No timestamp, raw numeric zero, casualty counter or deployment alias is masked.

## Five inputs and complete modeled handoffs

The public API accepts the original three before-files plus five immutable
source-clock input structures. Exact fingerprints select three original occupied
worlds or the original convergence world. The existing combat or second-two clock
profile calculates the first three days. Its modeled November 4 output object
feeds November 5, whose complete modeled object feeds November 6.

All five days exist before the first expected new-child file is opened. The
core reads only immutable original YTMAINT bytes, never a captured child-before,
child-after, transcript, probe, recipe or observed RNG state. Comparison-side
loaders are separate from synthesis. Object-identity spies, modeled marker
substitution and file-read bans test the actual prefix-to-child handoff rather
than assuming it from an API name.

Raw `rng_raw` witnesses are discarded during source extraction; poisoning them
cannot change typed inputs or predicted output. Every helper old state and final
scoreboard state is checked afterward, including the first three prefix days.
The **1182** count covers only the two new children across the three independent
observed streams per profile; the already established prefix is not counted again.

Admission remains explicit: original input fingerprints, five consecutive dates,
measured days 309/310 for the new children, midnight clock bounds and actual
three/four active-planet inventories. The mine profile requires its measured
second-two prefix and cannot substitute the noon or plain-midnight profile.
Unknown worlds, mutable/malformed arrays, reordered calendars, incorrect source
caller labels and unconsumed helper clocks fail closed.

## Economy and later selected combat

The new port and planet modules preserve the existing source arithmetic order,
raw time fields and retained reserved-record bytes. Ordinary slot 2 admits either
neutral Route Haven or friendly Convergence Haven in its actual context. Existing
homes retain their names, links and ownership without consuming creation clocks.

| Profile | November 5 physical force | November 6 physical force |
|---|---:|---:|
| Mercenary survivor | X4966 / M97337 | X2433 / M93846 |
| Planet survivor | X470 | X400 |
| Neutral survivor | X10000 + neutral37 | X8575 + neutral37 |
| Mine survivor | X9176 | X9176 |

The November 6 Mercenary profile derives eighteen earlier Xannor-phase defensive
battles, losing **2533 Xannor / 3491 Mercenaries**. The later Mercenary movement
phase starts at **93846** and retains that force through four activations; it
invents no second combat loss. The same mutable descending scan gives four
activations on November 5 too. Source-derived casualties and subsequent RNG
advancement agree with every independent helper/final witness.

The newly selected fatal sector-defense branch updates shared pursuit to the
actual encounter sector. The existing occupied source model already expressed
this rule; the new survivor caller now composes it explicitly. Original
`788c–788f` writes the source argument passed by the main caller. Without this
update, later groups take different routes and leave helper clocks unused.
The regression derives all eighteen later attacks from the encounter itself,
not from a constant expected target or captured after-state.

The remaining profiles derive the captured fatal planetary outcomes: Route Haven
loses incoming Xannor forces **146** then **70**; the neutral profile's Wanderer
attacks total **1425** on November 6; the mine profile's total **818** on November
5. Ground production precedes actual source-loop spending, preserving exact
planet records and the surviving titles. No unselected mine damage or resource
pickup is fabricated merely because mines and stored fighters exist.

## Physical force, aliases and publication

The stale group-8 pointer 109 in the modeled November 4 parent has no physical
Xannor force. The existing cache rule normalizes it from that modeled world,
then the new allocation derives two fighters and pointer 328. No captured cache
array supplies those values. Final aliases at 1436 (groups 2/19) and 2369
(groups 13/15) remain exactly as written by the original phases; a shared physical
deployment is not multiplied or canonicalized away.

Original public literals retain the zero casualty column:

```text
 *** Mercenaries: lost 1, dstrd 0 (Xannor ftrs dstrd)
```

The formatter keeps raw printed damage counters separate from capped physical
casualties and checks conservation for each owner. Scores derive from actual
surviving physical forces, with the Mercenary leader denominator where applicable.
Names remain unchanged, private mail remains empty, yesterday news is the prior
modeled public journal and inactive human ranks remain correct.

Neutral-survivor November 5 admits NEWS **00:00:00** and SCORE **00:00:01** from
separate explicit source calls. Its other new publication clocks are midnight.
The model does not copy the news clock into scores or widen historical APIs.
All five auxiliary files match the native files completely.

## Reused evidence and verification

The retained [foreign-defense read](../yt-xannor-mobile/rea/phase-paths.json)
at `0x17776`, length 370, includes the fatal pursuit write (Evidence
`ev_f347a1d79af5cfb2b7c955ceb51da9ee0acd852796b3d2eb1def1acf67c44c16`).
The [main caller read](chronology-native/rea.json) at `0x139d4`, length 1116,
contains the call passing the shared argument (Evidence
`ev_658ad14a8bd6dcde639d4f4ed3d0b1d6a29c37ce681e7e947b659598d786bae5`).
Existing economy, cache, ground and Mercenary evidence is reused. No new emulator
capture, native byte query or provider installation was needed for integration.
All raw control corpora, manifests and historical profile APIs remain unchanged.

The **63 tests** comprise four port, four planet, seven auxiliary, nineteen NPC
and 29 five-day tests. They cover complete equality, every helper/final witness,
read bans and exact handoffs, malformed/unknown input rejection, independent
publication clocks, zero-column casualties, fatal-defense pursuit, four later
Mercenary activations, physical scores, persistent mines and authentic aliases.
Synthetic primitive checks supplement the captured cases without claiming new
DOS runtime coverage. Relevant historical three-day profiles remain unchanged.

```sh
python3 scripts/replay_maintenance_survivor_records.py
python3 scripts/test_replay_maintenance_survivor_ports.py
python3 scripts/test_replay_maintenance_survivor_planets.py
python3 scripts/test_replay_maintenance_survivor_aux.py
python3 scripts/test_replay_maintenance_survivor_npcs.py
python3 scripts/test_replay_maintenance_survivor_records.py
```

README, plan, validation notes and portable CI are updated. Production Go,
dependencies, save 35 and generation fingerprints do not change. General MBF,
arbitrary worlds, active-player maintenance and selected mixed hazards/resource
pickup remain separate. These research checks do not establish live BBS
acceptance or native Windows crash durability. Next acquire
controls that actually select the remaining hazard or pickup branches before
broader research admission; bounded gameplay versions already exist.

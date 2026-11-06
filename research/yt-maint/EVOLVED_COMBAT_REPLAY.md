# Before-only replay of evolved foreign-force combat chains

All four [evolved combat control chains](EVOLVED_COMBAT_CONTROLS.md) now have a
separate before-only replay. **144 complete comparisons / 864 files** are
byte-exact, and all **1242 independent child helper/final RNG witnesses** agree.
All **56 new tests** pass. No field, raw numeric zero, timestamp, casualty,
publication line or stale group pointer is masked or patched from a target.

## Original inputs and modeled inheritance

The API accepts three original occupied before-files and three immutable day
input structures. Four exact initial world fingerprints select the measured
Mercenary-37, Mercenary-100000, neutral-37 and neutral-planet recipes. Unknown
world/name/news bytes fail before any synthesis read. Dates are restricted to
November 2/3/4, 2026 and child publication clocks to the measured midnight values.

The existing [occupied-world model](OCCUPIED_RECORD_REPLAY.md) calculates the
November 2 parent. Its modeled six-file object feeds the first child, whose
complete modeled object feeds the second. Actual captured child-before/after
files, public transcripts, recipes, cache probes and old RNG states never enter
synthesis. Only immutable original YTMAINT bytes are read by the core.

Source-qualified extraction now explicitly handles original parent active-slot
inventories of zero/one and evolved inventories of three/four. Actual slot indices
bind each planet DATE/TIMER pair; chronological helper caller labels and raw
TIMER values remain explicit inputs. The startup seed field derives from the
startup TIMER. Captured `rng_raw` fields are removed during extraction and are
used only for independent comparison after all three stages are computed.

Each complete chain is computed before its first target is opened. Three observed
clock streams per case and two new children are compared against six native
modes: four × three × two × six = 144. The original prefix is audited too, without
inflating the new-child 864-file count. Read bans, object-identity spies, modeled
markers and poisoned witnesses directly test these boundaries.

## Composed economy and Xannor paths

The separate planet module admits three named homes and optional neutral Route
Haven. It preserves original source floors, rounded bank/stock production,
ordinary TIMER minutes, retained field bytes and capped elapsed time. Existing
home paths skip creation clocks, while Xannoron's common later ground draw still
occurs. The retained port writer computes complete blocks without target reads.

Before-only Route Haven economy produces ground 510024 and 515102. Source-ordered
Xannor assaults then spend **22** and **19**, giving exact saved ground
**510002** and **515083**. Each child has eighteen fatal attacks, deriving
**2614** and **792** Xannor losses. The planet retains its neutral title and link.
Foreign physical owners survive the Xannor cache normalization; neutral 37 is
retained without silently adding it to an Xannor deployment or scoreboard.

## Surviving Mercenary combat and source-width rules

The new tail follows the original descending scan of mutable physical sectors.
The same surviving group is activated twice: endpoints 2689 → 1037 → 2645 on the
first child, then 2645 → 1963 → 2368 on the second. These are activation endpoints,
not adjacent warp steps. The model does not impose the modern snapshot-once policy.

A negative Xannor owner forces combat while still consuming the eager ordinary
`.95` gate draw. The actual observed offense starts with **97525 Mercenaries**
and **182 Xannor**. It derives **370 combat draws**, plus that gate draw: 182
Xannor and 188 Mercenaries die, leaving **97337** Mercenaries. The modeled combat
state advances from **10977382 to 628675**, then continues through both route
activations and the later lottery phase. Captured state is checked afterward,
never supplied to the combat routine.

The source operand at `8916` is an **eight-byte MBF double 200**. Its leading
four zero bytes are not a single-precision zero threshold. The model binds this
literal and batch **150** directly to the original binary. When both forces are
above 200, source rounds use that batch; otherwise each casualty is one. The
captured 182-defender offense exercises unit casualties. Threshold/tie/batch
boundaries are additionally covered with synthetic tests; they are not new DOS
runtime observations or a claim of arbitrary-world combat parity.

The defeated physical defense at sector 109 is written with original canonical
zeros. Group 8's saved pointer remains **109**, matching the later-phase stale
state rather than being normalized early. Its initial deployment at 673, same-day
Xannor move, Mercenary victim removal and continued Mercenary movement all derive
from the source order. Final physical force, rather than cached pointer count,
drives score publication.

## Six writers and derived receipts

| Case | Child 1 Xannor / Mercenaries | Child 2 Xannor / Mercenaries |
|---|---|---|
| Mercenary 37 aftermath | 9963 / 0 | 9963 / 0 |
| Mercenary 100000 aftermath | 5148 / 97525 | 4966 / 97337 |
| Neutral 37 control | 10000 / 0, plus neutral 37 | 10000 / 0, plus neutral 37 |
| Neutral Route Haven | 1408 / 0 | 616 / 0 |

Public writers use original executable literals, including `beloning`. The
Mercenary receipt prints initial combatants and the winner; it does not invent
an 188-casualty public counter. Actual losses are separately conserved against
physical before/after owners. The formatter correctly permits victory at an
intermediate sector followed by further travel, rather than requiring the final
force to remain at the battle site.

NPC scores derive from surviving physical forces ×100, including the Mercenary
leader denominator. Names remain exact, private output remains empty, yesterday
news copies the previous modeled public journal and inactive human ranks remain
correct. Independent publication dates/clocks are preserved within the admitted
midnight profile. All five auxiliary files match the native outputs completely.

## Evidence, checks and scope

The existing [Mercenary native read](collision-replay-native/rea.json),
`0x14600` length 3462 (Evidence
`ev_c92656dd4a34f4605e434c81cbd3e9f730962d0373f2a3fecfce72256fbfcd2f`),
contains the original mutable scan, fight and physical writers. Existing
planet/route and runtime evidence is reused. No emulator acquisition, native
byte query, provider installation or capture rewrite was needed for this replay.
The frozen 48-run combat corpus and all earlier manifests remain unchanged.

The 56 tests comprise five planet, six auxiliary, eighteen NPC/Mercenary and
27 full-chain tests. They cover complete equality, all helper/final witnesses,
file-read and handoff guards, exact causal casualties, source-width thresholds,
neutral/extinct controls, stale pointers, unknown initial worlds and malformed
or unmeasured date/clock/caller admission. Unknown selected damage, resource
pickup, merging or other unadmitted hazards fail closed.

```sh
python3 scripts/replay_maintenance_evolved_combat_records.py
python3 scripts/test_replay_maintenance_evolved_combat_planets.py
python3 scripts/test_replay_maintenance_evolved_combat_aux.py
python3 scripts/test_replay_maintenance_evolved_combat_npcs.py
python3 scripts/test_replay_maintenance_evolved_combat_records.py
```

README, plan, validation and CI are updated. Production Go, dependencies, save 35
and `qb36-v1` fingerprints are unchanged. Local research tests do not establish
live BBS acceptance or native Windows durability. Historical profile APIs and
admission guards remain unchanged. Next acquire mixed-hazard, resource-pickup or
longer surviving-force handoffs before broadening the measured replay boundary;
the bounded gameplay versions of those mechanisms already exist.

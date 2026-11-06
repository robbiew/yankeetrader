# Evolved foreign-force and surviving-combat handoffs

Four explicit two-child profiles now retain **48 complete original-DOS runs**.
Each first child copies all six output files from its corresponding mode of the
[occupied-route controls](OCCUPIED_ROUTE_CONTROLS.md). Each second child takes
its own first child's six files unchanged. All **288 inherited-file links**
match. All six output files agree across the six modes at all eight stages
(**288 complete after files**), without masks or output repairs.

This report covers acquisition and independent evidence verification. A
[separate before-only model](EVOLVED_COMBAT_REPLAY.md) now composes these chains. The [clock/date replay](EVOLVED_CLOCK_REPLAY.md) and published
PR #97 remain separate scopes. Production Go, dependencies, generation
fingerprints and save **35** are unchanged.

## Explicit recipes and parent identity

Each profile runs November 3 and November 4, 2026, requesting midnight. The
original parent ran November 2. The deliberately constructed parent fixtures
are already declared and frozen in the earlier corpus; there are no edits to
any world or side file between the original parent output and these children.
Parent manifest SHA-256:
`7c01a0ef401f3df96f413e4aefd046c7f8a57499a1dfa537c83ea950d0dc7a3a`.

| Parent fixture | Native parent state | First child | Second child |
|---|---|---|---|
| `route-mercenary-37` | Xannor 9963, Mercenaries 0 | 9963 / 0 | 9963 / 0 |
| `route-mercenary-100000` | Xannor 5148, Mercenaries 97525 | 5148 / 97525 | 4966 / 97337 |
| `route-neutral-37` | Xannor 10000, neutral 37 | Both retained | Both retained |
| `route-planet-neutral` | Xannor 4022, Route Haven ground 504975 | Xannor 1408 | Xannor 616 |

The small Mercenary parent has **no surviving Mercenaries**; it is an extinct
foreign-force aftermath control. The large parent supplies the actual surviving
force. Neutral owner-zero fighters remain 37 at sector 854 with their owner
unchanged; these controls demonstrate persistence, not assimilation or a general
neutral-owner rule. No absent foreign force is recreated.

Each stage contains two unobserved runs, one attach-only run and three observed
runs. Original YTMAINT and BRUN30 bytes are unchanged. Fresh disposable mounts,
the pinned DOSBox/Frida versions, 200000 cycles, actual launch/clock evidence and
complete natural-exit witnesses are retained. All 48 runs completed on the first
acquisition; no failed or forced-termination run is counted as evidence.

## A surviving Mercenary offense and authentic stale state

In the large-force profile, the descending mutable-sector scan selects the same
group twice on each child: activation endpoints **2689 → 1037 → 2645** first,
then **2645 → 1963 → 2368** second. These arrows denote activation endpoints,
not adjacent warp steps. The first child has no battle. This is original behavior,
not the modern snapshot-once route policy described in the gameplay docs.

The exact second-child public pair is:

```text
 *** 97525 Mercenaries attacking 182 fighters beloning to The Xannor!
 *** The Mercenaries Won!
```

The source typo is retained. Xannor physical force falls by **182** and the
surviving Mercenary force falls by **188**, to **97337**. The receipt states the
attacker, defender and winner; **188 is an observed save delta, not a printed
casualty counter or an independently predicted RNG result**. The victim is a
same-day Xannor deployment, so its force must not be incorrectly required at the
Mercenaries' eventual final sector in the child-before world.

Group 8 starts with 182 fighters at sector 673 and moves to sector 109 in the
Xannor phase. Sector 109 lies on the first Mercenary route. The later offense
removes that physical force, while the saved group-8 pointer remains **109**.
That authentic stale pointer is preserved byte-for-byte; it is not normalized
away during evidence packaging or verification. A later replay must compose
these phase writes and derive the following day's cache from physical ownership.

## Surviving planetary ground and side files

Route Haven keeps its original name, neutral title and physical link. Both
children contain **18 fatal Xannor attack/death pairs** against that planet.
The printed incoming forces total **2614** and **792**, exactly accounting for
Xannor force changes 4022 → 1408 → 616. Saved ground evolves
**504975 → 510002 → 515083** after ordinary production and combat. These are
retained before/after observations; their separate before-only economy/combat
composition is now complete in the linked replay.

All private-message files remain empty. Names retain their exact input bytes;
yesterday news is the prior stage's complete public journal. NPC score columns
agree with actual surviving physical owners. Separate source-qualified news and
score text clocks and raw port/active-planet timestamps are authenticated. The three-home
profiles have actual active indices 1/99/100; Route Haven additionally has slot 2.
No fixed four-planet inventory is falsely imposed on all profiles.

## Provenance and source boundary

[The frozen corpus](evolved-combat-controls/) contains **1318 files** and
11,229,698 bytes, including the four exact executed acquisition sources. Manifest:
`fd794dccfda332ab79c2d5a693d2649ebbc32c607863fbf2f10801ec4e0ecef5`.
Original YTMAINT is
`8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6`;
BRUN30 is `3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8`.

Existing [Mercenary source evidence](collision-replay-native/rea.json), read
`0x14600`, length 3462, covers original `464b–535a` including the mutable
sector scan, combat, public writer and physical writeback (Evidence
`ev_c92656dd4a34f4605e434c81cbd3e9f730962d0373f2a3fecfce72256fbfcd2f`).
The active-planet/foreign-defense evidence and complete source clock contracts
are reused. The retained source read is independently checked against every
relocated original byte. No new helper caller site or native byte query was required.

Future combat implementation must read source constants at their actual width:
the eight-byte MBF **double 200** at `8916` has four leading zero bytes; the older
four-byte annotation displaying zero is not the threshold. The original fight
uses the later batch-150 constant and ordinary RNG draws. This evidence milestone
does not itself synthesize those children; the separate replay now does.

## Independent checks and next work

All **43 provenance, semantic and source-width tests** pass. The verifier imports
neither the capture controller nor a replay model. It checks
immutable parent/output identity, exact per-mode six-file inheritance, actual
launch/CPU/date evidence, observer/lifecycle integrity, source-qualified clock
indices, raw timestamps, side-file rotation, physical ownership, literal public
outcomes and survivor-based scoreboard columns. Mercenary offense is bound to
its report phase; its unprinted loss is reported separately from printed summary
columns. Unknown public combat outcomes fail explicitly. Cross-mode differences
are classified rather than masked; all retained stages are equal.

```sh
python3 scripts/verify_maintenance_evolved_combat.py
python3 scripts/test_verify_maintenance_evolved_combat.py
# Fresh disposable acquisition with the pinned installed host and Frida:
python3 scripts/recover_maintenance_evolved_combat.py /tmp/new-evolved-combat \
  --scratch /private/tmp/new-evolved-combat-mounts \
  --frida-module /absolute/path/to/frida.js
```

The separate replay now composes these four chains from their original occupied
inputs, including three-home economy, Route Haven defense, Mercenary reactivation,
same-day victims, stale pointers, exact combat RNG and all six writers. The
historical convergence-only API still rejects these different initial contexts;
that is its unchanged scope boundary, not a numerical mismatch.
Do not repeat the completed clock/date capture or replay as missing work.
General MBF, arbitrary worlds, active-player maintenance, live BBS acceptance and
native Windows durability remain separate.

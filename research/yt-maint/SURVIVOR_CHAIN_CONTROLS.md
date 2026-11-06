# Longer survivor and foreign-defense handoffs

Four November 4 saved states now have two additional unchanged handoffs, on
November 5 and 6, 2026. The new corpus retains **48 complete original-DOS runs**,
**288 exact inherited-file links** and **288 complete after files**. Every one of
the eight stages agrees across all six modes. No record, pointer, timestamp or
side file is masked or repaired.

These are new later-day controls, not repeated November 3/4 captures and not a
new before-only replay. The existing [combat replay](EVOLVED_COMBAT_REPLAY.md)
and [clock/date replay](EVOLVED_CLOCK_REPLAY.md) remain unchanged. Production Go,
dependencies, save **35** and generation fingerprints are unchanged.

## Exact parent lineage

Each first child reads all six files from the corresponding mode of the declared
prior `child-2` output. Each second child copies its own first child's six files
unchanged. No fixture edit, reset, new player or side-file replacement occurs.
Both children request midnight; source clocks are retained independently.

| Profile | Exact November 4 source | Parent physical state | November 5 | November 6 |
|---|---|---|---|---|
| Mercenary survivor | Combat / `route-mercenary-100000` | X4966 / M97337 | X4966 / M97337 | X2433 / M93846 |
| Planet survivor | Combat / `route-planet-neutral` | X616 | X470 | X400 |
| Neutral survivor | Combat / `route-neutral-37` | X10000 + neutral37 | X10000 + neutral37 | X8575 + neutral37 |
| Mine survivor | Clock / `second-two` | X9994 | X9176 | X9176 |

The [combat parent corpus](evolved-combat-controls/) manifest is
`fd794dccfda332ab79c2d5a693d2649ebbc32c607863fbf2f10801ec4e0ecef5`.
The [clock parent corpus](evolved-clock-controls/) manifest is
`c6fc45c0d1adf29bf2104574d1e341791f9f9fa15d2059c52a04ecd917beb826`.
The frozen recipe and per-run metadata explicitly identify corpus, original
profile, parent stage and manifest. The metadata's `parent_source` retains that
original lineage for both stages; the second child's actual input bytes are
separately verified against its own first-child output.

Each stage has two unobserved runs, one attach-only run and three observed runs.
Original guests remain unchanged. Fresh disposable mounts, pinned host/observer
identities, 200000 cycles and complete source/lifecycle records are retained.
All 48 processes exited naturally on the first acquisition. No timeout, forced
termination, retry or diagnostic fragment is counted as a successful control.

## Newly selected foreign-defense combat

On November 6, the Mercenary-survivor profile selects **18 Xannor-phase sector
battles** against the surviving Mercenary force. The original public columns
sum to **2533 Xannor** and **3491 Mercenary** losses, exactly reconciling saved
physical totals 4966→2433 and 97337→93846. They occur before `Mercenary Report:`;
its first movement line already contains the surviving **93846** force.

One original receipt has a legitimate zero casualty column:

```text
 *** Mercenaries: lost 1, dstrd 0 (Xannor ftrs dstrd)
```

The original labels are preserved. Verification allows a zero column while
requiring some casualty and reconciling the complete faction deltas. It does
not replace the source wording with a new interpretation or accept a `0/0`
fiction. These are observed counters, not a newly predicted complete RNG stream.

The later Mercenary phase selects four descending-scan activations on each day:
activation endpoints **2368 → 1680 → 1389 → 1082 → 2812**, then
**2812 → 2499 → 1351 → 815 → 2790**. These arrows denote activation endpoints,
not adjacent warp steps. The first child's force remains 97337; the second's
later movements retain 93846. No Mercenary offensive attack receipt is selected
in these new controls.

## Continued planetary defense and persistent mines

- Route Haven survives eighteen fatal Xannor attacks each day, with incoming
  totals **146** then **70**. Its saved ground evolves
  **515083 → 520215 → 525399** after ordinary production and combat.
- Neutral-survivor November 6 selects five fatal Wanderer attacks, incoming
  forces 199 + 949 + 36 + 11 + 230 = **1425**. Neutral fighters remain **37 at
  sector 854**, with their owner unchanged.
- Mine-survivor November 5 selects four fatal Wanderer attacks, incoming forces
  163 + 35 + 554 + 66 = **818**. November 6 has no public combat. Its ordinary
  planet is friendly **Convergence Haven**, not neutral Route Haven.

All inherited planets retain their names, owners and unique current links.
The before/after ground values are recorded as observations; this evidence
checker does not synthesize the complete intervening economy/combat arithmetic.

Persistent mines are preserved and new group-20 deposits remain visible,
including mine-survivor sector **474**, from zero to one. **No mine damage or
planetary stock pickup is selected** by these eight stages. Mine presence does
not establish a selected mixed-hazard encounter, and neutral persistence does
not establish assimilation. Those branches remain separate work.

## Raw pointers and independent publication clocks

The Mercenary parent has the previously observed group-8 pointer **109** with no
physical Xannor force there. The known before-cache rule derives an empty group
from that state; the next run allocates it again. The new final saved pointer is
**328**, with two fighters there. This is source-informed interpretation of the
before/after records, not a new captured early-cache array or an input patch.

New terminal aliases also remain untouched. Mine-survivor November 6 retains
group pointers 2/19 at 1436 and 13/15 at 2369. Verification reports actual raw
pointers and whether their sectors contain owned Xannor force; it does not
canonicalize duplicate pointers or multiply a physical deployment by aliases.

Neutral-survivor November 5 prints NEWS **00:00:00** and SCORE **00:00:01**.
Both agree with their own actual source calls. A test rejects replacing the
score clock with the news clock. A future longer-chain model must explicitly
admit that measured distinction; the prior child's midnight-only text-clock
boundary is not silently widened here.

Names remain byte-exact, private mail remains empty and yesterday news is each
previous stage's complete public journal. Both NPC score columns agree with the
surviving physical owners, including Mercenary leadership. All six output files,
not only numerical fields or public counters, agree across modes.

## Provenance, validation and remaining scope

[The new frozen corpus](survivor-chain-controls/) contains **1318 files** and
11,442,647 bytes, including four exact executed acquisition sources. Manifest:
`2ce91ff7798d4da83f9ca5966fc999958b7a038808c4da4ed4c26889b3b2cc5e`.
Existing source-qualified DATE/TIMER/TIME contracts admit every observed caller;
no new helper call site, provider installation or native byte query was needed.

Existing [foreign-defense native evidence](../yt-xannor-mobile/rea/phase-paths.json)
includes the read at `0x17522`, length 367 (Evidence
`ev_f98e1a80cb77051c45c4aad58183cd47ef3c5629b15bef20c758495e0a9bcc72`),
and the read at `0x17776`, length 370 (Evidence
`ev_f347a1d79af5cfb2b7c955ceb51da9ee0acd852796b3d2eb1def1acf67c44c16`).
The retained Mercenary scan and clock evidence are reused too. These static
records identify source context; they are not new runtime casualty predictions.

All **47 independent provenance/semantic tests** pass, including parent-corpus
lineage rebinding, exact per-mode inheritance, actual launch/clock/lifecycle
integrity, public/console phase agreement, zero-column casualties, physical
conservation, score/source timestamp mismatches, raw pointers and immutable
inventory. First Mercenary movement force must equal inherited force minus
actual earlier defensive losses. All eight six-mode groups classify as equal;
classifiers report differences rather than masking them. All **4682** original
archive hashes and the reused mobile source evidence verify.

```sh
python3 scripts/verify_maintenance_survivor_chains.py
python3 scripts/test_verify_maintenance_survivor_chains.py
# Acquire only into fresh paths with the existing pinned host and Frida:
python3 scripts/recover_maintenance_survivor_chains.py /tmp/new-survivor-controls \
  --scratch /private/tmp/new-survivor-mounts \
  --frida-module /absolute/path/to/frida.js
```

Next compose the two additional children before-only from the already modeled
November 4 parents: measured days 309/310, evolved foreign-defense receipts,
reallocation after stale/duplicate pointers, surviving ground and the separate
score clock. Current replay APIs reject these later dates/lengths; that is a
scope boundary, not a measured numerical mismatch. General MBF, arbitrary worlds,
active-player maintenance, live BBS acceptance and native Windows durability
remain separate. Existing bounded gameplay mechanisms are not missing features.

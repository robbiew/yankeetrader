# Complete before-only initial placement/collision record replay

The twelve fixtures from [placement/cache research](PLACEMENT_COLLISIONS.md) now
have complete research replay: **36 source observations × six paired targets =
216 comparisons / 1296 individual files, zero mismatches**. Each synthesis
produces all 4151 world records plus five auxiliary files before any expected
output is opened. No field, timestamp, raw zero residue or side file is masked.
The retained native observations and raw outputs are unchanged.

This closes the prior selected-fixture integration task. It does not add Go
features, change dependencies/save format **35**, import DOS saves or establish
arbitrary evolved-world maintenance. Bounded production gameplay already exists.
The historical strict replay APIs and reports retain their original scopes; use
this new explicit entrypoint for the twelve additional fixtures.

## Inputs, source chronology and independent RNG checks

Core `synthesize(before_files, inputs)` accepts only three admitted before files
and immutable explicit clock/date inputs. Before-world digests select the twelve
retained recipes or the historical baseline; unknown bytes and altered side-file
inputs fail closed. The digests admit before-inputs, not target data or outcome
patches. Per-port and creation-phase dates retain their separate source writers.

The helper schedule contains measured TIMER bytes and source-family/caller labels
in their observed order. The model decides when to call each original helper and
checks that its computed caller matches the next clock entry. It derives every
old RNG state, retained low byte, reseed and draw from startup. The clock schedule
cannot select a branch or replace a computed state.

**Captured `rng_raw` values are excluded from `Inputs`.** They are read only by a
separate post-synthesis audit. Poisoning them with a consistent false zero leaves
inputs and all modeled outputs unchanged, while the independent audit rejects
them. Removing/reordering clocks, using a wrong source caller or leaving a clock
unconsumed also fails. Core read guards permit only the immutable original
YTMAINT executable; no target, cache probe, transcript, manifest or other observed
midstream state is read during synthesis.

Across all 36 observations, **2265 independent checks** bind every computed
helper-entry old state and both final scoreboard clock samples to the captured
raw RNG witnesses. The Base entry state is now calculated through all preceding
Xannor actions; it is no longer supplied as an observed midstream seed.

## Integration completed

- Wanderer and Base placement can reject multiple positive links. Each retry
  makes a new source-labelled helper call/reseed. Negative and noncanonical-zero
  links accept as the original source does; the admitted fractional-link cases
  remain explicitly synthetic gate fixtures.
- Cache normalization consumes each physical Xannor force once, clears stored
  pointers and preserves the original raw sector-clear zero `00008000`.
  Duplicate HQ/mobile pointers do not invent force. Existing valid mobile groups
  skip allocation; the duplicate-mobile fixture therefore makes 18 shrinking
  calls instead of 19.
- Candidate selection recognizes inactive positive-link preference. Shared
  preference, eager player scans, same-origin rejection, protected-sector retries,
  directed routes and fatal-edge scan suppression use the original source order.
  The already recovered bounded Wanderer production encounter is reused.
- Final Xannor writeback adds cached force to a destination's existing force,
  preserving unpointed friendly deployments and exact physical accounting.
- The later Mercenary phase consumes eager desertion draws for every positive
  defense, then scans mutable sectors in descending order. Its movement gate is
  evaluated even on empty origins. A force arriving at a lower-numbered sector
  can activate again in the same maintenance run.
- Departure clears force/title with the distinct source zero `00002800`, not
  the cache zero or canonical zero. The selected 37-force Mercenary case derives
  3000 → 1228 → 2957, with two activations, two movement gates and two target
  helper calls. These are modeled results independently compared with native
  outputs, not configured destinations.
- The lottery gate and optional unnamed-player draw follow all faction actions.
  Auxiliary files derive actual Xannor/Mercenary scores, percentages and modeled
  public Wanderer casualties. Movement-only console lines do not become invented
  public news; private messages remain empty.

| Fixture | Helper 1 / helper 2 calls | Total draws | Final RNG state |
|---|---:|---:|---|
| Wanderer rejects two | 44 / 19 | 19694 | `7bc3a3` |
| Wanderer rejects three | 44 / 19 | 22794 | `26cccf` |
| Wanderer positive fraction | 42 / 19 | 25242 | `4e809f` |
| Wanderer negative link | 41 / 19 | 25891 | `4307ee` |
| Wanderer raw-zero link | 41 / 19 | 25891 | `4307ee` |
| Base positive fraction | 42 / 19 | 25892 | `71d1f9` |
| Duplicate HQ | 41 / 19 | 25891 | `4307ee` |
| Duplicate HQ chain | 41 / 19 | 25891 | `4307ee` |
| Duplicate mobile | 42 / 18 | 24738 | `4defc7` |
| Neutral-sector pointer | 41 / 19 | 25892 | `36bef9` |
| Mercenary-sector pointer | 44 / 19 | 25897 | `547b1c` |
| Unpointed friendly merge | 41 / 19 | 25891 | `4307ee` |

The extra helper in the two-rejection fixture includes the actual optional
unnamed lottery selection. A fixed old 41/19 inventory would be incorrect.
The table records derived comparison outcomes, not model inputs.

## Additional original-byte evidence

[The new native packet](collision-replay-native/rea.json) retains one complete
REA/Ghidra 12.1.4 read of original YTMAINT at `0x14600`, length **3462**, through
`0x15386` exclusive. Evidence ID:
`ev_c92656dd4a34f4605e434c81cbd3e9f730962d0373f2a3fecfce72256fbfcd2f`.
It covers the desertion/Mercenary tail and lottery gate. The independent verifier
reconstructs every relocated byte and the original DS `859e` departure constant
from immutable executable SHA-256
`8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6`.
Static bytes are code evidence, not a new DOS execution. Earlier cache, placement,
writeback and planetary-helper packets remain unchanged and linked from the prior
reports. No new runtime output was acquired or rewritten to make this replay fit.

## Reproduction and validation

```sh
python3 scripts/verify_maintenance_placement.py
python3 scripts/verify_maintenance_collision_replay.py
python3 scripts/test_verify_maintenance_collision_replay.py
python3 scripts/test_replay_maintenance_collision_records.py
python3 scripts/test_replay_maintenance_collision_aux.py
python3 scripts/test_replay_maintenance_collision_mercenary.py
python3 scripts/replay_maintenance_collision_records.py \
  --output /tmp/collision-record-replay.json
```

Portable validation needs only Python standard library and retained artifacts;
it launches no DOSBox, Frida, Go application or network operation. All 216 complete
comparisons, raw-state audits and file hashes are reproducible. A full historical
matrix regression also matches all six files for its eight clock/date recipes.
The newly merged cursor-rendering changes from current main were integrated
without modifying that gameplay code for this research.

## Explicit remaining limits

The Mercenary routine admits only absent forces or the selected conserved 37-force
empty-route case. New mines, defense battles, planetary stock pickup, changed or
merged Mercenary forces and unsupported occupied-origin departures fail closed.
The Wanderer helper still requires the measured zero-ground, large-rate, empty
warehouse branch; unknown combat, deletion and numeric paths are not guessed.
Research guards bound retries/activations; they are not claims that DOS had those
work limits. Before fingerprints and explicit source-clock inventories prevent
accidental admission of unmeasured input worlds.

Next collect valid occupied-planet controls, actual foreign-force route encounters
and final-pointer convergence followed by an exact evolved-world chain. Extend
record synthesis only after those source branches are verified. Do not repeat
these twelve initial fixture integrations as missing work. General MBF, arbitrary
maintenance, DOS save conversion, live BBS acceptance and native Windows durability
remain separate.

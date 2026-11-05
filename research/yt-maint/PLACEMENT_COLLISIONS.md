# Bounded occupied placement and faction-cache collisions

This research retains **84 original-DOS controls**: 72 complete runs across twelve
a-priori recipes, plus twelve separately labelled early cache probes. Every
recipe has two ordinary unobserved runs, one attach-only run and three host-clock
observations; all six final output files are byte-identical across those six
full runs. No guest code changes occur in a full run. Four complete fresh REA
reads establish the selected original placement/cache/writeback bytes.

Two small research primitives add executable evidence:

- A **before-only cache normalizer** predicts all 40 location/force fields in
  each stopped original cache, **480 field comparisons / zero mismatches**.
- A **source-qualified placement replay** uses explicit original helper TIMER
  and old-RNG-state witnesses, the before-world links and the source gates.
  Its accepted destinations pass **432 checks** against the paired full runs.

This does **not** synthesize every final byte of the twelve new worlds from
before-inputs. In particular, a measured old RNG state at Mercenary placement is
an explicit midstream input, not a claim that all intervening movement, combat
and reseeding has been reconstructed. Full-file equality here establishes the
selected observer's neutrality; it is distinct from whole-world model equality.
The earlier [all-eight-clock Wanderer replay](WANDERER_ENCOUNTER.md) remains exact
and reproducible. No Go gameplay, dependencies, save 35 or `qb36-v1` fingerprints
change, and no DOS save interoperability is introduced.

## Avoiding repeated research

[Earlier sequencing](RNG_SEQUENCING.md) already showed one synthetic occupied
Wanderer destination and an extra helper reseed. [Mobile Xannor recovery](../yt-xannor-mobile/RECOVERY.md)
already described basic friendly-force combination and foreign combat. This
slice tests additional complete initial-world controls, multi-rejection state
continuity, fractional/negative/zero gate boundaries, raw cache consumption and
ownership mismatch at the exact source phase. It does not reopen those basic
formula or gameplay milestones.

## Declared inputs and actual outcomes

The original 4151-record before-world is the independently retained
`initial-controls/baseline-split` world. Only the sector fields in the frozen
[recipe](placement-cache-controls/recipe.json) are overridden. Player/planet
records, original binaries, graph, port economy and side-file before-inputs are
unchanged. Date is November 2, 2026, requested clock midnight, fixed host budget
200000 cycles. Actual shell clocks, per-writer registers and applied CPU arguments
are retained and independently verified.

| Recipe | Declared change | Accepted Wanderer / Base sectors | Cache total |
|---|---|---|---:|
| `wanderer-reject-two` | Positive inactive links at 1095 and 1792 | 1295 / 938 | 10000 |
| `wanderer-reject-three` | Also block 1295 | 2787 / 20 | 10000 |
| `wanderer-positive-fraction` | Link .25 at 1095 | 1792 / 4 | 10000 |
| `wanderer-negative-link` | Link -1 at 1095 | 1095 / 2598 | 10000 |
| `wanderer-zero-residue` | Numeric-zero bytes `00004800` at 1095 | 1095 / 2598 | 10000 |
| `base-positive-fraction` | Link .25 at baseline Base candidate 2598 | 1095 / 263 | 10000 |
| `duplicate-hq` | Group 2 pointer also addresses HQ 849 | 1095 / 2598 | 10000 |
| `duplicate-hq-chain` | Groups 2, 3 and 20 also address HQ | 1095 / 2598 | 10000 |
| `duplicate-mobile` | Groups 2 and 3 address one friendly 37-force sector 1000 | 1095 / 2967 | 10037 |
| `pointer-neutral-sector` | Group 2 points at sector 3000, force 37, owner 0 | 1095 / 2598 | 10000 |
| `pointer-mercenary-sector` | Same pointer/force, owner -2 | 1095 / 2598 | 10000 |
| `unpointed-friendly-merge` | Add friendly force 37 at sector 1548, with no group pointer | 1095 / 2598 | 10000 |

The occupied-link cases are explicitly **synthetic branch gates**. A positive
link to an inactive planet, a fractional link and a negative link are not claimed
to be consistent playable DOS worlds. They establish the predicate independently
of planet economics and active-player effects. Cache-pointer cases use integral,
in-range pointers and whole nonnegative force. Pre-existing special-planet links
1/99/100 are rejected by this missing-NPC placement profile because they can
change restoration and calendar-helper execution. No saturation, malformed pointer,
arbitrary large-number or modern save admission policy is inferred.

## Placement gates, reseeding and receipts

Both original loops test sector planet-link field 93 **numerically greater than
zero**, not whether it points to an active planet. Positive fractions reject.
Negative values and numeric zero—including a noncanonical raw zero—accept and are
overwritten. Neither gate tests sector force or owner.

Every rejection calls helper `78f3` again and reseeds from the actual TIMER FAC,
retaining the old state's low byte. The new observations add a read of the raw
four-byte RNG state at `DS:0234` to the existing clock observer. Paired before/after
DOS-handler snapshots must agree on that read; source signatures, far-call/BP
attribution, immutable host identity and the full clock inventory remain checked.
The independent verifier derives each selected candidate from the original LCG,
not from the target's planet link.

At this schedule the two-rejection chain is 1095 → 1792 → 1295, and the
three-rejection chain continues to 2787. The prior one-rejection observation was
not simply counted again as the new result. Changed time inputs on another host
are not automatically approved or fitted to these destinations.

Wanderer's optimistic “successfully warped” console receipt occurs **before** its
occupancy test, so the two/three-rejection controls print it three/four times.
The raw accepted link is authoritative. The Base's creation news occurs once
before its selection loop; its positive-fraction rejection does not publish a
second creation event. Base placement can choose sectors 4 or 20 in these DOS
controls. These source outcomes do not alter modern protected-sector policy.

## Cache consumption and duplicate ownership

The source performs distinct passes:

1. Read all twenty stored location pointers, initialize cached forces and clear
   all stored pointer fields using canonical zero `00000000`.
2. For each positive location, consume physical force only if its sector owner
   is Xannor -1. Clear the consumed physical force **and owner** with the distinct
   raw zero `00008000`.
3. Normalize duplicate locations in ascending slot order, retaining the lower
   slot and adding the higher cached force before clearing the higher slot.
4. If location or force is below one, clear both cached values canonically.

Physical consumption happens before duplicate normalization. A second pointer
cannot load the same force again because the first load already cleared its
owner. Both HQ-duplicate cases therefore normalize to the same single 10000-HQ
force. The non-HQ duplicate retains 37 only in the lower group-2 slot, for a
10037 cache total; it is not 10074.

Owner 0 and Mercenary -2 do not qualify for Xannor cache consumption. Their
pointers become empty cache slots, but their physical force/title remain at the
stopped cache boundary. **Do not attribute later final-state changes to this
loader.** The Mercenary-owner full run later moves that force during its own
maintenance phase, while the neutral owner-zero force remains in its sector.
The early probe isolates the source stage before either outcome.

Unpointed friendly force is likewise absent from the loaded cache and stays in
its sector. At final Xannor writeback, a positive cached deployment adds to the
sector's existing force rather than replacing it. The unpointed control combines
37 with the arriving group's force. That final addition has no owner predicate;
this selected control validates the friendly case, not every foreign-title
collision or duplicate-final-pointer next-day chain.

## Native and acquisition evidence

Original YTMAINT SHA-256:
`8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6`.
The four complete REA/Ghidra 12.1.4 observations in
[native/rea.json](placement-cache-controls/native/rea.json) are independently
compared with the original relocated image:

| Address / length | Evidence ID |
|---|---|
| `0x126c9` / 744 | `ev_c735edcbe656b109fab6c962d9a7b6f1dc190542d52f91a538751c205e4e0082` |
| `0x13e30` / 323 | `ev_3255ab9a457214c46a48d189275b4ac24a898f0068bb2e245e777cb758a6b98d` |
| `0x11f50` / 256 | `ev_919eaba46db3489f4f16d2354cd70f2b5b880a2ce7e3bd1c609682a7845c9434` |
| `0x14355` / 148 | `ev_96dcbb39e16fcfcdd818fddfdc97b8f74add2ac8a0ddfeffc247e16d3fe91315` |

Relevant CS offsets: cache pointer load/clear `26c9–276f`, physical force/title
consumption `2794–285e`, pair normalization `2861–292c`, invalid-cache clearing
`293a–29af`, final force addition `3ee8–3f4c`; Wanderer gate `1fbd–1fc7`, Base gate
`439d–43a7`. Native byte reads are static observations, not runtime captures.

Each early probe replaces only the declared five-byte dispatch at `29b7` and the
original return/cleanup area with a reconstructed 46-byte stop probe. It writes
168 contiguous DS bytes from `1c52` and exits before normal maintenance completes.
All 40 modeled cache fields within that packet are checked at raw-byte precision;
the two unused array entries are retained but not invented as model outputs.
Pointer/consumed-sector writes are separately checked in the stopped world.
These timing-perturbing diagnostics are not full-run output goldens. Unchanged
BRUN30 and the patched copy's exact digest are independently verified.

Every full run requires natural status-0 process termination, original DOS return
witnesses and completion footer. Timeout, forced stop, missing flush, altered
source/caller or dropped observation fails acquisition/verification. No automatic
retry, hash refreshing or target-derived output repair is supplied. Frozen
acquisition sources and an immutable complete-file manifest retain provenance.

## Reproduce and verify

```sh
python3 scripts/verify_maintenance_placement.py
python3 scripts/test_verify_maintenance_placement.py
python3 scripts/test_replay_maintenance_placement.py
python3 scripts/replay_maintenance_placement.py --output /tmp/placement-cache.json
```

Portable checks use Python standard library only. Fresh acquisition requires the
pinned installed DOSBox 0.83.0 ARM64 binary, existing Frida 17.23.2 module and
absent output/scratch directories:

```sh
python3 scripts/recover_maintenance_placement.py /tmp/placement-new \
  --scratch /tmp/placement-disposable \
  --frida-module /absolute/path/to/frida/build/src/frida.js
```

`--cases` / `--modes` permit explicitly labelled pilots; partial inventories do
not pass the accepted-corpus verifier. New PIDs/paths/timing and digests require
independent review; acquisition does not approve its own output manifest.

## Next unfinished integration

Extend complete before-only maintenance-stream/record replay to these new
fixtures, including dynamic helper-call inventories, inactive positive-link
candidate preference, existing mobile groups and later Mercenary actions.
Then expand valid occupied planets, actual foreign-force route combat and
final-pointer convergence followed by an exact evolved-world chain. Do not
repeat these twelve initial placement/cache controls as uncaptured work, or
claim that their bounded primitives already establish arbitrary maintenance,
general MBF, DOS save conversion, native Windows durability or live BBS acceptance.

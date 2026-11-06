# Initial maintenance: mobile Xannor encounters with The Wanderer

The explicit before-only encounter profile closes the `late` recipe left open by
[the historical clock/date matrix](CLOCK_MATRIX.md). All eight retained recipes
now have complete research replay: **144 world-and-side-file comparisons / 864
individual file comparisons, zero mismatches**. A separate six-run fresh late
corpus adds 18 complete comparisons / 108 files, also exact. No expected output
is opened during synthesis, no timestamp or zero-residue byte is masked, and no
capture is rewritten to match the model.

This is research, not new gameplay. Bounded Xannor planetary assaults and The
Wanderer lifecycle already exist in Go. Production code, dependencies, playable
`qb36-v1` recipes/fingerprints and save format **35** are unchanged. General DOS
maintenance compatibility, populated/evolved worlds and arbitrary MBF remain
unsupported.

## What was missing, and what was already recovered

The [planet-assault investigation](../yt-xannor-planets/RECOVERY.md) already
established eligibility, ground combat, the production gate/batch defect,
warehouse caps and deletion. Repeating those formulas was unnecessary. The
missing integration was the initial world's exact seeded stream, shared pursuit,
raw record residues and complete public/score output.

The late recipe requests November 2, 2026 at `23:59:59`, with 200000 fixed DOSBox
cycles and the original all-inactive before-world. Its shell actually reports
**23:59:58.80** because the BIOS clock is quantized. The runtime observer retains
actual per-writer DOS returns; it never substitutes the requested string for
TIMER, DATE$ or TIME$. This is the same saved-base-year world used by the matrix,
not a newly initialized replacement.

## Exact first encounter and shared pursuit

Before-only simulation sends group 2, force 382, through sector 658, whose slot-1
planet is the newly restored neutral Wanderer. The source branch starts with
RNG state `ea7184` after four single-range and one shrinking helper calls.

1. The production gate draws `0.056064069271087646`, below .5.
2. Three independent draws damage ore/organics/equipment production:
   `0.5436419248580933`, `0.5432496666908264`, `0.594902515411377`.
3. The next gate draws `0.9760157465934753`. DOS subtracts batch 450 from 382,
   producing the temporary negative force -68 before clearing force/location.

The location-subscript defect makes this batch 450 even for a smaller force.
The research oracle preserves it; modern Go's intentional nonnegative casualty
and bounded-combat policies are not changed. Each multiplication, division and
single-array assignment follows the recovered single-precision order. The
explicit profile requires all rates to remain above 500 and empty warehouses;
small-rate, ground-defense, warehouse-capping and deletion paths are rejected,
rather than implied to be generically recovered by this extension.

Death also writes sector **658 into shared preferred-target variable `DS:7bac`**.
It is initialized once before the group loop, not once per group. Groups 3–19
therefore pursue the same surviving Wanderer. An existing preferred target skips
their candidate-player scan; fatal arrival skips that sector's interception scan
and every later route edge. Group 20 retains its separate fallback rule.

This explains 18 successive attacks, not repeated allocation of group 2. The
observed public force losses sum to **6923**, leaving **3077** fighters across HQ
and group 20. The score is **307700**; no defeated force or planet stock becomes
loot. There are 50 candidate-player draws, 23700 entered-sector player draws,
53 production gates, 27 draws for each commodity, zero ground draws, two
surviving-defense desertion draws and one lottery gate.

The surviving Wanderer's rates are 2995.552734375 / 2861.62841796875 /
2778.564697265625. These are independently compared outcomes, never synthesis
inputs. Ground and empty stock bytes retain `00001c00`; zero-ground ownership
becomes the distinct original constant `00002000`. Canonicalizing either numeric
zero would lose byte equality. Bank, weapons, inherited day 305 and name/link
survive. Public attack/death pairs occur after regeneration and before Mercenary
news. Private `YTRMSG.DAT` remains empty; the score is derived from saved survivors.

## Original code and independent observations

Two fresh complete REA/Ghidra 12.1.4 `read_bytes` records are retained in
[wanderer-encounter/native/rea.json](wanderer-encounter/native/rea.json):

| Range | Length | Evidence |
|---|---:|---|
| `0x15efd` | 2091 | `ev_bab5078d8fe91099570327f08867b9b9569702b5a054a59a11345019600e2eac` |
| `0x13113` | 3357 | `ev_2ff3ec911afa94ab890843ee68160c0fb82d6c78f6f6cfdc9f56eee686fe0f29` |

The verifier independently reconstructs every relocated byte from immutable
YTMAINT.EXE SHA-256
`8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6`.
Static byte reads establish code identity, not execution. Relevant CS offsets:

- `3b07` runs mine/sector defenses, then `3b33` calls planetary helper `5efd`.
- `632e` is the production gate; `6351`, `6383`, `63ae` draw component damage.
- `655b–6586` stores ground and the source-specific owner zero.
- `66cf–66d7` writes the dying group's location through the preferred-target
  output argument; `66dc–66f3` clears force/location.
- `3302` bypasses candidate-player draws when preferred is nonzero; `33ee–3401`
  selects preferred above sector 7. `3b91` skips the fatal edge's player scan.
- `670b` appends the public result; this helper calls no private-message writer.

Fourteen separately retained nth-site diagnostics independently count the draw
families and stop at selected first-hit state/target boundaries. Nine execute to
normal maintenance cleanup; five deliberately terminate at the declared source
site. Their disposable YTMAINT copies contain only the reconstructed 46-byte
probe and five-byte site jump. BRUN30 and all archive originals remain unchanged.
These probes perturb guest timing and **are not untouched output goldens**.

The six accepted fresh controls are two unobserved, one attach-only and three
host-clock-observed runs, each with unchanged executables and natural status-0
exit. All six complete outputs agree. Actual metadata, source-qualified host
frames, independent acquisition snapshots and an immutable manifest retain their
provenance. Accepted controls and diagnostics were acquired in separate bounded
batches. The finalized combined reproduction command additionally completed
all twenty controls in a fresh directory; independent verification confirmed
all outputs match the retained corpus and every diagnostic count/state agrees.
A later separate acquisition attempt reported a missing Frida flush notification
and was rejected despite a naturally exited child. Its artifacts remain in the
external temporary acquisition directory; it is not counted as accepted evidence
or silently retried by the capture writer.

## Reproduction and portable checks

```sh
python3 scripts/verify_maintenance_wanderer.py
python3 scripts/test_verify_maintenance_wanderer.py
python3 scripts/test_replay_maintenance_wanderer.py
python3 scripts/replay_maintenance_wanderer.py --output /tmp/wanderer-matrix.json
python3 scripts/replay_maintenance_wanderer.py \
  --root research/yt-maint/wanderer-encounter/untouched \
  --output /tmp/wanderer-fresh.json
```

The original `replay_maintenance_clock_matrix.py` strict entrypoint and its
retained report stay reproducible, including their historical three unsupported
rows. Use the explicit Wanderer entrypoint for all-eight-profile replay. This
keeps original evidence and earlier scope claims auditable.

Fresh acquisition requires the pinned installed DOSBox 0.83.0 ARM64 host, an
existing Frida 17.23.2 module, and new absent output/scratch paths:

```sh
python3 scripts/recover_maintenance_wanderer.py /tmp/wanderer-new \
  --scratch /tmp/wanderer-disposable \
  --frida-module /absolute/path/to/frida/build/src/frida.js
```

A capture failure stops acquisition; it cannot be reclassified as successful.
Fresh host paths/PIDs legitimately differ and require independent review before
pinning. Portable verification uses Python standard library only, not DOSBox,
Frida, Go, original-DOS execution or network access.

## Next genuinely unfinished slice

The subsequent [placement/cache research](PLACEMENT_COLLISIONS.md) now retains
selected multi-rejection and duplicate/foreign-owner controls with bounded
primitives. Their [complete record replay](COLLISION_RECORD_REPLAY.md) is now
integrated. Next broaden valid occupied planets, route collisions and evolved worlds.
Unconfirmed encounter and numeric paths still fail closed. Do not repeat this selected Wanderer integration,
clock-neutral timestamp closure, complete initializer generation, calendar
controls or already implemented gameplay as missing work. Real BBS and native
Windows acceptance remain separate from this research.

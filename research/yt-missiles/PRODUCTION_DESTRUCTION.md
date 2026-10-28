# Planetary production damage and destruction research

This research now guides the playable Go implementation. One-hop missile attacks
apply production damage after ground forces reach zero and logically destroy a
planet when all three rates reach zero. This file remains the evidence and
compatibility record.

## Results

Controlled sessions in the unchanged original YT 3.6 establish:

1. Missiles left after ground defense reduce each of the three production rates
   by a separate random draw times 2,000 per production round. They do not each
   cause a fixed 1,000 loss or automatically receive the original volley size
   after previous interception phases.
2. After the loop, each negative rate is clamped to zero. There is no minimum-one
   repair in this path. A planet can survive with one positive rate and two zero
   rates.
3. Each corresponding cargo warehouse is capped at ten times its post-impact
   rate. A zero rate therefore clears that cargo stock. Smaller stocks are not
   increased to the cap; lazy growth can still add stock before impact.
4. All three rates at zero trigger destruction: the planet record's active-name
   length (offset 85) and the sector's planet-slot reference (offset 93) become
   zero. The raw name bytes, governor and weapon inventory remain in the inactive
   record. A banked destruction case also retains its 12,345-credit balance in
   the inactive record. This is logical deletion, not a complete record wipe.
5. Ore-only production is damaged. The earlier proposed ore omission was a
   static interpretation error, corrected below. Isolated organics/equipment
   production and ore generated from surplus stock are also damaged.

All cases launch 20 missiles into adjacent sector 101 from sector 100, start with
100 missiles and 500 turns, and persist 80 missiles and 499 turns. Attacker cash
remains 1,005: these fixtures show no credit salvage from bombardment/destruction.
Planet owner remains original player record 3, including in inactive records.

## Captured cases

The fixed DOS clock begins at 10/24/2026 00:00:00. Seconds pass naturally before
impact. Reported loss is measured against the lazily updated planet, so it is not
always the initial fixture rate minus the final saved rate.

| Case | Initial rates ore / organics / equipment | Saved rates | Result |
|---|---|---|---|
| partial-cap | 100,000 / 100,000 / 100,000 | 74,732.796875 / 82,999.25 / 81,298.9765625 | Survives; million-unit stocks fall to approximately ten times these rates |
| partial-clamp | 1 / 100,000 / 1 | 0 / 82,999.25 / 0 | Survives; ore/equipment stocks become zero |
| destroy | 1 / 1 / 1 | 0 / 0 / 0 | Destruction message; inactive planet and cleared sector reference |
| destroy-bank | 1 / 1 / 1; bank 12,345 | 0 / 0 / 0 | Deleted; raw bank balance remains 12,345, with no attacker cash reward |
| ore-only | 100,000 / 0 / 0 | 74,731.296875 / 0 / 0 | Ore takes damage |
| organics-only | 0 / 100,000 / 0 | 0 / 82,997.75 / 0 | Organics takes damage |
| equipment-only | 0 / 0 / 100,000 | 0 / 0 / 81,297.4765625 | Equipment takes damage |
| ore-stock-derived | 0 / 0 / 0; one million ore in stock | 74,731.1328125 / 0 / 0 | Lazy surplus raises ore production before the damage phase |
| zero-production | 0 / 0 / 0 | 0 / 0 / 0 | An already-zero active planet is logically deleted |
| ore-trigger | 100,000 / 1 / 0 | 74,731.296875 / 0 / 0 | Ore keeps the production phase eligible despite organics exhaustion |

Exact saves, transcript totals, input bytes and hashes are in
[production/evidence.json](production/evidence.json). Full before/after saves are
retained as deterministic gzip files; decompression recovers the exact original
bytes. The initial ore-trigger attempt timed out at its final scoreboard; its
normal retry is included, while the excluded attempt's logs remain separate.

## Why the apparent ore omission was wrong

The production loop at `1f42:7d36` reads `1a48`, then organics and equipment from
the local production array at `58fa` offsets 8 and 12. A prior reading treated
`1a48` as an unrelated ground-production value and inferred missing ore handling.

The lazy updater explicitly loads ore field `194c` into `1a48` at
`2e79:0ac4..0acd`, with neighboring organics/equipment cached at `1a4c/1a50`.
Its indexed surplus-update loop writes those cached rates again. The missile
path calls that updater at `1f42:7a2e`, then loads the updated saved production
into its local array. The ore-stock-derived DOS case confirms eligibility even
when ore was initially zero but lazy stock adjustment makes it positive.

There is a narrower static asymmetry: ore eligibility uses the cached entry
value, while organics/equipment eligibility uses their changing damage-array
values. The missile loop never updates cached `1a48`. Thus positive ore at entry
can keep consuming production rounds even after all array rates have become
negative; with zero ore at entry, exhaustion of the other two rates ends the loop.
The readable model preserves this distinction. Exact round/RNG counts are a
static derivation, not a captured DOS RNG trace. Do not silently replace this
with a claim that ore-only planets are immune.

## Byte-level map

Four fresh REA/Ghidra reads are independently compared with the relocated MZ
image by the verifier. Original executable SHA-256 remains
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.

| Original address | Meaning |
|---|---|
| `1f42:7a27..7a8f` | Lazy planet update before copying production/cargo into local arrays |
| `2e79:0ac4..0ae7` | Load saved production into cached ore/organics/equipment values |
| `2e79:0d9e..0e10` | Indexed cached-rate array setup in the lazy updater |
| `1f42:7d36..7de5` | Eligibility and three independent random losses, one missile consumed per round |
| `1f42:7df2..7e89` | Per-category negative clamp and stock cap |
| `1f42:7efc..7fa5` | Save rates and cargo back to the planet |
| `1f42:7fa8..7fe4` | Test all three post-clamp rates for zero |
| `1f42:7fe7..8058` | Clear planet active-name length and sector planet reference |
| `1f42:805b..8083` | Destruction report |

The cached-rate write following the indexed setup is also visible in the
preserved runtime-aware listing at `2e79:0e3e..0e7a`. Byte reads are evidence of
shipped instructions, not a decompilation of the QuickBASIC runtime or an emulator
trace of every operation.

## Implementation decisions

- World version 9 permits individual zero-rate categories. Version-8 worlds
  upgrade in memory without rewriting read-only loads; the next successful write
  persists version 9. Lazy and daily updates preserve zero rather than forcing a
  minimum rate of one.
- Apply lazy growth before impact, consume missiles across phases only once,
  accumulate random losses before final clamping, and cap each cargo type using
  its own resulting rate. Preserve one shared calculation budget.
- Destruction atomically removes the planet record, clears its sector link and
  revokes every landing session referencing it. Modern deletion discards the
  inactive residual inventory rather than retaining an inaccessible record.
  It does not transfer bank, inventory or credits, and does not kill the owner.
- The recovered cached-ore round-count asymmetry is preserved. A symmetric
  live-rate termination rule would be a modern policy change.
- Missiles left after the production loop ends dissipate; they create no extra
  effects or refund. Route continuation after destruction remains a later scope.
- Do not infer ship damage, estate transfer, faction behavior, return fire,
  allied-planet targeting or route continuation from these isolated planets.
  Wider/mixed encounters remain a separate research and implementation milestone.

## Verification and limits

Ten sessions completed normally across eleven DOS process attempts. One timeout
at the final scoreboard is excluded; its completed retry is included.

Run `python3 scripts/verify_production_evidence.py` without DOSBox or REA. It checks
full save hashes, input/transcript identities, normal completion, launch cost,
printed totals, clamping, stock caps, category isolation, logical deletion and
original relocated bytes. Five separate injected-RNG model fixtures verify the
readable algorithm; they are not extra DOS sessions.

For fresh experiments, first prepare a new disposable directory using
`scripts/prepare_recovery_workspace.py`, then run
`research/yt-missiles/production/run_cases.py <new-recovery-directory>`.
The runner uses the existing local DOSBox/KEYFEED tools, creates new fixture/result
directories and refuses existing ones. Never run it against the immutable archive.
Original RNG capture, bit-exact MBF32 rounding, larger/fractional numeric
boundaries and routing after destruction remain open. Native BBS acceptance is
also still distinct from the local PTY smoke and race-tested transaction.

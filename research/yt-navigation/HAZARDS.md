# Disruptions, scanner damage and automatic mine escape

Recovered 2026-10-26 from the original Yankee Trader 3.6 executable. This extends
[the encounter research](ENCOUNTERS.md); no Go combat hazards were enabled.
The [manifest](hazard-dos/results.json) retains **46 completed DOS sessions and
92 full before/after save snapshots**, plus inputs, transcripts and emulator logs.
All executable copies remained unmodified. Original YT.EXE SHA-256:
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.

## Disruption warnings and forced escape

The initialization listing at sub `1f42:c083..c0d8` assigns two session disruption
locations independently as `integer_part(RND * (sector_count - 2)) + 2`.
It does not reject duplicate locations. For ordinary counts above two this
selects sectors 2 through N-1. These are session variables, not sector mine fields.

Five probes use an explicitly constructed two-sector fixture, making both
locations sector 2 without patching code or forcing RNG returns. The header
describes 50 player slots, two sectors and no ports/planets. Sector 1 links to 2;
sector 2 links to 1. This is a bounded fixture, not a claim about the DOS universe
generator producing a normal two-sector game.

| Case | Result |
|---|---|
| `hazard-disrupt-scan` | S reports sector 2 and a space-time disruption; position 1 and 500 turns remain unchanged. |
| `hazard-disrupt-no` | Scanner reports disruption and asks whether to enter sector 2. Fresh N preserves position and all turns. |
| `hazard-disrupt-yes` | Fresh Y enters; the black hole forces warp without the manual W confirmation. Three warps eventually return to sector 1, leaving 262 turns. |
| `hazard-disrupt-bare` | Without a scanner, the move offers no scanner confirmation and follows the same three-warp escape, leaving 262 turns. |
| `hazard-disrupt-last` | The move spends the last turn. Three automatic warps still execute at zero turns and eventually return to sector 1 with zero turns. |

Normal movement costs one turn. Each forced warp separately commits its recharge
cost; it can land in the disruption again. The last-turn case distinguishes this
automatic path from manual W, which refuses to engage at zero turns. None of the
disruption probes damages shields or changes the scanner flag.

Static anchors: main `1000:0833..0880` handles the black hole and unconditional
warp call; sub2 `2e79:19bd..1a07` reports scanner disruption; sub
`1f42:5bac..5bf6` reports it on sensors. Safe destination selection, zero-turn
forced movement and repeated hazards need an explicit modern policy before Go
hazards are enabled; the original loop is not an acceptance requirement.

## Scanner damage

Twelve shielded single-mine cases, twelve unshielded single-mine cases, twelve
small-ship cases, four shielded twenty-mine cases and one ten-hold case use the
existing sector-100/101 navigation fixture. Each entry is separately confirmed.
The initial mine stock is one, or twenty for the burst series.

- All 25 unshielded cases destroy an installed scanner. The message agrees with
  the saved scanner flag changing from -1 to 0.
- The twelve shielded single-mine cases retain their scanners. Three of the four
  twenty-mine cases lose the scanner while shields remain positive. The losses
  occur without losing position, holds or normal turn accounting.
- Twenty mines resolve as nineteen bursts: two mines initially, then one per
  subsequent burst. All four burst cases finish with zero sector mines.
- Scanner loss is not a warning cost. Cancelled disruption entry preserves it.

The interpreted shielded branch at `1f42:66a5..66ff` tests an installed scanner
and `RND > 0.95` after a hit leaves positive shields. The unshielded path at
`1f42:687b..68be` clears an installed scanner directly. The first shield-collapse
branch bypasses that shielded random check; this detail is a static observation,
not a separately isolated collapse test in this suite.

These samples establish both loss paths and persistence, not an empirical
failure probability or scanner behavior under every combat weapon.

## Automatic mine escape

The branch at `1f42:6bfc..6c2e` tests **post-damage holds below ten** and a random
draw above 0.8, then calls emergency warp without a manual confirmation. Both
conditions matter. The readable [research model](encounter_rules.py) tests the
threshold/equality branches with injected draws; it is not an MBF/RNG emulator.

The twelve larger unshielded ships do not escape. Three small-ship cases do:

| Case | Saved sector | Turns | Remaining holds | Outcome |
|---|---:|---:|---:|---|
| `hazard-small-clock-02` | 2434 | 0 | 8 | Automatic warp followed by natural meltdown |
| `hazard-small-clock-06` | 1333 | 455 | 8 | Normal automatic escape |
| `hazard-small-clock-08` | 1480 | 398 | 8 | Normal automatic escape |

Each began in sector 100 with 500 turns and nine holds. In the normal cases,
one movement turn plus the reported recharge exactly equals saved expenditure.
The meltdown consumes the remaining turns and still saves the destination.
All damage cases retain a zero death marker; the observed moves are escapes,
not respawns. The ten-hold starting ship falls to nine holds but does not escape,
consistent with the additional random gate. This does not experimentally isolate
the exact equality-at-ten branch; that boundary comes from the decoded condition.

Fighter-encounter escape, death ordering under lethal damage, next-day engine
recovery and all-weapon scanner behavior remain separate research. Do not expose
hazards before authoritative combat/death/session invalidation is implemented.

## Reproduction and verification

```sh
python3 scripts/recover_navigation.py /tmp/yt-hazards-new --hazards
python3 scripts/verify_hazard_evidence.py
```

The destination must not exist. Each case has a recorded graph and field patches;
clock series begin at their named hour on DOS date 2026-10-24. Other cases start
at 00:00:00. Repeated normal quit input handles animation consuming typeahead.
Random outcomes can differ on replay. Only completed sessions were packaged.

[REA byte evidence](encounter-rea/hazards.json), from Ghidra 12.1.4, cross-checks
the shielded and unshielded loss branches, automatic escape predicate/call and
disruption generation. Addresses are linear DOS analysis coordinates using load
segment 0x1000, not file offsets. The ephemeral session was closed.

Verification covers source/executable/feeder identity, input/transcript/log and
snapshot hashes, patched graph/state, scanner persistence, zero-turn automatic
movement, mine depletion, recharge accounting and non-respawn death markers.
Negative controls restore a destroyed scanner or give an escaped ship ten holds,
recompute the snapshot hashes, and still fail semantic verification.

Validation on 2026-10-26 passed the hazard, encounter, follow-up, navigation and
avoid-list evidence verifiers, all 4,682 archived checksums and `git diff --check`.
The two semantic negative controls also passed. Go gameplay remains unchanged.

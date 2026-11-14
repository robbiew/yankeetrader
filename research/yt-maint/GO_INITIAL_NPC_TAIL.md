# Bounded Go initial no-hiring NPC tail

`qbmaint.ReplayInitialNPCTail` ports the existing independent Python reference's
initial no-hiring tail. It consumes one eager draw per positive physical Xannor
defense, then one super-planet lottery gate draw. A gate at or above .5 reseeds
the next helper-one sample and selects player record 2..51. The selected player
is inactive in this profile, so no super-planet is constructed and no world or
auxiliary bytes are written by this slice. Nil candidate clock is required when
the gate skips; a qualified raw clock is required when it selects.

## Evidence reused and limits

The recovered [sequence](sequence-native/FINDINGS.md) identifies eager RND46af
before the owner test and the equality-accepting lottery gate at 537e..538b.
The existing [NPC replay](../../scripts/replay_maintenance_npcs.py) already models
these draws and conditional unnamed-player selection. The initial capture
profile has zero port treasuries, no hired Mercenaries and twenty distinct
positive Xannor deployments. The API rejects funded ports, active players,
human/foreign defenses, missing groups, pending revenge and a missing modeled
Mercenary Base. Original native observations, hashes and acquisition sources
are unchanged; no captures or binary queries were added.

Inputs are the independently modeled post-base world, a 24-bit post-placement
state and an optional next raw helper TIMER. The function returns statistics
only and never mutates the world. Errors return zero statistics. It does not
implement tax-funded hiring, human desertion, active-player lottery outcomes,
auxiliary reports, arbitrary NPC worlds or playable maintenance policy.

## Whole-world composition

The portable fixture authenticates the base/mobile/source/clock chain and
retains 29 complete native YTDATA SHA256 oracles. Its final state, lottery value
and candidate are independent Python-model expectations, not newly measured
native endpoint witnesses. The original three late-clock Wanderer-combat runs
remain authenticated parent evidence but are excluded from this Go composition.

Go tests construct the before-only Wanderer, Xannoron, mobile-group and base
prefixes, verify the no-write tail and its RNG handoff, then compose Go clean
ports and inactive ranks using the qualified per-phase calendar/timer inputs.
All bytes of each final YTDATA world match its native digest, with no masks,
patches, target-derived inputs or normalized raw residues. Port/rank writers
commute with these admitted NPC operations because their byte ranges and
profile inputs are disjoint. This is bounded complete-world-file parity, not
complete six-file maintenance, DOS save loading or production integration.
Modern gameplay/save format 35 is unchanged.

Synthetic inverse-RNG inputs exercise exactly .5 and one RNG quantum below the
gate; they are labeled synthetic tests, not new native captures. Admission tests
cover both conditional clock inventories and atomic failures. Exporter corruption
controls bind state, clocks, branch, source/profile inventories and whole native
world identities.

```
python3 scripts/export_npc_tail_fixture.py --check
python3 scripts/test_export_npc_tail_fixture.py
go test -race ./internal/qbmaint ./internal/qbrng ./internal/qbmbf ./internal/qbinit
go vet ./internal/qbmaint ./internal/qbrng ./internal/qbmbf ./internal/qbinit
```

Next audit: the existing auxiliary-file Python writers and six-file before-only
composition. Check existing evidence and open PRs before migrating them; do not
repeat the completed ordinary initial NPC world/RNG sequence.

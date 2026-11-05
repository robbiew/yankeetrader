# Initial-maintenance NPC record synthesis

Worker owns scripts/replay_maintenance_npcs.py only. No branch switch, commit or
publication. The script creates a research bytearray from BEFORE only, measured
helper TIMER inputs and original executable constants/writer rules. Its synthesis
function never opens or receives a post-maintenance target or a patch list. CLI
comparison receives an after-world only after synthesis, for independent checking.

## Scope and API

synthesize(before,h1_timers,h2_timers,day=306,*,xannoron_timer,
           initial_state=0xc805,expected_old_states=None)->(worldbytes,statistics)

The beforeworld may already contain independent port updates. It must retain the
initial inactive50player/100planet fixture, original sector graph, tracked10000HQ
force, noexistingmobilegroups and noordinaryporttreasuries. No production save is
created. Arbitrary active-world NPCcombat, protected retry/planet saturation and
lottery success are rejected or outside this selected slice. Raw helper TIMERs
are used to compute RANDOMIZE, retaining derived oldstate lowbyte. Optional old
state arrays assert all41+19 reseed boundaries against prior independent probes.
The code reconstructs each four-draw shrinking allocation and each directed BFS
route in original column order; no final strengths, target sectors, path lengths
or after-world bytes are copied from observations.

## Native packet

Fresh REA/Ghidra12.1.4 read_bytes Evidence in rea.json:
-0x11d9d length436, ev_72238fc8070c6b162c4287f1f769228fd14978ef5b6242b90236532d69bcb631
 Wanderer restoration writer, ending1f51exclusive.
-0x1213d length677, ev_44dd0f0160573818d2402df611ae5b714ef46dea9d8882dc410c0150d8247a14
 Xannoron creation/time/rates/random ground/bank/final write, ending23e2exclusive.
-0x141c1 length695, ev_b2b664b352246ce2c2a9362f229e708b25187e7863f394cd5fab0dc507942ca3
 Mercenary Base restoration/destination/owner/refill writer, ending4478exclusive.

All3 reads independently match original YTMAINT.EXE bytes after in-range MZ
relocations at load segment1000. Target SHA256:
8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6.
Existing sequence/chronology native packets anchor helper algorithms, group-loop
indices, player scan eagerness and actual movement-array writes. This packet
adds record writers; it is static evidence, not an execution trace.

## Raw numeric residues and inherited fields

The embedded DS mapping DS7e60->source8e30 gives source=DS+fd0. Read preserved
constants from that hash-checked original, rather than canonicalizing numeric0:
-Wanderer zero82b0 is00001c00; cargo57/61/65,missiles69,ground77,mines125 copy it.
  Owner73 is later overwritten from canonical zero7f58 at2015..2024.
-Base zero8742 is0000a000; cargo/missiles copy it. Mines125 use distinct874e
  raw00003e00 after bank25M. Positive rates/ground/bank use original constants.
-Xannoron zero8386 is00007000 for cargo/missiles; mines125 canonical zero7f58.
-Xannoron time89 executes TIMER2186 /60 then INT2196. Measured rawTIMER
  cdcc4c7c(.05) from parent's new218e probe produces single0.000833333...;
  INTnumeric0 clears exponent but preserves mantissa, yielding0e745a00.
-All untouched fields remain inherited from each inactive slot. In particular
  planetfield81 remains original configuration day305, not0.

Historical doc correction: research/yt-wanderer/rea/NATIVE.md presently lists
field81 as reset during regeneration. The bounded writer does not address
FIELDdescriptor1890/offset81; complete before/after bytes and synthesis preserve
305. Parent was notified to correct that claim with new evidence in this update.

## Derived baseline outcomes (verification, not model inputs)

Wanderer1095. Xannoron groundfloor(R1*250)+floor(R3*25)=197+15=212;
banksingle(single(R2*10M)+100K)=1100336.5. Topfallback1314.
RemainingHQ1608.19mobilegroups total8392, conserving original10000.
All19 destinations/forces and all496 directed route edges are synthesized from
seeded draws and beforegraph. Each entered-sector scan consumes50eager player
RNDs, including group20's ordinary exclusion. This selected run never takes its
pre-step endpoint bypass; traversal exits after the final entered sector scan.
Candidate draws950; ordinary interception24800; desertion20; lottery1.
Total draws25891 and finalstate4307ee. Mercenary Base2598. Lottery.2618397474
fails its one-shot .5gate, so no further award draws or record changes.

Group final writeback stores location pointers in sector records1..20 offset105,
adds force to destination fields81, and writes owner-1 field85. Group20 endpoint
increments sector1314 offset129 to1. Retained warps, port links, other sectorfields
and all97unusedplanetrecords remain exact inherited bytes.

## Validation completed

python3 scripts/replay_maintenance_npcs.py --xannoron-timer-hex cdcc4c7c
 --compare research/yt-maint/sequence-controls/baseline--untouched/after-YTDATA.DAT.gz

Comparison is exact:
-3000sectorrecords:411000bytes,0mismatches,
 SHA256b53e6d6ad9642cfcaeb60a66799dff0af2c75f254f8fda28d18e4dbf6220a18e.
-100planetrecords:13700bytes,0mismatches,
 SHA2566d48986c82e70b53cfec10f8ea46a4bc367251ccc9dd6f11cd538652761196ae.

The same synthesized bytes independently match the chronology untouched world
and parent's fresh /private/tmp/yt-maint-record-inputs/untouched after-world in
both blocks. New independent repeat may be compared once returned. Source compile
check passes. No claims about full-world equality, port/economic synthesis or
auxiliary output are made by this component; parent integrates those separately.
No full Go/gameplay tests were run for this research-only component. Native
production BBS/Windows acceptance, general MBF and complete active-world combat
replay remain separate.

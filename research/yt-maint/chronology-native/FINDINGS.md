# Mobile Xannor phase chronology: static anchors and probe locations

Independent read-only native question. No DOS execution was performed by this
worker; parent owns dynamic measurements. Original YTMAINT.EXE SHA256
8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6.

## Retained observations

Two fresh REA/Ghidra12.1.4 read_bytes records in rea.json:
-0x13113 length529 (main3113..3323),
 ev_98fc8b0a3fcd219b71baf0bda38e8b767819a5358462e2c21e9c556b3e9151ac.
-0x139d4 length1116 (main39d4..3e2f),
 ev_658ad14a8bd6dcde639d4f4ed3d0b1d6a29c37ce681e7e947b659598d786bae5.
Both independently match original bytes after applying in-range MZ relocations
for load segment1000. Existing previous-milestone reads cover3311..33cb and
3b94..3c8f. Runtime-aware interpretation also uses the immutable historical
archive/analysis/yt-maint/qb-annotated.txt and already-correlated mobile/revenge
research reports. These byte observations are static, not execution traces.

## DS variable map

All following scalar numeric values are four-byte MBF singles. QB3f75 converts
them to integer indices when indexing arrays; QB3f7d storesFAC,3f7b copies single.

7b8c: current mobile group index, initialized2 at3113..311b; loop increments
       at3e0e..3e14, stores/tests through3e2b, returns311e through group20.
7bb4: selected final target sector before route construction.
7b68: reused numeric temporary; at group-selection entry holds random sector
       bound, at34xx/3a03 route traversal holds pre-step group source sector.
       At3c0e it remains the pre-step snapshot, not necessarily new current sector.
7b6c: reused helper result; fallback/candidate result before adoption.
7bc0: candidate player-scan index (2..player record boundary).
7bbc: candidate player-scan upper bound copied from18dc.
7bf0: ordinary interception player-scan index (2..player record boundary).
7bec: ordinary interception upper bound copied from18dc.
7be8: temporary group-index argument copied from7b8c before movement/ship helpers;
       it is NOT a sector variable.
7bc4: route target before BFS, then successor/next-sector temporary at3a03.
7bc8: BFS current queued sector (not route-hop counter).
7be4: BFS neighbor temporary (not route-hop counter).
7b18/7bcc: BFS queue head/tail temporaries, not a persistent route-hop count.

Mobile array: single at1c52+4*group is current sector; single at
1c52+4*(group+21) is strength. Do not mistake7be8 for current sector.
Cached players:18f4+4*playerRecord is cached sector;
18f4+4*(playerRecord+101) is cached cloak.

Path workspace:1cfa array has two3001-element portions; second base is4bde
(1cfa+4*3001). BFS initially uses the second portion for queue entries; route
reconstruction38dc..394d overwrites it with a successor map. During traversal,
next sector is single at4bde+4*currentSector. Endpoint maps to0. There is no
obvious standalone scalar route-hop counter. A dynamic claim about path length
must count traversal boundaries/map transitions, not just reuse a BFS temporary.

## Exact chronology around the group and player loops

1.311e..31e5: missing location/force can allocate through7939 at319e;4draw count
  stored3187=MBF4. Successful allocation installs configuredHQ as group location.
2.31e6..3227: choose fallback via78f3 at3205, retry if equal to current location.
  This is distinct from later candidate selection.
3.3234..33eb: one candidate attempt ordinarily,25 if revenge flag nonzero.
 78f3call327f obtains candidate. Sector force/owner/planet predicates may set
 preferred7bac. If preferred already nonzero,330e exits candidate search.
 Only otherwise3311..331f initializes upper bound/player loop starting2.
 Per-record3348 draws eagerly before combining sector match/cloak/revenge.
 Accepted player breaks; all-failed scan advances to52 after50visits for limit51.
4.33ee..347f adopts eligible preferred, group/revenge/preselected overrides and
 low-HQ override.34e5 calls route builder34eb;34e8 dispatches39d4 traversal.
5.39d4..3a00 skips traversal if currentsector's successor is0.3a03 guards force
 and location validity.3a5e..3a94 can bypass ordinary action/scan at group20's
 preselected target.3a97..3add derives source7b68, successor7bc4 and group7be8.
6.3b07 calls71af (mines/sector defense).3b33 then calls5efd (planet).
 Existing annotated71af at7255..7266 stores destination argument into group's
 array location before later action. Thus capture array location or7bc4 to
 observe arrived sector;7b68 remains old source.
7.3b3b..3b91 aborts further ordinary scanning for killed/invalid group. Otherwise
 3b94 copies51 upper bound,3ba2 initializes player loop2 and3baa begins a visit.
3bd6 constructs mismatched-position mask;3be6 constructs group20 exclusion.
These masks do not bypass RND3c0e.3c13 resolves cloak comparison (INLINE80);
3c1f combines rejection masks,3c23 selects eligible5811 ship-helper call3c66.
3c74 advances player,3c7c stores next index,3c86 compares limit,3c8d repeats3baa.
8.After completed player scan,3c90..3ca5 compares actual group location with
selected target7bb4. If not target,3cac repeats3a03 for next successor step.
At target, group20/top state may separately call5811 at3d15.3dc0 tests protected
positive location/force:3e0b can reroute same group via31e6; otherwise3e14 increments
group and3e2d starts next group's311e allocation check.

## What496 scans can and cannot prove

Parent's prior independent counters show24800 RND3c0e executions and no combat
helper RNG sites in the inactive-player fixture.50 cached players per complete
scan gives496 complete scan passes. The static group20 exclusion is eager: a
transit visit can still consume50draws even though no ordinary interception is
allowed. Group20 endpoint bypass3a94 is separate and can omit a final scan.
Consequently496scans is not automatically496route edges, nor may the final13scan
block be attributed to group19 without observing7b8c. With parent blocks indexed
across19groups, the expected actualgroup sequence is2..20, so finalblock belongs
to20. Stop probes observing7b8c/7bf0 at3c0e can settle attribution directly.

## Safe five-byte interrupt hook boundaries

The existing hook relocates exactly5bytes and only works for runtime dispatches
with no additional inline bytes. Good candidates:
-3199: argument setup before allocation call319e; sources7b8c,7b68,7bb0.
-3200: setup before fallback3205;327a: setup before candidate327f.
-3317: candidate upper-bound copy;331f: candidate loop initializer.
-3348: candidate RND (pre-draw state);33c0: post-player-loop preferred check.
-3b9a: ordinary upper-bound copy;3ba2: ordinary loop initializer.
-3c0e: ordinary RND(pre-draw);3c74: loop increment after eligibility/helper.
-3c93: group conversion immediately after completed ordinary scan.
-3e14: group increment;3e1c: group assignment/test.
Sources7b8c,7bc0,7bf0,7b68,7bc4 and known per-group array element addresses are
all four-byte numeric snapshots. Loop-init hooks fire before the new playerindex
is assigned, so capture index at RND, not init, for first-player identity.

WARNING:3c13 QB3f/a5 consumes extra INLINE80 at3c18: total6bytes. A5-byte
relocated instruction reads trampolineE9 instead of its real inline argument.
3c16 is inside that dispatch, invalid.3c08 likewise has INLINE80. Do not use
these with the existing five-byte hook.3c74 gives state after the eager draw
only if5811 has not consumed additional RNG; this must be constrained/validated
for a no-combat fixture, not asserted generally. The next RND's pre-state can
also constrain chronology without claiming a single simultaneous trace.

## Final packet: third focused observation and explicit argument proof

Final rea.json contains3 fresh observations (not4); the third is:
0x171af length188 (main71af..726a),
ev_de4563c2b8f859f2df6603802b0a7aa0b73f8fcc4978996cf2685d7700edd827.
All3 records were checked against the relocated original. Original snapshot of
four reads from the preceding milestone is separate and unchanged.

The31xx range is529bytes ending0x13324 exclusive, not530bytes. The39xx range is
1116bytes ending0x13e30 exclusive. The new71xx range ends0x1726b exclusive.

Movement call3b07 supplies:
[BP+12] group-index pointer7be8;
[BP+14] next-sector pointer7bc4;
[BP+16] old-sector pointer7b68;
with arraydescriptor base1c52 and strength-index offset21.
71b7 copies group index into7d10.7250 converts group tointeger;7255/7257 multiply
by4;725b loads next-sector pointer[BP+14];7261/7266 stores that numeric value into
array[group]. This is why post-helper cachedsource7b68 and actualarraylocation
can differ, and why7bc4 is a useful arrived-sector snapshot in the bounded pilot.

Group start is explicit:3113 loads constant7fd0 (MBF2),3116 preparesloopvalue,
311b jumps3e19, which stores2 into7b8c and compares withMBF20 before311e body.
Thus19blocks indexed0..18 are actualgroups2..20, not1..19. Group20's ordinary
exclusion3be6 contributes a rejectionmask but still executes3c0e; endpoint
bypass3a94 is a separate path. These are static code facts; the parent's first/
last stop snapshots are needed to verify which paths ran in each tested world.

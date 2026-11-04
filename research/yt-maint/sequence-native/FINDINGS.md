# Maintenance sequencing static anchors

Read-only static investigation; no target execution by this worker. Original
YTMAINT.EXE SHA256 8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6.

Fresh REA/Ghidra12.1.4 read_bytes observations (full evidence in rea.json):
- 0x178f3 length240, ev_83e7420f94915b498d61fcbb597e0831fb3d83484d6aa35185ade10ee43a0060
- 0x11f51 length120, ev_9f4084c0abfb6edb2d20a37178f239ce0f341f028d23dd433e5effb979bdde70

Both reads independently matched original source after applying all in-range MZ
relocations at Ghidra's load segment1000. The first range includes both helpers;
the second includes the Wanderer caller and its exact retry branch.

## Helper control flow

Module-relative offsets (REA address subtract10000):
78f3 enters;78f8 TIMER;7900 RANDOMIZE;7908 RND(1);7933 far-return4.
This helper has no backedge and draws exactly once per entered normal call.
7939 enters;793e TIMER;7946 RANDOMIZE;794e/795c inspect both input values for0.
If either is0,796d branches79d8 -> far-return6 without initializing output.
Otherwise initialization7970..7983 precedes the loop. RND at7989; the output at
79ac becomes the next bound,79bf updates loop counter,79d1 compares counter to
saved count, and79d6 JNA7986 is the only loop backedge. This is repeated shrinking
bounds, not a candidate-occupancy rejection loop. Existing confirmed controls:
research/yt-xannor-mobile/RECOVERY.md count4 and HQ bound;
research/yt-mercenary-maintenance/RECOVERY.md count2,bound10000 per mine;
research/yt-xannor-lifecycle/RECOVERY.md zero-bound stale output.

## Wanderer occupancy retry

1f51..1f63 takes sector-count into helper argument storage7b68.1f76 pushes output
7b6c and bound7b68; far call1f83 targets78f3.1f8b..1f98 emits optimistic receipt
before occupancy validation.1f9d..1fb9 indexes/reads the selected sector.1fba loads
FIELD descriptor189c, runtime3d/19 at1fbd retrieves its value; runtime3f/a9 at1fc2
compares with0; JA1fc7->1f76 retries only when positive. Accepted1fc9+ writes MBF1
to descriptor189c (planet-slot link at record offset93).

This selected path rejects only positive planet93; it does not reject Earth,
fighters,mines,ports,disconnected routes,or the former source. Source unlink is
before selection. No finite retry budget appears in this loop. These existing
semantic claims were already corroborated in research/yt-wanderer/rea/NATIVE.md;
the new byte read anchors exact sites for the dynamic follow-up.

## Literal far-call inventory

A bounded raw main-image search for9A<helperLE> plus aligned context finds:
78f3:1f83,26a3,2ddf,3205,327f,4375,4541,48ca,53af,543d,549a,730d.
7939:319e,4a9f.
This inventory is static literal encoding coverage, not proof that all calls
execute, nor coverage of indirect/computed calls. Parent should measure hits.

Additional caller loops include2e62->2dd2 and3227->31e6. Their semantics require
context and must not be attributed to the Wanderer selected path.

## Tool notes and limits

MCP advertises stale JAVA_HOME25.0.5.0.2, which is absent. Existing CLI process used
installed25.0.5.0.3 without changing configuration. Initial sandbox CLI failed at
Swift module-cache ownership preparation; the authorized escalated rerun worked.
Original artifacts and all repository files remained unchanged by this worker.
CLI processes completed and owned sessions cleaned up automatically; no MCP target
was opened. Raw ndisasm output is not authoritative for QB pseudo instructions:
each CD3[def]xx9090 encodes a5-byte runtime dispatch and ordinary x86 disassembly
misinterprets its inline selector. main-masked.asm is a disposable navigation aid,
not source/native evidence or an executable.

## Follow-up: dynamic high-count site interpretation

Parent independently measured baseline site counts3348=950,3c0e=24800,
46af=20,537e=1,helper78f3entries41,helper7939entries19/draws76. These counts
are parent runtime observations, not measurements made by this static worker.

-3348 is candidate discovery's eager cached-player cloak draw. Loop initialization
3311..3324 sets limit from18dc and starts at record2; step33a1 and comparison33b3
return33ba->3328 until limit or accepted preferredsector. The cached player slots
2..51 give50 records in this fixture.19groups*50=950 fits a complete failed scan
for each active group2..20. Evidence/semantics: existing
research/yt-xannor-revenge/RECOVERY.md Candidate search and eager random draws.
Fresh read0x13311 length187 ev_586646966304423964e134343ec3104f96e2fe82e9c7c3b2cd48e4951404e7a6.

-3c0e is ordinary interception's eager cloak draw.3b94 sets loop limit from18dc,
3ba2 initializes record2, and3c74 increments with3c8d->3baa backedge. Each visited
cached player consumes a draw even if its position mismatches or current group20
is excluded; those predicates are ORed into the mask before/after the eager draw.
3c1c JBE accepts equality with cached_cloak-.33 (existing native/runtime recovery).
24800/50=496 complete fifty-record scan passes is the safe arithmetic relationship;
calling496 the exact route-hop count additionally needs route-boundary evidence.
Fresh read0x13b94 length252 ev_1033598d6eb1a65c191cf946d6a3a4455616507ac1442d12a0ada20a98389519.

-46af is defense desertion. Outer4687 passes only positive fighters(field81,
descriptor1890). The owner>1 mask at46a4..46ae is combined after RND46af and
RND*100 comparison46bf. Thus positive-force groups with owner-1 still consume
the eager draw although they cannot desert.20 draws is consistent with the20
positive Xannor force sectors retained by the initial-maintenance oracle; no
claim that this is an invariant for other worlds. Existing confirmed strict
conversion predicate:research/yt-mercenary-maintenance/RECOVERY.md human groups.

-537e is exactly the one-shot super-planet lottery gate.5371 prints Running
Super Planet Lottery.5383 compares with MBF.5 and538b accepts equality; failure
jumps5761. Later individual player/planet/sector selections are separate helper
calls, not repetitions of this gate. See maintenance-lottery/RECOVERY.md.

-19helper7939 reseeds with76draws fits19missing mobile group allocations of
four shrinking-bound draws each, the recovered Group2..20 allocation phase.
The only literal allocator call is319e; the other helper7939 caller4a9f is
Mercenary mine damage (count2). This decomposition needs actual caller provenance
or phase/world corroboration before asserting19allocation calls rather than
only19helper calls. Existing initial world has no deployed mobile forces before
maintenance and all20force pointers after.

-41helper78f3 calls cannot be uniquely attributed from total alone. Plausible
initial-world decomposition isWanderer1 +top/fallback26a3one +19group fallback
3205 +19candidate327f +MercenaryBase730d one. This is an inference until measured
caller snapshots (returnIP[BP+2] equals original caller offset+5) or individual
caller counters distinguish lottery53af and conditional relocation2ddf.

Both fresh follow-up reads were independently checked against original bytes
with MZ relocations, using the same process as the first pair. The combined
rea.json now contains four records.

## Caller-provenance refinement supplied by parent's new probes

Parent now measured actual helper1 returnIPs:
[1f88,26a8] + [320a,3284] repeated19times + [437a]; helper2 [31a3]19times,
all returnCS01a3. These are parent runtime observations. They resolve the earlier
aggregate-only inference; the final base call is4375, NOT730d.

The exact caller decomposition for this baseline is therefore:
1.Wanderer destination helper at1f83 (return1f88).
2.Xannor preselected top/fallback sector helper26a3 (return26a8), before mobile
  group selection. Existing revenge RECOVERY.md identifies missing/protected/top
  failure fallback8..N; annotated2684..26c8 forms adjusted sector bound and calls.
3.Nineteen ordinary mobile-group fallback selections3205 (return320a), each paired
  with one candidate selection327f (return3284), for groups2..20 in order.
4.One Mercenary Base restoration placement4375 (return437a).
  Exact archived annotated context41e8 emits home-base creation notice,4239 names
  Mercenary Base,4304..430f writes owner-2,4314 writes150000ground,4324 writes25Mbank.
  4355..4363 derives sector count,4375 chooses candidate,439a..43a2 loads planet93,
  and43a7 JA4368 retries if occupied. This is base creation, not tax-funded fighter
  hiring (the separate new-group placement starts4534).

Sum1+1+19+19+1=41, now anchored to actual caller sequence rather than guessed from
aggregate counts. The helper2 caller319e (return31a3) is missing mobile-group
allocation;19calls*4draws=76. The mine-damage caller4a9f does not occur in this
measured helper2 sequence. No new native reads were required; final fresh read
bundle remains exactly4records. Earlier static callsite730d remains a genuine
literal helper call elsewhere in the image, but it was not hit in this baseline.

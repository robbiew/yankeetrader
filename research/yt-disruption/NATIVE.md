# Static native disruption and arrival rules

These are **static shipped-artifact observations**, not DOS runtime observations.
The immutable original `archive/dos-original/YT.EXE` has SHA-256
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
REA/Ghidra12.1.4 observed the DOS MZ initialized image at load segment0x1000.
The complete inline Evidence bundle is [rea/yt.json](rea/yt.json):15 complete
byte reads and one independently verified load-image observation. Its profile
digest is `92fec87c3e8c374652fd603898f727129f4c0cecccf8cee1c17c98a90aced029`.
No executable bytes were patched and no host-native execution was performed.

The original MZ header is3584 bytes, the load module170737 bytes, with870
relocation words and no appended overlay. An independent reconstruction applied
load-segment0x1000 to every relocation and matched all15 observed ranges byte for
byte. Original-file offsets therefore must not be compared to loaded far-call
bytes without relocation adjustment. The QB-aware historical listings under
`archive/analysis/yt-combat/{main,sub,sub2}` supply interpretations of runtime
interrupts and inline payloads; an ordinary x86 decompiler can misread those
payloads as instructions. No decompiled text is presented as original source.

## Observation ledger

Addresses below are provider-normalized linear byte coordinates. Subsegment
`1f42:xxxx` corresponds to `0x1f420+xxxx` in this loaded image.

| Surface | Linear start | Bytes | Evidence ID |
|---|---|---:|---|
| MZ image/header/relocation verification | — | entire initialized image | `ev_03514cdc41e9c75482e17cee3453202b476020e2c67335ece260857148a762e9` |
| Header sector-interval load | `0x2b1e7` |69| `ev_c383b3cc9010d8928fb340c85aa1bca9dac21793b4ff7386c413f4b9b14525b9` |
| Two session-location draws | `0x2b4a3` |88| `ev_f80bd6331599696b058befef3b93e284a7aeea115cf27f016e4659e83fd90c8e` |
| Arrival shell: disruption, mines, fighter admission | `0x1081f` |486| `ev_3846c3cab1c600a3663bae1b5ec4106925e9c47a0e651fcd2fdada0f5e3fc597` |
| Shared emergency-warp helper | `0x293e4` |1084| `ev_724b6d3c98f42409e2009dcd038214d6304acde2d8d6e9a689aaeed0d4335971` |
| Random destination helper | `0x20ef9` |34| `ev_7293ba4bb6d86c13974ef3b9ec190a4bed2e9a1215d35d183dfafaac0c8c61c2` |
| Manual-W command gate | `0x11594` |134| `ev_93413ead2540c9a5a139d4c6a853f7070e4d9449ac858e5fed1983aea978236c` |
| Sector display's disruption label | `0x24fbe` |88| `ev_e221006d6c74e2de90ff8a63e215a83c40bea5c4f1d200a6b9ae3aed36d21d82` |
| Scanner disruption/mines/fighter warnings | `0x300de` |998| `ev_534c0a4c1450ae13f9db595003eb7ce71d854fa980943812830514c9dd38d7dc` |
| Embedded MBF −2 (`a714`) | `0x369c4` |4| `ev_689478b87ee8c77374025da941c23b29b21bba507ec8f0f0b118e10abf1ee6bd` |
| Embedded MBF +2 (`a3ca`) | `0x3667a` |4| `ev_36c14920cfc1f10bed2c4f201889c331fe29acbf26654f66b78dea580dc3b652` |
| Embedded70/.75 and adjacent bytes (`c3d6`) | `0x38686` |18| `ev_3328a9c0a85b2165209b4a37faccb0712c74abd1e03e7e60d5c4b84a7133bc76` |
| Embedded +1/−1 (`a372/a376`) | `0x36622` |8| `ev_767039ced2c4ee19d2845214c1ccf4b73e8355d6db6a7faa64ebf9de03bbf6d4` |
| Exploratory initialization prefix | `0x2b49a` |98| `ev_0ed025074a690bc07b3e7e1abce61869621c6805bc067e3f2ad4a3894ce1d963` |
| Exploratory shifted display suffix | `0x24fbc` |78| `ev_14d6c6abdf8fd7b18f678b6b1f83dcbf9052e70d0683b3fd6c846db4100e0cb6` |
| Exploratory data read, text rather than intended constant | `0x36c1a` |4| `ev_e969ca529daa7d8fcbe337aff7c52457ac5c9d741fe92cf89de1886a0808a15a` |

The last three observations are retained for provenance. The shifted display
suffix is not a full helper boundary; the exploratory data bytes `65 63 6b 69`
are text and support no numeric interpretation. The correct −2 constant is the
separate `0x369c4` read. Initialized source-data mapping is DS0x6190 at linear
0x32440, hence a DS offset maps at `0x2c2b0+offset` in this image.

## Initialization and deterministic control geometry

Header loading at sub`1f42:bdc7..be0b` loads descriptors1954 and1958 into
session scalars19dc and19e0. The FIELD mapping established in the preceding
planetary recovery binds these to header bytes53 and57. In the standard fixture
they are51 and3051, so `N=header57−header53=3000` sectors.

Sub`1f42:c083..c0d8` computes two **eager independent** RND-based assignments,
first to session variable1878 and then187c. The arithmetic interpretation is:

```
black_hole_1 = INT(RND * (N - 2)) + 2
black_hole_2 = INT(RND * (N - 2)) + 2
```

No loop or predicate requires distinct locations, excludes the current player's
sector, consults mines/fighters/ports/planets, or checks reachability. For the
normal3000-sector interval the mathematical range is2..2999, excluding Earth1
and sector3000. For a declared two-sector interval, both become2 because the
multiplier is zero. For a three-sector interval, both remain2 under the usual
`0<=RND<1`/INT model. These intentionally narrow layouts are branch-control
fixtures, not proof of normal-world frequency, randomness distribution, or a
valid minimal modern Go world.

Shrinking header57 changes a record-table boundary as well as the sector count.
Changing header61 changes the planet-record base; changing header93 changes its
end/count. Any narrow-range control must explicitly remap sectors/ports/planets
and retain those patches. It must not assume the ordinary physical planet record
4053 remains the referenced planet after moving the declared base. This obtains
actual hazard branches without patching YT.EXE or BRUN30.EXE. Raw sector byte133
remains unmapped and cannot be used as a black-hole flag.

The native variables are session locals, not an identified persistent planet or
sector field. Other references in the scanned listings include sector display,
scanner, missile deflection and plasma logic; those command-specific branches
are not interpreted as part of this arrival slice. This does not claim a complete
original RNG-state recovery.

## Arrival precedence and repeated forced warp

Main`1000:081f` reloads persisted player state through local GOSUBa41c, including
player sector57. At0833..0854 it compares that sector independently to1878 and187c,
ORs the results, and bypasses the disruption branch only if both comparisons fail.
A match at0857..0889:

1. Prints `A *-BLACK HOLE-* grabs you!`.
2. Calls display routine sub`1f42:a406` for that label.
3. Calls the **shared emergency-warp helper** sub`1f42:9fc4` (linear0x293e4),
   with the same UI/string argument style used elsewhere.
4. Unconditionally jumps back to main081f, reloading the saved warp destination
   and running the arrival checks again.

The forced call has no manual-W confirmation, positive-turn or installed-scanner
predicate between the equality test and9fc4. The helper itself has no such gate.
A landing back in either session hole can therefore produce another forced warp,
including after a preceding warp has spent all remaining turns. There is no
explicit per-arrival chain counter in the observed main-shell loop. This is a
static control-flow conclusion; individual chain lengths require DOS witnesses.

Only after the sector fails both disruption comparisons does the shell read the
sector record at088a..0916. It checks mines129 and calls the existing mine helper
63e1 at0937 when applicable. Mine return can reload081f or take the death/exit path.
Fighter-owner/team admission follows at0952..09bb. Consequently mines or hostile
fighters in the **hole's sector** do not get their ordinary arrival handling before
the forced warp; those at the eventual non-hole landing still can. This ordering
must be corroborated by before/after world and transcript controls.

Planet thrusters return to the same main081f shell after their paid edge/route or
physical stop. The step helper itself does not compare1878/187c. It saves the ship
at its planned next sector, while Wanderer selection may save the planet elsewhere;
subsequent forced warp acts on the ship record, not the planet link. There is no
planet-table write in9fc4. A transported planet can remain at an intermediate
hole while the ship is forced onward. Actual saved outcomes remain a DOS question.

## Shared warp accounting and remaining numerical limits

Sub`1f42:9fc4..a400` is the same routine recovered for manual emergency warp in
[scanner/manual-warp research](../yt-scanner-warp/RECOVERY.md). It prints the engine
heat display, samples heat, selects and persists a destination, and debits recharge
turns. The existing mathematical interpretation is:

- Budget from two initial draws: `70*(RND+RND)`.
- Heat increases only on a fresh strict `RND>.75` decision; a31-mark stop causes
  meltdown text and consumes every remaining turn.
- Destination helper1ad9 receives `N=header57−header53` and computes
  `INT(RND*N)+1`, so it admits1..N, the current sector and either hole.
- One eager draw after destination selection can update a temporary on`RND>.95`;
  the recharge calculation later overwrites that temporary. It is not evidence of
  a destination reroll or override.
- A non-meltdown recharge is `min(current_turns,4*heat+INT(4*RND))`; the saved
  player turn field is the old balance minus that debit. Zero-cost mathematical
  branches are possible; a natural zero-cost sample is a separate observation.

The helper's explicit persistent writes at a3b8..a3e4 are player sector57 and
turns49. It also updates its in-memory player-position cache at a3e7..a3fa. This
range contains no direct debit of ship credits, fighters, shields, cloak or cargo,
no planet relocation write, and no ship-death routine. Later arrival/mines/combat
can have their own effects; that is not a claim of whole-command immunity.
The `engines are disabled` and `solar day` strings alone do not establish a
persistent engine-damage field or next-day repair. Variable1880 is used broadly
for UI/control bookkeeping elsewhere, and must not be relabeled as such a field
from one heat-branch write.

Exact BRUN30 random-state reproduction, floating-point evaluation order, the loop
limit's complete MBF conversion behavior and extreme numeric boundaries remain
unverified by these static bytes. The formulas describe the current research
model, with its existing boundaries; fresh DOS witnesses must establish which
arrival branches actually execute and what the persisted player/planet/hazard
records contain. Modern finite chain limits, transactional saves and receipts
are deliberate reconstruction choices, not properties claimed for original DOS.

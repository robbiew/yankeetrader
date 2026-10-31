# Native byte evidence and source interpretation

This is a static companion to the DOS controls, not runtime evidence. The original
`archive/dos-original/YT.EXE` has SHA-256
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
REA Ghidra 12.1.4 observed its initialized DOS-MZ load image at segment `0x1000`.
The complete inline Evidence is preserved in `yt.json`: 19 complete byte reads and
one verified load-image observation. The analysis session was closed after export.
No native execution, emulation, code patching or decompiler reconstruction was
performed by this track.

The byte ranges were independently checked against a reconstruction from the
original MZ file: header 3584 bytes, 870 relocation entries, each relocation word
adjusted by load segment `0x1000`. All 19 byte observations matched. A raw-file
comparison without relocation fixups would incorrectly reject captured far calls.
The preserved QB-aware listings supply interpretations of inline runtime payloads;
ordinary x86 decoding mistakes these payloads for instructions. The separate
`0x275e2` exploratory read is a shifted suffix, not the full step helper.

## Captured ranges

Address is the analyzed linear address; the second column gives the corresponding
original module address or embedded data constant. Endpoints are inclusive.

| Analyzed address / bytes | Original address / purpose |
|---|---|
| `0x12fb4` / 980 | main `1000:2fb4..3387`, thruster route quote, confirmation and loop |
| `0x274e2` / 1191 | sub `1f42:80c2..8568`, full movement step |
| `0x275e2` / 1191 | exploratory shifted suffix `1f42:81c2..8668` |
| `0x13515` / 395 | main `1000:3515..369f`, denied landing and force prompt |
| `0x2809f` / 689 | sub `1f42:8c7f..8f2f`, landing access |
| `0x28355` / 1012 | sub `1f42:8f35..9328`, ground battle |
| `0x23efb` / 135 | sub `1f42:4adb..4b61`, nested random bound helper |
| `0x28b6f` / 192 | sub `1f42:974f..980e`, own/team predicate |
| `0x20436` / 951 | sub `1f42:1016..13cc`, path search and route reconstruction |
| `0x13d14` / 380 | main `1000:3d14..3e8f`, planet command shell and inline dispatch |
| `0x1a41c` / 350 | main `1000:a41c..a579`, persisted player reload into login locals |
| `0x2b0df` / 264 | sub `1f42:bcbf..bdc6`, random-record file and FIELD bindings |
| `0x2b1e7` / 69 | sub `1f42:bdc7..be0b`, header loading |
| `0x2b45f` / 160 | sub `1f42:c03f..c0de`, suffix including two disruption-location draws |
| `0x10833` / 87 | main `1000:0833..0889`, disruption arrival and forced warp call |
| `0x37e7c` / 4 | embedded DS `bbcc`, MBF32 `52 b8 7e 80`, approximately 0.995 |
| `0x3758e` / 4 | embedded DS `b2de`, MBF32 `cd cc 4c 7f`, approximately 0.4 |
| `0x37f86` / 4 | embedded DS `bcd6`, MBF32 `00 00 a0 84`, -10 |
| `0x32450` / 4 | embedded DS `61a0`, MBF32 `00 00 20 84`, 10 |

Embedded constants use the initialized source-data mapping, not uninitialized
runtime DS: DS `0x6190` corresponds to analyzed `0x32440` and source file offset
`0x23240`. Evidence IDs and complete provider identity are retained in the JSON.

### Retained Evidence anchors

These are exact retained IDs in [yt.json](yt.json); addresses above select the
remaining observations from the same target. Static interpretations below also
use the preserved QB-aware listings and are cross-checked by the separate DOS
controls, rather than treating raw bytes alone as runtime proof.

| Claim surface | Evidence ID |
|---|---|
| MZ identity and relocations | `ev_03514cdc41e9c75482e17cee3453202b476020e2c67335ece260857148a762e9` |
| Thruster quote and route | `ev_2d2b0c088298fbf5d5effb73885995881ee8af619b0a1113b5315eb3a9178170` |
| Movement, collision and stop | `ev_888dba03d262eac91b655fe85f755516972bd150cd64d82dd83a6f2ccd9621aa` |
| Explosion random helper | `ev_fa96d7767bca1e8c198c99a2fe61d6a9966cd5c3ce07cddd2c5f9d77d643b920` |
| Denied landing and quantity | `ev_9308ee25bccb06d0059006c9f095191b6a7fd1c770e6342f6e099a0c4bae3d07` |
| Access and takeover | `ev_8165ee58132fd8bce5ddc6dbd293ef6bfc27fcd9c80ac52f7f6fbd0047db51c7` |
| Human ground combat | `ev_f594366b93b46b4e2ad46589103b5e2357d2f62c89483e24475a1713096ec7a6` |
| FIELD byte mapping | `ev_3bb91a3625e1c740b4a268475d8eca4cc15dfd2200562426bc12b913692af508` |
| Main-shell disruption check | `ev_fc086f1ab76517359254a037f2e450f142d8da1da9f2b5552569db1881074da0` |

## Record mapping: avoid linear-descriptor guesses

The FIELD sequence binds 41 initial text bytes and then four-byte numeric strings.
Most descriptors advance regularly, but the tail does not:

| Descriptor | Raw byte offset |
|---|---:|
| `1948` | 41 |
| `194c` | 45 |
| `1950` | 49 |
| `1954` | 53 |
| `1958` | 57 |
| `195c` | 61 |
| `1960` | 65 |
| `1964` | 69 |
| `1968` | 73 |
| `196c` | 77 |
| `1970` | 81 |
| `1974` | 85 |
| `1978` | 89 |
| `197c` | 93 |
| `1980` | 97 |
| `1984` | 101 |
| `1988` | 105 |
| `1994` | 109 |
| `1990` | 113 |
| `1998` | 117 |
| `199c` | 121 |
| `19a0` | 125 |
| `19a4` | 129 |

Descriptor `198c` is not bound in this FIELD sequence. Raw byte offset 133 is not
bound either. Consequently raw133 mutation controls are unmapped-field negative
controls; they do not create a black hole. Carried ground forces are player121,
cloak is player125, and the destination step's `19a4` check is sector mines129.

Black holes are two session variables, `1878` and `187c`, initialized independently
at `c083..c0d8` from a random position within the header's sector interval. The
normal arrival shell compares the player's sector to those variables. There is
no black-hole comparison inside `80c2..8568`. Actual disruption aftermath of a
planet move is not established by this slice's raw133 tests.

## Thruster interpretation

Main `2fb4..3386` asks for a destination, rejects current/out-of-range sectors,
uses path helper `1016`, displays a route and total ten-turn-per-hop cost, and
checks that the full quoted cost is affordable before confirmation. Only Y
continues the `Move the planet? (Y/[N])` prompt. No additional owner predicate
appears between planet shell dispatch (`F!MPC1234569LTAB$`) and this handler.
That does not prove universal access: normal landing admission remains earlier.

For each edge, the caller passes next sector, previous sector, stop flag, and
last-edge flag. Step `80c2` performs the following ordering:

1. Read source sector. Reject source planet slot `header[93]-header[61]` (100 in
   the standard fixture) before unlinking or charging turns. This tests the
   reserved slot, not its owner or name.
2. Read destination planet93. If positive, print the occupied-sector warning and
   set the stop flag, but continue into destruction processing.
3. Read moving planet ID, clear source planet93 and save source, then load the
   planet and name.
4. Draw RND and compare to approximately0.995. If above threshold **or** the
   collision stop flag is set, destroy the moving planet by zeroing its
   active/name-length85 and first numericized name field, save it, and emit
   public destruction news. Destination's pre-existing planet remains.
5. On destruction, invoke helper4adb with two iterations and current ship
   fighters61. For a positive initial fighter count F it repeatedly computes
   `n = INT(RND*n)+1`, replacing n each iteration. Subtract the resulting loss
   from ship fighters and save. There is no shield debit, explicit ship-death
   routine, or ten-turn debit in this failure branch. For F=0 the helper exits
   without assigning its output; any stale-output effect needs runtime evidence.
6. On success, reserved planet slot1 (Wanderer) chooses a random empty sector and
   stops the route. This original selection loop is unbounded in a full universe.
7. Read actual destination. Nonzero mines129 set stop. Nonzero fighters81 call
   own/team predicate on owner85; a nonfriendly result sets stop. These guards
   still continue with movement and do not themselves resolve mines or combat.
8. Write the actual destination planet93, then player turns49 minus10 and
   sector57 from the caller's planned next edge, saving both records. These
   destinations differ for the Wanderer: its random empty-sector relocation is
   not the ship's planned next sector. The caller stops after this committed edge
   if stop is set.

Therefore prior successful edges remain committed when a later edge fails. A
failed collision/stress edge does not reach the turn charge. A hostile fighter
or mine edge does reach the charge and movement before returning to the shell.
The helper itself makes no credit debit.

Both route completion and early stop jump to main081f. Its `GOSUB a41c` reloads
player sector57 and turns49 (among other values), followed by normal arrival
logic: disruption warp, sector mines, and fighter admission. Hence a step-level
stop is not proof that the whole command has no further damage, credit or turn
consequences. DOS before/after controls must distinguish the helper's writes
from this subsequent shell behavior.

## Landing and ground-combat interpretation

Access8c7f first runs lazy planet updating and reloads it. Zero ground, self
ownership, and friendly team ownership bypass denial. The no-governor takeover
condition is an unowned planet or a human owner's nonzero death/killer marker
at player45. This is **not** ownerTeam89=0 and not alive marker45=0. The takeover
branch sets remaining garrison to `INT(oldGround * RND * RND)` at
`1f42:8e01..8e24`, with single-precision products before integer truncation, and
can assign current ownership (save at `8e71..8e7a`). It does not subtract the
product or use a fixed60% survival factor. An
active foreign defended planet is denied and can offer forced landing.

Main3515 shows defending/carried ground after denial. With no carried ground it
returns without offering the force prompt. Otherwise it asks
`Do you wish to try to force a landing? [y/N]`, then accepts a committed force
between1 and the carried count through `Use how many ground forces? ... [0]`.
Only affirmative confirmation invokes combat8f35; cancellation is separate.

Battle8f35 updates/reloads the planet again and truncates defending ground to an
integer. It removes the **whole committed force from player121 and saves** before
public attack news and battle exchanges. While both sides remain positive:

- If a selector draw is greater than approximately0.4, replace attacker A with
  `max(0, INT(A - fresh_RND*D))`.
- Otherwise replace defender D with `max(0, INT(D - fresh_RND*A))`.

These are two fresh draws per exchange. Integer conversion follows subtraction;
`A - INT(RND*D)` is a different rule. No cloak modifier appears here. When D is
exhausted, positive surviving A becomes the planet's garrison77 and ownership73
becomes the attacker. With no surviving attacker it sets both owner and garrison
zero. On defeat it saves remaining integer D and preserves the owner. Winning
survivors are not returned to ship cargo; uncommitted carried ground remains.
This helper contains no turn debit or ship-fighter/shield/death handling.
Production, stocks and bank are not explicitly changed by battle, although the
preceding lazy update may separately accrue production.

These interpretations describe the original executable's ordering; modern
bounded loops, reserve-slot protections, live-owner/generation revalidation,
transactional rollback, replay handling and truthful post-save receipts remain
implementation decisions. No Go gameplay is changed by this native track.

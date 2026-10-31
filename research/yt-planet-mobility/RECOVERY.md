# Planetary thrusters and player forced landing — bounded follow-up

This extends the [first planet recovery](../yt-planets/RECOVERY.md) and
[earlier ground-assault recovery](../yt-missiles/RECOVERY.md). The capture milestone was research only and retained save version **23**.
The subsequent [Go implementation](IMPLEMENTATION.md) now provides bounded ordinary
thrusters and player forced landing with atomic saves and save version **24**. Every DOS run uses
an independently copied fixture; no active game or original archive was reset.

The retained corpus contains **55 normally returned controls**, 110 world
snapshots, two exact reload/auxiliary chains, 19 native byte reads and one verified
MZ load-image observation. An independent verifier reconstructs each input and
checks semantic effects, normal return, clock/keys, complete retained hashes and
MZ relocations. All **41 rehashed corruption controls** challenge and reject altered semantic or
provenance claims.
The final validation log records their completed count and command results.

## Questions and evidence boundary

| Question | Status | Evidence |
|---|---|---|
| Destination/path admission and ten-turn costs | Answered within the controlled graph | `move-*`, `turns-*` |
| Confirmation, blank/invalid targets and insufficient turns | Answered | `move-cancel`, `move-blank`, invalid-route controls, 9/10/19/20/21 turns |
| Occupied first/later destination and fighter-loss bounds | Answered for these worlds | Four `collision-*` controls plus native step/random helper |
| Owner/team/unguarded relocation access | Answered within these cases | `control-owned`, `move-teammate`, `move-unguarded`, `move-neutral` |
| Reserved slot100 and Wanderer movement | Answered within these cases | `move-captured-xannoron`, `move-wanderer` |
| Intermediate mines/fighter stops and arrival | Answered for the seeded hazards | `move-mines`, hostile/own/later fighter controls |
| Sector133 as an anomaly flag | Rejected hypothesis | Two `move-anomaly-*` raw-field controls plus native FIELD bindings |
| True session-random disruption/black-hole encounter after thrusters | Unresolved | Static arrival path exists; no targeted black-hole landing control |
| Forced-landing admission, commitment, win/loss and replay | Answered within the seeded states | `force-*`, `land-*`, two exact parent follow-ups |
| Tiny/fractional input and defenses | Answered within the tested values | `force-one`, `force-fraction`, `land-fractional-defender` |
| Arbitrary RNG/MBF parity, mid-write DOS crash or concurrent ownership change | Unresolved | Neither a finite corpus nor static interpretation establishes these |
| Safe modern implementation | Now implemented separately | [Bounded Go actions and save24](IMPLEMENTATION.md); research evidence below remains unchanged |

## Setup and provenance

The exact baseline is the archived `fixture-planet-transfer/YTDATA.DAT`,
SHA-256 `2a63d12af095a59227840946be57fd4b7e4dafb5724d4019de694da7c4194b19`:
4,151 records × 137 bytes. Player record2 is Q and record3 is Enemy. Planet slot2
(record4053) is Test Planet, initially in sector100. The declaration explicitly
sets the controlled directed graph, safe source/destination fields, current date,
ship resources and distinguishable planetary resources. Common patches, per-case
patches and full-record slot copies are retained; copied special slots have their
old references explicitly cleared. Original owners/teams/NPC slots elsewhere are
not silently reconstructed or inferred from names.

Runs preserve exact key bytes, DOS date/time output, raw CP437 logs and decoded
text, before/after world bytes, auxiliary files before/after, executable/runtime/
keyboard-feeder hashes and a batch-written `MOBILITY_PROGRAM_RETURNED` marker.
Completion requires that marker and no emulator timeout; completed actions in old
timed-out sessions are historical evidence, not counted among these returned
controls. The two children load their exact parent world and auxiliary output at
00:01:00 rather than inventing a similar fixture or rolling the clock backward.

Exploratory probe1 is excluded entirely. Its leading blank Enter at a landed
planet invoked the native default Take All command after cancellation. The retained
runner sends Q directly at that boundary. A separate fractional-defender probe
showed that admission occurred before any force prompt; its queued numeric input
then entered a cargo menu. It was replaced with a clean L-only admission control.
These corrected input streams are part of the retained recipe.

## Thruster routing, admission and cost

From the landed planet menu, `!` asks for a destination, prints a shortest path
and quotes **10 turns per hop** before confirmation. It requires enough turns for
the entire quoted path, rather than starting a partial trip on an unaffordable
quote. In the controlled graph:

| Control | Result |
|---|---|
| One/two/four ordinary hops | Ship and planet reach101/102/104; spend10/20/40 turns |
| 9 turns for one hop | Refused; sector100 and nine turns retained |
| 10 turns for one hop | Reaches101; zero turns remain |
| 19 turns for two hops | Refused; sector100 and19 turns retained |
| 20/21 turns for two hops | Reaches102; zero/one turn remains |
| Current, zero, negative, >3000 or unreachable destination | No planet movement or turn charge |
| N or blank confirmation | No movement or transport charge |
| Six-hop route to Earth | Ordinary planet reaches sector1;500→440 turns in this historical fixture |

Cancel/refusal does **not** imply a byte-identical world: landing/menu processing
still performs lazy economic updates, login news is written and logout refreshes
scores. The independent checks isolate transport resources/links and bound those
other changes instead of attributing them to movement.

Thrusters are reachable through existing landing permission. A teammate can move
a defended foreign planet. A foreign caller on an unguarded planet can move it
while its governor remains the other player. An unowned unguarded planet stays
unowned. The test does not establish that arbitrary guarded foreigners can bypass
landing permission. The 35→25-turn control retains cloak1; this thruster path does
not reproduce ordinary one-turn movement's observed cloak drop at25.

### Collision, reserved slots and successful prefixes

A first-edge collision destroys the moving planet, clears its source link, leaves
the existing destination planet byte-exact, and keeps the ship at100 with500
turns. With10,000 fighters it saves9,674:326 lost. A collision on the second edge
first commits the100→101 hop; the ship then remains101 with490 turns while the
moving planet is destroyed. The failed edge is not charged ten turns. Its sampled
fighter loss is2,678. One fighter can become zero without killing the ship; the
zero-fighter control stays zero. Shields, cargo, credits, carried ground and the
death marker remain unchanged by these captured collision outcomes.

Native code draws for stress on each edge and branches to the same destruction
path above approximately0.995. For positive fighter stock F, the two-stage helper
repeatedly computes `n = INT(RND*n)+1`, starting at F, so its result is1..F. This
is static arithmetic, not a measured stress-explosion distribution or proof of
all RNG/rounding behavior. The zero-stock helper's output assignment is ambiguous
statically; the explicit runtime zero-stock witness establishes only this case.
Logical planet destruction clears activity/name fields; other underlying native
asset cells can remain. Do not describe inactive bytes as surviving usable assets
or claim that every field was zeroed.

The standard reserved last slot100 refuses transport even after being assigned
to Q and renamed through the copied Test Planet record. This branch is slot-based,
not name/owner-based. A modern implementation should protect actual faction
identity rather than accidentally classifying every human planet at ID100 as
Xannoron.

The controlled Wanderer-slot1 branch is different from ordinary joint movement:
the slot was populated with the same controlled Test Planet record, and the quoted
two-hop route stops after its first paid edge. The ship reaches101, while the
planet appears in an independently chosen empty sector305 and vanishes from the
ship's sensors. The old slot1 reference is cleared. One observation does not
establish uniform random placement; the original search loop is unbounded when
no suitable sector exists. Go has no active Wanderer lifecycle, so this special
case cannot be labeled implemented as part of ordinary planet transport.

### Intermediate hazards and shell aftermath

The helper can stop **after** linking the planet and moving/charging the ship:

- Three destination mines stop at101 after one paid hop. Normal arrival then
  resolves all three mines, reducing shields10,000→8,859. Both ship and planet
  remain101 in this witness. The helper's stop itself did not mean no damage.
- A hostile100-fighter group stops the route at101; the later-hostile control
  stops at102 after two paid hops. The captured caller quits at the encounter
  prompt: defenders remain and no sector battle or bribe debit is claimed.
- Own sector fighters permit the full two-hop route.

Two exploratory-named `move-anomaly-*` controls set raw sector133 to1. They finish
their normal two/three-hop routes without damage, retaining that raw cell.
Native FIELD bindings prove133 is unmapped; mines are129. They are bounded
negative raw-field controls, **not black-hole tests**. Actual disruptions use
session-random locations and a later main-shell check; a targeted thruster-to-
black-hole runtime outcome remains unverified. [Native ranges and interpretation](rea/NATIVE.md).

## Player forced landing

Landing reloads and lazily updates the planet before permission. Self, same
nonzero team and unguarded access bypass assault. A defended active foreign human
is denied; positive carried ground then permits a separate Y/N force prompt and
committed-force quantity. Zero carried troops gets no force prompt. N/blank,
zero/negative/excessive quantities and junk do not commit troops or spend turns.

An unowned defended planet and a planet whose human governor has a nonzero death
marker each adopt Q without an assault in these controls, reducing100 defenders
to60 through unrest. Static access code at `1f42:8e01..8e24` sets the remaining
garrison to `INT(oldGround * RND * RND)`, with native single-precision products
before truncation. It does not subtract that product or apply a fixed60% rule;
the two100→60 observations do not establish a random distribution. Foreign unguarded and teammate controls retain their old
governor. These access/adoption branches are separate from combat; they must not
be inferred from ownerTeam0 or mislabeled a successful attack.

The commitment is removed from the ship before the original combat loop and
public notice, exposing a non-atomic native ordering. With positive A attackers
and D integer defenders, every exchange draws a selector and a separate magnitude:

```
if RND > 0.4: A = max(0, floor(A - RND * D))
else:         D = max(0, floor(D - RND * A))
```

`floor(A - RND*D)` differs from `A - floor(RND*D)`. This is human ground combat,
not missile bombardment, NPC fighter assault, surrender or a cloak modifier.
The native loop has no fixed work limit. On a win, positive surviving attackers
become the planetary garrison and Q becomes governor; survivors are not returned
to ship cargo. A losing attack preserves the other governor and remaining defense.

| Retained control | Result |
|---|---|
| Commit1000 from1000 against100 | Ship ground0, captured garrison923, governor2 |
| Commit100 from1000 against10 | Ship ground900, captured garrison92 |
| Commit10 from1000 against10,000 | Ship ground990, governor3 and10,000 defenders retained |
| Commit1 against1 | Ship ground999; attacker loses and defender1 remains |
| Enter1.9 against2 | Quantity truncates to1; ship ground999, defender2 and governor3 retained |
| Fractional defender0.25 | Admission update truncates it to0; ordinary landing, no attack or troop debit, governor3 retained |
| Owner−2/−1 at ordinary slot2 | Tested assaults capture with garrison923; not a claim about every reserved home-slot admission branch |
| No ship fighters or shields, commit1000 against10 | Ground assault still proceeds; captured garrison992; no ship-death handling |

The tested ground battles retain500 turns and sector100. No ship fighter,
shield, cash, cargo or weapon expenditure is attributed to ground combat. Planet
stocks/production may grow during the preceding lazy update; capture preserves
that economy and bank rather than bombing it. Typed public news reports attack,
actual committed forces, failure/remaining defenders or capture. Raw private
account identities are not substituted for the authenticated display alias.

`captured-reentry` and `failed-retry` consume exact parent worlds and auxiliary
files at a later clock. The former verifies owner access without another assault;
the latter verifies an additional commitment from the parent's uncommitted troops.
See the corpus/verifier for exact child outcomes. None of these tests establish
interrupted or concurrent native combat safety, exact RNG state reproduction,
maximum numeric-force handling, every rare simultaneous-exhaustion outcome or
native BBS socket behavior.

## Recovered implementation contract (completed in the linked Go milestone)

These are modern design choices, not additional recovered DOS facts. The linked
implementation records the resulting policies and validation:

1. Keep landed `!` for thrusters and the denied-LAND force prompt; main `!` already
   launches missiles and must retain that meaning. Provide clear compact commands.
2. Separate movement and ground-assault intents. Bind season/ship incarnation,
   authenticated caller, current team/permission, resources, live session deadline
   and one consumed login nonce. Thrusters also bind landing token, ordered copied
   path and relevant occupancy/hazards; ground attack binds the actual target and
   committed quantity. Reject zero/fractional/unsafe integer input deliberately.
3. Introduce a nonreusable planet incarnation if needed for slot-reuse protection.
   ID/name/owner/timestamp equality alone cannot prove that an unlanded target is
   the same planet after destruction/recreation. Cover every constructor: ordinary
   creation, both faction restorations, super-planet awards and Genesis bootstrap.
   Any such persisted allocator requires a deliberate later migration; this
   research changes no schema and allocates no planet generations.
4. Keep no-governor adoption distinct from hostile assault. Recheck actual owner
   death/unowned state rather than team0; any new Go adoption behavior must be
   explicit, with garrison/title changes saved together. Do not charge an attack
   merely because the prepare-time owner subsequently died. Prepare without
   charging or publishing. Quote persisted base/revision separately
   from lazy economic projection; do not make every confirmation automatically
   stale merely because its projected timestamp advances. Revalidate current
   permission, material defenses, path/hazards and post-lock clocks before RNG.
5. Use finite BFS/route work and check `hops <= turns/10` before multiplying costs.
   Ordinary routes are consequently bounded by available turns. Human ground
   rounds also need an explicit work budget and a documented exhaustion outcome.
   Do not silently return spent committed troops after a real defeat.
6. Build the whole confirmed outcome under the existing world lock and save once.
   A physical later-hop collision can commit its legitimate successful prefix,
   losses and logical deletion together; an injected invalid RNG/storage/validation
   failure must not leave separately saved dangling links or half an assault.
7. Maintain bidirectional planet/sector references. Movement/destruction revokes
   every landing grant on the old position, including other callers; do not
   teleport their ships. Decide explicitly whether the mover returns to the main
   sector interface or receives a new grant. Handle reached mines/hostile defenses
   through supported existing aftermath in the same atomic action where needed.
8. Use persistent faction identity for transport restrictions. Do not infer homes
   from a player's name or reused slot. Decide captured Xannoron/HQ coordination
   explicitly; moving the planet must not silently move the independent HQ or
   restore NPC ownership. Wanderer transport and unsupported disruption behavior
   remain separate until their Go lifecycle exists or safe bounds are specified.
9. Reuse epoch/ship-generation and estate cleanup for any supported fatal aftermath,
   with explicit hazard/self attribution and no invented enemy salvage. Direct
   ground assault does not kill the player's ship in these recovered controls.
10. Return accurate committed receipts for prefix/final positions, actual turns,
    troops/losses, capture/destruction and remaining resources. Preserve joined
    output/durability warnings, end fatal logins and refuse replay. Use appropriate
    typed player-assault news/report kinds; do not label player actions as Xannor.

Required implementation checks include fresh confirmation/typeahead/cancellation,
invalid/no-path/tied paths, 9/10/19/20 turn boundaries, altered permission/team/
ownership/route/hazards, multiple landed callers, concurrent movers/attackers,
planet destroy/recreate and epoch reuse, lazy-update timing, faction-home states,
collision prefix and zero fighters, bounded RNG/work faults, ground win/loss and
quantity truncation departure, rollback/durability/replay and both real interfaces.
Native Windows crash durability and live BBS gameplay remain separate acceptance.

## Reproduction and verification

```
python3 scripts/recover_planet_mobility.py /private/tmp/yt-planet-mobility-fresh --workers 4
python3 scripts/verify_planet_mobility.py
python3 scripts/test_planet_mobility_verifier.py
```

Capture requires the existing DOSBox Staging installation and refuses an existing
destination. Verification uses standard-library Python and retained originals,
without a DOS emulator, REA installation or application dependency. The verifier
defaults to the retained corpus; fresh captures do not overwrite it. New RNG/time
results need independent semantic review rather than silently replacing frozen
witnesses to make them pass. Full-world and
auxiliary witnesses supplement bounded semantics for unmodeled MBF/time effects;
they do not establish a universal maintenance formula or a new random generator.

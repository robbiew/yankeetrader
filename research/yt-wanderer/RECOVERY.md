# The Wanderer — lifecycle and special transport research

This is research, not a Go gameplay implementation. The current Go door remains
save version **24** and has no active Wanderer. Ordinary planetary thrusters and
forced landing are implemented in the preceding
[mobility milestone](../yt-planet-mobility/IMPLEMENTATION.md).

The retained primary corpus contains **57 normally returned DOS controls**,
114 before/after worlds and **nine exact parent world/auxiliary chains**. Static
corroboration retains 14 native byte observations, three verified MZ load images
and 1006 checked relocation entries across YT-INIT, YTMAINT and YT. Two separate
diagnostics retain an eight-second nonreturning pointer-saturation probe and a
normally returned maintenance run whose later Xannor attacks destroyed the
already-relocated Wanderer. These diagnostics are not counted as 57 isolated
successful controls. The independent verifier and rehashed corruption tests
check both semantics and provenance; final commands/counts are in
[validation notes](../../evidence/VALIDATION.md).

## Questions answered and boundaries

| Question | Answer in this corpus | Controls/source |
|---|---|---|
| Initial appearance | YT-INIT chains maintenance, which builds/links slot1; standalone RMT-INIT stops with it inactive until a later maintenance run | `init-defaults`, `reset-defaults`, `reset-first-maintenance`; native initializer ranges |
| Daily identification/restoration | First sector reference to slot1 controls the branch; name/activity alone do not | Linked, missing, inactive, duplicate and renamed maintenance controls |
| Ownership and bank | Relocation clears the governor; exact-zero bank refills to 250000, positive bank is preserved apart from prior production/interest | Owned/foreign/zero/one-bank controls |
| Destination eligibility | Empty planet reference only in selected code; origin, Earth, mines, fighters and disconnected candidates are admitted in controlled states | Source-only and only-candidate controls |
| Replay and clock rollback | Native maintenance reruns despite its same-day notice; backward dates can also repeat relocation and capped economic work | Exact same-day/next-day/backward children |
| Landing and naming | Owner/team/unguarded access and neutral unrest follow generic rules; slot1 cannot be renamed even after its display name changes | Landing, naming, banking and fighter-transfer controls |
| Thrusters | Require the full quoted route budget, then stop after one charged edge; ship and planet have independent destinations | One/two/three-edge, affordability, cancel and reentry controls |
| Hazards/collision | Planned arrival mines affect the ship; mines/fighters at the planet's different destination do not; an occupied planned edge destroys the moving planet | Separate planned/planet hazard controls and collisions |
| Safe modern lifecycle | Concrete bounded contract below; no new Go action/schema in this research | Current-source audit and recovered evidence |
| Exact RNG/MBF distributions, stress frequency, native crash/concurrency/live BBS acceptance | Unresolved | Not established by finite snapshots or static byte reads |

The selected empty-candidate tests deliberately saturate sector planet pointers
with duplicate slot2 references while preserving faction references. They are
**synthetic malformed-pointer controls**, not a valid universe containing3000
unique planets; the original table holds100 slots. They isolate the native
predicate and failure mode. No real game or original archive was modified.

## Data, identity and capture provenance

The source is the immutable archived `fixture-planet-transfer/YTDATA.DAT`,
SHA-256 `2a63d12af095a59227840946be57fd4b7e4dafb5724d4019de694da7c4194b19`:
4151 records of137 bytes. Slot1 is absolute record 4052; sector records start at 52,
and their zero-based field 93 holds a planet-slot reference. The initial fixture
places The Wanderer at 585. Each isolated non-parent setup explicitly moves the
reference to 100, preserves distinguishable Wanderer assets, supplies Q/Enemy,
quiets unrelated sector/port state and preserves both faction homes. Numeric and
padded-name writes are declared in the recipe; no hidden fixture reconstruction
is inferred from a name. Exact controlled bytes and full auxiliary files are kept.

Every normal control retains input keys/redirection, date/time output, raw CP437
program log, decoded transcript, normally returned batch marker, executable and
runtime hashes, and all retained file hashes. Parent controls reload their exact
parent world and complete auxiliary output before any declared patches. The
post-transport maintenance isolation explicitly sets both player score caches
to zero; this removes the large later Xannor assault from the separately retained
confounded run. It is a declared input change, not an edited result.

Repeated metadata is stored as deterministic gzip of the original complete JSON;
`recipe.json` remains readable. Two corrected-capture manifests retained complete
rows after an initial cleanup bug deleted redundant per-case metadata. Those
per-case JSON bytes were reconstructed using the identical serializer and gzip
settings from the untouched manifests, and every original referenced file hash
was checked. The runner now retains compressed per-case metadata. No experimental
values, world bytes or program output were edited to make a result pass.

An exploratory reentry input originally sent Q at a buy-planet Y/N prompt and
therefore failed to return; it is excluded from the retained normal corpus. The
corrected reentry explicitly declines with N and uses the same exact transport
parent. Fresh captures refuse an existing destination and never mount originals.

## Initialization, restoration and daily relocation

### Initializer versus season-reset program

A direct YT-INIT capture supplies `Y\r\n\r\n` through redirected input. It initializes
planet slots inactive, then invokes YTMAINT before returning to the batch. The
result has an active neutral `The Wanderer`, one sector link, rates 5000 each,
zero cargo/missiles/ground/plasma/mines/fighters and bank 250000 in this witness.
Its production day is deliberately backdated ten days.

Standalone RMT-INIT is a different program. It normally returns after reset with
no active planet slots or Wanderer link. Inactive record-buffer bytes are not
usable owned assets. An exact follow-on maintenance capture builds and links
The Wanderer. Do not attribute that later creation to the reset's earlier return.

### The reference, not name/activity, selects restoration

Maintenance scans sectors for slot1. If it finds a reference, it clears the first
one and stops scanning. A linked Wanderer moves even when active/name-length85
is zero; that case stays inactive rather than being regenerated. A renamed linked
slot1 retains its changed name. Duplicate source references are not repaired:
only the first reference is removed, another remains, and the newly selected link
can leave duplicates. This is a recovered DOS defect, not a safe Go requirement.

When no reference exists, P.H.O.E.N.I.X. restoration partially overwrites slot1:

- Name `The Wanderer`, active12, production day today minus10.
- Ore/organics/equipment base production5000 each, stocks zero.
- Missiles, owner, ground, legacy field 81 and mines zero.
- Bank250000.

It does not explicitly replace time89 or fields93/97/101/105/109/113/121/129.
Bolts, fighters and stale tail values can survive. Crucially, active planets have
already undergone ordinary production before this branch. In the stale-tail
control, the large fighter increase and small bolt/time changes precede partial
restoration; they are not new regeneration grants. The inactive/missing control
skips that production and preserves its41 plasma and 47 fighters exactly. New Go
restoration should use an explicit clean template with a fresh incarnation rather
than treating inactive DOS buffer bytes as legitimate modern inventory.

After selection, maintenance always clears governor73 to zero and refills bank
only if it is exactly zero. In these same-time controls1234 stays1234 and 1 stays1;
zero becomes250000. Ordinary earlier interest changes1234 to 1246 in the one-day
child. Ground and stocks may also grow before relocation. Daily movement is not
an owner-preserving transport operation.

### Eligibility and replay

The selected native search rejects a positive candidate planet pointer and keeps
trying; it does not inspect ports, mines, fighters or graph reachability. A source
is unlinked before selection and may be selected again. The source-only control
returns to 100. A sole empty Earth candidate is accepted, as are sole mined,
foreign-fighter and disconnected candidate300 cases. These establish the declared
predicate in synthetic worlds, not a uniform random destination distribution.

The no-vacancy diagnostic is intentionally bounded to eight seconds. It restores
the record, prints many optimistic `Wanderer has successfully warped!` lines, and
never commits a link or reaches the return marker in that interval. Static code
shows the retry without a work bound. The text is printed before acceptance, so
it cannot be treated as proof of a committed move. This is a partial native write,
not evidence of atomic storage or an indefinitely timed runtime observation.

Same-day maintenance prints `Maintenance not needed!` but still runs the phases:
its exact child relocates again. Fresh bootstrap's ten-day production backdating
causes bank 250000→275000 on the next same-day or next-day maintenance capture.
A backward-date child also relocates and raises bank 1234→1357 through the native
capped economic path. Do not reproduce those repeat-payment/rollback behaviors
silently in the modern forward-only daily-maintenance system.

## Landing, ownership and special thrusters

Owner and same-team access retain the governor. An unguarded foreign visitor can
land without taking title. Guarded active foreigners deny access; declined force
entry spends no troops. Guarded neutral entry adopts the governor with unrest;
the observed23→2 garrison is one sample, not a fixed fraction. Banking and fighter
transfers work through ordinary landed operations. Rename rejects slot1 even when
its saved display name is already `Traveller`; it is a slot guard in DOS.

Transport admission quotes a shortest directed path and requires its full budget:

| Control | Saved outcome |
|---|---|
| One edge, 10 turns | Ship reaches101, turns0; Wanderer relocates independently |
| Two edges, 19 turns | Refused without moving or charging |
| Two edges, 20 turns | Ship reaches101, turns10; route stops after one edge |
| Two/three edges, 500 turns | Ship reaches101, turns490; not the later quoted endpoint |
| N/blank confirmation | No transport movement or turn debit |

In these transport witnesses the random planet destination is2368, while the ship
reaches101 and old source100 is cleared. This sampled coordinate is not a fixed
Wanderer destination or proof of a uniform distribution. Owner/team/unguarded
visitors can transport it through existing permission; transport itself preserves
the governor, unlike daily maintenance. A changed display name does not remove
slot1's transport behavior. Exact reentry at the ship's101 location finds no
planet; declining a new purchase cannot repeat or charge the previous transport.

An occupied planned first edge causes destruction before random placement, with
no ten-turn charge. The positive-fighter witness loses1184 of10000 fighters;
zero fighters stay zero. Shields remain10000 and there is no ship death in these
collision witnesses. The preexisting destination planet is not destroyed.

Planned ship-arrival mines explode and reduce shields10000→8467 in the retained
control. When mines or foreign fighters instead occupy only the random planet
location, the ship still arrives safely at 101 without losing shields/fighters;
the three mines or 100 fighters at 2368 remain. A hostile planned arrival stops at
its encounter without inventing a battle charge. Keep the planned ship destination
and the independently chosen planet destination distinct throughout aftermath.

The native private message says the Wanderer vanishes from sensors; it does not
reveal2368. The new public newspaper delta is just the login, not a Wanderer move
or destination notice. An accurate modern receipt should report the known ship
arrival, actual charge and vanished planet without disclosing its hidden location.
Internal saved outcome coordinates and player-visible knowledge are separate.

## Later-phase interference and modern implementation contract

The separately retained post-transport maintenance run first reports a successful
warp, then multiple Xannor assaults, then destruction of The Wanderer. Its final
missing link is therefore not a relocation failure. The isolated replacement
control uses declared zero-score patches and preserves the normal relocated
planet. Phase order and all later supported aftermath must compose in one modern
transaction; restoration should wait until the next eligible maintenance phase
rather than recursively replacing a planet repeatedly attacked in the same run.

Future implementation choices, explicitly distinct from additional DOS facts:

1. Add persistent mobile-planet identity/reference with deliberate migration and
   validation/capacity rules. Current save version 24 has no valid slot1 planet and at most
   99 planets. Never infer identity from a display name or an unrelated reused slot.
   Preserve generation on movement; allocate a new one on restoration. Read-only
   migration must not create free assets or invent past Wanderer history.
2. Define slot1 preference and 100-total capacity without overwriting player/faction
   planets. Build one sorted finite empty-candidate set, including the virtually
   vacated source when appropriate. No candidate must safely hold/defer without
   erasing links, repeatedly drawing or emitting a false success.
3. Make initial/Genesis bootstrap explicit; modern `New` sets today's watermark,
   so immediate `Maintain` deliberately does nothing. Bootstrap with a clean,
   documented resource template and current timestamp, avoiding accidental
   ten-day catch-up awards. Choose scarce-sector priority with both faction homes.
4. Keep daily relocation inside forward-only once-per-date maintenance, after the
   agreed economic phase and before supported NPC actions. Deliberately specify
   the recovered daily governor clear/zero-bank refill. Regeneration must not
   preserve garbage inactive-buffer stocks; ordinary movement preserves legitimate
   assets after their normal economic update.
5. Compute accepted destinations before mutating references; save source/destination,
   title/resources and any publication together. Revoke all landing grants, leave
   other ships in place and expire old quotes. Any restored same-slot/name object
   must have a new incarnation and epoch-bound confirmations.
6. Extend current confirmed transport with its one-edge Wanderer stop and distinct
   coordinates. Retain the recovered whole-quote affordability check unless a
   documented modern policy changes it. Planned-edge collision/stress happens
   before relocation; ship mine/encounter aftermath uses the ship's planned sector,
   not the random planet's unrelated destination. Preserve bounded existing death,
   estate, rollback and committed durability handling.
7. Restrict rename by persistent special identity rather than name/slot accidents.
   Use existing ordinary permission/adoption rules with fresh revalidation. Protect
   Mercenary/Xannor home identity separately; marking Wanderer as an unchanged
   `FactionHome` would make it immovable under the present transport guard.
8. Return only truthful saved receipts: actual turns, ship position, destruction,
   known versus hidden planet position and aftermath. Do not publish secret
   destinations, account identities, banks or tokens. Resolve all later NPC effects
   before describing the final daily outcome. Keep native/live acceptance separate.

Required future tests include bootstrap/minimum capacity, reserved/full slots,
origin-only/no-candidate placement, generation/RNG exhaustion, preserved and
restored identities, current permissions/title resets, same-day/rollback dates,
multiple landed callers and concurrent maintenance/transport, stale planet/epoch
reuse, planned-versus-random hazards, collision and actual receipts, whole-save
rollback, committed warning/output failures and both real interfaces.

## Reproduce and verify

```
python3 scripts/recover_wanderer.py /private/tmp/yt-wanderer-fresh --workers 4
python3 scripts/recover_wanderer.py /private/tmp/yt-wanderer-blocked --exploratory --workers 1
python3 scripts/verify_wanderer.py
python3 scripts/test_wanderer_verifier.py
```

Capture requires the installed DOSBox Staging and refuses an existing destination.
The explicit exploratory command is the time-limited malformed-pointer test; it
is expected not to return and is not a normal successful control. Verifiers use
retained artifacts and standard-library Python without an emulator, REA or Go
runtime dependency. Fresh RNG/time outputs require independent review before any
new frozen witnesses are accepted; never overwrite preserved results to force a
pass. [Native ranges, identities and Evidence IDs](rea/NATIVE.md) support the static
claims. Full RNG/MBF parity, stress distributions, native mid-write/concurrent
safety, live BBS acceptance and native Windows durability remain unresolved.

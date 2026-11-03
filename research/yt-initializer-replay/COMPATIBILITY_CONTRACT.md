# Proposed production QB generation contract

Status: **design for a subsequent implementation; no flags or save fields below
are available yet**. Current playable generation remains unchanged at save 34.
The [complete initializer replay](RECOVERY.md) establishes bounded original
output; it does not itself define a safe playable JSON world.

## Goal and boundary

Add one explicitly selected, versioned generation recipe that consumes the
recovered QB stream in its original order, then projects representable results
into the existing modern world. Name the proposed profile `qb36-v1`. Describe
it as **QB generation with documented modern adaptations**, not exact DOS saves,
original maintenance, clock emulation or a bit-exact running DOS game.

Keep the exact source candidate and playable projection conceptually separate.
The source candidate must match the retained complete-record controls before
projection. Never alter the exact research fixture to accommodate gameplay
validation. The production implementation must run natively in Go, using the
verified `internal/qbrng` primitive and explicit float32 operation boundaries;
Python, DOSBox, original EXEs and REA must not become game dependencies.

## Explicit inputs

Proposed initialization syntax, **not a working command in the current build**:

```text
yt -data NEW-DIRECTORY -init -generation-profile qb36-v1 \
   -qb-state 0xc805 -qb-date 2026-11-02
```

- Require a raw **post-RANDOMIZE, pre-first-RND** state in `0..0xffffff`.
  Accept unsigned decimal or an explicit `0x` hexadecimal prefix. Reject signs,
  overflow, trailing input and out-of-range values before generation. Do not
  silently mask a caller's invalid state merely because `qbrng.New` can mask it.
  Zero is a valid raw state.
- Require an explicit source date. Version 1 admits only the replay model's
  bounded 2026–2028 range and validates a real Gregorian calendar date. Reject
  January 10 until its source port-watermark zero residue is verified. The
  evidence directly covers selected dates, not every admitted date; any broader
  exactness claim needs additional tests/evidence. Consider tightening admission
  if implementation finds an unverified arithmetic boundary.
- Do not derive a raw state from modern `-seed`, Unix time, formatted DOS time,
  IEEE zero or the host clock. TIMER's raw MBF residue matters. A future clock
  conversion interface needs its own recovered contract.
- Source date describes the original candidate's bookkeeping. Modern creation,
  maintenance and session clocks continue using the actual current UTC time.
  No historical maintenance date may grant repeated production or turns.
- Fix version-1 geometry at 3,000 sectors and 1,000 ports. Reject conflicting
  explicit `-sectors` values. Both map and economy come from one QB stream;
  independent modern streams cannot be presented as a QB sequence.
- Reject explicit `-dos-warps`, `-dos-ports` or `-seed` together with the proposed
  profile. Those switches retain their existing meaning outside this profile.
  The existing default `-seed 36` must not count as an explicit conflicting flag.
- The source candidate uses the default `YTSCORE.ASC` field. The game does not
  expose a DOS scoreboard path as a new file-write location. Research path
  variation remains separately testable.

## Exact source generation

Consume the HQ draw first, followed by graph generation/repair/shortcuts, all
port placements and then every port's economy/name/class draws in recovered
order. Adding an adaptation must not consume or reorder this source stream.
The original duplicate weighting, float32 rounding boundaries, raw FIELD/FAC
residues and candidate collision behavior belong to the source model.

Store a SHA-256 of the complete synthesized 568,687-byte source candidate.
This is a generation provenance fingerprint, **not a checksum of the evolving
JSON save or a loader-time assertion that players have not changed the world**.
Preserve algorithm/version, raw state, source date and fingerprint as one recipe.
The source candidate is not a supported DOS export or import format.

## Playable projection and deliberate adaptations

| Source behavior | Proposed playable behavior |
| --- | --- |
| Six ordered warp slots, including holes and Earth's self-warp | Keep nonzero destination order, omit only Earth's redundant self-warp; preserve the existing no-self-link invariant. |
| Duplicate port placement can orphan an earlier port | Reject the unpublished candidate with a clear collision error. Do not move a port, shuffle again or quietly choose another state. |
| Original graph retries may not terminate | Use named, versioned draw/work budgets. Exhaustion rejects the unpublished candidate; no hidden fallback graph or reseeding. |
| Source HQ may fall in protected sectors 1–7 | Reject the unpublished candidate. The current Xannor invariant requires HQ outside protected space. |
| Source HQ has 10,000 fighters and owner -1 | Initialize the modern HQ state and one attributed sector defense with 10,000 fighters; reserve is zero, avoiding double-counting force. |
| Inactive player and planet records contain raw placeholders/residue | Create no players or inactive modern planets. Preserve raw bytes in the source fingerprint, not invented active JSON entities. |
| Pre-maintenance ports have zero supply and backdated dates | Keep the existing modern initial ten production days of stock, with current UTC update watermarks. Do not execute old DOS maintenance to materialize it. |
| Startup reference prices come from YT.EXE's separate pre-RANDOMIZE sequence | Reuse existing recovered DOS references; do not advance the universe QB stream for prices. |
| Original initial maintenance creates/changes NPC state and auxiliary files | Retain the modern bounded bootstrap/maintenance lifecycle. No exact maintenance or newspaper-timestamp replay claim. |

Require final world validation, unique reciprocal sector/port references and
forward/reverse Earth connectivity. Preserve current limits, atomic store
creation, ownership checks and new-directory protection. An admission failure
must leave no playable world published and must identify the rejected condition.
Use source state `a90a05` as the retained duplicate-port rejection regression;
state `c805` is the canonical successful source-record replay control.

Bootstrap interactions need explicit integration coverage: retained HQ location
must not be silently relocated by home creation, Wanderer placement or faction
restoration. If a candidate cannot represent the required homes safely, fail
before publishing it. Existing old-profile bootstrap behavior stays unchanged.

## Saves, reset policy and reproducibility

Introduce a new schema only when the profile is implemented (next available
version; 35 if no intervening change). Save 34 remains current for this design.
Represent the recipe with a typed optional field. Reject unknown algorithm
versions, invalid state/date/hash, incomplete recipes and inconsistent map/port
profile selections. Earlier schema saves claiming the new field must fail
rather than downgrade silently.

No recipe is inferred for old worlds. Normal upgrades preserve complete maps,
ports, prices, settings, players and current profile selections. Loading never
rerolls a universe. Never use a provenance fingerprint as an excuse to replace
an evolved world with its initializer output.

**Version-1 reset policy: preserve the source recipe and repeat its layout.**
Genesis and administrative resets reuse the stored QB state/date and source
candidate fingerprint. This makes generation reproducible without truncating a
modern reset seed into a 24-bit state. Document that map, names, economy and
initial HQ repeat across seasons for this profile. Modern reset/bootstrap RNG
and season timestamps retain their existing separate seed/clock behavior;
these do not change the persisted QB recipe or imply exact DOS maintenance.
Changing the QB recipe requires explicit creation of a separate new world in
version 1; do not add an implicit in-place reprofiling operation.

Extend Genesis intent binding to include the complete recipe, so a pending
confirmation cannot reset after provenance/settings change. Preserve exact
season guards, winner/admin distinction, history, old-login invalidation,
lottery settings and the archive-first administrative reset protocol. All new
candidates remain unpublished until generation, projection, required bootstrap
and validation succeed. Failures before replacing `world.json` preserve active
state and history; existing archive-on-failure behavior follows the established
store contract. A directory-sync `DurabilityError` after replacement means the
reset committed: preserve the committed receipt, new season and history, report
the durability warning, and inspect the active world before any retry. Never
report that committed reset as rolled back or repeat it automatically.

Private full-world export, archive extraction and stopped-node restoration must
round-trip the recipe. Use the existing archive integrity mechanism as well as
recipe validation. Rollback to a binary lacking the new schema requires an
older compatible backup, as with current schema upgrades. No direct DOS `.DAT`
restore/import or new automatic archive importer is included.

## Implementation sequence and acceptance

1. Port the bounded source generator into a pure Go component. Compare all ten
   complete source fingerprints and RNG endpoints against retained evidence.
   Include sparse zero-residue, January cancellation and inherited FIELD tests.
   Export compact golden fixtures for Go tests so production tests require no
   Python/emulator/original binary. Verify fixture provenance independently.
2. Implement the projection and admission limits, with meaningful regressions
   for the retained port collision, protected HQ, exhausted work, connectivity
   and no partial publication. Fix budget constants before calling the profile
   stable; test their failure paths with injected bounded streams/work limits.
3. Add CLI selection, typed saved provenance and validation, including explicit
   flag-conflict checks, old-save preservation and pre-version field rejection.
4. Extend both reset paths, intent binding and archive/restore coverage before
   calling the profile playable. Confirm identical source recipe/layout across
   reset, actual current UTC maintenance watermarks, separate modern bootstrap
   state, stale confirmation rejection and pre-replacement failure immutability.
   Separately inject post-replacement directory-sync failures in both reset paths:
   require committed receipts/new-season history, visible durability warnings,
   and no repeat reset when retried with the old expected season or intent.
5. Update README/sysop examples, save/rollback notes and CI together. Exercise
   headless initialization and real terminal navigation/trading under the new
   profile. Keep default and existing DOS-rule CLI regressions green.

The first source-generator slice is now [implemented in Go with portable fixtures](GO_IMPLEMENTATION.md).
The profile/projection, CLI and save/reset sections of this contract remain
future implementation work. This document defines their design only. It does not authorize
claiming any proposed command or save field as shipped, and it does not repeat
already completed native initializer recovery as a new research task.

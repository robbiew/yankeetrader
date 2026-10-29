# Xannor HQ and Xannoron lifecycle implementation

This implements the bounded lifecycle recovered in [38 completed DOS runs and
three relocation stalls](RECOVERY.md). It does not implement mobile targeting,
ship attacks, revenge/cloak searches, or bit-exact QuickBASIC randomness.

## Persistent identity and phase order

World version **14** adds optional `World.Xannor` with `HQ` sector and `Reserve`
fighters, and permits one `Planet.FactionHome = "xannor"` alongside the existing
Mercenary home. Sector defenses are the authoritative deployed groups: each
sector contributes once, without pointer aliases or a second cached copy.
Reserve contains only undeployed HQ fighters left by an unfinished reclaim.
The HQ and reserve are validated independently of the planet so destruction or
capture cannot leave a dangling planet pointer. Combined reserve and deployed
HQ force may not exceed the existing one-billion-fighter limit.

Once per UTC day, normal planetary/port production and taxes run first, followed
by human desertion, Mercenary routes/hiring and base restoration. Xannoron
restoration and HQ actions follow; player turns/session resets and the new
score-cache publication follow them. Xannor regeneration therefore uses the
previously published stored score. This modern order gives an unplaced Mercenary
home first claim on scarce space, but it cannot claim an existing Xannor HQ.
Newly created HQ fighters do not participate in that day's Mercenary routes.
All phases, casualties, identity, links and the maintenance date share the
existing locked atomic world transaction. Same-day replay and clock rollback do
nothing; missed days do not multiply faction activations.

## Xannoron restoration and capture

A missing home prefers free planet slot 100, falling back to free slots 2–100.
It creates at an existing permitted HQ or chooses one from a sorted finite pool
outside protected sectors 1–7. Candidates must have no planet, no mines and no
foreign defense. Existing Xannor defenses are allowed. Full sector or planet
capacity defers creation without drawing randomness, overwriting assets, or
spinning. An existing HQ that is blocked is not silently moved just to create a
home; a successful reclaim or ordinary empty-HQ relocation may make room, after
which the same phase retries creation once.

New Xannoron has production 100,000 for each commodity, owner -1, ground
`floor(R*250) + floor(R*25)` (0–273) and integer bank
`100,000 + floor(R*10,000,000)`. New inventories are empty because no old record
is reused. Existing Xannor-owned homes gain `floor(R*25)` ground, capped at the
modern quantity limit; an exactly zero bank becomes 1,000,000. Positive banks,
production and stocks are preserved, in addition to ordinary production earlier
in the day. The observed DOS retained-fighter/plasma behavior is not a reason to
copy assets from unrelated or destroyed planet records.

Identity survives rename and capture. Human-owned and neutralized homes retain
their name, location, ground, bank and ownership through the faction phase;
ordinary economic production remains active. There is no automatic retitling,
ground assault or duplicate home. Guarded landing, capture through existing
landing/garrison operations, private report permissions and missile destruction
use the existing planetary rules. Destruction removes the record and identity;
rebuilding waits for a later daily run and safe capacity.

## Regeneration, reclaim and relocation

Let `T` be the greatest nonnegative **stored score of a living player** and `X`
the sum of all deployed Xannor defenses plus HQ reserve. Regeneration is
`floor(T/500)` when `X <= floor(T/100)`, otherwise zero. This retains the recovered
strict cutoff, including regeneration at equality, and caps allocation at free
HQ capacity. Dead retained aliases cannot fund it. Initial HQ force is zero;
only this regeneration creates sector fighters. Existing mobile groups contribute
to the cutoff but do not move or split in this milestone.

Existing HQ-owned defense is detached once into the local HQ force, combined
with reserve and regeneration. A foreign defense at HQ is challenged, including
human player **1** and Mercenaries. While both sides exceed 250, each casualty
batch is 250; otherwise it is one. `R <= .5` removes defenders; greater draws
remove attackers. Work stops at 10,000 rounds. Surviving defenders retain their
owner; surviving undeployed attackers persist in reserve. Neither side is
silently discarded when work is exhausted. A failed reclaim stays at the HQ.
This battle affects sector defenses only, never a captured planet's title or
ships in that sector.

An empty pre-regeneration HQ without a reclaim attempt, including zero force and
zero regeneration, or a successful reclaim with survivors attempts relocation.
It samples once from a finite sorted pool excluding the old HQ, all planets,
mines and foreign defenses. A friendly destination must have room for **all**
survivors; capacity overflow holds at the old HQ instead of deleting fighters.
The selected defense combines with survivors exactly once. An Xannor-owned home
at the old HQ moves with it, preserving the entire planet record and replacing
both sector references. A captured home stays in place even if HQ relocates.
If no candidate exists, the old HQ and all survivors remain intact. Zero-force
relocation creates no defense and cannot use a stale RNG result as strength.

These are deliberate adaptations: the DOS one-foreign-fighter absorption,
unrelated-planet overwrite, owner-1 exception, unbounded search, forced captured
retitling and phantom-force bug are not reproduced. Modern integers and the
shared Go RNG are not claims about DOS rounding or exact draw-sequence parity.

## Migration and validation

Normal versions 1–13 upgrade in memory and persist version 14 only on the next
successful update. A version-13 save keeps all Mercenary identities, newspaper,
radio, players and assets unchanged. No old name, reserved slot or Xannor sector
defense infers a home/HQ; eligible creation happens during future maintenance.
Legacy saves containing the new HQ or Xannor home identity are rejected, rather
than accepting future-schema state under an old version number. Unknown or
mismatched faction owners, duplicate homes, invalid links, protected/missing HQs
and out-of-range/combined-overflow reserves fail validation.

Stop all nodes and back up the data directory before upgrading. Older binaries
cannot read version 14; reverting requires the matching stopped-world backup,
which discards subsequent progress. See [storage and recovery](../../README.md#storage-and-recovery).

Game tests cover strict regeneration cutoffs, living stored scores, force
conservation, both casualty boundaries/ties, first-account reclaim, bounded
unfinished battles, captured titles, capacity/mine/foreign-defense exclusions,
independent faction identities, landing/capture, actual missile destruction,
rebuilding and daily replay. Store tests cover unchanged read-only migration,
legacy-state rejection, atomic rollback, concurrent daily maintenance, persisted
unfinished reserves and validation rollback. The real terminal smoke covers
migration, creation, score-funded force, replay, compact/classic encounters,
landing denial, real capture and captured-home persistence during relocation.

```sh
go test -race -count=1 ./...
go vet ./...
go build -o bin/yt ./cmd/yt
python3 scripts/smoke_xannor_lifecycle.py
python3 scripts/smoke_mercenary_base.py
python3 scripts/verify_xannor_lifecycle.py
python3 scripts/verify_archive.py
```

These are local engine/process/terminal checks. Live BBS acceptance and native
Windows durability remain separate validation.

Validation passed locally: full race-enabled Go suite and vet; the new Xannor
terminal smoke; Mercenary hiring/routes/desertion/base, mines, missiles, radio,
newspaper, spies, salvage, teams and planetary-missile terminal smokes; both
faction evidence verifiers and all 4,682 archive hashes; Linux/Windows
cross-builds; Python syntax and changed relative documentation links. The old
Mercenary route fixture now sets stored score zero to isolate it from Xannor
regeneration while retaining its exact force/mine/title assertions.

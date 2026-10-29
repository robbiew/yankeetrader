# Mercenary base lifecycle

Daily maintenance now creates or restores the Mercenary Base using the recovered
[creation and reserve rules](RECOVERY.md#reserved-mercenary-base-behavior). This
slice covers the Mercenary home; Xannor HQ lifecycle and full NPC ship combat are
not added here.

## Identity and ownership policy

Planet.FactionHome = "mercenaries" identifies one stable home. Its current owner
is a separate title: MercenaryOwner (-2), an existing player, or neutral (0).
A name or planet slot never establishes home identity. Renaming and capture keep
the marker, while actual planet destruction deletes the record and marker.
Only one marked home is valid, it must have a consistent sector/record reference
outside protected sectors 1–7, and unknown factions/unsupported negative owners
are rejected. Ordinary unmarked planets still cannot have negative owners.

The DOS phase forcibly retitles a captured home. The modern policy preserves
human and neutralized titles: no retitling, reserve replenishment or duplicate
home creation while that marked planet exists. Capturing/neutralizing the home
therefore stops faction restoration until destruction. This does not grant
permission to overwrite any human ownership.

## Finite creation and reserve repair

When no marked home exists, prefer free planet slot 99. If occupied, select the
first free slot 2–100, preserving legacy player planets even when named Mercenary
Base. Choose once from a finite sorted list of sectors outside the Union with
no planet and either no sector defense or a Mercenary defense. Human/Xannor
defenses are excluded. Ports, ships and mines do not by themselves exclude an
otherwise eligible sector; creation does not spend their resources or move them.

The home uses one of the existing 99 planet slots.
No free slot or eligible sector means defer creation without retries or errors;
all other daily phases can still commit. Creation supplies:

| Field | Initial value |
|---|---:|
| Name | Mercenary Base |
| Owner | Mercenaries (-2) |
| Production per commodity | 100,000 |
| Ground forces | 150,000 |
| Planet bank | 25,000,000 |
| Stock/cargo/weapons | zero |

The base adds no sector fighter group. Ground forces enforce existing landing
permissions and remote-report privacy. For an existing Mercenary-owned home,
restore ground below one to 150,000, and an exactly zero bank to 25,000,000.
Positive values, production, stocks and names are not reset. General planet
production/interest still apply normally before repair; existing route pickup
can take the base's produced fighters without transferring title or ground.

Restoration runs after desertion, existing-group routes and hiring, preventing
a newly created planet from changing that same day's routes. Its timestamp is
current UTC time, so no initial production is backdated. Missing bases rebuild
even with zero tax. Same-day replay/clock rollback cannot replenish or resurrect
a destroyed base. A later daily transaction can rebuild after actual missile
destruction, which removes both record and sector link.

## Save version 13 and transactions

World version 13 introduces the optional FactionHome field and narrowly permits
Mercenary ownership for the marked home. Versions 1–12 upgrade in memory without
adding homes or changing existing players/planets. Existing version-12 newspaper
history and other saved state are preserved. Read-only loading does not
rewrite files; the next successful update persists the new version. A legacy
save containing the new marker is rejected rather than trusted or discarded.
Older binaries must not operate on version-13 worlds; follow the stopped-world
backup/rollback guidance in README.

The existing locked save commits home links, identity, reserves, production,
routes, hires and date together. Aborted/invalid updates publish nothing; eight
concurrent maintenance calls produce one valid home. No repair attempts to
silently fix corrupt/orphan saved references: validation rejects those worlds.

## Validation

Game tests cover creation defaults, empty/positive reserves, legacy slot/name
preservation, captured and neutralized homes, capacity exhaustion, protected
sectors, unsupported identity/owners, duplicate/orphan references, guarded
landing, report privacy, real missile destruction/rebuild, production feeding
route pickup, and daily replay. The hiring-only no-carry fixture suppresses base
production so it continues to measure hires independently of NPC stock pickup.

Store tests cover version-12 migration and read-only preservation, next-update
persistence, legacy marker rejection, rollback, concurrent creation, reload and
captured-title persistence. Existing migration chains now assert WorldVersion;
the original base milestone advanced terminal assertions to 13. They now follow
current version 14 while legacy inputs remain legacy.
The new real-process smoke exercises version-12 migration through -maint,
creation, landing denial, reserve repair, replay and captured-base access in a
separate GoDoors process. Whole disposable fixtures retry on UTC rollover with
bounded attempts; stable-date failures propagate.

Validation passed: the full Go race suite, vet, faction and migration-sensitive
terminal smokes, three UTC-rollover/failure controls, DOS maintenance evidence
checks, all 4,682 archive hashes and Linux/Windows cross-builds. A negative
control with the restoration call omitted fails the daily lifecycle regression. Managed
worktree builds use a temporary module-file override to the existing GoDoors
checkout, leaving committed module files unchanged. CI on this unpublished
branch and live BBS acceptance remain unverified.

[Xannor lifecycle research](../yt-xannor-lifecycle/RECOVERY.md) now establishes the
bounded home/HQ rules. Their implementation, further faction-home combinations,
full NPC ship combat and bit-exact QuickBASIC RNG/MBF parity remain separate.

Current version 14 extends faction identity for [Xannor HQ/home lifecycle](../yt-xannor-lifecycle/IMPLEMENTATION.md).
Mercenary base creation also preserves an existing Xannor HQ sector, even while
its home is destroyed; version-13 home identities and assets migrate unchanged.

# Modern teams and shared planets — 2026-10-26

The Go door implements team creation/joining, four-member capacity, captain-only
rename/password/removal, confirmed departure, visiting-member succession and
teammate planet resource locations through `T` / `TEAM`. Operations cost no
credits or turns. Team and member numbers shown in the menu come from the world.

`Player.Team` is the sole membership relation. Teams have separate IDs, names,
captains and bcrypt invitation hashes; there is no second mutable roster. Every
mutation reloads and checks the current membership/role under the world lock.
A departing captain leaves a vacancy. The first remaining member to visit the
team menu or complete login becomes captain, matching DOS's visiting-member rule.
The last departure deletes the team and makes the slot reusable.

Invitations retain DOS's four printable characters and case-insensitive matching.
They are entered separately at a masked prompt, excluded from command repeat,
and hashed with a random bcrypt salt. They are not displayed in rosters or
receipts. A removal is a kick: the same invitation permits rejoining until the
captain changes it, and the menu says so. This is not a permanent ban list.

Planets and ports keep individual owners. Members can use defended teammate
planets through the existing landing, transfer and banking rules. Removal or
departure immediately clears landing tokens whose permission was lost, including
other callers visiting the departing owner's planet. Every subsequent planetary
transaction still checks current permissions. Port reporting/collection remains
personal; membership does not grant another member's treasury.

## Saved worlds

The team milestone introduced world version 3; the subsequent [ship lifecycle
build](../yt-ships/LIFECYCLE.md) uses version 4. In the team milestone, version-1
and version-2 worlds upgrade in memory
with an empty team table and persist on the next successful update. Player IDs,
identity, assets, balances, dates and avoidance preferences are preserved.
Read-only loading does not rewrite files. Experimental legacy saves with nonzero
team IDs and no team metadata are rejected rather than inventing captains or
invitations. Current format validation rejects missing teams, nonmember captains,
empty/overfull teams and malformed invitation hashes. A vacant captain (zero) is
valid only on an otherwise nonempty team.

Older binaries cannot read version 3. Keep all nodes on the same new binary and
back up the stopped world's data directory before upgrading. Restoring the old
binary requires restoring its corresponding backup and loses later progress.

## Evidence and bounds

Fourteen selected membership scenarios from the [21-session DOS recovery](RECOVERY.md)
are exported as secret-free Go fixtures. Their source snapshots and SHA-256
values remain in the immutable archive; `scripts/verify_team_evidence.py`
checks all 28 selected saves against the fixtures. Sorted derived membership is
compared with DOS membership, rather than copying its independently stored slot
order. The controlled promotion fixture retains the departed player in its
DOS cached roster; Go derives the roster from authoritative player membership.
DOS's stale departed captain is represented explicitly as vacancy until
the next visitor. Neither old plaintext passwords nor the overlaid sector-team
storage is imported into the modern save.

Tests cover these DOS outcomes, name cleanup, rejected role changes, password
rotation/rejoin, simultaneous final-slot joins and successor visits, invalid
saves, version upgrades, departure/removal access revocation and retained assets.
Session tests exercise both frontends, interrupted creation, stale captain
prompts and exclusion of passwords from command repeat. Real PTY/GoDoors tests
cover masked create/join, shared banking, private port accounts, removal/rejoin,
retained assets and succession: `python3 scripts/smoke_teams.py`.

Sector defenses, team fighter donations, combat, captain death cleanup and exact
DOS team-menu screen cells remain in the combat/presentation stages. Option 6 is
not offered until sector defenses exist. Resource search currently lists teammate
planet locations/owners; full DOS ship/defense inventory listings remain pending.
Live-BBS acceptance of these new team commands has not been performed.

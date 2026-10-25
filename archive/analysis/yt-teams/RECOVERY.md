# Teams and shared assets

First-pass recovery from the supplied original YT.EXE, using its runtime-aware listings and isolated DOSBox games. This extends the earlier [planet management](../yt-planets/RECOVERY.md), [combat](../yt-ships/RECOVERY.md), and [trading](../yt-trade/RECOVERY.md) specifications. All tests modify copied saves, not the archival executables or a live universe.

Validation: **150 checks pass across 21 original DOS sessions**. Checks cover concrete actions, saved fields, conservation, and binary integrity; they are not 150 separate games.

## Team storage

There are 50 team slots. The metadata is overlaid on otherwise reserved portions of the first 50 sector records: **team t lives in record `51+t`** in the default 50-player universe. These records still contain sector warp links and normal sector contents. Do not interpret them as separate all-team records or clear them wholesale.

| Record field | Team meaning |
|---|---|
| Bytes 0..40 | Team name, padded |
| MBF offset 73 | Name length |
| MBF offset 77 | Captain's player record ID |
| MBF offset 109 | Member 1 |
| **Bytes 113..116** | **Four raw password characters, not an MBF number** |
| MBF offset 117 | Member 2 |
| MBF offset 121 | Member 3 |
| MBF offset 125 | Member 4 |

Each human player's field 89 contains its team slot, or zero for no team. Empty member slots are zero. `1f42:95f4..9749` loads team metadata and regards a team with all four member slots zero as dead. The team menu dispatch is `1000:55d6..5796`.

The Go schema should give teams their own table and IDs. The sector overlay is a DOS storage optimization, not a gameplay requirement.

## Creation, names and passwords

`T;2` creates a team in the first free slot (`1000:57b5..591d`). Names must be at least three characters; the name helper stores at most 41 characters. The creator becomes captain and occupies member slot 1; the other three slots become zero. There is no credit or turn charge in the tested creation. `team-create-confirm` creates Orion as team 1 with captain/member 2. `team-short-name` rejects AB without assigning the player or creating a membership.

The password helper (`1000:657f..660a`) requires exactly four input characters and persists them directly in the record, without hashing. `team-password` changes ABCD to WXYZ. Joining with lowercase `abcd` succeeds against stored ABCD, so ordinary join comparison is case-insensitive after input normalization. Raw password bytes should never be exposed through a generic numeric-record decoder or copied into modern logs.

## Joining and capacity

`T;3` lists teams and accepts a team number and password (`1000:5920..5c1d`). It rejects a dead slot, a full roster, or an incorrect password. Successful joining fills the first zero membership slot and writes the same team ID to the joining player.

DOS tests establish that:

- Joining captain 3's team writes player 2 into slot 2.
- A wrong password leaves player and roster unchanged.
- Four existing members reject a fifth applicant, before password entry.
- Members cannot access create/join again while on a team through the ordinary menu.

The join writes player membership and roster separately in the DOS implementation. Go should commit them together and enforce capacity transactionally. Simultaneous fifth-member joins and conflicting membership operations have not been exercised in DOS.

## Captain permissions and succession

Ordinary members receive quit, resource search, and defense-reinforcement options. Only the captain receives banish, password change, and team rename. These are not merely hidden menu items: `team-member-privilege` sends option 8 as player 3 and gets Invalid Choice while the password remains ABCD.

The status routine `1f42:856e..87c9` checks whether the stored captain still names a valid player belonging to this team. If not, the **current visiting/logging-in member** is promoted and the team captain field is updated. It is not a lowest-player-ID election.

`team-quit` removes captain 2 from both their player record and the team's member slot but initially leaves captain field 2. In `team-successor`, player 3 logs in from that exact saved world at a later DOS time and becomes captain. `team-promote` independently tests a controlled captain-no-longer-member fixture. Captain death is described by the manual, but these succession tests exercise resignation/invalid membership rather than a complete lethal encounter with a team captain.

## Leaving and banishment

`T;4` asks for confirmation, clears player membership, and removes the player from its roster slot (`1000:5c2e..5df2`). If no members remain, it also clears captain, password and membership slots. The old name can remain in the sector text area: empty roster, not erased name, determines whether the slot is free. `team-last` verifies this cleanup.

Banishment (`1000:6216..63a0`) lets the captain walk the other members and confirm one removal. It clears that player's team and their roster slot, then prints **Done. Now change your Team Password!** The password itself does not change. `team-banish` removes player 3, and `team-rejoin` starts from that saved world and successfully rejoins using ABCD. It is a kick, not a durable ban list.

For Go, define removal/rejoin policy explicitly. Preserving the original prompt while presenting the operation as a permanent ban would be misleading. Rotate the invitation secret or track a deliberate admission rule if removal must prevent immediate re-entry. Hash any stored join secret, avoid logging it, and recheck current role/membership on each privileged operation. Concurrent active-session revocation remains untested in this phase.

## What sharing actually permits

Assets retain **individual** ownership. Team membership grants selected access; it does not pool every balance or automatically retitle possessions.

- **Planets:** teammates may land through another member's ground defenses and take cargo or use the planet bank, as validated in the preceding planet suite. After captain 2 quits, the still-defended planet owned by member 3 denies landing (`team-quit`).
- **Sector defenses:** a teammate's fighters allow ordinary passage. `team-defense` moves 100→101 through 100 fighters owned by player 3, costing one normal movement turn without fighter losses.
- **Reinforcement:** team option 6 transfers a positive quantity from the ship to the **current sector's** existing defense. It does not ask for a remote sector. Sending 123 changes ship fighters 1,000→877 and defense 100→223, leaving owner 3 unchanged (`team-transfer-current`). This helper does not check the defense owner's team: `team-transfer-foreign` performs the same donation to owner 4's hostile defense, then remains blocked by those reinforced fighters. No resources are duplicated.
- **Withdrawal:** main `F;0` does not let player 2 reclaim a teammate's sector fighters; it reports that fighters already exist and leaves both inventories unchanged (`team-withdraw-defense`). Reinforcement is not equivalent to unrestricted withdrawal.
- **Ports:** `$` does not collect another team member's treasury. `team-port-account` has no personally owned ports and receives You don't OWN any ports, while player 3's 10,000-credit treasury remains intact. This verifies the no-personal-ports path; mixed personal/team treasury collection has not received a separate test here.
- **Personal assets after departure:** `team-quit-assets` retains the quitter's own planet, sector defense and port ownership; their own 7,000-credit port treasury can still be collected after leaving. Former teammate access is revoked without confiscating individually owned assets.

The resource-search option (`1000:5df5..609e`) enumerates other members and their planets/defenses, showing the shared resources available through ownership links rather than moving them into team ownership. `team-search` exercises that listing with deliberately distinguishable owned assets.

## Evidence and limits

`fixtures.py` builds isolated copies with deterministic memberships and asset ownership. It preserves warp and sector fields outside team metadata. `prepare_followups.py` copies recorded first-session results for successor/rejoin tests; those followups advance DOS time to 00:01:00 so they do not trigger the known clock-rollback production defect. `scenarios.json` records actors, input streams, source fixtures, timings, hashes, and excluded probes. `validate.py` checks concrete recorded outcomes and archival binary integrity.

Data/logs live under `../yt-combat/experiments/team-*`. Timeouts at a waiting menu are not normal logouts; counted assertions rely on explicit messages and committed records. The initial creation probe lost queued input and the initial reinforcement probe selected an empty current sector; both remain preserved and are excluded from the successful-action set.

Remaining work includes simultaneous team mutations, active-session banishment, team membership during captain death cleanup, mixed port-account collections, malformed roster repair, and any separate NPC/team relationships. The modern engine should maintain one authoritative membership relation and validate eligibility at action commit rather than trusting independent cached rosters.

### Replay instructions

From the YT36 root, build fixture directories only when they do not already exist, then use `analysis/yt-combat/run_clock_session.py` with a fresh output directory, source fixture, exact recorded keys, and deadline from `scenarios.json`. Set `YT_PLAYER` and `YT_DOS_TIME` as recorded. Complete the primary banish and quit runs before calling `prepare_followups.py`; its output becomes the source for the later-clock rejoin/successor runs. Existing evidence is never overwritten.

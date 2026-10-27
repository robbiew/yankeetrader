# Computer reports and faction fighter encounters

Recovered 2026-10-26 using original Yankee Trader 3.6 in isolated DOSBox Staging
copies. [Evidence](utility-dos/results.json) contains **23 completed sessions and
46 full before/after saves**, inputs, transcripts, emulator logs and patch/hash
provenance. This is a bounded research slice, not a Go gameplay implementation.
The executable SHA-256 remains
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.

## Computer commands and report access

The menu exposes 17 numbered commands. Earlier navigation work implements 3
(autopilot), 7 (avoid slots) and 10 (path finder) in Go. This slice tests menu
discovery, port report (2), planet report (9), own-fighter finder (11), the empty
treasury-report path (12), own-planet finder (13), and the empty spy-list path (15).

| Probe | DOS result | Turns spent |
|---|---|---:|
| `utility-menu` | Shows the 17 original command labels | 0 |
| `utility-fighters` | Lists the player's 123 fighters at 101 and 789 at 106; omits Enemy's 456 at 102 | 0 |
| `utility-planets` | Lists the player's Test Planet at 102 | 0 |
| `utility-planets-foreign` | Same planet assigned to Enemy: None found | 0 |
| `utility-port-known` | Remote commerce report for Test Port at 101, including stocks, cargo and prices | 0 |
| `utility-port-empty` | Sector 104 has no port: No information available | 0 |
| `utility-port-guarded` | Enemy sector fighters block the report: No information available | 0 |
| `utility-planet-report` | Unowned planet: full production, inventory and bank report | 0 |
| `utility-planet-owned` | Personally owned planet: full report despite its garrison | 0 |
| `utility-planet-unguarded` | Enemy-owned planet with zero ground forces: full report | 0 |
| `utility-planet-private` | Enemy-owned planet with 12 ground forces: only its name and ground forces | 0 |
| `utility-planet-guarded` | Enemy sector fighters deny the report entirely | **1** |
| `utility-treasury` | No personally owned ports: You don't OWN any ports | 0 |
| `utility-spies` | No spies: You do not have any spies | 0 |

All reports preserve ship position, credits, fighters, shields, holds and cargo.
The guarded planet query is the turn-cost exception. These checks do not assert
whole-save immutability: reporting may exercise original lazy world updates and
ordinary login/quit bookkeeping.

The full planet report includes a 10,000-credit bank and weapon stocks in this
fixture. It is not universally public: planetary ownership/garrison controls
detail, and sector fighter defenses can block access before detail is shown.
Port denial and planet denial have different turn behavior. Do not expose all
stored planet fields through a single unrestricted Go report query.

The empty-spy path discards the stacked exit command in the tested `C;15;1`
stream; a fresh quit still exits normally. This suite does not establish populated
spy reports, team sharing, treasury aggregation, ranking or communications.

Static anchors: main `1000:8477..8639` contains the menu; `8d60..8efa` handles
port-report input and availability; `a1f9..a36c` searches personally owned sector
fighters. Permission conclusions above come from paired DOS fixtures, not only
the annotated listing.

## Fighter encounters and NPC factions

All nine encounter probes begin at sector 100 with 2,000 ship fighters and
100,000 credits. Moving to 101 costs one turn and encounters 100 sector fighters.
The scanner is absent to isolate the restricted encounter menu. NPC ownership
uses -2 for Mercenaries and -1 for Xannor; the human comparison uses player 3.

| Probe | Result |
|---|---|
| `npc-merc-attack` | Committing 1,001 fighters produces a surrender refusal. All 100 defenders are destroyed; 61 attackers are lost. |
| `npc-xannor-attack` | Same commitment also produces refusal; all 100 defenders are destroyed and 61 attackers lost in this recorded run. |
| `npc-human-surrender` | Same commitment, accepted human surrender: 100 join, zero casualties, ship fighters become 2,100. |
| `npc-merc-bribe` | Offer 50,000: accepted; ship credits 100,000 → 50,000 and fighters 2,000 → 2,100. Defending count and owner clear. |
| `npc-merc-cancel` | Blank offer cancels; credits, ship fighters and Mercenary defenses remain unchanged. |
| `npc-human-bribe` | Humans reject the bribe; this fixture does not trigger forced combat or debit credits. |
| `npc-xannor-bribe` | Xannor reject the bribe and force combat with the ship's full fighter force. 64 attackers are lost and all 100 defenders destroyed. |
| `npc-warp-cancel` | W;N does not engage warp; ship, defenses and turns stay unchanged after the initial hop. |
| `npc-warp-escape` | W;Y escapes to sector 252; 90 recharge turns plus the movement turn leave 409. Defenses and ship fighters remain intact. |

Except for the accepted warp's recharge, every case ends with 499 turns. Fighting,
bribing and surrender do not add a turn cost in these probes. Clearing defenders
also clears sector ownership. Unresolved encounters retain both count and owner.
All death markers remain zero; this is not death/respawn testing.

The saved sector is already 101 while the game says the fighters must be defeated
before entry and restricts available commands. Quitting or cancelling escape does
not roll the hop back. A modern implementation must represent the unresolved
encounter or enforce equivalent authoritative action guards, so saving position
alone cannot unlock docking/trading or ordinary movement through hostile defenses.

The mercenary payment is the **offered amount**, not a proven minimum price or
fixed per-fighter tariff. Acceptance/refusal odds, cheap/negative/over-budget
offers, mercenary planet guards and all combat outcomes remain separate boundaries.
The casualty figures above are recorded samples, not deterministic constants.
Existing fighter/surrender algorithms are in [combat recovery](../yt-combat/RECOVERY.md).

Static anchors: main `1000:0952..0b1d` restricts hostile fighter encounters;
`0c83..0da8` handles surrender/faction checks; `12c1..14e4` handles bribe refusal,
negotiation and forced combat; `14e7..1587` commits accepted bribes and recruitment.
[REA evidence](encounter-rea/utilities.json), from Ghidra 12.1.4, cross-checks the
bribe discriminator/commit path, fighter finder and report-availability bytes.
Addresses are linear DOS analysis coordinates using load segment 0x1000, not file
offsets. The ephemeral session was closed without changing an executable.

## Reproduction and verification

```sh
python3 scripts/recover_navigation.py /tmp/yt-utilities-new --utilities
python3 scripts/verify_utility_evidence.py
```

The destination must not exist. DOS date/time are 2026-10-24 00:00:00; the runner
copies the archived fixture and records every field override. A delayed quit
retry tolerates output routines consuming typeahead. Replay need not reproduce
identical random casualties or destinations. Only completed sessions are packaged.

The verifier checks artifact hashes, fixture patches, graphs, inventory and turn
accounting, report visibility boundaries, bribe debit/recruitment, surrender,
casualty reconciliation, retained defenses and warp cost. Research does not enable
Go hazards or change the established terminal commands.

Remaining navigation/utility research includes nearest-port, port-pair and
adjacent-profit reports, populated spies and communications. NPC daily movement,
full encounter randomness and combat/death concurrency remain distinct from this
bounded interface/transaction research.

Validation on 2026-10-26 passed the utility, hazard, encounter, follow-up,
navigation and avoid-list evidence verifiers, all 4,682 archive checksums and
`git diff --check`. Semantic negative controls injected a private-bank disclosure
and changed the accepted bribe debit, recomputed the relevant hashes, and were
still rejected. All changes remain on `codex/navigation-encounter-research`;
Go gameplay and the original archive remain unchanged.

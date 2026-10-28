# Direct ship combat, cloak, retaliation, and death — YT 3.6

## Results

Recovered the direct-attack path and related lifecycle routines from the imported YT.EXE. Validated through **17 standalone DOS sessions plus two paired-session experiments**: 21 DOS processes in 19 scenarios. `verify_evidence.py` passes **141 checks**, including six separate injected-RNG model checks. This is partial reverse engineering, not restored original BASIC or a bit-exact RNG/MBF emulator.

Three reported exploits now have local DOS reproductions: stale-position attacks, actions after online death, and mines at Earth damaging replacement ships. A fourth confirmed defect misattributes an enemy missile-retaliation death as suicide and incorrectly applies the self-death cooldown. Same-day human-kill respawn also refills the entire turn allowance; that observed rule needs an explicit anti-farming policy in the modern game.

Original YT.EXE SHA256: `c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`. All original executables remain unchanged, as do the game copies. Experiments use constructed records in isolated worlds, the normal LOCAL.EXE interface, and BIOS-fed keyboard commands.

## Direct attack calculations

Target selection and fighter duel: `1000:292b..2df8`. Shield duel: `1f42:9c6b..9d37`. Listings: `../yt-combat/main/qb-annotated.txt` and `../yt-combat/sub/qb-annotated.txt`. All addresses refer to the Ghidra import; normalized target annotations resolve segment aliases.

Ordinary direct attack selects other ships in the attacker's **cached** sector, excludes positive cloak values in the cached player table, and skips positive matching team IDs. The target's live record is subsequently loaded for equipment. Critically, the tested path does not revalidate its current sector before committing damage.

The attacker chooses a committed force C, which is removed from the ship before the duel. With committed attackers A and defending ship fighters D still alive:

```
batch = max(1, floor(min(A, D) / 20))
if RND + attacker_cloak / 10 < 0.45:
    A -= batch
else:
    D -= batch
```

The defender's cloak normally prevents selection; this loop applies the attacking player's cloak advantage. At cloak fractions 0..1, the probability of an attacker casualty batch is approximately 45% down to 35%. The direct ship duel has **no fighter-surrender branch**, unlike a sector fighter group.

If D reaches zero and A survives, those survivors attack shields S:

```
while A > 0 and S > 0:
    batch = 100 if A > 100 and S > 100 else 1
    if RND >= 0.5:
        A -= batch
    else:
        S -= batch
```

The shield stage has no cloak adjustment. Committed survivors are returned to the attacker's uncommitted fighters afterward. If shields reach zero the ship is killed; if the committed force runs out, the surviving target remains. These direct attack cases did not deduct turns.

| DOS case | Observed result |
|---|---|
| ship-kill | 10,000 aboard; commit 1,000 vs 10 fighters/10 shields. Lose 4 in fighter combat, eliminate all 10 defenders, then finish shield combat with 987 committed survivors. **9,987 fighters aboard** afterward. Target killed. |
| ship-fight | Commit 1,000 vs 1,000 fighters/10,000 shields. Lose 451 in fighter combat; the 549 survivors are exhausted against shields. Target survives with **9,550 shields**; attacker retains 9,000 uncommitted fighters. |
| ship-retaliation | Commit all 10 fighters against 1,000,000. Lose all 10, destroy 21 defenders. Target's 1,000 missiles remain untouched: no automatic missile counterfire from this direct fighter attack in the tested path. Attacker's ship survives with one shield. |
| ship-hidden | Target with cloak fraction 1 is not offered by ordinary Attack. No damage. |
| ship-team | Both players have team ID 1: game prints “NOT attacking team member”; no damage. |

A display discrepancy also appeared: immediately after the fighter stage, the “remain” message reports the uncommitted force (9,000), omitting committed survivors until they are restored. Final saved accounting is correct in these tests.

## Cloaking and anti-cloak

- Positive cached cloak hides a ship from ordinary direct target selection (`1000:29a8..29c7`). The missile path has a target override, so cloak is not absolute immunity to explicit retaliation.
- Attacker cloak improves the fighter-stage casualty odds as above.
- Spending a turn at a remaining-turn count divisible by 25 reduces cloak by 0.01, clamped at zero (`1000:a712..a786`). `ship-cloakdecay` begins with 476 turns and full cloak; one move saves **475 turns and approximately 0.99 cloak**, displayed as 99%.
- Buying anti-cloak at Earth costs **500,000 credits** in this release (`1000:6d7c`, `78b0..791a`). It clears the session's cached cloak table across player slots, rather than writing every victim's stored energy to zero (`1f42:932e..94fa`). The buyer's cloak display becomes FAIL for this session.
- `ship-anticloak` buys the device at sector 1, remotely reveals Enemy in sector 2, then moves there and receives an Attack prompt for Enemy. Enemy's stored cloak remains **1**. The attack was declined to keep this visibility test separate from damage.

This confirms the remote-reveal component of BAL-001. It does not reproduce the entire galaxy-wide reconnaissance/attack/reward chain or establish the desired balance for the Go game.

## Missile retaliation

Modern follow-up: [implemented one-hop missile and return-fire scope](../yt-missiles/IMPLEMENTATION.md).

Retaliation routine: `1f42:9d3d..9fbe`. It excludes invalid/self targets, dead retaliators, and retaliators without missiles. It temporarily switches actor identity and overrides target concealment, then invokes the normal missile routine.

Let S be the original attacker's **stored score loaded for the session**, and M the retaliator's available missiles:

```
if M < 1: no shot
N = floor(S * 0.00001) + 1 if S > 0 else 0
if N == 0 or N > M:
    N = floor(RND * M) + 1
consume N missiles from the retaliator
fire toward the attacker's recorded encounter location
```

This is not simply min(score-based volley, stock): when the score-based value exceeds stock, the code falls back to a random 1..M volley. Only the positive-score case and nonpositive-score fallback were dynamically tested here; the over-stock fallback is a static recovery.

- `ship-counter-six-adj`: original attacker stored score 500,000; target has 100 missiles. Target returns **6 missiles**, saving 94. The fully cloaked attacker loses 8,479 fighters, retaining 1,991,521; shields remain 2,000,000.
- `ship-counterdeath-adj`: attacker has 10 fighters/one shield and nonpositive stored score; target returns **731 of 1,000 missiles**, saving 269. Transcript reports Q destroyed and exits the attacker session.
- The dead attacker's final record nevertheless contains **death marker 2 (self), sector 0, 10 fighters and one shield**. `ship-counter-relogin` proves the impact: it prints the suicide message and refuses another ship until tomorrow, despite the recorded enemy counterattack. The death/actor-identity handling and stale equipment state need correction.

Early attempts aimed missiles at the same sector as the launching ship. They self-destructed and did not exercise retaliation; those negative probes are excluded from the evidence counts and conclusions.

## Death, salvage, and respawn

Kill processing: `1f42:2993..2dd7`; salvage: `1f42:2ddd..3566`; login handling: `1f42:1576..1860`; replacement construction: `1f42:356f..36de`.

Player record fields relevant here:

| Offset | Meaning |
|---:|---|
| 41 | Last-play/update day used by the login path |
| 45 | Death/killer marker; zero is alive, positive player record IDs identify the killer; self ID selects suicide handling |
| 49 | Remaining turns |
| 53 / 57 / 61 | Shields / sector / fighters |
| 81 | Credits |
| 89 | Team ID |
| 97 | Missiles |
| 109 | Stored score |
| 125 / 129 | Cloak fraction / carried sector mines |

Kill processing clears the session's cached position, saves sector zero and a killer marker, and handles ownership/title changes. It is not one atomic all-fields/all-sessions transition. Do not assume a dead record has zero balances/equipment: some remain deliberately available to salvage, and active session state can also write stale values back.

In `ship-kill`, the attacker salvages **6,689 credits and four mines**. Saved attacker credits become 7,694; the dead victim still stores 12,345 credits and five mines. Its five mines also become a sector hazard. Retained values alone are not proof of repeatable salvage duplication, but they are dangerous when combined with the confirmed ability of a dead session to continue acting. Exact salvage distributions and all ownership transfers remain outside this pass.

The replacement constructor resets the tested player to sector 1, 500 turns, 100 shields, 25 fighters, 10 holds, 1,005 credits, one missile, full cloak, and zero plasma/mines. The numeric starting values come from config where applicable.

| Login experiment | Result |
|---|---|
| ship-relogin-same | Human-killed Enemy gets a replacement immediately on the same date. |
| ship-relogin-next | The same dead record also rebuilds on the next date; this test advances the DOS date without running daily maintenance, isolating login behavior. |
| ship-refresh-turns | Human-killed Enemy starts dead with only **37 turns**. Same-day login rebuilds with **500**, confirming a refill rather than merely observing an already-full allowance. |
| ship-self-same | Constructed self-death marker, current day: no replacement; told to return tomorrow. |
| ship-self-next | Same self-death fixture on the next date: normal replacement. |
| ship-counter-relogin | Actual enemy counterfire death is treated as self-death and blocked the same day. |

Only self-death cooldown and human-kill replacement were exercised across dates; NPC-specific/deleted-killer branches were read but not validated in new DOS tests. Repeated cooperative kills to farm the refill have not been run as a complete economic cycle; the refill primitive is confirmed and tracked separately as a balance/exploit risk.

## Confirmed concurrency exploits

### EXP-004: dead session continues moving

`ship-online` runs two original DOS games against the same isolated directory. Enemy logs in and waits; Q logs in later and kills Enemy. Captured snapshots show Enemy marked dead at sector zero. Enemy then requests ship info, which shows sector zero/zero defenses, yet its existing session accepts **M;101**, spends a turn, and saves **death marker 2, sector 101, 499 turns**. Credits remain 12,345. This is not a normal respawn: no replacement was constructed.

Evidence: ATTACK.LOG, VICTIM.LOG, before-attacker.dat, snapshot-*.dat, final YTDATA.DAT; orchestration `online_probe.py`.

**Modern fix:** a death generation/version invalidates all live sessions and pending command chains; every mutation requires an alive player in the current generation. A dead session must not move, spend, transfer, salvage, or restore cached equipment.

### EXP-003: attack a ship that already moved away

`ship-stale-position` starts the attacker after the victim is online but delays its Attack command. The victim moves from sector 100 to 101 while the attacker remains at 100. The attacker still offers Enemy as a target and kills it.

Host-observed record transitions in events.json, listed by nominal polling offset after attacker launch (0.1-second polling plus processing overhead; ordering is authoritative, durations are approximate):

- 0.0 seconds: victim alive at sector 100.
- 19.2 seconds: victim alive at **sector 101**.
- 30.8 seconds: victim's fighters and shields become zero while its record still says sector 101.
- 31.1 seconds: death marker becomes 2 and sector becomes zero.

Separate DOS clocks were reset for each process, so ordering uses the host polling sequence and record snapshots, not comparisons of the two game clocks. This reproduction establishes the stale-target bug and also exposes a window of partially updated death state.

**Modern fix:** lock/reload both players and validate alive status, location, team protection, and target eligibility when committing the attack. Save damage, death, ownership, loot, and session invalidation atomically.

## EXP-002: mines at Earth survive death and harm replacement ships

`ship-earthdeath` attacks a mine-carrying ship at Earth with a fragile attacker. The target carries 100 mines. Its destruction places all 100 in the sector; explosions kill the attacker. **60 mines remain at sector 1** afterward.

`ship-earth-respawn` logs the human-killed victim back in. Its new standard ship spawns at Earth among those mines. Explosions remove its 100 shields, 25 fighters, missile, and some cloak/holds; emergency warp takes it to sector 44 and costs **91 turns**, leaving 409. **49 mines remain at Earth.** The ship escaped rather than dying, but essential spawn access remains hazardous and the replacement loses most starting defenses.

This is a replacement-ship test, not a first-ever-account registration test. It confirms the protected-spawn violation and its practical harm without overstating that every entrant must die.

**Modern fix:** enforce the protected-sector invariant when equipment is dropped by any cause, including enemy kills, retaliation, and self-death. Do not rely only on the voluntary mine-placement command. Recheck the invariant before a new or replacement ship enters.

## Reproduction and limits

- `fixtures.py` creates the first five direct-combat fixtures from the earlier missile fixtures. Further captured scenarios preserve complete before.dat/YTDATA.DAT records and KEYS.TXT input scripts.
- `online_probe.py`, `stale_probe.py`: bounded paired-process reproductions; only their dedicated test directories are shared.
- `../yt-combat/run_clock_session.py`: local keyboard-driven runner, with optional YT_PLAYER and YT_DOS_DATE environment choices. Default date is 10/24/2026, time midnight.
- `verify_evidence.py`, `evidence.json`: captured evidence verification. Run `python3 analysis/yt-ships/verify_evidence.py` from the distribution root. The 141 count includes individual assertions, not independently sampled battles.
- `recovered_rules.py`: readable fighter/shield duels, cloak tick and counter-volley arithmetic with injected RNG. It is not the modern rules engine and does not emulate every MBF rounding operation.

The Earth replacement probe was stopped at a subsequent command prompt after the emergency escape. Other completion states are recorded in evidence.json. No modern Go implementation, exploit fix, remote publication, or archival binary patch was made in this research pass. Balance policy for same-day PvP replacement and global anti-cloak needs explicit design and playtesting; neither should be silently confused with the confirmed concurrency/lifecycle defects.

## Loot/estate follow-up — 2026-10-27

A separate [37-session recovery](LOOT.md) now establishes the salvage sampling
shape, new-hold/cargo behavior, ordinary-port capture and treasury handling,
active planet retention, Mercenary defense conversion, team removal and a chained
self-attributed death's port cleanup. This extends the first-pass scope above;
exact RNG/MBF equivalence and complete combat integration remain unverified.

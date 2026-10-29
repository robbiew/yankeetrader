# Confirmed bribery and recruitment

`BRIBE [credits]` attempts negotiation with the current hostile fighter group.
`BRIBE <adjacent sector> <credits>` attempts entry and negotiation with an adjacent
group. The classic encounter also accepts B; ordinary B outside an encounter
retains port acquisition. Without an amount, current-sector Mercenary negotiation
prompts for it; blank cancels. Use a positive whole-credit offer within the
current balance. Invalid, fractional, zero, negative and unaffordable offers are
rejected before randomness or a resource change. This deliberately fixes the DOS
parser's surprising invalid-input combat and fractional-credit behavior.

Every attempt requires a fresh exact Y. Queued semicolon answers, command repeat,
typeahead, cancellation, disconnect and expired confirmation cannot approve it.
The warning identifies the defending force, offered money, entire ship force at
risk, and (for adjacent entry) the one-turn cost and destination mines. A remembered
Mercenary grudge is announced explicitly. A planet-guard refusal or ordinary
human refusal pays nothing and leaves the group in place.

## Recovered decisions

[The resolved DOS decision tree](HOSTILITY.md) supplies eager random-draw order,
strict inequalities, sector-planet refusal, Xannor aggression, human retaliation,
5% Mercenary hostility and the additional weaker-ship condition. A surviving
negotiation accepts when the offer is at least `D * (1 + 2*r)`. Go uses integer
money and normal `[0,1)` random draws, with the documented decimal .05/.9/.33
boundaries. It does not promise QuickBASIC RNG/MBF bit parity or particular
casualties. Adequate money never removes pre-offer hostility risk.

Fighter combat that destroys Mercenaries sets hostility for that login, across
groups. Reconnect starts without the flag; hostility is not a new world field.
Only committed casualties publish it, including a committed directory-sync
warning. Failed calculations, deadline checks and pre-replacement save failures
do not publish hostility. Missile damage is not a recovered producer of the flag.

## Transaction boundaries

A quote snapshots the bound generation, origin/target, exact defense group,
planet reference, money, total fighters, turns, cloak, mines and hostility state.
A random, login-local single-use confirmation token prevents replay, including
unchanged human/planet refusals and use from another login. A newer quote or a
separate defense action invalidates an older token. Commit consumes a token once
and rechecks the world and deadline after acquiring the locks, before randomness.
The event clock is sampled inside those locks. Deadline expiry during calculation
also rolls the update back.

Accepted payment, recruitment and removal of the group commit together. Ship
capacity is checked before randomness/removing defenders. Current-sector attempts
cost no turns. Adjacent attempts spend one entry turn, use existing cloak decay
and invalidate docking/landing tokens. Remote sectors and adjacent attempts while
already blocked by origin fighters or mines are refused.

Refusal/insult combat commits the entire current ship force through existing
sector-defense battle logic, with surrender disabled. It preserves existing loss,
emergency-escape and mine/estate attribution safeguards. A powerless ship forced
into combat uses the existing emergency escape policy rather than adding a new
DOS ship-attack algorithm. This is an explicit modern safety adaptation. Victorious
or noncombat entry resolves destination mines; payment, entry and aftermath all
roll back together on failure. Accepted recruits can subsequently be lost to that
minefield: terminal output reports recruitment followed by the actual aftermath.
An unresolved group continues blocking ordinary actions, including after a
noncombat refusal. Successful output is not required to preserve a committed
world change, and a durability warning must not trigger automatic replay.

No save-format change is needed: version 12 remains current.
[Daily hiring](../yt-mercenary-maintenance/IMPLEMENTATION.md) and
[NPC route actions](../yt-mercenary-maintenance/ROUTES.md) are implemented
separately. Human-defense desertion, base restoration and full NPC ship combat
remain outstanding; route pickup already takes planetary fighters without
transferring title or ground forces.
Existing estate conversion already supplies Mercenary groups in ordinary worlds.

## Validation

Injected game tests cover exact offer/random boundaries and eager draw counts,
all refusal types, capacity, zero-force escape, stale warnings, invalid RNG,
adjacent entry/cloak/turns, origin blockades and ordinary-action guards. Store tests
cover concurrent confirmation/replay, cross-login tokens, unchanged refusal replay,
expiry during lock waits, failed save/late escape RNG rollback, adjacent payment
plus mine-aftermath rollback, committed durability warnings and hostility reset.
Door tests cover malformed input, literal confirmation/queued answers, EOF,
authoritative changes, deadline expiry and classic B dispatch.

`scripts/smoke_bribes.py` drives real GoDoors compact/classic sessions through
cancellation, adjacent recruitment and saved debit, reconnect/cleared-group replay
and human refusal. Every real random hostility outcome is validated; up to eight
fresh disposable attempts are allowed to exercise the recruitment branch too.
It never retries an unclassified failure. The transcript is
`evidence/bribes-smoke.txt`. CI runs this and both original-DOS evidence verifiers.
Full race-enabled tests, vet, relevant terminal/evidence checks and Linux/Windows
cross-builds are local evidence; live target-BBS acceptance remains separate.

# Bounded broadcast radio

## Original DOS evidence

Six completed sessions of the unmodified DOS 3.6 executable establish broadcast
send, abort and chained reading. The [retained controls](dos/results.json) include
exact key feeds, DOS clock logs, full compressed before/after worlds, captured
auxiliary files and binary hashes. Runs use synthetic accounts in fresh copied
fixtures; the archive and live BBS data are never mounted for execution.

Computer 5 accepts `ALL`, announces a broadcast to all players and sends
`YT BROADCAST PROBE`. Unlike [team radio](../yt-team-radio/IMPLEMENTATION.md),
DOS stores **one** 86-byte mailbox record: leading MBF value **30**, destination
**-2**, sender player record **2**, followed by the padded 74-byte text. Abort
creates no record. The sender's history labels the destination `All`.

| Control | Mailbox leading value after login | Delivery |
| --- | --- | --- |
| Broadcast send | 30 | Composer and sent history show the body |
| Abort | No record | No successful transmission |
| Enemy reads the sent world | 28 | Login delivery and history |
| Sender reads the sent world independently | 28 | Login delivery and history |
| Enemy reads its exact previously read world again | 26 | Login delivery repeats; history remains |
| Sender reads Enemy's exact previously read world | 26 | Sender still receives login delivery and history |

These runs show a shared field decreasing by two on each tested reading login,
including a repeat by the same reader. They do not establish the complete
retention policy, exhaustion threshold, maintenance expiry or concurrent-DOS
behavior. Do not describe that shared field as independent read receipts or
infer a universal lifetime from its initial value alone.

Children reopen their parent's exact final world and captured auxiliary files,
without patches. Both actors retain position, turns, membership, credits, cargo,
scanner and weapons. Score-cache normalization during the original login is
separate from these conserved resources.

Reproduce with `python3 scripts/recover_broadcast_radio.py <new-directory>`.
The runner refuses incomplete parents and resolves parent dependencies in waves.
`python3 scripts/verify_broadcast_radio.py <new-directory>` independently rebuilds
the starting worlds and checks source-fixture auxiliary baselines, login identities/aliases,
keys, clocks, binary hashes, exact world/auxiliary
chains, complete message headers/body, decoded mailbox values and resources.
Nineteen corruption controls include fractional fields, scanner loss, counter
transitions, replay-chain damage and rehashed clock/header/startup changes.
No new decompilation or exact original RNG/numeric claim is made.

## Deliberate Go delivery policy

`RADIO ALL`, or `ALL` at computer option 5, explicitly confirms a broadcast to
all **current active accounts**, including the sender. The confirmation and final
preview show the recipient count. The final preview also explicitly warns that
the literal body and sender alias will be published in the Galactic Newspaper. The existing composer accepts 1–74 printable
ASCII characters, treats semicolons/slashes literally and requires a fresh
separate Send/Abort input. No broadcast is sent by logging in or joining a team.

Go uses individually addressed private copies with independent read flags,
consistent with team radio. This is a deliberate adaptation of the DOS shared
record, not a claim of matching the repeated-notification behavior above.
One reader never consumes another's notification, and an acknowledged copy is
not announced again. Copies use existing INBOX, login delivery and MESSAGES;
sent history lists each private destination. One typed public newspaper event is saved with the batch; private direct/team
mail is never projected into the newspaper.

The frozen recipient snapshot includes every nonretired account, in player-ID
order, regardless of team or whether the player is online. A dead account can
receive mail for its replacement ship; retired accounts are excluded. Later
joiners/reactivations cannot read earlier private copies, but may read the public
newspaper entry within its ordinary retention window. Any join, retirement or
alias change during composition requires confirming the current recipients
again. A successful retained draft can be retried after a later roster change
without creating more copies or resetting read flags.

## Transactions and compatibility

Broadcast and team radio share the same staged private-copy commit helper.
Broadcast stages that batch and the newspaper append in an outer candidate world.
Journal clock rollback or sequence exhaustion rejects a fresh send before either
archive changes. The existing rolling 1,024-event today/yesterday bound applies.
Ship-generation and season guards, five-minute draft expiry, session deadlines,
private histories and successful-output acknowledgement continue to apply.
Failed validation, insufficient space, message-ID overflow or an aborted update
publish no partial broadcast. A post-replacement directory-sync failure reports
committed copies and the public entry with a durability warning that ends the
login, preserving the warning even when receipt output fails. Retrying the same draft is idempotent, including after journal pruning.

Sending costs no turns or assets. Each recipient, including the sender, consumes
one of the existing 4,096 mailbox slots. The entire active roster (at most 50)
must fit; the game refuses a send rather than silently skipping recipients or
evicting old history. The public snapshot uses a new `radio-broadcast` news kind and bounded
`BroadcastText` field. World version **27** upgrades versions 1–26 without
backfilling old private mail; pre-27 worlds claiming new broadcast news are
rejected. Read-only upgrades never rewrite saves. No global read counter is added. Direct and system radio
retain their existing format and permissions.

## Validation and remaining work

Game tests cover current/retired/dead account eligibility, all 50 active accounts,
late-join privacy, independent reads, literal text, no resource charge, snapshot
copying, stale rosters, expiry, generation/season guards, capacity, overflow,
late failure and incomplete/retried batches. Store tests exercise aborted
transactions, committed durability warnings and concurrent retries. Door tests
cover the explicit ALL preview, fresh Send/Abort and roster changes during body
entry or final confirmation. Existing team-radio tests cover the shared helper.

`scripts/smoke_broadcast_radio.py` drives real compact and classic GoDoors PTYs:
ALL confirmation, sender/self-copy, multiple offline recipients, independent
read state, abort, no repeat notification and later-account isolation. The
transcript is [broadcast-radio-smoke.txt](../../evidence/broadcast-radio-smoke.txt).
Direct and team PTY regressions remain separate CI checks.

Native BBS transport/crash acceptance, full DOS shared-counter lifetime and
simultaneous writers, and the DOS multiline editor remain separate work.


## Public publication follow-up

The [extended evidence](extended/RECOVERY.md) supports this explicit publication
slice. One ALL send creates one public event, regardless of recipient count.
The body remains 1–74 printable ASCII bytes and is rendered literally beneath a
PUBLIC BROADCAST heading. Public events contain no private recipient IDs, request
IDs, account identities, passwords or read flags. The sender alias is an immutable
snapshot. Direct, team and system radio retain their existing private scopes.

[Validation details](../../evidence/BROADCAST_NEWSPAPER_VALIDATION.md) cover atomic
rollback, committed warnings, concurrent retries, capacity/sequence/time failures,
public/private isolation, migration and both terminal interfaces. This is not an
implementation of DOS shared notification budgets or multiline editing.

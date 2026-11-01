# Team radio

## Original DOS controls

Nine completed sessions of the unmodified DOS 3.6 executable establish team
routing and delivery. The [retained evidence](dos/results.json) includes exact
key feeds, DOS date/time logs, full compressed before/after worlds, all auxiliary
file snapshots, binary hashes and transcripts. Inputs use synthetic accounts in
fresh copies; the archive is never mounted for execution.

| Control | Result |
| --- | --- |
| Three-member send | One 86-byte private record each for sender Q, Enemy and Third |
| Two-member send | One record each for Q and Third; Enemy excluded |
| Abort | No private records created |
| No team | Rejected; no private records created |
| Enemy reads | Only Enemy's unread flag clears; sender and Third remain unread |
| Sender reads | Only the sender's own unread flag clears; sent history lists every copy |
| Enemy leaves before reading | Original copy still delivered to Enemy |
| Outsider reads | No team message displayed; no flags change |
| Enemy joins after sending | No old team message displayed; no flags change |

Each mailbox record contains three MBF numbers (unread flag, destination player
record, sender player record), followed by the padded 74-byte text. Both sends
use `YT TEAM PROBE`. This is the same ordinary private-message format as the
[direct-radio controls](../yt-navigation/COMMERCE_RADIO.md#radio-send-abort-delivery-and-history),
not a persistent team subscription. Successful sends include the sender.

All nine controls preserve the acting player's position, turns, credits,
combat equipment and cargo. Children start with their parent's exact final world
and auxiliary files; the two membership-change cases then apply their declared
membership/roster patches before login. These are controlled eligibility probes,
not a claim that they exercised the team-menu leave/join workflow in DOS.
The Go PTY check separately exercises actual team commands.

Reproduce using `python3 scripts/recover_team_radio.py <new-directory>`.
`python3 scripts/verify_team_radio.py <new-directory>` independently rebuilds the
starting worlds and checks binary/input/snapshot hashes, auxiliary chains,
packet destinations and text, separate unread flags, reports, normal returns and
resource conservation. Sixteen corruption controls exercise this verifier, including fractional mailbox
fields and scanner removal with refreshed witness hashes. Decoded MBF fields
are compared directly without integer truncation.
The capture refuses a child of an incomplete parent. No new decompilation or
original RNG/numeric parity is claimed by these radio controls.

## Go behavior and confirmation

Use `RADIO TEAM` or enter `TEAM` at computer option 5's recipient prompt.
The current team and each recipient alias/player number are shown before
confirmation and again before Send/Abort. The sender is explicitly included.
The existing single-line composer accepts 1–74 printable ASCII characters;
semicolons and trailing slashes stay literal. Send/Abort must be a separate
fresh input. Broadcast and DOS multiline editing remain separate milestones.

Recipient selection captures the whole current roster in player-ID order.
Prepare and commit both recheck that snapshot, including sender membership,
recipient aliases and team metadata. Roster, name, captain or invitation changes
require composition again. An identical name/number with a newly created team's
fresh password hash cannot inherit an old draft. The team snapshot and hashes
remain private in memory and are never printed or serialized with the draft.
The draft expires five minutes after preparation and is bound to the live sender's
ship generation and season; the door also enforces its session deadline.

Every member receives an ordinary private copy, including the sender. Copies
appear in existing login notifications, INBOX and MESSAGES, with independent
acknowledgements. The sender's sent history lists the individual destinations;
the recipient sees a normal private message. There is no new team-mail read
permission: outsiders and later joiners cannot read original recipients' copies,
and leaving a team does not revoke an already addressed private message.
No read receipt for another recipient is exposed.

## Atomicity and compatibility

The model stages all copies and message IDs before publishing any. Store.Update
then validates and atomically replaces the world under its existing lock.
Capacity and sequence overflow must permit the whole batch; otherwise nothing
is sent. A team send consumes one archive slot per member, including the sender,
against the existing 4,096-message limit. Sending costs no turns or assets.

Retries of the same retained prepared batch return its original message IDs
without duplication or resetting unread flags, even after a later roster change.
A partially present batch is rejected rather than repaired by sending duplicates.
Aborted callbacks, failed validation and failed replacement publish no copies.
A directory-sync error after replacement reports that the copies were committed
with a durability warning; retrying the same draft remains idempotent.

No new persistent fields, membership lists or shared receipt state are added.
The existing private-message schema and validation remain in use: world version
26 is unchanged and no migration is needed. Existing direct and system radio
continue to use their current behavior. Team selection is explicit; no team
message is sent just by joining or visiting a menu.

## Validation and remaining work

Game tests cover recipients, self-copy, independent reads, private histories,
no-turn/resource costs, roster/alias/team changes, replacement/season/expiry,
capacity/sequence exhaustion, late failure rollback, snapshot ownership and retry.
Store tests cover concurrent retries, aborted transactions and a committed sync
warning. Door tests cover literal text, fresh Send/Abort, recipient previews and
roster changes during composition or final confirmation.

`scripts/smoke_team_radio.py` uses real GoDoors PTYs for actual team creation,
join, leave, compact/classic sends, abort, offline/private delivery and late-join
isolation. Its transcript is [team-radio-smoke.txt](../../evidence/team-radio-smoke.txt).
Existing direct-radio smoke remains a separate regression check. CI reruns both
terminal flows, evidence verification and corruption controls.

Native BBS transport/crash acceptance, simultaneous original-DOS writers,
full multiline editing and broadcast radio remain outside this slice.

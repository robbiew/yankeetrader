# Direct radio and message history

## Recovered behavior

The existing [commerce/radio research](COMMERCE_RADIO.md) and its preserved
`commerce-dos/radio-*` sessions establish alias search, recipient confirmation,
one-line send, abort, login delivery, unread clearing, retained received history
and sender history through computer option 6. The DOS record has three MBF
fields and a 74-byte text field. This milestone adds no new DOS experiments.
A complete multiline editor, broadcast/team routing, retention policy and
concurrent delivery behavior have not been established by these fixtures.

## Implemented scope and modern policies

Computer 5 / `RADIO [alias or player number]` accepts one printable ASCII line
of 1–74 characters. Exact aliases win over substring matches; ambiguous searches
must be narrowed. If multiple accounts have the same exact alias, use the
player number; map iteration never selects an arbitrary recipient. Recipient confirmation precedes literal text entry. Queued
commands/typeahead are discarded before composition and before Send/Abort;
only a separate exact `S` sends. Semicolons and trailing slashes remain text.
Blank text or any other final response cancels without saving. Self-mail and
mail to offline or destroyed-ship accounts are permitted.

A five-minute draft binds the sender's ship generation and confirmed recipient
alias. The locked commit rechecks them and current archive capacity. A random
draft token makes retries idempotent, including retries after the recipient has
read the message. Sending changes no ship resources or turns. Ordinary encounter
mutation guards still apply to sending.

Computer 6 / `MESSAGES` exposes only the caller's sent and received messages;
`INBOX` filters unread incoming messages. Five-entry pages use increasing IDs,
refresh from the save after input, and never expose account identities, transport
tokens or sender read receipts. Alias snapshots and history survive later alias
changes and ship replacement. Message checks occur at login and command
boundaries, not while the caller remains idle at a prompt.

Delivery marks one recipient-owned message read only after its complete terminal
output succeeds. A narrowly scoped store operation permits this metadata update
during encounters without enabling resource mutations. Failed output keeps the
message unread. Delivery is at least once: a crash between output and save, or
concurrent sessions, can repeat a notification. Read messages remain in history.
The archive retains at most 4,096 world messages; reaching the limit rejects new
sends rather than silently discarding history. No deletion interface is included.

## Save compatibility and validation

World version 11 adds the radio archive and its next ID. Versions 1–10 upgrade
through the existing chain to an empty archive, preserving assets, mine grace
and account state. Read-only load does not rewrite saves. Stop all nodes and
back up the world before upgrading; older binaries cannot load version 11.
The loader rejects malformed IDs, tokens, aliases, text, timestamps, references
and archive overflow.

Game/store tests cover privacy, recipient-only acknowledgment, stale recipients,
ship replacement, expiry, rollback, concurrent retry, cursor pagination,
encounter guards and migration. Door tests cover literal composition, abort,
confirmation rechecks, failed output, login/reconnect and classic options 5/6.
`scripts/smoke_radio.py` exercises the actual GoDoors terminal with literal text,
Send/Abort, sender/recipient history, third-party exclusion and reconnect;
its transcript is `evidence/radio-smoke.txt`. CI runs this smoke alongside the
preserved commerce evidence verifier. These checks do not constitute native
live-BBS acceptance or full DOS screen/editor parity.


## Team-radio follow-up

[Team radio](../yt-team-radio/IMPLEMENTATION.md) now uses the same private-message
format for confirmed, atomic roster copies, including the sender. Independent
read flags and existing history/delivery permissions apply; no save migration
is needed. The earlier direct-only restrictions in this milestone are historical.
Broadcast and the DOS multiline editor remain separate work.


## Broadcast follow-up

[Broadcast radio](../yt-broadcast-radio/IMPLEMENTATION.md) now confirms ALL
current active accounts and saves ordinary private copies atomically, including
the sender. This is an explicit modern policy; retained DOS controls document
a distinct shared record and repeat-delivery behavior. World format stays 26.
Multiline editing and native BBS acceptance remain separate work.

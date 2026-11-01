# Broadcast research disposition and bounded follow-up

This is a research contract, not new Go behavior. The separate
[PR #58](https://github.com/robbiew/yankeetrader/pull/58) already implements
a documented adaptation using ordinary private copies for the current active
roster. This research supplements that work with original public newspaper,
shared-budget and exhaustion evidence; it does not replace that implementation
or relabel private-copy delivery as DOS parity.

## Recovered behavior versus the existing adaptation

DOS ALL is one public record per body line, addressed to -2. It starts with a
global budget of 30, and each automatic startup delivery reduces that budget
by two. Opening computer history does not spend another two. Reconnecting
can therefore announce the same line again and consume another shared delivery;
the operation is neither independent per-recipient unread state nor date-based
expiry. Broadcast text also enters the newspaper. See [recovery](RECOVERY.md)
and [native evidence](NATIVE.md) for observed cases and search boundaries.

PR #58 deliberately freezes current nonretired recipients, including the
sender, and stages ordinary private copies in one transaction. It excludes
future/reactivated recipients, keeps independent read flags and uses save26.
That policy prevents one reader exhausting another reader's notification.
It does not implement the original shared public record or its newspaper copy.

## Scope that must be chosen before another gameplay change

Keep the current direct/team/private history rules and explicit confirmation
of the current ALL audience. A newspaper addition would require an explicit
public-content preview before Send, a narrowly typed broadcast-news event,
bounded printable text and an atomic save with every radio copy. Private
direct/team bodies must never flow into that public event. If public newspaper
projection is intentionally omitted, document that adaptation explicitly.

An original-style global archive would be a different design: a distinct
public scope, integer remaining budget, history eligibility, sender history
after exhaustion, bounded pruning and fresh-session acknowledgements. Do not
encode -2 into the current private destination field: its validator requires a
real player. Do not replace the shared DOS counter with a day-based expiry
while claiming parity. New persistent fields would need a deliberate schema
migration and old-save defaults, rather than silently changing version26.

If that archive is selected, choose explicit finite storage and page bounds
before coding, stage the public message and newspaper event in one candidate
world, and preserve generation/season/alias/deadline checks. A prepared send
must be single-use/idempotent, including a retry after a committed storage
warning. Successful-output acknowledgements must not consume the same budget
twice when retried within one login. Concurrency, output failure and capacity
limits must not leave a partial message/newspaper publication or underflow.

## Validation required for a chosen follow-up

Cover Send/Abort, zero turns, no-team/current-team senders, literal single-line
text, changed authority, full archives and sequence exhaustion. Test private
and public scope isolation, sender/self history, shared versus independent
read behavior, reconnects, simultaneous readers/writers, reset/ID reuse,
rollback and committed warnings. Both compact and classic terminal flows must
show the actual audience and saved result; failed or cancelled sends print no
success receipt.

The complete DOS multiline editor, new/dead-account runtime eligibility,
maintenance's 72-versus-74-byte text-width issue, a long natural counter chain,
exact random/numeric behavior and native/live BBS acceptance remain separate.
No new send API, migration, Go gameplay or save26 data is added by this research.


## Selected implementation disposition

The user selected public newspaper publication with atomic saves and accurate
receipts. [The version-27 implementation](../IMPLEMENTATION.md) now provides that
slice alongside the retained private-copy delivery policy. The original-style
shared archive and its delivery-budget acknowledgements remain unimplemented.
The no-gameplay/save26 statement above describes the research milestone only.

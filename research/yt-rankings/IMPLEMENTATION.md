# Player/team scoreboard implementation

Computer `4` and `RANK`/`RANKINGS` generate player and team rankings from current
supported assets. `RANK OLD`, or `O` at the computer prompt, reads stored scores.
Both work with zero turns and spend no credits, inventory or movement turns.
The [27-session DOS recovery](RECOVERY.md) establishes the weights and scope.

## Supported scoring and deliberate policies

Ship shields earn 50 points; carried/deployed sector fighters 100; holds 2,500;
ore/organics/equipment cargo 20/30/40; credits 1; missiles 1,000; plasma 1,000,000;
ordinary port titles 50,000; ground forces 750; carried mines 2,500.
Cloak and planetary assets add no points. Scanners and NPC ranking rows are
outside the current Go implementation and are omitted.

Port counts come from authoritative current port owners, correcting the DOS
cached-count consistency gap. Personal deployed defenses count once for their
current owner. Teammates' assets are not assigned to the caller; team scores sum
current members' individual scores. Dead accounts remain listed with zero
score. Player ties sort by account ID; team ties sort by team ID. Both lists use
ordinal ranks rather than shared ranks.

Percentages use each list's leading score, truncate to two decimal places using
exact integer division, and display 0.00% for nonpositive scores or leaders.
Separate team normalization, truncation and negative-score handling are explicit
modern policies where DOS coverage remains incomplete. Each individual score
saturates at the existing save limit, 9,000,000,000,000,000 points. Team sums use
int64; the maximum 50 validated accounts remain safely within that range.
Percentage multiplication uses arbitrary-precision integers, avoiding overflow.

## Cache timing and transactional behavior

Only an explicit UPDATED/`RANK` request publishes new scores. One Store.Update
rechecks the bound live session and computes all players from the same locked
world, then saves every score together. Failures roll back the whole update.
The report and missile retaliation therefore use coherent published values.
Unlike DOS, normal quit and daily maintenance do not yet refresh this cache.
This policy keeps display work from introducing hidden changes at disconnect.
Retaliation continues to use the last published score until another update.

OLD means stored score values with **current** aliases, membership and port
counts, not a retained historical scoreboard file. No last-update time is shown
because none is stored. Newly created/migrated accounts can legitimately show
zero until rankings are updated. Dead rows show zero regardless of old caches.
No additional save fields or version change are needed; the radio prerequisite
already uses version 11 and the stored score field existed earlier.

A report uses one immutable snapshot across ten-line pages. Each page verifies
that the caller's ship session is still current and time remains. Pagination
reads a separate literal response, retaining pending main/computer commands.
Stopping midway does not undo a completed cache update. Output failures likewise
leave a successfully saved score update committed; a retry recomputes from
current state. Only public scoreboard fields are projected: no identities,
passwords, planet banks, trade tokens or individual asset breakdowns are sent.
Ordinary encounter mutation guards still apply to UPDATED requests; OLD remains
a bound read. No general-purpose encounter bypass is added.

## Validation

Tests compare supported weights directly with independently retained DOS golden
scores, including stored-cache replacement, linear holds and one-million-point
plasma. Additional tests cover title/defense transfer, current membership,
dead/zero/negative scores, stable ties, saturation, safe percentages, atomic
publication/rollback, concurrent updates, expired and invalidated sessions,
classic/compact input, paging, privacy and missile-volley cache use.

`scripts/smoke_rankings.py` drives real GoDoors PTYs through computer option 4,
OLD/updated reports, zero-turn requests, real team creation/join, stored cache
reconnect and authoritative port transfer. Its transcript is preserved in
`evidence/rankings-smoke.txt`; CI runs it alongside the DOS evidence verifier.
These tests establish neither native live-BBS acceptance nor full DOS screen,
scoreboard-file, maintenance or NPC parity.

The full race-enabled Go suite, vet, focused ranking regressions, ranking PTY
smoke, preserved 27-session DOS verifier and diff/format checks passed locally.

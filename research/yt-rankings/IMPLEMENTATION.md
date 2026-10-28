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

An explicit UPDATED/`RANK` request, clean logout and successful daily maintenance
publish new scores. Each computes all accounts from one authoritative world and
saves their caches together. Daily maintenance publishes after its economic and
turn phases, including worlds with no living caller. Its UTC-date guard prevents
same-day or backward-clock attempts repeating those phases or refreshing scores.

A confirmed classic quit, compact `Q` or normal Escape exit publishes scores
before reporting a successful save. The bound session and real deadline are
checked inside the store lock. The narrow logout operation can change only score
metadata, even during unresolved encounters; it cannot clear hazards, move ships
or open general resource mutations. Interrupted input, declined confirmation,
disconnect, expired time and destroyed/replaced sessions do not publish a logout
snapshot. Failure rolls back the entire cache update. If output fails after a
successful save, the committed cache remains saved.

Missile retaliation consumes the most recently published score. Other economic
and combat actions do not continuously rescore the world; the cache can remain
stale between these explicit boundaries. Replacement alone preserves the cached
value until the next boundary. These timings are modern transactional policies,
grounded in DOS's observed quit-time generation and maintenance scoreboard phase;
full DOS abnormal-exit timing and maintenance parity remain unverified.

OLD means stored score values with **current** aliases, membership and port
counts, not a retained historical scoreboard file. No last-update time is shown
because none is stored. Newly created/migrated accounts can legitimately show
zero until a publication boundary. Dead rows show zero regardless of old caches.
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
a bound read. Logout publication has a separate narrow metadata path; no general-purpose
encounter bypass is added.

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

The follow-up automatic refresh tests cover empty/all-dead worlds, maintenance
replay and rollback, concurrent publication, both encounter guards, expired and
stale sessions, declined/disconnected logout, output failure and cached reconnect.
`scripts/smoke_automatic_scores.py` drives real compact/classic quits and the
operator `-maint` command, including same-day replay; its transcript is
`evidence/automatic-scores-smoke.txt`.

Automatic-refresh validation passed the full race-enabled suite, vet, the
automatic-score PTY/maintenance CLI smoke, rankings smoke, missile/replacement,
planet-missile and sector-fighter terminal smoke, preserved ranking evidence,
and formatting/diff checks. Live-BBS acceptance remains unverified.

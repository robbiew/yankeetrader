# Confirmed spy triggers and login-local shared visibility

## Player-facing behavior

This implementation follows the retained [DOS controls](RECOVERY.md) and
[contract](CONTRACT.md). Earth hiring remains 333,000 credits per spy, at most
three per login. `SPIES` / computer 15 lists positions; `INTEL` retains the last
30 reports in five-report pages. Reports are acknowledged only after successful
output. Disconnect ends the network and its detection memory without a refund.

Successful movement (including each autopilot hop), docking, validated positive
missile/plasma launches and consequential unavailable planet queries advance the
network once. Fighter deployment/reinforcement, mine drops, sensor/list/history
screens and successful free planet reports do not advance it. Invalid input,
insufficient resources, declined consent and rejected actions do not progress it.
A missing planet or hostile sector defenses makes computer 9 / `PLANETREPORT`
unavailable: the saved query spends one turn and advances spies. Invalid sectors
and exhausted turns do neither. The receipt names the actual reason and remaining
turns. Successful own/foreign reports retain their existing privacy/access rules.

An accepted plasma launch that cannot reach its destination is still spent and
advances spies once. Missile preflight continues rejecting unreachable routes.
These are the existing distinct weapon policies, not a claim of complete DOS
routing or random-sequence parity. Safe zero-warp hold, finite RNG checks,
per-spy last-reported suppression across empty sectors and independent ordering
of the three spies remain intact.

## Private visibility and action boundaries

One cache belongs to each bound login. Spies import existing sensor/anti-cloak
detections and stage their new generation-bound grants. A successful world
replacement publishes the action, report/location memory and new grants together.
The shared cache is union-merged, retaining concurrent detections and anti-cloak
activation counters. The same login uses those grants for later sensor reads and
attack eligibility. Actual attacks still recheck living target identity,
ship generation, season, location and authority from the current world.

Saved target cloak never changes. Another login, including a fresh login by the
same account, cannot inherit or supply this cache. Neither spy state nor detection
memory is serialized. There is no new target warning, radio message, newspaper
entry or read receipt. The original target-relogin controls support that narrow
notification boundary rather than proving every possible DOS path.

Weapon-trigger scans run after input/quote validation and before impact, so
reports capture pre-impact defenses. Newly staged grants remain private until
the action saves and cannot expand the already confirmed target snapshot.
Missile dialogs now use a fresh, login-bound single-use nonce and complete quote
digest. Changed, altered, cancelled, replayed and cross-login confirmations fail
without spending resources or publishing a spy step. The preview is rendered
from the same immutable world snapshot used to build the quote.

The store retains its arrival/session/world locks and encounter guards. Deadline
checks cover queued world and visibility-cache access. Invalid RNG, stale
session/generation/season, validation failures and failures before replacement
publish neither action effects nor staged intelligence. A directory-sync warning
after replacement preserves committed effects and private state. Missile and
planet-query receipts render those actual results and join any output failure
with the committed warning; EOF cannot hide it or resume the login. Failed report
output leaves intelligence unread while the login remains alive.

## Compatibility and validation

World format stays **27** with no migration, dependency change or persistent spy
fields. Historical implementation documents describe the earlier trigger set and
spy-only cache; this document supersedes those restrictions.

[Validation record](../../../evidence/SPY_TRIGGER_IMPLEMENTATION_VALIDATION.md)
covers game/store/interface regressions, real compact/classic terminals, the full
race suite, vet, evidence verifiers and cross-builds. `smoke_spy_triggers.py` is
part of ordinary CI. Exact DOS RNG/MBF arithmetic, indirect/unconfirmed command
paths, live BBS acceptance and native Windows crash durability remain separate.

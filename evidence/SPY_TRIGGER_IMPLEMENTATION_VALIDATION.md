# Spy triggers and shared visibility: implementation validation

Implementation branch: `feat/spy-triggers-shared-visibility`, following research
`000af99c2678b262bb0c7a8c2e06252f69a1b809`. World format remains 27. No dependency
or original archive changes are part of this milestone.

## Runtime and transaction coverage

The full race-enabled Go suite and vet passed with the supported local GoDoors
checkout supplied through an external validation modfile. Repository dependency
files were not changed. Linux/amd64 and Windows/amd64 cross-builds passed.

New regressions exercise:

- Atomic publication of world effects, spy locations/reports and visibility on
  success or a committed directory-sync warning; no publication on callback,
  validation, RNG or deadline failure.
- Sensor and anti-cloak detections feeding spies without an extra cloak draw or
  shimmer; spy detections feeding sensor and attack eligibility and an actual saved attack with target
  generation checks, immutable saved cloak and no persistent warning/mail/news.
- Eight concurrent spy updates and eight competing single-use missile commits,
  including committed-warning replay, unread acknowledgement and fresh-login
  isolation.
- Missing/blocked consequential planet queries versus successful free reads,
  invalid input, exhausted turns and expiry; exact saved turn/resource receipts
  in both interfaces.
- Missile pre-impact defense snapshots without expanding the confirmed hidden
  ship target set; stale, altered, cancelled and cross-login quote rejection.
- Spent unreachable plasma progression, stale plasma and invalid weapon RNG
  rollback; session/world/visibility lock-wait expiry.
- Fighter deployment/reinforcement without spy progression, output failures that
  preserve unread intelligence, and committed warning propagation through EOF,
  closed pipes and other receipt failures without resuming the login.

The new real GoDoors PTY check passed compact and classic flows for fighter
transfers, charged missing reports, one-step missile/plasma progression,
unreachable spent plasma, anti-cloak sharing and reconnect privacy. It asserts
actual resources, ship detail, cloak, format version and absence of spy mail/news.
Transcript: [spy-triggers-smoke.txt](spy-triggers-smoke.txt).

The initial terminal fixture incorrectly assumed zero-valued cloak was serialized;
it now accepts the existing omitted-zero encoding. An initial receipt-failure test
matched the format string instead of rendered output; that test fixture was
corrected before the successful full race run. Neither required a gameplay policy
change.

## Broader checks

The first broad terminal pass exposed an unrelated randomized Xannor mine fixture:
a daily Wanderer arrival in empty intermediate sector 10 added planetary combat
losses to a mine-only assertion. A diagnostic repeat captured 33,938 losses with
the Wanderer destroyed; a separate unmodified repeat passed. Production Xannor,
Wanderer and maintenance code is unchanged. The mine-only fixture now returns
directly through its occupied HQ with the three mines there. Its planetary case
still exercises intermediate mines before hostile ground defenses. This isolates
the asserted mine loss range without weakening the force/resource bounds.


All **55 terminal/control commands** from the current CI workflow passed after
the fixture correction. Its mobile Xannor scenario also passed five consecutive
isolated repetitions. All **74 portable evidence/control commands** passed,
including 36 spy controls, three world/auxiliary reload chains, 20 native
observations, the spy corruption checks and **4,682 original archive hashes**.
The subsequent actual saved-attack/stale-target regression passed with the race
detector as well. No production gameplay logic changed after the successful full race suite.
Generated historical smoke captures are restored after validation; the new spy
trigger transcript is retained. No live world is used by the disposable fixtures.

## Limits

These are local tests and cross-builds, not GitHub CI results, live BBS acceptance
or native Windows crash-durability tests. Original DOS random streams, exact MBF
arithmetic and unconfirmed/indirect spy paths remain unresolved. No persistent
target notification is invented beyond the tested original detection boundary.

## Publication prerequisite integration

Before publication, PR #62's current head `83c990a` was merged into this branch.
README and validation append conflicts were resolved retaining both histories.
The prerequisite adds only its isolated Xannor planetary smoke fixture and docs;
the production Go tree remains identical to validated `a074705`. The updated real
Xannor planetary PTY passed ground victory, production/caps, captured-home
destruction, no-loot/replay and compact/classic private-history checks.

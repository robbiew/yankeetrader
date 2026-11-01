# Ship, cloak and disruption intelligence

## Recovered controls

Six completed sessions of the original DOS 3.6 executable add positive runtime
controls to the earlier spy research. Unmodified YT.EXE, BRUN30 and LOCAL run in
fresh disposable copies; no session arrays or executable instructions are patched.
The runner preserves key feeds, full compressed before/after worlds, transcript,
scoreboard and hashes in [dos](dos/results.json). Reproduce with
`python3 scripts/recover_spy_intelligence.py <new-directory>`, then run
`python3 scripts/verify_spy_intelligence.py <new-directory>`.

| Control | Observed report |
| --- | --- |
| Uncloaked Enemy at 101 | Enemy, team 1, 1,000 fighters, 10 shields |
| Full-cloak Enemy at 101 | No report |
| Half-cloak Enemy at 101 | Shimmering notice, followed by the same ship details |
| Two uncloaked ships at 101 | Enemy then Third, with each ship's actual fighters/shields |
| Caller alone in spy sector 100 | No report |
| Three-sector header, spy at 2 | Space-time disruption notice |

Each finishes with 1,667,000 credits and 497 turns. Saved cloak fractions of the
caller and target records remain unchanged. The caller-only probe's final hunt
location follows the ordinary randomly selected Earth warp; only its first two
locations are fixed. The narrow disruption control changes the declared sector
interval and follows the existing disruption research's deterministic sector-2
policy; it does not establish normal-world random frequency.

The earlier populated fixture had never cleared Enemy's baseline full cloak.
Its absence of ship reports was therefore not a positive uncloaked control.
The successful partial-cloak sample establishes that the shimmering branch can
run; one sample does not measure its probability or prove exact tie handling.

The preserved relocated bytes in [rea.json](../rea.json), independently checked
by `verify_spies.py`, cover the spy routine. Existing annotated interpretation at
sub2 `2e79:1f22..210e` checks the caller and cached sector, compares cloak with a
random draw, clears the session cache on detection and emits ship fields.
`2e79:1dda..1e18` checks the login's two disruption locations. These are static
interpretations corroborated by the new runtime controls, not a claim that
QuickBASIC was decompiled. Original random-sequence parity remains unknown.

## Bounded Go policies

Existing hiring, triggers, search-before-movement, suppression, 30-report history
and acknowledgement rules remain. Reports add actual living nonretired ships'
public aliases, team numbers, fighters and shields in player-ID order. The caller
is excluded. Teammates are eligible. Dead/retired records are excluded even if
an inconsistent sector remains; that is an intentional modern safety rule.
Disruption findings use only the observer login's bound pair, not another
login's hidden locations. Intelligence does not trigger an arrival or forced warp.

Uncloaked ships need no draw. An undetected cloaked ship requires a finite draw
in [0,1); strictly `draw > cloak` reveals it to this spy network. Exact-tie
exclusion is a conservative modern policy, not an observed DOS tie. Detection
is keyed by target ID and ship generation, shared among this login's spies,
and expires with the login. A newly detected ship prints a shimmering notice;
later reports reuse the detection without repeating it. Full cloak cannot be
newly detected by this policy. Detection never changes saved cloak energy,
the target's session, combat/sensor visibility or persistent radio history.
Sharing spy detections with combat and notifying targets remain separate work.

All detection memory, nested ship snapshots, movement and reports are cloned
under the existing action transaction. Invalid RNG, rejected actions and failed
world replacement publish none of them. A failed terminal write leaves the
report unread. Fresh/replacement sessions cannot inherit prior intelligence.
There is no schema migration; world format remains 26.

## Validation and limits

The independent evidence verifier reconstructs each patched starting world and
checks exact key feeds, binary and snapshot hashes, clean returns, report types,
complete line-anchored ship fields/order, locations, charges and unchanged saved cloak. Shield-only
corruption controls reject numeric suffix extensions with refreshed hashes. Corruption
controls check that semantic and provenance damage is rejected.

Game/store/door regressions cover detection thresholds, generation changes,
reconnect isolation, late invalid-RNG rollback, nested-copy isolation, saved-world
immutability, caller/dead exclusion and disruption findings. The real GoDoors
PTY spy smoke covers ship details in compact and classic flows, history and
unchanged saved cloak. Full race tests and vet are recorded at delivery.
Native BBS acceptance, target notification, exact odds/RNG/MBF arithmetic and
broader DOS spy triggers remain open.


## Subsequent trigger and shared-visibility research

[The new research](../triggers/RECOVERY.md) establishes further original-DOS
trigger rules and shared observer visibility, with no persistent target warning
on its tested detection/relogin route. The spy-only detection memory described
above remains the current Go policy; it has not silently become sensor/combat
visibility. The version-26 statement describes this historical implementation
slice; the current build is version 27. See the separate
[implementation contract](../triggers/CONTRACT.md) before aligning gameplay.

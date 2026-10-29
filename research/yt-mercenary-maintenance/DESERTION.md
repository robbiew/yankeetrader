# Human-defense desertion

Daily maintenance now checks human-owned sector fighter groups before existing
Mercenary route actions. The recovered comparison is strict:

```text
if random_draw * 100 > deployed_fighters:
    defense_owner = MercenaryOwner
```

Fighter count is unchanged by conversion. At the exact threshold the group keeps
its owner; 100 or more fighters can never satisfy the condition for draws in
[0,1). These are deployed sector fighters, not ship fighters or planetary ground
forces. No negotiation, payment, faction-base restoration or player death is
introduced by this phase.

## Identity, protection and order

DOS checked owner > 1 because its player records begin at 2. Go uses positive
living player IDs, including player 1; negative Mercenary/Xannor owners never
participate. Existing valid world validation still applies to all saved groups.
Protected Union sectors 1–7 neither convert nor consume a desertion draw. This
is a modern protection policy, consistent with hiring and route exclusions.

Eligible human groups are processed in stable descending sector order, consuming
one draw per group, including groups too large to desert. This avoids map-order
variation without claiming exact QuickBASIC RNG replay. Converted groups enter
the existing route snapshot immediately and receive its ordinary single-action
behavior. They may then move, merge, fight or encounter mines. Fresh tax-funded
hires still begin routing on the following day.

Conversion changes only the deployed group's owner. Human aliases, team
membership, credits, ships, port titles/treasuries, planetary titles, ground
forces and stocks stay unchanged by desertion itself. The normal other daily
phases still perform their documented production, tax, route and turn changes.
Owned-fighter reports and subsequent score publication use the new ownership;
callers encountering their former group use the existing BRIBE/combat controls.

## Persistence and validation

The existing UTC maintenance marker and locked transaction cover desertion,
routes, hiring, score publication and the day together. Same-day replay and clock
rollback do not consume randomness or reroll a retained group. Abort or failed
validation leaves the published save unchanged. The phase needs no new fields;
save version 12 and its migration behavior are unchanged.

Deterministic game tests cover both player IDs 1 and 2, one/50/99-fighter strict
ties and just-above thresholds, 100/1,000/maximum-size immunity, protected and NPC
exclusions, force and unrelated-asset conservation, stable order, conversion
before routing, current owned-group reports, score publication and replay.
The phase-order regression fails with the desertion invocation temporarily
omitted and passes after restoration. The public maintenance API uses the normal
random source; an internal helper permits controlled game regressions.

A store regression checks abort and invalid-save rollback, eight concurrent
updates with exactly one daily run, fresh-store persistence and unchanged
same-day/rollback saves. It accepts either valid random conversion outcome and
checks ownership/report consistency, avoiding a probabilistic unit assertion.

The real-process smoke checks a 100-fighter group and fresh one-fighter probes,
preserves protected groups and ship assets, verifies exact tax/force persistence
and same-day replay, then reconnects through compact and classic GoDoors to an
observed converted group. Every sampled outcome is checked; at most eight fresh
probes seek conversion, matching the bounded pattern of bribery smoke coverage.
UTC rollover restarts the entire disposable fixture up to three times, while
stable-date failures propagate. CI includes the new smoke.

The full Go race suite, vet, focused regressions, the four terminal smokes listed
below, maintenance evidence and all 4,682 archive hashes passed locally. The
negative control also failed as intended.

Validation commands:

```sh
go test -race ./...
go vet ./...
go build -o bin/yt ./cmd/yt
python3 scripts/smoke_mercenary_desertion.py
python3 scripts/smoke_mercenary_hiring.py
python3 scripts/smoke_mercenary_routes.py
python3 scripts/smoke_bribes.py
python3 scripts/verify_mercenary_maintenance.py
python3 scripts/verify_archive.py
```

Managed-worktree Go commands use a temporary module-file override pointing the
existing GoDoors replacement to /Users/robbie/GitHub/godoors. Committed module
files are unchanged. CI on this unpublished branch and live BBS acceptance are
not yet verified.

Next implement reserved Mercenary-base restoration with an explicit ownership
policy. Full NPC ship combat and bit-exact DOS RNG/MBF parity remain separate.

# Daily Mercenary hiring

Daily maintenance now funds Mercenary sector defenses using the taxes actually
debited from ordinary ports. Earth is excluded. Taxes are rounded separately at
each port before summing; the total fits int64 under the validated world limits
(at most 3,000 linked ports, each treasury bounded by MaxMoney).

## Recovered rules and modern policies

For collected tax T, N = floor(T/10). N < 1 hires nothing; N from 1 through 9
hires one group of N; N >= 10 requests ten groups of floor(N/10). Neither rounding
remainder is saved. This matches the [preserved DOS accounting](RECOVERY.md).

Placement draws without replacement from a sorted finite list of sectors with no
existing defense. Each draw removes one candidate; there is no rejection loop.
The Go game's Union protection excludes sectors 1–7, whereas DOS allowed 2–7.
Ports, planets, mines and present ships do not exclude otherwise empty sectors.
A player present at a new group sees the existing defense encounter on reconnect
or their next action; recruitment and combat retain their existing confirmations.
Hiring does not consume mines, move ships, transfer titles or take planet stocks.

If fewer sectors exist than requested groups, only that many full groups are
placed. Group size is not recomputed to concentrate the budget into those slots.
A completely full universe still completes all daily phases. Unplaced funding,
rounding remainders and force exceeding MaxQuantity (1,000,000,000 per group) are
discarded, without refund or carry. Capping is a modern quantity policy, not a
claim about DOS large-number behavior. Existing groups are never topped up,
replaced or moved. These choices avoid the DOS capacity hang and partial debit.

## Transactions and compatibility

Hiring runs after port production/taxation and before score publication inside
World.Maintain. Existing-group route actions now precede hiring; fresh groups
first act on the following day, a deliberate modern scheduling policy.
[Human-defense desertion](DESERTION.md) now precedes existing-group routing.
The existing UTC date guard handles same-day replay and clock
rollback. Missed days still perform one daily phase, following existing policy.
Both the administrative -maint command and login run maintenance through the
existing locked Store.Update transaction. A rejected update publishes no tax,
hire or date changes. A directory-sync warning after replacement is committed;
retrying that day does not hire or tax again. Random selection need not be
replayed identically after an aborted update, because no world was published.

Groups use the existing MercenaryOwner and SectorDefense representation. Save
version 12 and migration behavior are unchanged. No new balance field, NPC title,
base, public journal event or player command is introduced.

## Validation

Game regressions cover the DOS rounding boundaries, per-port tax rounding, Earth
exclusion, exact next-day balances without carry, repeated/rollback dates, full
and scarce placement, protected sectors, planet/mine preservation, and maximum
world economics with quantity capping. The rounding regression also fails with
the hiring call temporarily omitted, then passes with it restored.

Store regressions cover aborted callbacks, rejected saves, concurrent maintenance,
fresh-store reload, full-universe progression and committed durability warnings.
The real-process smoke runs -maint twice, checks exact saved force/tax balances,
reconnects through GoDoors to the resulting defense encounter, and runs the next
controlled full-capacity phase under a timeout. A separate fresh fixture verifies
that login alone taxes and hires without a prior -maint run. UTC-date changes restart the
whole disposable fixture up to three times; stable-date failures propagate.

The full race-enabled suite, vet, focused regressions, listed evidence verifiers
and all three terminal smokes passed locally. CI has not run on this unpublished
branch.

Validation commands:

```sh
go test -race ./...
go vet ./...
python3 scripts/verify_mercenary_maintenance.py
python3 scripts/verify_bribes.py
python3 scripts/verify_bribe_hostility.py
go build -o bin/yt ./cmd/yt
python3 scripts/smoke_mercenary_hiring.py
python3 scripts/smoke_bribes.py
python3 scripts/smoke_automatic_scores.py
```

For this managed worktree, local Go validation uses a temporary -modfile pointing
the existing ../godoors replacement at /Users/robbie/GitHub/godoors; committed
module files are unchanged. CI includes the new evidence verifier and smoke.
Live BBS acceptance remains unverified.

## Outstanding

[Route actions and planetary pickup](ROUTES.md) are now implemented as a
separate follow-on, as is [human-defense desertion](DESERTION.md). Reserved-base
restoration, full NPC ship combat and bit-exact DOS RNG/MBF parity remain separate
milestones.

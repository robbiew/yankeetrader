# Bounded Xannor HQ victory credit rewards

The supported fighter and missile commands now award bounded, exact credits for
clearing a positive Xannor-owned sector force at the authoritative Xannor HQ.
[The original recovery](RECOVERY.md) remains the source of the eligibility and
recipient rules. Modern credit limits, atomic persistence and truthful receipts
replace the original floating-point and separate-write behavior.

## Eligibility and payment

The battle must remove a previously positive force whose prior owner was Xannor
at the current saved HQ outside protected Union space. Merely being at the HQ
coordinates, defeating a different owner, damaging part of a force, retreating,
cancelling, or having a pending revenge target does not earn payment. A missile
may clear HQ along its route before its requested destination. A legitimate
return volley uses the same rule and pays its retaliating player, not the original
launcher. Plasma remains unimplemented; its recovered missing-owner-check defect
is not copied.

Only the acting living, nonretired player's account receives:

```text
credited = min(1,000,000, MaxMoney - current ship credits)
```

The current limit is 9,000,000,000,000,000 credits. A near-full account receives only
its remaining capacity, and a full account receives zero. Integer arithmetic
keeps the result exact even where DOS single precision enlarged or erased a
million-credit addition. No direct payment is shared with teammates, bystanders,
planetary banks or port treasuries. Current player identity is used rather than a
hardcoded slot.

A new qualifying victory against a restored HQ force may earn another award,
even with an already pending revenge target. There is no lifetime award flag or
redeemable saved receipt. Reconnect does not pay. Existing force snapshots and
ship-generation validation reject immediate duplicate/stale confirmations; the
locked store serializes competing confirmations so only the victor can remove
and earn from a given force. A fresh restored force requires an actual new battle.

## Atomic persistence and aftermath

The award runs inside the existing combat store transaction. Force removal,
missile/fighter expenditure, exact credit addition, revenge, public news and any
subsequent mine, retaliation, salvage or death effects commit together. Failed
callbacks and invalid final worlds leave the previous save bytes unchanged.
News sequence exhaustion or a clock predating saved news rejects an unreportable
victory instead of silently paying without a public event. A full journal uses
its normal bounded pruning rules; it is not sequence exhaustion.

The award precedes later combat/mine aftermath. If that aftermath destroys the
actor, normal death, revenge cleanup, salvage and replacement rules still apply.
A fatal-mine case retains the credit addition on the destroyed player record;
ordinary replacement resets ship credits to the starting amount. The reward
never grants a separate recoverable balance or revives the ship.

A post-rename directory-sync failure retains the existing explicit committed
error behavior. Reload reads the committed payment and cleared force; retrying
the old confirmation cannot pay again. The success receipt is printed only after
the store returns success. No synthetic success or rollback promise is printed
for a committed durability error.

Payment changes live score inputs. Existing explicit, login/logout and daily
stored-score publication remains unchanged; this milestone does not publish the
score cache during combat. This is narrower than the historical research
proposal's score-publication wording and preserves current retaliation/ranking
policy.

## Receipts and public privacy

Both interfaces print `Credits added: N` with the actual bounded addition after a
successful save, including forced defense combat following a refused HQ bribe.
A partial or zero addition also explains the ship credit cap.
The number describes the addition before subsequent aftermath, not a promise of
post-death spendable funds. Cancellation, rejection and rolled-back saves print
no reward success receipt.

Typed newspaper news snapshots the victor's alias and says they defeated the
Xannor HQ. The public event contains no credited amount, account balance, team
payment, planet details or port counts. The original launcher's terminal does
not expose a counter-volley victor's private addition. There is no new private
mail or delayed redemption flow for that counter-volley award.

## Save compatibility

World version 20 adds the `xannor-hq-victory` news kind. Valid earlier saves,
including version 19, upgrade in memory and write version 20 on their next
successful update. Read-only loading does not rewrite files. Existing assets,
identities, history, ship generations and pending revenge are retained. Migration
never pays pending old revenge or invents victory news. A legacy-labelled save
containing the new event kind is rejected. Older binaries cannot read version 20;
follow the README's stopped-world backup and coordinated upgrade procedure.

## Validation

Validated locally on macOS arm64 on 2026-10-30 with Go 1.27.3:

- Full race-enabled Go suite and vet passed. Focused game tests cover exact large,
  full and near-full balances, actor/team isolation, both weapon paths, routed HQ
  interception, non-Xannor/off-HQ/partial/retreat negatives, restored-force wins,
  stale generations, fatal mines/retaliation and the counter-volley recipient.
- Store tests cover byte-exact rollback, invalid final state, exhausted journals,
  eight concurrent callers/two contenders, reload, read-only version-19 migration,
  future-kind rejection, fatal mine/replacement and committed directory-sync
  failure without repayment. Door tests cover both interfaces, actual amount/cap
  receipts, forced-bribe-combat victories, cancellation, rejected saves and
  public/private separation.
- Nineteen real terminal smoke scripts passed, including the new fighter/missile/
  forced-bribe reward smoke through normal, one-credit, full-account and cancellation
  cases in both interfaces, including adjacent-HQ bribe refusals that force combat. That smoke also checks newspaper privacy and reconnect without
  repayment. The other 18 cover newspaper, awards, Mercenary base, mines, missiles,
  radio, salvage, spies, teams, Xannor lifecycle/mobile/planet/revenge/ship combat,
  ports, reports, trade reports and overcrowding.
- The 38-session reward verifier with 12 native byte observations, 16 rehashed
  semantic corruption controls, revenge evidence verifier and all 4,682 archived
  file hashes passed. Linux/amd64 and Windows/amd64 cross-builds passed.

Validation used an external temporary module-file override for the existing local
GoDoors checkout; repository module files and GoDoors sources are unchanged.
Live BBS acceptance and native Windows durability remain unverified. Exact DOS
RNG/MBF parity and interrupted original-DOS writes remain outside this milestone.

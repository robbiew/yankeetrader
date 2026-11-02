# Planet creation and port-sale notification implementation contract

This research adds **no Go behavior, saved fields or dependency changes**. Current
world format remains 27. The following is a scoped follow-up contract, not a
claim that these events/notices have shipped.

## Public planet creation

After a successful ordinary player creation, publish one typed public snapshot
of the creator alias and accepted planet name, rendered as:

```
  -  <alias> made a planet: <name>
```

Append only after all current action, identity, location, funds, capacity,
name and generation validation succeeds. The planet/sector link, 25,000-credit
debit and public event must share one authoritative transaction. A missing or
replaced login, changed season, invalid name, occupied sector, exhausted capacity,
expired session, failed save or declined confirmation must publish no success
entry. Retry/cancelled text is not the accepted name. A new typed saved event
requires an explicit format migration/validation policy; do not reuse assault
news or silently backfill historical creations.

Keep the supported Go safety policies explicit. DOS truncates long names to 41
characters and reserves three special names; Go currently rejects overlong input
rather than truncating and has its own generation/session guards. Decide any
additional naming alignment deliberately, rather than advertising all original
name behavior merely because an event was added. Creation remains turn-free.
No sector, team, fee, bank, cargo, ship state or account key belongs in this
public event. Future planet renaming/deletion cannot rewrite the snapshot.

## Port acquisition is a private seller event

The observed ordinary-port acquisition path does **not** publish purchase news.
Do not add a public acquisition entry in the name of DOS parity. A public
announcement would be a separate modern feature requiring explicit design scope.

For a successful buyout from another owner, capture the buyer alias, former port
name, sector and asking price for a durable **private notice to the old owner**.
The observed DOS text is:

```
<buyer alias> bought your port "<old port name>" in <sector> for <price> credits
```

The asking price is not the entire seller payout: the tested 31-credit sale also
returns 777 treasury credits, giving the seller 808. Keep price and total payout
accurate and distinct in any modern receipt. An unowned purchase has no former
owner to notify. Initial decline, insufficient funds, already-owned/no-port
rejections and failed saves send no purchase notice. A rejected rename after
accepted purchase is not proof that the purchase was cancelled.

If implemented, owner change, buyer debit, seller price-plus-treasury settlement,
treasury clearing and private notice must save together. Validate current quote,
owner/location/price, credit bounds, ship generation, season and session deadline
before mutation. Preserve Earth's existing unsupported-ownership policy; these
controls concern ordinary port 2, not every acquisition route.

The DOS packet uses recipient 3 and system sender -2 in the test fixture; -2 is
not a human buyer ID. Its legacy display label is The Mercenaries. The automatic
read decrements its counter from 1 to 0 and history does not decrement it again;
that observed retention mechanism is separate from a modern independent unread
flag policy. The current Go radio model has a different bounded/private
storage design. Use an explicit supported system-notice type and migration if
needed; do not forge a player sender, route it through public news, or copy the
original shared read counter without an explicit policy. Keep existing direct,
team and ALL privacy/delivery behavior intact. A port rename must not rewrite an
already captured old-name notice or cause a second settlement.

## Atomicity, receipts and validation

No effect or private/public notification before replacement; typed committed
storage warnings retain the actual saved action and notification. Preserve such
warnings even when receipt output fails or reaches EOF. A retry must not duplicate
a paid action, public success event or seller settlement. Reading history must
not synthesize actions, disclose another account's private notices or replay fees.

Regression coverage should include positive/negative cases, name retries,
old-name snapshots, unowned versus owned/team-owned ports, exact credit/treasury
accounting, reconnect recipient privacy, capacity, replay, concurrent nodes,
stale generation/season, lock-wait expiry, rollback, committed warnings and
failed receipt output. Exercise compact and classic interfaces, update README
in the same commit and keep gameplay validation separate from DOS research.

No exact DOS RNG/MBF arithmetic, character attributes, all original aliases,
concurrent-writer coherence or native Windows crash durability is established.

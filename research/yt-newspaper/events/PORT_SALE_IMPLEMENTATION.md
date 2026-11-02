# Private former-owner port-sale notices

An ordinary owned-port buyout now saves the recovered message:

```
<buyer alias> bought your port "<old port name>" in <sector> for <asking price> credits
```

The recipient is the former owner. `System: port-sale`, system sender 0 and the
legacy display label **The Mercenaries** explicitly identify this supported
system notice; no human sender is forged. Structured `PortSale` fields preserve
both full 41-character names, sector and integer asking price. Ordinary radio
text retains its 74-character limit; the system message is rendered from its
validated fields rather than truncated or split across mailbox records.

## Atomicity and privacy

Ownership transfer, buyer debit, seller price-plus-current-treasury credit,
treasury clearing and one unread notice save in one transaction. In the retained
31-credit/777-treasury case the seller receives 808, while the notice says 31.
Unowned purchases have nobody to notify and retain the existing unowned balance
policy. Team ownership remains personal ownership; teammates receive no copy.
No public purchase newspaper event is added.

Quotes bind the displayed port, owner, sector and price to a private snapshot,
old name, buyer generation/season and five-minute lifetime. Changed previews,
location, ownership, price, port name, epoch, life or clock rollback are rejected.
An owned-sale confirmation's private request token is retained in its notice;
replaying it after a later resale is rejected, even if owner/price match again.
A fresh deliberate repurchase still works. Current treasury is settled under
the lock, so new commissions between preview and commit are not lost.

The bound store checks actual session expiry under the save lock, before and
after mutation, and rejects a different buyer identity. Rejected inputs, declines,
insufficient funds, payout overflow, invalid recipient metadata, exhausted radio
IDs and failed/aborted saves publish neither settlement nor notice. A full
4,096-message archive blocks owned buyouts atomically; unowned purchases need no
notice slot. No old mail is silently deleted. Earth's ownership remains unsupported.

Only the former owner can read the notice through inbox and sent/received history.
The buyer and other accounts receive no history copy. Ordinary successful-output
acknowledgement clears the independent unread flag; history persists and does not
repeat settlement. Later port/buyer renaming cannot change the captured text.
This independent unread policy intentionally differs from the DOS shared counter.

A successful replacement with directory-sync failure remains committed and ends
the login. The buyer's receipt says the ownership and seller notice were saved;
receipt output failure cannot hide the typed durability warning or invite retry.

## Save compatibility and validation

World format 29 introduces the typed private payload. Supported formats 1–28 upgrade
in memory and persist on the next successful update, with no notices invented
for old sales and no money moved by migration. Pre-29 saves claiming a sale
system marker or typed payload are rejected. Existing direct/team/ALL, lottery
system radio and public creation events keep their existing privacy and retention.
Back up the stopped door and upgrade all nodes together; older binaries cannot
read save version 29.

Game/store/door tests cover owned, teammate and unowned purchases; exact settlement;
long names and immutable snapshots; strict system/payload validation; archive
capacity; wrong identity, changed quotes/life/season, lock-wait and late expiry;
rollback, committed warnings and failed receipts; concurrent competing buyers,
duplicate retries and old-confirmation reuse after resale; private history and
no-backfill read-only migration.

The [PTY transcript](../../../evidence/port-sale-notices-smoke.txt) covers compact
and classic confirmation/decline, settlement, seller-only reconnect delivery,
read/history retention, old names and absence of public purchase news.
Native research remains separate: [recovery](RECOVERY.md), [contract](CONTRACT.md).
No live BBS, native Windows crash durability, exact DOS wrapping/attributes or
simultaneous DOS-writer behavior is established by these checks.

[Completed local validation](../../../evidence/PORT_SALE_NOTICES_VALIDATION.md).

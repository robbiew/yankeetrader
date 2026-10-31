# Acquisition research disposition

## No new purchase implementation

The proposed Mercenary plasma-sales backlog item is closed as removed historical
behavior. The archived change log places its introduction in DOS 3.3 and removal
in 3.4. Version 3.6 provides planetary production and inventory transfers; its
Mercenary home planet is a defended capture target, not the old Mother Ship.
See [recovery](RECOVERY.md) and [bounded native evidence](NATIVE.md).

Do not implement the old five-million-credit price as a current merchant rule.
No seller eligibility, quantity cap, hostility threshold, tax sink, turn/cloak
charge, payment/delivery ordering or reconnect contract has been established
for the removed 3.3 feature. Historical descriptions do not justify mapping its
behavior onto the 3.6 home planet or a roaming Mercenary fighter group.

## Existing supply remains supported

Keep the implemented planet production, authorized whole-stock/item transfers,
combat salvage and bounded firing policies. Acquisition controls in this slice
exercise existing DOS planet take/deposit and Earth menus; they do not replace
prior production/estate research or prove all maximum numeric cases. Original
sequential player/planet writes do not imply atomicity; the Go transfer paths
continue to use their existing guarded transaction and actual saved receipts.

This research changes no Go gameplay, stock limits or save26 fields. It does not
call for a purchase intent, payment API, migration, new equipment option or tax
accounting path. Restoring a Mother Ship shop would be an explicitly chosen
optional extension with new policy, rather than a missing DOS 3.6 milestone.

## Remaining work

Additional ship/cloak/disruption spy intelligence, broadcast/team radio and DOS
multiline editing, public event types, exact original numeric/RNG behavior,
original world/save interchange, balance and native/live acceptance remain
separate. A historical 3.3 purchase reconstruction would require a matching
versioned executable and its own runtime observations.

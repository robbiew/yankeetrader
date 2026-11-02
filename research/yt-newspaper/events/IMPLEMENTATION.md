# Public planet-creation news

Ordinary successful creation publishes the recovered line:

```
  -  <alias> made a planet: <accepted name>
```

The planet, sector reference, 25,000-credit debit, nonreusable generation and
public snapshot save in one transaction. Creation is turn-free. The compact
CREATE command is the action request; classic creation retains its purchase and
name confirmation flow. Declined names are not published. Overlong/unsafe names
are rejected rather than DOS truncation; additional DOS reserved-name parity is
not claimed. There is no extra publication fee or confirmation.

Only alias and accepted planet name are captured. No sector, account key, team,
assets, price or message body is stored in this event. Rename, destruction and
later account changes cannot rewrite it. Any eligible newspaper reader may see
it in compact or classic mode. The existing 1,024-entry today/yesterday journal
retention and paging rules apply; old events may be pruned normally.

CreatePlanet validates inputs, available slot/generation, newspaper clock and
sequence before mutation. The bound store checks location, real session deadline,
ship generation and season under the save lock and checks expiry after creation.
Rejected or aborted transactions publish neither effects nor news. Occupied-sector
retries and concurrent duplicate requests cannot repeat the debit or event.
A committed directory-sync warning ends the login and remains detectable even if
the success receipt cannot be printed. News exhaustion blocks creation atomically.

## Save compatibility

World format is 28. Supported versions 1–27 upgrade in memory and persist only on
successful updates. No public creation entries are inferred from historical
planets. Pre-28 saves claiming the new event are rejected. Stop and back up the
door before upgrading all nodes together; older binaries cannot read save28.
The prior broadcast and spy privacy rules are unchanged.

## Validation and limits

Game tests cover immutable public snapshots, public-reader access, privacy fields,
retries, negative inputs, resources/capacity/generation/news failures, malformed
events and no-backfill migration. Store tests cover abort rollback, committed
warnings, concurrent retries, changed location/generation/season and pre/late/
lock-wait expiry. Door tests cover classic declines/name retries, exact literal
rendering in both modes and output failure retaining committed warnings.

The [terminal smoke](../../../evidence/planet-creation-news-smoke.txt) exercises
compact duplicate rejection, classic decline and accepted-name retry, exact debit,
no turn charge, reconnect newspaper reads and rename-proof snapshots.
Run `python3 scripts/smoke_planet_creation_news.py` after building `bin/yt`.
Native evidence remains separately checked by verify_newspaper_events.py and its
54 corruption variants. Private former-owner port-sale notices are not implemented.
No live BBS, native Windows crash durability, exact DOS wrapping/colors or
simultaneous original-DOS writer behavior is claimed.

[Completed local validation](../../../evidence/PLANET_CREATION_NEWS_VALIDATION.md).

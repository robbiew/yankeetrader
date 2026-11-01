# Spy trigger and shared-detection implementation contract

Research is distinct from gameplay implementation. Do not enable target warnings
or change visibility merely by merging these evidence files.

## Confirmed differences to resolve

1. Current Go advances spies after accepted sector-fighter transfers. Fresh DOS
   controls do not. Remove or explicitly retain that modern adaptation through a
   deliberate implementation choice; do not call it recovered trigger parity.
2. Positive validated DOS missile/plasma launches advance spies once. Current Go
   launch paths need an explicit spy-aware transaction before claiming parity.
   It is one accepted-command trigger, not one per weapon or route hop. Invalid,
   cancelled, zero/negative, insufficient-stock and failed-save paths must not
   publish a spy step or report. The retained unreachable-plasma control is a
   later targeting failure after accepted input, not a preflight rejection. Current
   Go plasma also commits a spent unreachable shot; current missile preflight
   rejects an unreachable route. Follow each weapon's actual accepted/committed
   result when staging spies, preserving these named policies rather than treating
   all route failures as equivalent.
3. DOS's unavailable Computer-9 planet query consumes a turn and advances spies.
   Keep successful/read-only reports free. A future implementation must distinguish
   missing/blocked information from input errors, obsolete sessions and cancelled
   queries, and atomically apply only the supported consequential query.
4. Spy detections share observer-local visibility with sensors and attack
   eligibility in DOS. Go currently keeps spy detection separate. Any alignment
   must preserve ship generation and season guards, private login scope and
   immutable saved target cloak; no global reveal or cross-login inheritance.
5. No persistent target notification was observed for the tested detection route.
   Do not invent a radio/news warning, fee, target cloak loss or target read receipt.

## Atomicity and access

Stage spy locations, last-reported locations, reports and detection memory with
the action's candidate world. Publish the entire set only after the action saves.
Keep committed replacement warnings distinguishable from uncommitted failures,
and retain them even if receipt output fails. A failed action, invalid RNG,
stale confirmation, expired session, wrong generation or changed season publishes
neither action effects nor intelligence. Do not authorize an attack from a stale
rendered report: recheck the current living ship and authority under the lock.
A newly staged reveal must not silently expand a previously confirmed target
snapshot; preserve sealed-intent validation when composing these actions.

Share successful detections only through the observer's bound login state.
Preserve successful-output acknowledgement and bounded private history. No
persistent schema change or new public message is justified by these findings.
Keep the existing safe zero-warp hold and rejection of invalid RNG as named Go
safety policies rather than reproducing an unbounded original loop.

Retain per-spy last-reported suppression across intervening empty sectors and
independent movement/reporting for all three spies. Avoid advancing spies just
because a report/history screen is rendered or a terminal page is acknowledged.

## Required implementation validation

Cover positive/zero/excessive/cancelled launch input, blocked versus successful
planet reports, fighter transfers and ordinary read-only commands; session-lock
expiry and stale generation/season; rollback, committed warnings, retries and
concurrent nodes. Test report suppression, all-spy ordering and visibility sharing
without saved target-cloak mutation or unauthorized target notifications. Prove
sensor/attack eligibility is reevaluated from authoritative state, and ensure
failed output does not consume unread intelligence. Exercise compact/classic
interfaces and update README in the same commit or PR.

Exact original random sequences/ties and all indirect command paths remain
unresolved. Runtime results cannot establish simultaneous-DOS cache coherence,
full battle odds or native Windows crash durability.

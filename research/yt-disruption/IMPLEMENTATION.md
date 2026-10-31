# Bounded disruption arrivals

The [61-control recovery](RECOVERY.md) and [candidate contract](CONTRACT.md) now
have a Go implementation. Save version **25 is unchanged**: the location pair
lives only in the bound login. The existing persisted `WarpSequence` also counts
forced disruption warps. Upgrade all running nodes together; old binaries do not
apply the new arrival rules. Read-only loading/migration never creates hazards.

## Recovered behavior and explicit modern limits

A successful login independently samples two sorted, valid interior sectors,
excluding Earth and the highest sector. For normal contiguous worlds this is
2..N-1; duplicate locations are allowed. The pair is captured once with the player,
ship generation and season. Menus, sensors and warning preparation do not reroll
it. Another login has its own pair. Reconnecting can encounter a newly selected
hole at the saved position; it does not reuse or repay an earlier receipt.

Startup and reached ship arrivals resolve disruption before mines or fighter
admission. Forced warp requires no consent, scanner or positive turn balance.
It can select every valid sector, including the same/other hole, current sector,
Earth, avoided sectors and disconnected sectors. A later non-hole landing resolves
its own mines and preserves ordinary hostile-fighter encounter gates. Mine grace
never grants immunity from a black hole. A ship-only forced warp never transports
a planet or another caller.

Ordinary planetary thrusters check disruption when their helper finishes or
stops at mines/fighters, preserving the recovered intermediate-edge boundary.
A route can pass a bare intermediate hole. A hazard stop at that same hole sends
the ship onward before consuming its hazards, while the transported planet stays
there. Wanderer transport still charges one planned edge and independently moves
the planet; its hidden position stays concealed after subsequent ship warps.
A collision/stress failure retains the existing physical prefix and failed-edge
accounting. Confirmed adjacent bribe/breach approaches into a known hole spend
the movement turn but do not fight, pay or recruit its skipped fighter group.

The shared heat kernel caches the original two-draw budget, performs at most 139
heat steps and stops at 31 heat. Destination and overwritten/recharge draws retain
the recovered order. Recharge is `min(turns,4*heat+floor(4*r))`; meltdown consumes
the remaining turns. Forced recharge directly debits turns and does **not** invoke
ordinary movement's cloak threshold. Original movement and manual/mine-escape
cloak policies remain separate. The mine-escape kernel's old overwritten-loop-
variable discrepancy is fixed with shrinking/growing mixed-draw regressions;
its finite physical-safe-destination policy is retained. A physically safe mine
escape can still land in this login's hole, so it receives another arrival check.

**Modern chain policy:** at most **32 disruption warps per transaction**. The
33rd would abort the entire origin action and all staged aftermath, spending no
resources and publishing no success receipt. Invalid/nil/NaN/infinite/out-of-range
draws, exhausted warp sequences, invalid clocks and stale authority also abort.
No free escape or arbitrarily committed partial chain is substituted. Existing
mine-burst limits remain, and each heat/destination selection is finite. These
are explicit safety choices; DOS did not have a finite arrival-chain cap.

## Atomicity, intent binding and visibility

The bound store installs a transient arrival context on its freshly locked world.
Existing mine-resolution seams apply hole-first arrival only to that login's
actor; administrative maintenance and other players retain their own semantics.
A final store hook also covers ordinary movement and escape paths that return
without a mine call. Planetary and warp receipts finish their arrival before
calculating final resource/position totals.

One world replacement contains the accepted origin movement/transport, recharge,
reached damage, mine escape/death, actual killer attribution, estate cleanup,
planet links/grant revocation and supported publication. Fatal callbacks still
commit before the obsolete session ends. Callback/validation/storage aborts leave
both the save and committed receipt state unchanged. Spy advancement is staged
after arrival; failures publish neither partial world changes nor partial reports.
The login context and receipt are installed only after successful replacement,
including a committed directory-sync warning.

The session lock serializes arrival state and receipt delivery; it is ordered
before spy/world locks. Startup and updates recheck deadlines after lock waits
and after calculation. Captured season and ship generations guard same-ID reuse.
The monotonic warp sequence invalidates zero-cost/same-position confirmations:
travel snapshots, mine entry, bribe/defense, direct ship attacks and missile target
snapshots include it. Existing fresh single-use tokens and planetary incarnation/
route/permissions/garrison checks remain intact. Exhaustion refuses before a
forced warp draws or spends. No new generic mine/defense bypass is introduced;
startup/current-arrival resolution uses its narrow existing encounter entry point.

Local sector views, adjacent sensors and installed danger scanners expose the
specifically observed disruption warning. A scanner can warn before entry; a
fresh refusal spends nothing. Generic reports/news/save JSON do not publish the
hidden pair, random seed, draw stream or hidden Wanderer destination. New missile
or spy disruption intelligence is outside this milestone.

## Player interface and receipts

Both classic and compact interfaces automatically resolve startup/reached holes.
Normal `M` movement and accepted scanner/mine warnings retain their usual consent
boundaries. Each saved forced step reports its known source, destination, heat,
recharge and meltdown state, followed by actual final sector, total action turns
spent and remaining turns. Later mine escape is labeled as an intermediate
landing rather than misreported as the final position. Mine attribution and
hostile encounter messages remain connected to play.

An involuntary interruption discards pending command input and ends autopilot,
even if the saved position happens to fit the old course. Earlier completed hops
remain spent. Aborted chains print no saved success. Committed durability warnings
survive EOF/closed-pipe/other output failures and end the login; they are never
treated as permission to replay spending.

## Validation and remaining acceptance

Regression coverage includes independent interval/duplicate draws, no persisted
location fields, clocks/invalid draws, startup and zero/low turns, hole hazards
preserved, reached damage/death/defenses, cloak conservation, repeated chains,
finite exhaustion, sequence capacity, ordinary/Wanderer planetary boundaries,
adjacent bribe/battle precedence and 32 seeded casualty/resource-conservation
worlds. Store tests cover whole-save rollback, validation/late draw/chain abort,
concurrency, exact committed receipts, no replay, reconnect, deadline lock waits,
and epoch/incarnation reuse. Both interfaces cover startup, movement/autopilot
interruption and receipt-write failures with committed warnings.

The real unseeded terminal check uses actual sensors to choose a current-session
hole; it tests both interfaces, fresh accept/refuse, initial mine/fighter bypass,
recharge arithmetic, queued-course interruption, zero-turn startup and private
news. Historical trade/combat/screen checks explicitly select quiet login paths:
a recorded forced warp or disruption scanner warning stops and restores only that disposable attempt
before retrying a fresh login, at most 128 times. Other errors propagate. This
does not disable or seed production disruption. Five helper regressions check
exact restoration, stable lock inode, bounded retries, real-failure propagation
the distinction between scanner warnings and ordinary sensor observations, and
the dedicated observer's unfiltered results. Two older maintenance fixtures
also isolate unrelated Wanderer production/random events that were reproduced
on the unchanged code; their original resource/report assertions remain.

See [executed validation](../../evidence/VALIDATION.md) for current results. Exact
BRUN30/MBF numeric and RNG parity, disruption combat/spy extensions, long-running
balance, live BBS gameplay and native Windows crash durability remain separate.
PTYs and cross-builds do not establish live/native acceptance.

### Current-sector queued input review fix

Both command-loop arrival checks now pass the pending command queue to the
committed-arrival receipt and restart the input loop before dispatch. This covers
a second login moving the same ship into a hidden disruption sector between
queued commands or during the input wait. Startup still resolves before normal
actions. The save schema and hazard rules are unchanged.

Four real-store regressions (compact/classic, both interleavings) failed before
the fix and pass afterward: stale commands are discarded, a fresh command line
is read, and zero-turn forced arrival remains committed.

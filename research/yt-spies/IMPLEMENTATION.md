# Spies and intelligence reports

Earth's normal shop option 9 hires spies; compact callers dock with `P` and use
`HIRE <starting sector> [starting sector ...]`. Each costs 333,000 credits,
with at most three active per login. All requested starts, the current Earth
docking token/expiry, ship generation, session deadline and funds are checked
under the world lock. The injectable game clock is sampled after both the
login mutex and world lock are acquired; time spent queued cannot extend docking
validity. Regression tests advance the clock across expiry while each lock is held.
Partial or rejected hires charge nothing. The original
docking turn is the only purchase turn cost. Computer 15 / `SPIES` lists current
hunt locations. These are ordinary player commands, with no research/debug path.

## Search and reports

Successful manual movement (including confirmed mine entry), each completed
autopilot hop, docking and sector-fighter transfers advance spies once. Search
precedes **spy** movement, using the committed action's current world snapshot.
A rejected/cancelled action never advances spies. Ordinary sensors, list/history,
trade, free information screens and maintenance do not advance them. This is
an explicit supported trigger set: other DOS unavailable-information branches,
battle/escape triggers and full daily spy behavior are not claimed.

Each spy reports mine count, planet name/projected ground forces and sector
fighters belonging to someone other than the caller, including teammate and
Xannor/Mercenary groups. Defense owner/team labels are captured at report time.
No planet balances, production, warehouse stock, weapons, account identities,
session credentials, ships or cloak state enter a report. Planet projection
uses current lazy growth on a copy and does not mutate the planet. Intel grants
no landing or combat access and cannot change/reveal a target's cloak.

A finding records its sector as that spy's last reported sector. While hunting
there again, the spy suppresses contents and continues moving. An empty sector
does not replace that remembered sector. Selection is uniform among stored
outgoing warps, equivalent in distribution to rejection of empty DOS warp slots;
RNG stream equivalence is not claimed. A zero-warp sector stays put safely.
Self-loop DOS evidence is exercised with this stationary policy because Go
world validation forbids self-loop warps.

## Session and transaction policies

Each login has its own network, bound to the caller and ship generation;
reconnect starts empty without refunding committed hires, matching the observed
DOS save/reconnect slice. Separate simultaneous logins do not share spies or
report acknowledgements. The three-spy cap applies to each login. No spy state
is serialized and no save version changes are needed (version 11).

The store clones network state under the same lock as each eligible action and
publishes the clone after the validated world replaces `world.json`. Failed
actions, invalid RNG, validation failures, save failures before replacement and
expired sessions publish no spy movement/reports. Directory-sync errors after
replacement return a typed committed-update warning and still publish the clone,
so visible credit deductions or movement never lose their corresponding spy
state. Hiring displays that warning with the granted spies, rather than reporting
a rejected purchase. The directory-sync boundary has an isolated failure-injection
regression in addition to the real obstructed-rename rollback control. A fatal
movement action still saves its death; the obsolete login cannot access the
prior network. Replaced ships cannot hire, list, read or
acknowledge the previous incarnation's reports. Encounter guards remain in place;
read-only list/history work like radio reads without permitting world mutations.

Reports print automatically between commands, before a docking menu and between
autopilot hops. A report is marked read only after every line prints successfully.
An output failure leaves it unread for a retry within the same live login;
disconnecting ends the whole network. `INTEL` shows the last 30 reports in pages
of five. When full, the oldest report is evicted even if unread. This bounded,
private, session-only history is a deliberate adaptation; it never creates a
persistent direct-radio entry. Reports are snapshots, not live surveillance.

## Evidence and validation

The seven [DOS probes](RECOVERY.md) supply golden location, report-count, mine,
planet-force, defender and resource controls. Game tests read the preserved
expected outcomes, including free sensor/list controls and stationary suppression.
Additional tests cover complete-batch purchase rejection, stale tokens/generations,
clock/credit/cap boundaries, projected-field privacy, late RNG rollback, ownership,
copy isolation, bounded history, acknowledgement, concurrent hires, failed store
validation/aborted actions, expiry, reconnect isolation and failed terminal output.

`scripts/smoke_spies.py` exercises the real GoDoors PTY in compact and classic
ASCII modes: Earth option 9, computer 15, current locations, mine/defender reports,
history, exact resource charges, zero-warp safety and reconnect loss. The transcript
is `evidence/spies-smoke.txt`, and CI repeats it. This is local terminal validation;
live BBS transport acceptance remains a separate check.

Ship/cloak runtime eligibility, shimmering odds, target notification, disruption
reports, broader original triggers and exact MBF/RNG equivalence remain research
boundaries. No speculative report types are advertised as playable.

Validation passed: full race-enabled Go suite and vet; spy/commerce evidence and
4,682-file archive verification; spy, port, navigation, mine, sector-fighter,
radio and automatic-score real-terminal smoke checks. Linux and Windows builds
are checked separately from native BBS acceptance.

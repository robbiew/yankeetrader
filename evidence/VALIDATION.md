# Trading and planet milestone validation

Validated locally on macOS arm64, 2026-10-25, with Go 1.27.3. Source and executable hashes are in `build.json`.

| Check | Result and scope |
|---|---|
| `go test -race ./...` | Pass across CLI, session, rules, and storage packages; output in `go-test.txt` |
| `go vet ./...` | Pass |
| Native build | `bin/yt`, macOS arm64 |
| Real PTY/GoDoors playthrough | Pass: Earth purchase → move → ore purchase → move → sale → quit |
| Save/reconnect | Pass: spent turns, cargo, money, and equipment preserved |
| Door32 local transport | Pass: stable record 42 keeps its ship across an alias change |
| Same-day maintenance via CLI | Two repeats preserve the exact save bytes |
| Competing processes | Three processes each commit ten increments without lost updates |
| Killed lock holder | Subsequent action acquires the kernel-released lock and commits |
| DOS trading fixtures | Five recorded ore trade outcomes match cash, cargo and treasury assertions |
| Linux amd64 build | Cross-compiles; native runtime not tested |
| Windows amd64 build | Cross-compiles; native file durability and inherited BBS socket not tested |

The terminal smoke run is fully disposable; its transcript is `local-smoke.txt`. The existing default world at `../data` is preserved; validation uses disposable worlds. No research DOS files or GoDoors library files were modified.

The two store helper tests are child-process entry points, not independent gameplay scenarios. Tests and smoke evidence establish the initial implemented loop, not full DOS gameplay parity. The generator/reference prices are provisional, and complete daily maintenance, team management, combat, NPCs and Genesis remain unimplemented. See the README's scope and storage notes before running a live BBS.

Build dependencies were available locally. Go module checksums are preserved in `go.sum`; the GoDoors source checkout was at revision `170c451faafedda81df7118012db9df129e16a7b` with pre-existing local changes. Those changes were left untouched.

Planet validation adds 19 original-DOS golden scenarios, with source snapshot hashes verified against 96 packaged evidence files. Cases cover creation, access, production, bank changes, investment and transfers. The two large-bank cases intentionally assert corrected integer debits rather than reproducing DOS rounding. Fractional production comparisons allow small DOS floating-point/time differences; this is not bit-for-bit MBF parity.

Tests additionally cover exact interest, maintenance-versus-visit ordering, clock rollback, rejected-action rollback, simultaneous bank updates, competing cargo pickup, stale access and version-1 migration. A real PTY/GoDoors playthrough creates a planet, deposits funds, invests, transfers and reloads cargo, reconnects and withdraws its bank balance. Daily planet ordering is covered by recovered-rule assertions; the 19 DOS golden cases exercise the interactive path.


## Bounded daily awards and inactive-player retirement

Save version 18 adds one-shot super-planet awards after NPC actions and safe
retirement before production. Retirement preserves stable authenticated identity,
death attribution and private history while releasing estates and active capacity.
The cutoff requires 14 days since both last authenticated activity and death;
returning identities receive new ship generations. Limits are 50 active accounts
and 256 lifetime identities, with no ID reuse.

Validation for this milestone: full race-enabled Go suite and vet; focused gate,
cutoff, capacity, fresh initialization, public/private separation, team/history,
post-assault landing-token and migration checks; 32 seeded worlds with 32 award
attempts each; atomic rollback/validation/concurrency and committed-durability
store tests; 14 affected real terminal smokes including the new compact/classic
maintenance smoke; research verifier with 11 rehashed semantic corruption controls;
all 4682 archive hashes; Linux/Windows cross-builds. The new terminal smoke uses a
saved award fixture for UI delivery and actual CLI maintenance for retirement;
game/store tests exercise deterministic award creation.

Live BBS acceptance and native Windows durability remain unverified. See
[implementation policies and compatibility](../research/yt-maintenance-lottery/IMPLEMENTATION.md).


## Bounded plague and civil-war maintenance

Validated locally on macOS arm64, 2026-10-30, with Go 1.27.3. Save version 19
adds typed public outbreak news while preserving the existing atomic store.

- Full race-enabled Go suite and vet pass. Focused rules cover strict gates,
  conditional/eager draws, post-growth effects, near-cutoff rate increases,
  one-pass outbreaks, caps, civil override, exact bounded credit debits,
  whole-unit ground, preserved title/home/weapons and public privacy.
- Capacity/ordering checks exercise 1,000 ports and 99 planets, full/exhausted
  journals and 32 deterministic seeded worlds. Store regressions cover abort and
  validation rollback, eight concurrent callers, reload, replay/clock rollback,
  committed directory-sync failure and read-only version-18 migration/rejection.
- Eighteen real terminal smoke scripts pass: new overcrowding, newspaper, awards,
  Mercenary base, mines, missiles, radio, salvage, spies, teams, Xannor lifecycle,
  mobile, planetary, revenge and ship combat, ports, reports and trade reports.
  The new smoke uses actual CLI maintenance for port outbreaks and replay;
  retained typed planet news checks UI delivery. Actual planetary event/damage
  behavior is deterministic in game, store and door tests. Older combat smoke
  garrisons now sit at the strict civil-war threshold to isolate assault rules.
- The 56-run DOS verifier, 16 rehashed semantic corruption controls and all 4,682
  original archive hashes pass. Linux/amd64 and Windows/amd64 cross-builds pass.

Validation used an external temporary module-file override pointing to the local
GoDoors checkout; repository module files and GoDoors sources are unchanged.
Live BBS acceptance and native Windows durability remain unverified. See the
[implemented policies and compatibility](../research/yt-plague-civil-war/IMPLEMENTATION.md).


## Bounded Xannor HQ victory credit rewards

Validated locally on macOS arm64, 2026-10-30, with Go 1.27.3. Save version 20 adds
typed HQ victory news. Exact integer payment is capped to ship credit capacity,
with receipts reporting the actual addition after a successful atomic combat save.

- Full race-enabled Go suite and vet pass. Focused tests cover fighter/missile
  eligibility, remote route interception, current actor/team isolation, large/full/
  near-full balances, stale confirmations/generations, restored-force repeat wins,
  mine/retaliation death, counter-volley attribution, news capacity and privacy.
- Store regressions pass for byte-exact abort/validation rollback, late news errors,
  eight concurrent callers/two contenders, reload, fatal mine/replacement, committed
  directory-sync failure and read-only version-19 migration without retroactive
  payment. Door tests cover accurate normal/partial/zero receipts and cap text in
  both interfaces, cancellation, aborted saves and public-news privacy.
- Nineteen real terminal smoke scripts pass: new HQ rewards, newspaper, awards,
  Mercenary base, mines, missiles, radio, salvage, spies, teams, Xannor lifecycle,
  mobile, planets, revenge and ships, ports, reports, trade reports and overcrowding.
  The new smoke exercises actual fighter/missile victories, normal/one-credit/full
  additions, cancellation, both interfaces, public privacy and reconnect without
  repayment. Historical regenerated smoke captures are preserved unchanged.
- Reward/revenge evidence verification, 16 reward semantic corruption controls,
  all 4,682 archive hashes and Linux/Windows amd64 cross-builds pass.

An external temporary module-file override points to the local GoDoors checkout;
repository module files and GoDoors sources are unchanged. Live BBS acceptance and
native Windows durability remain unverified. See the
[implemented policy and compatibility](../research/yt-xannor-hq-reward/IMPLEMENTATION.md).

PR #44 receipt follow-up: a new regression reproduced the missing success receipt
after forced combat from a refused HQ bribe. The bribe handler now displays the
same saved actual-credit/cap receipt before mine aftermath. Compact/classic tests
cover full, one-credit and zero-credit awards, cancellation and an aborted save;
the real HQ reward smoke also exercises adjacent-HQ forced bribe combat.


## Bounded danger scanner and manual emergency warp

Validated locally on macOS arm64, 2026-10-30, with Go 1.27.3. Save version 21
adds persisted scanner ownership and a warp replay sequence without granting
legacy ships equipment or changing their location/resources.

- Full race-enabled Go suite and vet pass. Tests cover exact Earth scanner debit,
  duplicate/quantity/affordability/docking errors, installed asset score value,
  scanner loss, own/team warnings, stale state, partial autopilot, finite bounded
  warp work, 64 seeded worlds, capped recharge, zero-cost same-sector replay,
  meltdown and daily turn reset and mine/defense/fatal arrival consequences.
- Store validation covers byte-exact rollback after callbacks, invalid final state
  and late mine errors; eight concurrent purchase/warp contenders; current state
  rechecks; lock-wait expiry during preparation and commit; committed directory-sync
  failure, reload and retry; death/replacement generations; version-20 read-only
  migration and future-state rejection. Door tests verify real saved receipts,
  fresh/stacked/cancelled/disconnected confirmation and extra automatic-escape debit.
- Twenty real terminal smoke scripts pass, including the new compact/classic
  scanner purchase/reload, exact debit/duplicate refusal, scanner manual/autopilot
  warnings, hostile entry and normal/one-turn random warp receipts. The other 19
  affected terminal scripts also pass. Historical regenerated captures are restored.
- The 41-session/10-native-observation scanner/warp verifier, 23 rehashed semantic
  corruption controls, 46-session hazard verifier and all 4,682 archive hashes pass.
  Linux/amd64 and Windows/amd64 cross-builds pass.

An external temporary module-file override points to the existing local GoDoors
checkout; repository module files and GoDoors sources are unchanged. Live BBS
acceptance and native Windows durability remain unverified. The modern daily-turn
reset is validated; original next-day engine repair and lethal warp-arrival parity
remain unverified. See [implementation and compatibility](../research/yt-scanner-warp/IMPLEMENTATION.md).


PR #45 review/CI follow-up: mixed-draw regressions failed before the fix and
passed after caching the warp heat budget once, including exact draw count,
destination, heat, recharge and persisted turn checks. The Earth port parity
smoke now checks real scanner availability while retaining unsupported-item and
DOS character/color assertions. All ten port parity cases and the scanner/warp
terminal smoke passed. The full race-enabled suite, vet, scanner evidence and
semantic corruption checks, and Linux/Windows cross-builds were rerun for the fix.
Regenerated historical port captures were restored.


## Cloak-energy and anti-cloak research

Validated locally on macOS arm64, 2026-10-30: 37 normally completed original-DOS
controls, 74 before/after snapshots, four exact world/auxiliary reconnect chains
and ten complete REA native byte observations. The independent verifier rebuilds
the declared input graph/port/player setup, freezes the recipe, checks all hashes
and input streams, rejects unexplained world bytes, and verifies exact credits,
MBF energy, turns, score effects, activation/decline/repeat behavior, global and
adjacent visibility, the original own-decay suppression and reconnect reset.

Twenty-three corruption controls include rehashed payments, energy, saved target
state, turn debit, scores, notices, confirmations and sensor output; altered
parent auxiliary inputs, keyboard streams, completion claims, native bytes and
frozen declarations are also rejected. The existing 41-session scanner/warp
verifier and its 23 corruption controls still pass, as do all 4,682 archived-file
hashes. REA's Ghidra session was exported and closed. Failed or preparatory probes
remain outside the retained corpus. README, plan and CI checks are updated.

This milestone adds research and evidence tooling, not Go gameplay. Save version
21 remains unchanged. Whole-program random/numeric parity, concurrent original
observers, target replacement during activation, live BBS acceptance and native
Windows durability remain unverified. See the
[research report and proposed implementation](../research/yt-cloak-equipment/RECOVERY.md).


## Bounded cloak purchasing and login-local anti-cloak

Validated locally on macOS arm64, 2026-10-30: full race-enabled Go suite and vet,
exact whole-point recharge limits/debits/defaults, paid activation/repeats/empty
results, score and ordinary decay preservation, stale login/ship/cache/nonce
checks, parallel spending, world/cache-lock expiry, byte-exact rollback and committed
directory-sync/reload/replay, and concurrent sensors waiting for the cache outcome.
Compact/classic tests check exact saved receipts and safe fresh decisions.

Twelve real terminal smoke scripts plus the ASCII port variant pass: new cloak
purchasing/activation, Earth-port parity, cloak, attacks, scanner/warp, startup,
idle clock, ports, navigation, missiles, bribery and spies. The new flow verifies
exact balances, blank defaults, zero-new-target paid repeats, reconnect/observer
isolation, unchanged victim energy and normal cloak decay during activation.
Historical generated captures were restored. The 37-session/10-native-observation
cloak evidence verifier, 23 corruption controls, existing 41-session scanner/warp
verifier and all 4,682 archive hashes pass. Linux/Windows cross-builds pass.

Save version 21 is unchanged: existing energy persists and anti-cloak remains
login-local. README, usage and CI are updated. Validation uses an external module
file for the existing local GoDoors checkout; repository module files and GoDoors
sources are unchanged. Live BBS acceptance and native Windows durability remain
unverified. See [implemented policies and compatibility](../research/yt-cloak-equipment/IMPLEMENTATION.md).


## Earth's paid Pick-6 lottery research

Validated locally on macOS arm64, 2026-10-30: 49 normally completed original-DOS
controls, 98 before/after worlds, three exact parent-world/auxiliary reload edges
and twelve complete REA native byte observations. The corpus covers five-credit
affordability, valid/invalid/leading-zero input, configured daily bounds and
fallback, repeated play/refusal, same-date reconnect, next-date reset, duplicate
and permutation matching, all six advertised payout tiers, public-news threshold,
score publication and high-balance MBF defects. Excluded mistimed or incomplete
diagnostic streams are not counted as successful controls.

The independent verifier rebuilds declared setup, freezes the recipe, checks
clock/keyboard/binary/file identity and exact reload chains, validates credits,
counts, turns, days, score caches, scoreboard and news scope, and rejects every
unexplained world/auxiliary change. Twenty-seven corruption controls include
rehashed credit, daily count/reset, cached/printed score, payout/input/refusal
receipts, public-news additions/omissions, parent auxiliary input, declared-clock
binding, native bytes, completion and frozen-recipe attacks. Existing cloak and
scanner/warp evidence verifiers and their 23 corruption controls each pass; all
4,682 archived-file hashes pass. REA evidence was exported and sessions closed.

README, plan, capture attributes and CI evidence checks are updated in this same
milestone. No Go gameplay or save schema changes are included: version 21 is
unchanged and paid Earth item 4 remains unavailable. The next implementation
contract deliberately uses exact integer money and atomic fee/prize/quota/news
settlement. Original interrupted/concurrent callers, year rollover, full RNG/MBF
parity, live BBS acceptance and native Windows durability remain unverified.
See [recovered rules and evidence](../research/yt-earth-lottery/RECOVERY.md).


## Bounded paid Earth lottery

Validated locally on macOS arm64, 2026-10-30: full race-enabled Go suite and vet,
all seven outcome tiers, permuted/duplicate tickets, exact five-credit fees at
small and large balances, all winning credit caps, finite default/configured
quotas, same-date persistence, UTC next-date/rollback/midnight guards, and actual
death/replacement without quota reset. Schema version 22 migration upgrades
version-21 saves in memory without changing file bytes, then writes only on a
successful update; legacy future fields and malformed lottery state/news reject.

Store checks cover immutable ticket/nonce binding, stale/cancelled/cross-login
quotes, parallel capped net-zero outcomes, authoritative sequence/quota replay
protection, post-world-lock and clock-callback expiry, deadlines around random
calls, entropy failure, byte-exact rollback, directory-sync committed warnings,
reload and replay. An expiry regression exposed a missing deadline recheck after
the clock callback; it passes after adding that check before any random draw.
Neither failed storage nor expired calls print a saved receipt; committed storage
warnings retain the actual settlement and cannot repay a ticket. The main loop
now ends the login on a propagated committed warning; a receipt-boundary typed
warning regression verifies that later queued commands do not buy another ticket.

Both interface tests verify exact saved receipts, fresh literal confirmations,
blank/No/stacked/invalid/disconnected/expired paths, classic item 4 and compact
LOTTERY dispatch, and actual capped-win public wording. The new real PTY script
passes for both interfaces: five OS-random tickets each, independently checked
multiset outcomes and every fee/gross/actual award/cap/balance/remaining-play field,
invalid/cancelled/typeahead safety, news threshold/scope, persisted exhausted quota
across reconnect, and a typed capped-news rendering fixture.

All 44 real terminal invocations (41 distinct smoke scripts plus three ASCII
variants) pass, including the new lottery flow; the newspaper rollover helper
tests also pass. The port parity smoke now compares the implemented lottery
credit-affordability column directly against the preserved DOS characters/colors.
All 148 regenerated historical captures were inventoried against their script
output paths, backed up, and restored to their prior hashes rather than included
as feature changes. The 49-session/12-native-observation paid lottery verifier and
27 rehashed corruption controls, existing cloak and scanner verifiers and their
23 corruption controls each, and all 4,682 archive hashes pass. Linux/amd64 and
Windows/amd64 cross-builds pass.

README, playable status, usage, save compatibility, reconstruction plan and CI
are updated in the same implementation commit. An external temporary module-file
override points to the existing local GoDoors checkout; repository module files
and GoDoors sources are unchanged. Live BBS gameplay and native Windows durability
remain unverified, as does full original RNG/MBF/animation parity. See
[implementation policies and compatibility](../research/yt-earth-lottery/IMPLEMENTATION.md).

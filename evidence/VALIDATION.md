# Trading and planet milestone validation

This is a chronological validation ledger. Older feature restrictions describe
their dated milestone; use the [current plan](../research/RECONSTRUCTION_PLAN.md#current-work)
and [README](../README.md#status) for implemented features and current scope.

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


PR #48 receipt-error follow-up: both regressions failed before the fix: a non-EOF
receipt failure lost the committed durability warning, and a joined EOF warning
was treated as a normal compact-session disconnect. The receipt path now joins
storage/output errors, and both compact EOF handling and deferred disconnect
cleanup retain committed warnings for the session-ending guard. Focused race-enabled door/store tests, affected-package
vet and the real compact/classic lottery terminal flow passed after the fix.
The finding was summary-only, with no inline review thread to resolve. README
and implementation notes were updated in the same fix commit.


## Genesis endgame and safe season-reset research

Validated locally on macOS arm64, 2026-10-30: 24 normally returned isolated DOS
controls, 48 before/after worlds, two exact parent-world/auxiliary follow-ups and
thirteen complete REA native byte observations across YT.EXE and RMT-INIT.EXE.
The corpus separates thirteen successful resets, six in-game refusals or
cancellations, two standalone cancellations, two deliberate fault outcomes and
one first-maintenance run. No timed-out preparatory alias-registration probe is
counted. Every retained control returns to a batch-written DOS completion marker;
raw CP437 logs and their decoded transcripts agree.

Controls verify cached versus actual admission at the 300-port default, equality,
19-to-200 fallback, threshold 20, in-game disabled 301, standalone normalization,
blank/No cancellation, record clearing/map reachability/configuration carryover,
zero-lottery-to-one and invalid-cargo-to-50 changes, stale-scoreboard retention,
blank winner reporting despite a case-paired mapping, missing initializer/error53,
consumed invalid markers, marker-based resume without fresh confirmation and the
separate required first maintenance. The records-only control retains cached
player117 zero after logout; no claimed ownership-cache repair occurred.

The independent verifier freezes declarations, reconstructs every input/parent
world and auxiliary chain, checks binary/file/date/clock/keyboard/return identity,
validates complete reset record patterns and directed reachability, and bounds
nonreset changes. Independent full-world hashes preserve legal native noncanonical
MBF zeros and broader maintenance effects; complete news/scoreboard witnesses also
bound the one maintenance follow-up. This supplements semantic checks without
claiming complete YTMAINT formula parity.

All 42 rehashed semantic/provenance corruption controls pass: altered setup,
accounts/titles/treasuries/configuration/stocks/warps/planet residue, cached count,
score, noncanonical zero bytes, maintenance dates/homes/stocks/auxiliary files,
completion/winner/confirmation notices, aliases/radio/news/scoreboard/marker
outcomes, exact parent auxiliary inputs, keys/clock/date/return/completion claims,
native bytes and frozen declarations are rejected. Notice attacks modify and
rehash both raw logs and decoded transcripts. The existing 49-control paid-lottery
verifier and its 27 corruption controls pass; all 4,682 archive hashes pass. REA
sessions were exported and closed, and archived originals remained unchanged.

The modern source audit identifies season-ID reuse, direct spy/cache binding,
nonpersistent winner news, immediate maintenance no-op and unbounded generator
rejection risks for a future reset. The proposed contract requires a monotonic
epoch captured inside login, actual owned-port recount, bounded winner results
inside the same atomic world replacement, finite generation, explicit bootstrap,
preserved supported settings, stable world.lock identity, accurate saved receipts
and rollback/durability/replay tests. These are requirements, not implemented
behavior or reproduced current reset vulnerabilities.

README, plan, provenance guidance, capture attributes and CI evidence checks are
updated in the same research milestone. Go gameplay and save version22 are
unchanged; Genesis remains unavailable. Native winner reconstruction in other BBS
mappings, mid-write crash/concurrent DOS resets, full RNG/MBF equivalence and
live/native acceptance remain unverified. See the
[bounded research and implementation contract](../research/yt-genesis/SAFE_RESET.md).


## 2026-10-30 — Bounded Genesis and safe season resets

Implemented on `feat/genesis-season-reset`, following the locally committed
24-control [research contract](../research/yt-genesis/SAFE_RESET.md).
[Implementation, usage and boundaries](../research/yt-genesis/IMPLEMENTATION.md).
README and reconstruction plan are updated in this same implementation milestone.
No active BBS universe was reset, no archival files changed, and nothing was
published as part of implementation.

Save version **23** adds monotonic season epochs, optional generation seed and
Genesis threshold, and up to 128 public winner results in world.json. Legacy
versions establish epoch one without reset, awards, historical seed invention,
history backfill or read-only writes. Configuration omission remains distinct
from explicit zero, including a zero-disabled paid lottery. The bounded generator
retains the connected ring and adds four unique destinations by finite shuffle.

Eligibility recounts actual non-Earth personally owned ports (default 300; explicit
zero disables, 20–300 valid). A quote binds sorted ownership, live public score,
ship/incarnation, epoch, settings, geometry and maintenance state. A two-minute
quote and real post-lock session deadline limit authorization. Both interfaces
require a new exact GENESIS line after queued input is discarded. Candidate
bootstrap, archive append and epoch advance commit in one replacement under the
existing lock inode. New stock and implemented faction homes exist before the
first new player. Same-day maintenance does not repeat initialization.

Completed validation:

- Full `go test -race -count=1 ./...` and `go vet ./...`, using a temporary module
  override for the existing local GoDoors checkout. Repository go.mod/go.sum are
  unchanged. Linux/amd64 and Windows/amd64 builds passed; native Windows execution
  and durability were not tested.
- Focused race regressions cover threshold minus/equal/above, disabled/invalid and
  unreachable defaults, authoritative title counts versus cached scores, supported
  custom port geometry, rich old accounts/assets/teams/messages/news/mines/defenses/
  factions being replaced, optional settings, minimum/maximum generation, bootstrap
  idempotence, live public scores and archive privacy/capacity/continuity.
- Stale ownership/settings/ship/clock/epoch and altered quote rejection; generation,
  nil-candidate, bootstrap and validation fault injection; byte-exact storage
  rollback; post-rename DurabilityError with committed result; single-use/revoked
  confirmations; concurrent eligible logins committing exactly one result.
- Actual child-process termination before replacement preserves the old bytes;
  termination after replacement leaves a valid complete new epoch/history. The
  persistent world.lock inode is unchanged. These are local process-kill controls,
  not power-loss durability evidence.
- Old logins reject new-season views, updates, logout score publication, radio,
  battle and spy acknowledgements, spy snapshots/hiring, and new confirmations
  after reusing the exact player ID/generation. Visibility/spy caches and prepared
  attack, missile, bribe, defense, mine entry/placement, scanner, warp, radio,
  lottery and anti-cloak values also reject epoch reuse before RNG or mutation.
- A captured-login/binding interleaving rejects an old epoch after another reset.
  The final audit also found and fixed classic startup retaining an ID from its
  screen lookup if the identity disappeared before authentication. Its actual
  identity decision now repeats under the login lock; a regression resets between
  lookup and authentication, reuses the ID for another BBS identity, and verifies
  the original caller receives only its own newly registered slot.
- Joined committed-warning/output failures remain discoverable, including EOF;
  successful or durability-warning resets end the invoking login and never query
  the obsolete player to reconstruct a receipt.
- All **45 real terminal invocations** configured in CI pass, including new
  `smoke_genesis.py`, compact/classic cancellation of queued/lowercase/chained
  answers, one exact saved reset receipt/logout, fully initialized new world,
  reconnect/public history, disabled-lottery retention, configuration CLI bounds
  and no replay. The newspaper date-rollover helper tests pass. Existing smoke
  fixtures now assert save version 23; deliberately old fixtures exclude the new
  fields. The first startup check caught an unnecessary help overlay; it was
  removed, and startup was rerun successfully with all 23 original menu rows and
  attributes intact (including the existing G entry).
- All **52 preserved-evidence verifier/control commands** configured in CI pass,
  including Genesis's 24 DOS controls/13 native reads/42 corruption controls and
  all **4,682 archive hashes**. No DOS or REA rerun was needed for implementation.
  The 148 tracked terminal captures regenerated by smoke checks were individually
  inventoried and backed up, then restored to their exact prior committed hashes;
  only this validation log is retained as the evidence-directory change.

Remaining: live BBS gameplay/door acceptance, native Windows crash durability,
full DOS generator/RNG/MBF equivalence, original winner mapping and mid-write DOS
reset behavior, The Wanderer lifecycle, explicit season archive export/admin reset
and remaining unimplemented game systems. Local tests/cross-builds do not establish
those outcomes.

## 2026-10-30 — PR49 history paging review fix

Verified review finding 4429293900: SEASONS reopened and validated world.json for
all 128 history rows in addition to its initial snapshot, holding the shared lock
for 129 reads. The first snapshot now validates page one; subsequent live session
checks happen only after paging pauses. A full 128-result report performs seven
reads, while each page renders the original immutable history snapshot.

The new real-store regression temporarily removes world.json during page rendering
and restores it at paging prompts. It failed before the fix for 20/21/128 results,
and now passes for 0/1/20/21/128. Separate compact/classic controls reset the world
and reuse the same numeric player/ship ID during a paging pause; the obsolete
login rejects before displaying row 21. The full race-enabled door suite,
affected-package vet, real compact/classic Genesis terminal smoke, the 24-control
Genesis evidence verifier and all 42 semantic corruption controls passed.

Also addressed the review's summary-only documentation note: RECOVERY.md now
explicitly scopes the unavailable/schema22 statement to its historical research
milestone and links the playable schema23 implementation. README and implementation
notes are updated in this same fix commit. No save schema or archival data changed.

## 2026-10-30 — Planetary thrusters and player forced-landing research

Completed a bounded follow-up to the historical planet/missile recovery on
`feat/planet-thrusters-landing-research`. This is research only: no Go gameplay,
dependency or save-schema changes; both actions remain unavailable and schema23
is unchanged. README, reconstruction plan, original recovery's follow-up pointer,
CI verification and capture-byte attributes are updated in this same milestone.
[Findings, bounds and proposed implementation contract](../research/yt-planet-mobility/RECOVERY.md).

Retained evidence: **55 normally returned DOS controls**, **110 before/after world
snapshots**, **two exact parent-world/auxiliary reload chains**, **19 native byte
reads** and **one verified DOS-MZ load-image observation**. Every executable ran
only against copied fixture files in newly created disposable directories. The
baseline is the exact archived fixture-planet-transfer world, SHA256
`2a63d12af095a59227840946be57fd4b7e4dafb5724d4019de694da7c4194b19`.
All archived originals remained unchanged; the independent archive verifier
passes all **4,682 hashes**. The REA native session was exported and closed.

Completed observations include ten-turn-per-hop/full-route budget checks at
9/10/19/20/21 turns, blank/No/invalid/current/unreachable targets, four-hop movement
and ordinary Earth placement, first/later collision with successful-prefix
persistence, zero/one fighters without ship death, owner/team/unguarded access,
reserved slot 100 refusal and Wanderer's separate planet/ship destinations. Mines
and hostile fighters stop after entering a paid edge; normal shell arrival can
then consume mines and damage shields. Raw133 controls are negative unmapped-field
checks, not black-hole tests. The35→25-turn witness keeps cloak unchanged.

Forced-landing controls distinguish denial/no-troops/cancellation/invalid
commitments, full/partial win, loss, one-on-one, fractional-input truncation,
fractional defense admission, neutral/dead-governor unrest, teammate/unguarded
access, faction owners at ordinary slots, and a ship with no fighters/shields.
Captured survivors remain as garrison; no combat turn debit is observed. Exact
follow-ups show captured reentry without another assault and retry990→980 carried
ground while defenders10000→9989. Static unrest uses INT(G*RND*RND), not a fixed60%.
Native random/MBF arithmetic is kept separate from runtime observations and modern
bounded/atomic policy.

Validation passed:

- Independent positive verifier reconstructs every baseline/common/case patch and
  slot copy, exact parent and auxiliary chain, returned marker, clock, key stream,
  transcript/raw log identity, all retained file hashes, narrow world mutation
  scopes, routes/turns/planet links, collision target preservation, mine aftermath,
  separate Wanderer relocation, public scores/news and ground trace/conservation.
  Frozen complete world and auxiliary witnesses supplement bounds for native
  timing/MBF effects; this is not a universal lazy-growth formula claim.
- All **41 rehashed corruption controls** reject with intended semantic/provenance
  diagnostics: setup, movement/turns/cloak/links, death/collision/Wanderer/mines,
  troops/capture/loss/fractional admission, team recount, production/bank/weapons,
  unrelated cargo, completion/battle/news/score, keys/date/clock/return/auxiliary
  chains/declarations, native bytes and MZ relocation tampering.
- All19 read observations match the original executable after independently
  applying its **870 MZ relocations**. The load-image witness also verifies file
  identity, sizes, entrypoint, exact relocation records and backed memory mapping.
- All **52 existing CI evidence/control commands** pass, including prior Genesis
  24-control/13-native/42-corruption verification and original archive hashes.
  The two new verifier commands are added to CI. New Python sources parse and
  whitespace checks pass. No Go/terminal regression rerun was needed because no
  application source or interface implementation changed.

Input-quality exclusions are explicit: initial probe1's blank landed Enter invoked
Take All after cancellation, so the entire exploratory probe is excluded. A first
fractional-defender probe landed without an assault prompt and consumed later
keys as planet-menu input; it was replaced by a clean L-only control. Slot-copy
controls were recaptured with complete common-stage metadata. Final retained
raw worlds/logs/keys and result metadata were copied unchanged, not rewritten to
fit expected outcomes.

Remaining research/acceptance boundaries include true session-random disruption
arrival, stress explosion frequency, maximum/rare/simultaneous ground outcomes,
exact original RNG/MBF parity, interrupted/concurrent DOS actions and native BBS
socket behavior. The safe Go contract still needs implementation: fresh intent and
planet/ship/season identities, current permissions and lazy projection, finite
work, whole-command atomic outcomes, grant revocation, explicit faction policy,
accurate saved receipts and fault/concurrency/replay tests. Native Windows crash
durability and live BBS acceptance remain separate.

## Planetary thrusters and player forced landing — 2026-10-31

Implemented locally on `feat/planet-thrusters-forced-landing`, following the
55-control [research](../research/yt-planet-mobility/RECOVERY.md) and the
[bounded implementation contract](../research/yt-planet-mobility/IMPLEMENTATION.md).
Save version 24 adds a monotonic planet-incarnation allocator and typed player ground news;
version-1 through version-23 reads upgrade in memory and write only on a successful transaction.
All constructors, including both faction restorations, super awards and Genesis
bootstrap, allocate identities. Faction homes remain immovable after capture.

Validation completed locally:

- Full `go test -race ./...` passed, including migration, rollback, concurrency,
  replay, committed durability and complete-session capture-grant revocation.
  This managed checkout used an external temporary `-modfile` pointing at the
  existing GoDoors checkout; repository dependency files were unchanged.
- `go vet ./...` and Linux/amd64 and Windows/amd64 cross-builds passed.
- Game/store/door regressions cover 9/10/19/20/21-turn affordability, shortest-route
  confirmation snapshots, collision/stress prefixes and zero fighters, multiple
  landed callers, hostile/friendly sector defenses, mine damage/fatal self-source
  attribution and late-hazard rollback; strict troop quantities, capture/defeat,
  vacant-government unrest, 4096-round exhaustion/no-refund retreats, 32 seeded
  conservation worlds, lazy economic projection, exact same-slot replacements,
  epochs, current permissions, modified routes/resources/hazards, concurrent movers
  and attackers, nonce tampering/cross-login/replay, lock/action deadline expiry,
  read-only migration and rejected legacy future fields.
- All 47 CI terminal command invocations passed locally, including ANSI/ASCII DOS
  comparisons and the existing startup, commerce, ownership, teams, radio/intel,
  combat, faction, scanner/warp, lottery and Genesis scenarios. The new real PTY
  milestone checks ten movement/collision/cancellation/assault/adoption cases
  across classic and compact interfaces, with a reconnect after each. The final
  build repeated all ten new cases successfully. Fresh confirmation ignores
  queued answers; saved receipts show actual positions, costs, losses, retreats,
  garrisons and remaining stock. A cancelled compact trip retains its leave
  handle. Capture revalidates its exact saved grant before displaying the planet.
- All 54 preserved-evidence verifier/control commands passed, including 55 returned
  mobility DOS controls, 19 native byte reads/MZ mapping, 41 rehashed mobility
  corruption controls and all 4682 original archive hashes. Archive files were
  unchanged. Updated Python sources parsed; 167 local documentation links resolved.
- Generated existing terminal captures were inventoried and backed up outside the
  repository, then all 148 tracked outputs were restored and verified against HEAD
  hashes. Preserved research/screens were not replaced by this implementation.
  README, plan, implementation notes and CI/active schema fixtures are included
  with this milestone.

These results establish local bounded modern behavior, not full native RNG/MBF
parity, a measured stress distribution, Wanderer/disruption transport, long-running
balance, live BBS acceptance or native Windows crash durability. Every physical
prefix/collision/assault/mined-arrival outcome saves once under the world lock;
software/RNG/validation failures discard the full candidate. Committed directory
sync warnings remain joined with receipt-output failures and end the login.

## The Wanderer lifecycle and transport research — 2026-10-31

Completed the bounded [Wanderer recovery](../research/yt-wanderer/RECOVERY.md)
on `feat/wanderer-lifecycle-research`, following the ordinary mobility milestone.
This update contains research, capture/verification tools, README/plan and CI
changes only. Go gameplay, dependencies and save version 24 are unchanged.

Evidence retained and independently checked:

- 57 normally returned original DOS controls, 114 world snapshots and nine exact
  parent-world/complete-auxiliary chains. Capture uses copied original files,
  declared state/name/occupancy/hazard patches, preserved clocks/keys/redirection,
  raw CP437 program logs and a normal-return batch marker. Controls cover direct
  YT-INIT versus standalone RMT-INIT/bootstrap, reference-driven partial restoration,
  inactive/duplicate/renamed states, daily governor reset and zero-bank refill,
  source/Earth/mined/guarded/disconnected placement, same/next/backward dates,
  ordinary landing/team/adoption/name/bank/transfer operations, whole-quote
  affordability, one-edge ship/planet separation, cancellation, collisions,
  separate planned/random hazards and reconnect/maintenance follow-ups.
- One eight-second no-candidate diagnostic explicitly requires timeout/nonreturn,
  partial restoration and absent accepted link despite optimistic warp messages.
  One additional normally returned maintenance diagnostic requires relocation
  before later Xannor assaults/destruction. Neither is counted as an isolated
  normal control. Pointer saturation is an explicit malformed-reference fixture,
  not a claim that the original supports 3000 distinct planets.
- 14 REA byte observations, three verified MZ load images and all 1006 relocation
  fixups across YT-INIT/YTMAINT/YT. Full inline Evidence, executable identities,
  addresses, mappings, limitations and an Evidence-ID ledger are retained. Every
  opened native session was exported and closed. These static reads corroborate
  selected code, rather than purporting to observe execution.
- `verify_wanderer.py` passed independent setup/semantic/privacy/provenance checks,
  frozen complete-world/auxiliary witnesses and both classified diagnostics.
  `test_wanderer_verifier.py` rejected 55 deliberately rehashed corruptions:
  51 ordinary semantic/setup/clock/key/return/native/privacy mutations and four
  timeout/interference mutations. The final two-test run passed in 69.356 seconds.
- All 56 CI evidence-verifier/control commands passed locally, including the new
  pair, existing research and all 4682 original archive hashes. Original archive
  files were unchanged. Three new Python sources parsed and 167 local documentation
  targets resolved. No Go tests or terminal smoke suite was rerun for this
  research-only delta; prior gameplay validation remains in the preceding entry.
- A fresh one-control DOS reproduction verified that the corrected capture writer
  retains compressed per-case metadata and satisfies independent semantics/file
  hashes. Repeated original metadata is stored losslessly compressed. Three
  duplicate per-case metadata files from corrected captures were reconstructed
  deterministically from their untouched complete top-level manifests after fixing
  a cleanup omission; captured values/worlds/logs were not edited. The original
  invalid reentry input is excluded; the retained control explicitly declines a
  new purchase with N and uses its exact transport parent.

Boundaries: finite controls and selected native ranges do not establish universal
RNG distributions, bit-exact MBF economics, stress probability, concurrent/mid-write
DOS safety, live BBS gameplay or native Windows durability. The follow-up contract
requires explicit mobile identity/capacity/migration, finite placement, modern
once-per-date maintenance, clean restoration, atomic links/title/assets/grants/
NPC aftermath and known-versus-hidden location receipts. The native destination
remains concealed; no public Wanderer movement notice is invented. The existing
Go door still has no active Wanderer lifecycle or special transport branch.

## Bounded Wanderer lifecycle and special transport — 2026-10-31

Implemented the [save25 Wanderer contract](../research/yt-wanderer/IMPLEMENTATION.md)
on top of the 57-control recovery. Unique persistent identity in reserved slot 1
allows 100 total planets without taking ordinary slots 2–100. Older-save loading
upgrades in memory without minting assets or rewriting the file. Initializer and
Genesis bootstrap a clean current-dated Wanderer; daily restoration uses a fresh
incarnation, finite sorted placement and explicit faction-home priority. Daily
movement clears its governor, refills only a post-economy zero bank, preserves
other legitimate assets and revokes landing grants. Final receipts reflect later
NPC destruction, without restoring a second Wanderer during the same run.

Special transport retains full-route affordability, but successful movement
charges/stops after one edge. Planet and ship destinations differ; planned-edge
collision/stress precedes random relocation, and ship hazards resolve only at the
ship's reached sector. Both interfaces seal candidate occupancy, planet/ship/
season identity, permission, budget and hazards into fresh single-use confirmation.
Saved receipts report actual costs and known ship position while concealing the
random planet destination. Administrative receipts likewise omit coordinates and
join committed storage warnings with output failures.

Executed locally:

- Full `go test -race` suite and `go vet` passed. The temporary validation modfile
  selected the local supported GoDoors checkout; repository dependencies did not
  change. Additional race-enabled Wanderer game/store tests passed after adding
  the 100-planet capacity and competing-mover regressions.
- Game/store/door/CLI regressions passed for clean template, finite/deferred
  placement, invalid draws, schema24 read-only migration, marker validation,
  movement/restoration incarnations, asset/grant conservation, forward-only daily
  guards, final NPC destruction, captured private history, full-route turn budgets,
  split positions and planned/random hazard roles. Atomic callbacks, late RNG and
  validation failure roll back the whole save; concurrent daily runs and movers
  commit once. Changed candidate occupancy, daily relocation and replacement
  invalidate quotes. Committed durability warnings survive failed receipt writes,
  including EOF/closed-pipe failures; aborted saves print no success receipt.
- All **48 CI terminal commands** passed, including the new Wanderer compact/classic
  initialization, budget refusal, fresh cancellation, one-edge or physical
  stress/collision outcome, hidden receipt, reconnect, daily neutralization/refill
  and no-replay scenarios. Genesis verifies three fully bootstrapped planets.
  Existing transport, NPC battles/revenge, equipment, trade, reports and lifecycle
  scripts passed with save25 assertions. Isolated historical save/DOS fixtures
  remove post-schema bootstrap assets; ordinary creation scenarios use an empty
  sector. Empty neutral occupancy fixtures keep a random Wanderer from intercepting
  isolated ship/revenge battles without a debug RNG flag or weaker assertions.
  The ordinary collision fixture uses canonical whole-second timestamps so Go's
  fractional-second serialization cannot fail its untouched-target comparison.
- All **56 CI evidence/control commands** passed, including 57 returned Wanderer
  controls, both separately classified diagnostics, 14 native byte observations,
  all55 rehashed Wanderer corruption controls and **4682 archive hashes**.
- Linux/amd64 and Windows/amd64 cross-builds passed; formatting, edited relative
  links and diff whitespace checks passed. Generated terminal captures were backed
  up, inventoried and restored by verified path/hash, preserving historical evidence.

README, implementation/recovery/plan notes, terminal fixtures and CI include this
milestone. Full DOS RNG/MBF fidelity, targeted disruption, long-running balance,
live BBS gameplay and native Windows crash durability remain unverified/separate.
Cross-builds and PTYs are not live/native acceptance.

## PR50 assault-preview correction — 2026-10-31

Validated review finding4432205875: another session could change the planet or its
garrison while the caller answered initial consent/troop-quantity prompts. The
new sealed intent accepted that newer state while the final question retained the
old displayed name/defenses. Both classic/compact regressions failed before the
fix at both pauses, drawing combat RNG and spending10 troops against changed state.

The sealed assault intent now checks the original identity/incarnation, sector,
name, governor, projected integer garrison and assault/adoption status before the
final question; a changed carried ground stock also requires reconsideration.
Material elapsed growth is projected from the fresh intent without saving it.
An unchanged displayed integer garrison remains valid. A rejected preview cancels
its intent, performs no draw, spends no troops and prints no saved receipt.

Validation passed: full race-enabled Go suite and vet, 24 classic/compact prompt-
interleaving regressions (garrison, same-name replacement, rename, elapsed growth,
governor and carried troop changes at both pauses), game projection/adoption checks,
all ten real classic/compact mobility PTY scenarios, 55 retained DOS controls/19
native reads and all41 semantic/provenance corruption controls. Temporary validation
modfile selected the supported local GoDoors checkout; dependencies and save24 are
unchanged. README and implementation notes are included in the fix. Live BBS and
native Windows durability remain separate acceptance.

The verified PR50 correction was then merged locally into the unpublished
Wanderer milestone, preserving its complete implementation/research documentation.
Race-enabled Wanderer/assault-preview/ground-action game, door and store tests,
affected-package vet, all ten ordinary transport/landing PTY scenarios and the
Wanderer compact/classic PTY scenarios passed after propagation. Save25 and the
Wanderer destination/privacy rules remain intact; this merge was not published.

## Disruption and black-hole arrival research — 2026-10-31

Completed the [arrival recovery](../research/yt-disruption/RECOVERY.md),
[native analysis](../research/yt-disruption/NATIVE.md) and
[candidate implementation contract](../research/yt-disruption/CONTRACT.md).
This is research, evidence/tooling, documentation and CI only. Go gameplay,
dependencies and save version **25** are unchanged; disruption is not playable.

Retained evidence and validation:

- **61 normally returned DOS controls / 122 full world snapshots**, including
  startup, ordinary movement, scanner accept/refuse, autopilot, manual warp,
  zero/low turns, cloak conservation, initial/reached mine/fighter hazards,
  chained forced warp, a separately attributed mine escape/death, ordinary
  thruster helper-return timing, collision/cancellation and hidden Wanderer
  split destinations. Four exact world/auxiliary reload chains preserve their
  parent's complete outputs without reapplying setup patches.
- Narrow declared-table controls are separate from normal-width 3000-sector
  header controls. Original sensors locate session holes 592/1051 in the latter;
  targeted startup/movement/ordinary-planet/Wanderer controls corroborate the
  recovered arrival rules. No raw field 133 hole flag or patched executable is
  used. Full-header fixtures still have controlled graph/occupancy and are not
  ordinary-world frequency samples.
- One unsupported one-sector, zero-turn diagnostic observed two hole/warp
  reentries before its **40-second timeout**, without a normal return marker.
  It is incomplete and excluded from the 61 returned controls. The native
  unconditional arrival loop explains the observation; finite modern chain
  exhaustion remains an implementation policy to define explicitly.
- **15 complete native byte reads and one reconstructed MZ load image / 870
  relocations** passed independent original-binary checks. Three exploratory
  reads are classified; the mistaken text-as-constant probe contributes no
  numeric claim. No executable changes or archive execution occurred.
- `verify_disruption.py` passed independent MBF/setup, complete world/auxiliary
  conservation, exact parent chains, heat/recharge/turn arithmetic, origin versus
  forced/mine warp distinction, planet links/collision/lazy growth, death marker,
  sensor/receipt/privacy, score/news and raw log/keys/clock/return checks.
  Frozen complete witnesses additionally reject otherwise unmodeled byte changes.
- All **65 rehashed corruption controls** passed: 58 complete-control semantic/
  provenance mutations and seven separately incomplete-diagnostic mutations.
  These cover assets/turns/cloak/hazards/death/planets, setup and chain identity,
  news/score/privacy, raw/transcribed receipts, keys/date/clock/return/completeness,
  frozen declarations, native bytes/relocations/mappings and diagnostic status.
- A fresh disposable `quiet-origin` capture-writer check returned normally.
  Independent setup and semantic/auxiliary checks, original binary identities,
  all retained file hashes, exact raw/rendered logs, keys, DOS clock and return
  marker passed. The reviewed corpus was not regenerated by this smoke check.

All **58 CI evidence/control commands** passed, including all **4,682 archive
hashes**. All three new Python scripts parse, edited relative links resolve and
staged diff checks pass. Git preserves the exact working bytes of all **754 new
research artifacts**, including DOS keys, clocks, return markers and raw logs.

README and the reconstruction plan distinguish research completion from future
bounded session-local disruption gameplay. Exact BRUN30 random state/MBF extreme
boundaries, unrelated disruption combat/spy branches, broad balance and native
Windows/live BBS acceptance remain open. No Go suite, terminal smoke or cross-build
is claimed for these research-only changes.

## Bounded disruption and black-hole arrivals — 2026-10-31

Implemented the [arrival contract](../research/yt-disruption/IMPLEMENTATION.md)
on macOS arm64. Save **25** and repository dependencies are unchanged. Two
independently selected, possibly duplicate interior holes belong to the captured
ship/season login. No location pair, draw state or synthetic map flag is saved.
Startup and reached arrivals force warp before local mines/fighters, including
at zero turns. Origin movement/transport, recharge and reached mine/escape/death
or defense aftermath share one atomic replacement. Ordinary planetary helper-
return timing, independent Wanderer/ship positions and private receipts remain.

Executed validation:

- The full **race-enabled Go suite** and **vet** passed on the final source.
  Validation used the temporary modfile selecting the local supported GoDoors
  checkout; no repository module/dependency change was made.
- Game regressions cover independent interval/duplicate draws, no persisted
  runtime state, stale epochs, nil/invalid draws and clocks, zero/low turns,
  preserved cloak, initial mines/fighters bypassed, reached damage/death and
  hostile gates, 32-step chain exhaustion, sequence capacity, scanner warnings,
  ordinary/Wanderer helper-return positions and adjacent bribe/battle precedence.
  **32 seeded worlds** check bounded work and asset/turn conservation. Mine
  escape can reach a login-local hole and reenter the arrival resolver; its
  intermediate receipt remains distinct from the final ship position.
- Shared heat accounting caches the original two-draw budget. Shrinking/growing
  mixed-draw regressions assert exact mine-escape draw counts, destinations and
  costs; manual and physical-safe escape destination/cloak policies remain
  distinct from forced disruption. Same-position warp sequences invalidate
  travel, mine entry/placement, bribe/defense, attack and missile confirmations.
- Store regressions cover whole-save callback/validation/late-RNG/chain rollback,
  concurrent action serialization, lock-wait expiry, captured epoch/incarnation,
  committed directory-sync warnings, one-time receipts and reconnect without
  replay. A valid fatal mine aftermath advances the generation and commits before
  the obsolete login ends; unexpected replacement/season changes are rejected.
  The fatal-generation regression corrected a failure caught by the real mine
  smoke. A separate startup mine-only regression checks that damage/death is
  reported even when no black-hole warp occurred.
- Both interfaces pass startup/move/autopilot and EOF/closed-pipe/other receipt
  failure regressions. Committed warnings survive output errors and EOF paths;
  interruptions discard queued commands. Aborted calculations print no saved
  success. Receipts show known warp costs/heat, actual final sector and balances;
  hidden pairs and Wanderer destinations are excluded from public output.
- All **50 CI terminal/control commands** passed. The new unseeded compact and
  classic controls use actual sensors to find a current-session hole, test fresh
  acceptance/refusal, mine/fighter bypass, recharge arithmetic, autopilot
  interruption, zero-turn startup and public/private separation. The ten new
  scenarios were repeated against the final build. Existing transport, ground
  actions, NPCs, reports, equipment, Genesis and chained mine-death checks passed.
- Historical terminal fixtures explicitly select quiet login paths. A forced
  warp or disruption scanner warning stops the disposable attempt; after its
  process is stopped, exact pre-login save bytes are restored before a fresh
  login, at most 128 attempts. Ordinary sensor observations are retained, other
  failures propagate, and dedicated disruption controls run unfiltered. All
  **five helper regressions** passed, including stable lock inode and real-error
  propagation. Two older maintenance failures reproduced on the unchanged code
  were isolated from unrelated Wanderer production/random events without
  weakening their original resource/report assertions.
- All **58 evidence/control commands** passed, including the unchanged 61 returned
  DOS disruption controls, four exact reload chains, separately incomplete
  diagnostic, 15 native byte observations, all 65 rehashed corruption controls and
  **4,682 archive hashes**.
- Linux/amd64 and Windows/amd64 cross-builds passed. Changed Python scripts parse;
  edited relative links and diff whitespace checks pass. **148 regenerated
  captures** were restored; all **226 pre-existing evidence files** then matched
  the pre-suite path/hash snapshot before appending these validation notes.

README, implementation/recovery/plan notes, regression/terminal checks and CI
include the milestone. CI now allows 30 minutes for the expanded bounded suite.
Exact BRUN30/MBF fidelity, remaining disruption combat/spy intelligence,
long-running balance, live BBS acceptance and native Windows crash durability
remain unverified/separate. Cross-builds and PTYs do not establish native/live
acceptance.

## PR51 CI time budget and maintenance fixture isolation — 2026-10-31

The current-head CI job 124596023177 on 3fa74b9258c9bc7889541e81f75e034045401791
was cancelled after reaching its configured 15-minute limit. GitHub's annotation
explicitly reports maximum execution time, rather than a failed game assertion.
Formatting, race tests/vet and preserved evidence checks succeeded. The terminal
step continued passing through human-defense desertion before cancellation;
Linux/Windows cross-builds had not yet run. Evidence alone took 7m17s, leaving
insufficient room for the complete 48-command terminal/control sequence.

The job now permits 30 minutes. Its name, required commands, action pins, race
flags, evidence verifiers, terminal checks and cross-builds are otherwise exactly
unchanged; no check is skipped or bypassed. README documents the budget.

Two independently reproduced Wanderer-related intermittent fixtures are isolated
without weakening their existing assertions: the tax/recruitment test freezes
unrelated production for every planet, including The Wanderer; the revenge
consumption/concurrency/durability test supplies deterministic maintenance draws.
Their unchanged-head versions reproduced extra route pickups or intercepted
revenge battles, respectively. Each fixed test passed 25 race-enabled repetitions.
The full `go test -race -count=1 ./...` suite and `go vet ./...` passed locally
using the temporary validation modfile for the supported local GoDoors checkout.
Go formatting, edited links and diff checks passed. Production Go code, save 25,
dependencies, and retained DOS/terminal evidence are unchanged. GitHub must still
complete the full check sequence on the new pushed head before merge readiness.

## Plasma launch, routing and disruption research (2026-10-31)

Research only; no Go gameplay or save change. The retained corpus has 62 normally
returned DOS controls, 124 complete world snapshots, two exact world/auxiliary
reload chains, 13 complete native byte reads and an independently reconstructed
MZ image with all 870 relocations. Native decision/impact coverage ends at the
plasma return opcode; its final two operand bytes are outside this fresh read
set. Existing historical listings are not presented as additional runtime runs.

The independent verifier checks original binary/base identities, exact controlled
setup, clocks/keys/return markers, complete raw CP437 and auxiliary witnesses,
launch resources, route/energy and indiscriminate damage receipts, deaths/wrecks,
planet projection/destruction and full saved-world mutation footprints. All
53 corruption controls pass: 47 rehashed DOS semantic/provenance changes and six
native/declaration changes. Matched non-firing projection controls prevent raw
warehouse-derived production from being mistaken for unconditional plasma damage.
Numeric score checks allow bounded original MBF rounding; exact retained bytes
are additionally pinned. Fresh clocks are not required to reproduce casualty
counts or an unrecovered random sequence.

All 60 current CI evidence/control commands passed locally, including the new
plasma verifier/corruptions, existing milestone verifiers and all 4682 immutable
archive hashes. A separate fresh quiet-origin capture-writer control returned
normally from a disposable copied DOS world. Final capture declarations match all
62 retained controls; research document links and diff whitespace checks pass.
CI adds the two new portable plasma checks without removing existing checks.

Go sources, dependencies and schema25 are unchanged; the full Go race/vet suite,
terminal smokes and cross-builds were not rerun for these research-only edits.
Plasma firing remains unimplemented. The candidate contract separates original
rules from finite-budget, atomic-save, self/friendly death and privacy policies.
Live BBS acceptance and native Windows crash durability remain unverified. See
[recovery and reproduction](../research/yt-plasma/RECOVERY.md) and
[the proposed implementation](../research/yt-plasma/CONTRACT.md).

## Bounded plasma launching and atomic aftermath (2026-10-31)

Plasma is now available in both interfaces as `PLASMA`/`+`, separately from the
historical research-only stage above. The launch uses fresh single-use consent,
one shared bounded energy pool, directed/hole-rebuilt courses and indiscriminate
physical damage. Costs, death/estate/salvage, wreck mines, local arrival, planet
cleanup and qualifying HQ reward/revenge/news commit together. Schema26 adds
explicit plasma death semantics; supported older saves migrate without assets.

Validation on macOS arm64 with Go1.27.3 and the local GoDoors dependency override:

- Full final `go test -race -count=1 ./...` and `go vet ./...` pass. Repository
  module/checksum files and the GoDoors checkout are unchanged.
- Focused rules/storage/interface checks cover 32 seeded conservation worlds,
  zero/invalid RNG and work limits, stored-exit ties/range, friendly/self/cloaked
  hits, resource/energy sharing, stock-derived production, retirement and landing
  revocation, actual HQ owner/headroom, self/friendly/posthumous attribution,
  surviving/fatal local wreck-mine chains and remaining-layer conservation.
- Store coverage includes byte-identical rollback after death/loot/late hazards
  and HQ publication, capacity failures, competing logins, altered/replayed/cancelled
  consent, real Genesis reset with reused IDs, world/cache lock expiry, expiry
  during a random draw, read-only version25 migration and committed durability.
- Both interfaces cover exact fresh confirmation, strict integer input, EOF,
  concealed-state changes, self-death login termination/replacement timing and
  preservation of committed storage warnings through receipt-output failures.
- All **51 current CI terminal/control commands** pass locally. The new real
  GoDoors smoke retains **ten compact/classic scenarios**, with accepted/cancelled/
  stale launches, hidden physical hits, self death, mixed wreck/planet impacts and
  surviving reconnects without replay. Its current transcript is
  [plasma-smoke.txt](plasma-smoke.txt).
- The broader terminal run reproduced an old public-newspaper test hang when a
  legitimate random award added a page. Public-history viewer checks now opt into
  bounded automatic page answers and a fresh quit. A deterministic six-event
  fixture exercises that path; explicit pager-choice tests retain their default
  behavior. No production newspaper or random-award rule was changed. Older
  smoke assertions now expect current schema26 while historical input versions
  remain intact.
- All **60 current CI evidence/control commands** pass, including the 62-control
  plasma corpus, its 53 corruption controls and every one of the **4682 original
  archive hashes**. No new original-DOS runtime or RNG parity is claimed by the
  implementation tests.
- Linux/amd64 and Windows/amd64 final cross-builds pass. This is build evidence;
  native Windows file/socket/crash durability and live BBS play remain untested.

Before the broad run, all 226 existing evidence files were backed up; 148
regenerated historical captures were restored byte-for-byte. Only this validation
note intentionally changes among those files; the new plasma transcript is
retained separately. README, reconstruction plan, implementation policies and CI
are updated in the same implementation commit. Concrete limits, financial policy,
privacy and unsupported follow-ups are in
[IMPLEMENTATION.md](../research/yt-plasma/IMPLEMENTATION.md).

## Mercenary plasma acquisition research — 2026-10-31

Research-only update on feat/mercenary-plasma-sales-research, based on the
published bounded plasma feature and its propagated disruption review fix.
No Go gameplay, dependencies or save26 fields changed.

- Retained 17 normally returned original DOS 3.6 controls, 34 complete world
  snapshots and two exact saved-world/auxiliary reload chains. Fourteen complete
  exact-declaration controls reused verified baseline/file hashes; corrected
  deposit and both reloads were freshly executed. The incomplete deposit pilot
  that entered quit confirmation is excluded from the canonical corpus.
- A separate fresh quiet capture completed normally through the committed
  writer recipe in a new disposable directory. Child captures refuse incomplete
  parents. Archived executables/worlds were copied before execution.
- Independent acquisition verifier passed all 17 controls, exact setup/raw-log/
  menu/stock/credit/turn witnesses and both reload chains. Reload assertions allow
  observed fractional planetary production and bank growth without replaying the
  transfer.
- Twelve retained native byte reads and one reconstructed MZ load image match
  the original YT.EXE after all 870 relocations. Static interpretations and bounded
  search coverage are documented separately from runtime observations.
- All 38 acquisition corruption controls passed (30 rehashed DOS semantic and
  provenance cases, six native/declaration cases and two altered archived-document
  cases). Related plasma verification passed all 62 controls, two reload chains
  and all 53 corruption controls. All 4,682 immutable archive hashes verified.
- README, plan, prior plasma backlog notes and CI evidence commands were updated.
  Syntax, relative documentation links and diff checks passed.

Commands: scripts/verify_mercenary_plasma.py,
scripts/test_mercenary_plasma_verifier.py, scripts/verify_plasma.py,
scripts/test_plasma_verifier.py and scripts/verify_archive.py, each run with
Python 3. No full Go, terminal smoke or cross-build suite was rerun for this
research-only update; the original DOS capture is not Go/live BBS acceptance.
Native Windows durability and complete DOS RNG/MBF parity remain separate.

The versioned sources establish Mother Ship sales introduced in 3.3 at
5,000,000 credits per bolt and explicitly removed in 3.4; the 3.6 Mercenary
home planet is distinct. Current Earth and planet acquisition controls
corroborate that removal within the inspected paths. Historical 3.3 seller
eligibility, caps, hostility and write order remain unproved. No new merchant
implementation is pending for DOS 3.6 parity.

## Ship, cloak and disruption spy intelligence

- Six fresh completed original-DOS controls and the independent verifier establish
  ship name/team/fighter/shield reports, full-cloak suppression, one positive
  partial-cloak shimmering branch, ordered multiple ships, caller exclusion and
  a login-local disruption notice. All retain 1,667,000 credits, 497 turns and
  unchanged saved cloak. Fourteen corruption controls reject altered provenance,
  keys, snapshots, cloak state, ship details and report types, including shield-only
  changes with refreshed transcript hashes.
- Full `go test -race ./...` and `go vet ./...` passed. A targeted race run covers
  the final additional shared-detection, ship-order and private-disruption tests.
- Real compact and classic GoDoors PTY spy smoke passed with actual ship details,
  history, resource charges, unchanged cloak and reconnect isolation; the updated
  transcript is `evidence/spies-smoke.txt`.
- The original seven spy sessions/REA-byte verifier and all 4,682 archive hashes
  passed. No original random-stream or exact probability claim is made.

World version remains 26. Native BBS acceptance, target notifications, shared
combat visibility, broader triggers and exact DOS RNG/numeric parity remain
outside this slice. See [policies and evidence](../research/yt-spies/intelligence/IMPLEMENTATION.md).


### Mercenary-route fixture isolation

PR #56 CI exposed a route-smoke assumption: an existing Wanderer can relocate
into sector 8 before Mercenary actions and legitimately hold the test group.
The disposable fixture now starts without The Wanderer, allowing normal
restoration after route actions. Mine and pickup assertions remain unchanged;
no gameplay RNG or production code is altered. Three fresh route smokes and
the dedicated compact/classic Wanderer smoke passed locally.

## Team radio

- Nine completed DOS 3.6 sessions establish private roster fanout including the
  sender, independent unread flags, abort/no-team rejection and recipient-at-send
  delivery after membership changes. The independent verifier checks exact
  world/auxiliary chains, binaries, keys, packet contents and conserved resources.
  Eighteen corruption controls passed, including root-baseline/login-identity checks,
  fractional routing/read flags and
  scanner removal with refreshed hashes. Existing commerce/direct-radio and fourteen
  team-membership evidence controls also passed; all 4,682 archive hashes matched.
- Full `go test -race ./...` and `go vet ./...` passed. Final recipient-preview and
  committed-durability-warning changes passed targeted race-enabled radio tests.
- Real compact/classic GoDoors PTY checks passed for actual team creation/join,
  private copies, abort, sender/recipient delivery, leaving and late joining.
  The new transcript is `evidence/team-radio-smoke.txt`. The existing direct-radio
  smoke passed separately; its incidental regenerated capture was restored.
- Linux/amd64 and Windows/amd64 cross-builds passed. These are build checks, not
  native platform socket/crash acceptance.

World format remains 26; team radio reuses ordinary private mailbox records.
Native BBS acceptance, broadcast and DOS multiline editing remain open.
[Evidence and policies](../research/yt-team-radio/IMPLEMENTATION.md).

The combined spy/team state after verified PR #57 integration passed the full
race-enabled Go suite and vet, plus spy, team-radio and isolated Mercenary-route
PTY checks. Spy evidence and all fourteen corruption controls passed again.
Incidental regenerated terminal captures were restored.

### PR #59 reload-clock review correction

Confirmed both retained reloads declare 00:00:00 and record 0:00:00.00am in
DOSTIME.LOG and the DOSBox command stream. Corrected the report's erroneous
00:01:00 description and stated that exact saved-state chains do not establish
one minute of elapsed time. Capture bytes and gameplay are unchanged. README
was updated in the same fix; current-main spy-intelligence changes and their
validation history are preserved.

## Broadcast public-record and shared-lifetime research — 2026-11-01

Research-only on feat/broadcast-radio-research, based on PR #59's reviewed
e83d231 tree. No Go gameplay, dependencies or save26 fields changed. This is
separate from PR #58's private-copy adaptation and preserves its six-control
corpus rather than overwriting or recounting it.

- Sixteen fresh normally returned DOS controls retain 32 full before/after
  worlds, raw CP437/rendered logs, explicit DOS clocks, return markers and all
  mutable auxiliary bytes. Four unpatched parent edges preserve exact world
  and auxiliary state; four other children declare only mailbox-budget edits.
- Every capture explicitly resets DOS date/time to 10/24/2026 00:00:00. No
  elapsed-minute or monotonic-clock inference is made. A fresh send and a fresh
  abort capture-writer check returned normally outside the canonical corpus.
- Independent verifier passed packet structure, negative broadcast destination,
  integer budget 30→28→26, repeat-reader and nonmutating-history behavior,
  budget 2/1/0/-1 visibility, resource conservation and public newspaper header/
  body publication. The two-line control binds one packet per line and one
  newspaper sender header. Aborts do not create publication.
- Nine YT byte reads and two maintenance byte reads plus their two complete
  MZ load-image observations independently match original bytes after all 870
  YT and 108 maintenance relocations. Both REA sessions were closed.
- All 43 corruption controls passed: 34 rehashed DOS semantic/provenance cases,
  including public-news header/body deletion and fractional fields, and nine
  native/declaration cases. Existing nine-session team-radio evidence and its
  corruption tests passed. All 4,682 immutable archive hashes matched.
- Three new Python scripts parse, relative documentation links resolve, and
  diff checks pass. README, plan, exact DOS evidence attributes and CI evidence
  commands are updated in the same research commit.

Executed: scripts/verify_broadcast_lifetime.py,
scripts/test_broadcast_lifetime_verifier.py, scripts/verify_team_radio.py,
scripts/test_team_radio_verifier.py and scripts/verify_archive.py, with Python 3.
No full Go race/vet, Go PTY or cross-build suite was rerun for this research-only
slice. Original DOS controls are not native BBS or Windows durability acceptance.

Maintenance pruning is static-only evidence; no maintenance process was run
against these captures. Its 72/74-byte text declaration mismatch, exhausted
author-history eligibility, new/dead account runtime cases, concurrent original
writers and the complete multiline editor remain explicit limits. The public
newspaper result was checked directly against canonical saved YTNEWS.DAT bytes.

## Bounded broadcast radio

- Six completed original-DOS controls verify send/abort and exact chained
  recipient/sender reads, including the shared mailbox leading field changing
  30 → 28 → 26 and repeat-reader delivery. Nineteen corruption controls reject
  rehashed root-mailbox, wrong-actor, field, scanner, counter, clock, chain, header and startup changes.
  The Go private-copy policy is explicitly distinct from that DOS shared record.
- Full `go test -race ./...` and `go vet ./...` passed. Tests cover 50-account
  fanout, dead/retired eligibility, future-account isolation, stale confirmation,
  independent reads, expiry, capacity/overflow, partial publication, concurrent
  retry and committed directory-sync warnings. Team radio exercises the same
  shared private-copy commit helper.
- Compact/classic GoDoors PTY broadcast checks passed, with explicit ALL count
  confirmation, literal text, abort, offline delivery, separate acknowledgements,
  no repeated notification and late-account isolation. The new transcript is
  `evidence/broadcast-radio-smoke.txt`. Existing team and direct PTY checks passed
  separately; their incidental regenerated captures were restored.
- Team-radio evidence and all eighteen team corruption controls passed, and all
  4,682 archive hashes matched. Linux/amd64 and Windows/amd64 cross-builds passed;
  these do not establish native BBS transport or crash durability.

This historical private-copy milestone used version 26. Current public ALL
publication uses version 27; older binaries cannot read those saves. See
[broadcast publication validation](BROADCAST_NEWSPAPER_VALIDATION.md).
DOS shared-counter lifetime, simultaneous original
writers, multiline editing and native BBS acceptance remain separate work.
[Evidence and policies](../research/yt-broadcast-radio/IMPLEMENTATION.md).

## Multiline radio editor

See [implementation and native controls](../research/yt-radio-editor/IMPLEMENTATION.md)
and [compact/classic PTY transcript](radio-editor-smoke.txt). Six native controls
and sixteen semantic corruption controls accompany atomic game/store and door
confirmation tests. Character-level DOS wrapping and live BBS acceptance remain
separate.

Local validation passed: full Go race tests and vet, focused editor tests, six
DOS controls, sixteen rehashed corruption controls, all 4,682 immutable archive
files, and Linux/Windows amd64 cross-builds. These are local checks; hosted CI
has not run for this branch.

Existing direct, team and broadcast PTY regression checks also passed.

Editor verifier review fix: a seventeenth rehashed corruption reproduces an
Abort newspaper leak with no delivered mailbox records; the verifier now rejects
both aborted input lines independently of the expected delivered lines.

CI fixture correction: reproduced captured-home return with only one HQ fighter
when the unrelated Wanderer occupied the emptied HQ. The fixture now removes
the Wanderer and exhausts planet-generation capacity so its separate restoration
is deferred. All exact assault, return, privacy and replay assertions remain.


## Spy triggers and target notifications — original-DOS research

The [recovery report](../research/yt-spies/triggers/RECOVERY.md) retains 36
normally returned DOS controls, 72 full world snapshots, three exact target
world/auxiliary reload chains, raw/normalized logs, keys and DOS clock/return
markers. Initial fixture/looting pilots informed clean controls and are not used
to claim empty-sector traversal or spy-only resource conservation.

Twenty complete REA byte observations, all 870 reconstructed MZ relocations and
a bounded complete main-code search anchor four direct trigger encodings. The
independent verifier checks actual branch execution, ordered spy/ship details,
actor/alias identity, declared world patches, unchanged private target cloak,
normal bookkeeping and weapon-specific effects. Ordinary plasma-hit news is
separate from a spy warning. All 42 rehashed semantic/provenance/native corruption
controls pass, and a positive changed elapsed-display control passes without
relying on a full-output golden hash.

Run `python3 scripts/verify_spy_triggers.py` and
`python3 scripts/test_spy_triggers_verifier.py`. Fresh copied captures can be
checked through `--dos <capture-directory>` without replacing the retained native
dossier. All 4,682 original archive hashes are independently verified. All 74 portable CI evidence/control commands pass for this milestone, including
new spy checks and the existing radio/editor/evidence regressions.

No Go, saved schema27, dependency, archive or live BBS change is included. Full
Go/PTY/cross-build suites are not rerun for this research-only update; their
previous results remain historical. Exact RNG/ties, broader indirect dispatch,
simultaneous DOS processes and native/live acceptance remain explicit limits.

## Public planet-creation news (save28)

The [implementation validation](PLANET_CREATION_NEWS_VALIDATION.md) records atomic
creation/publication, negative and stale-session coverage, no-backfill migration,
compact/classic evidence and completed local checks. Private seller notices and
live BBS acceptance remain separate. Earlier save27 milestone descriptions are
historical compatibility records.

## Private former-owner port-sale notices (save29)

The [implementation validation](PORT_SALE_NOTICES_VALIDATION.md) records atomic
buyout/settlement/notification, private snapshots and read/history behavior,
strict payload/no-backfill migration, quote replay protection and completed local
checks. Earlier private-seller deferrals and format28 statements above are
historical milestones. Live BBS and native Windows durability remain separate.

## Multi-caller simulated BBS victory campaign

[Campaign findings and retained captures](MULTICALLER_DOOR_CAMPAIGN.md) cover six
concurrent Door32 callers, legitimate configured Genesis victory, private scopes,
contention, carrier loss, real expiry and old/new epoch overlap with reused IDs.
A reproduced input-deadline defect is fixed and regression tested. This is a
POSIX stdio/TCP simulation, not production BBS or native Windows acceptance.


## Opt-in DOS port generation and pricing — 2026-11-02

Save 33 adds an initialization-only `-dos-ports` profile. Existing saves retain
all ports and fixed reference prices on upgrade. Genesis and administrative
reset retain the profile; private archives include it. The implementation uses
the recovered naming/economy rules with a modern Go random stream, reachable
graph and unique finite placement, not exact seed-to-DOS-world parity.

Validation includes race-enabled tests across all Go packages and `go vet`;
focused generation/name/economy/price/report/migration/reset tests; CLI creation,
archive, reset and admission checks; compact/classic terminal quotes; and existing
Genesis compact/classic terminal acceptance. Independent verifiers check three
fresh DOS pre/post-maintenance worlds, seven startup pricing controls, declared
binary/fixture identity and exact native byte reads. Nineteen verifier tests
include rehashed semantic corruption, missing return evidence, changed inputs,
broken reload chains and missing/empty/truncated native observations. The archive
verifier confirms all 4682 archived files remain intact. CI includes the new checks.

See [rules, evidence and boundaries](../research/yt-port-generation/RECOVERY.md).
Full QB RNG/MBF arithmetic, original graph generation, `.DAT` interchange and
production BBS economy acceptance remain unverified work.


## Opt-in DOS warp generation — 2026-11-02

Save 34 adds the independent `-dos-warps` initialization profile. Existing worlds
retain their saved maps; save33 port settings/economies are preserved. Genesis
and administrative resets retain both profile choices; archive exports include
the full map and settings. README and sysop upgrade/rollback guidance are updated.

Local validation passed: all Go packages under race detection; vet; focused warp
rule, deterministic generation, connectivity, native-table replay, fractional
shortcut, migration, profile/reset and stale-quote tests; new CLI/PTY checks in
compact/classic interfaces; existing port-profile and season-administration CLI
acceptance. Nine phase/native verifier tests and eleven rounding tests pass,
including rehashed phase/graph/golden/patch/calendar/normal-return corruptions
and missing, empty, truncated or false native observations. Four phase captures
and five one-write rounding controls returned normally under DOSBox, using
explicit disposable executable patches and an exit-only maintenance child.

[Rules, provenance and reproduction](../research/yt-warp-generation/RECOVERY.md).
The modern RNG, finite retries, small-world handling, duplicate rejection and
Earth self-warp removal are explicit differences. Exact QB seed sequence and full
MBF boundary arithmetic remain open. CI includes new verifiers and terminal checks;
new-head hosted results, native Windows and production BBS acceptance are separate.

## Raw QuickBASIC RNG seeding and selected graph replay — 2026-11-03

The shared `internal/qbrng` primitive implements the verified 24-bit argumentless
RND recurrence and RANDOMIZE transformation from actual four-byte MBF inputs.
The initializer path is `RANDOMIZE -TIMER`; midnight's noncanonical zero residue
is retained as seed input rather than reconstructed from a numeric zero.
Startup-price construction now uses the shared primitive with identical results.
There is no schema change beyond 34 and no switch of active generation streams.

Validation passed locally: all Go packages under race detection, vet, existing
price/port regression tests and compact/classic port-profile CLI/PTY acceptance.
Portable Go fixtures check all 4096 native state/FAC pairs from 16 copied-executable
controls, including low-byte preservation, canonical/residual zero, and exact
RND 0/max output boundaries. Six original-initializer clock controls retain raw
start/end time/date and prove only bounded correlations, not exact clock strings.
Thirteen native byte contracts are checked against original relocated MZ images.

A research model obtains its seed from verified traces and exactly reproduces
all 18000 warp cells in four retained graph-phase/clock controls. Ordered native
repair logs and final states/draw counts are also checked. The negative controls
explicitly preserve the zero/one-prefix resynchronization limit, reject wrong
seeds/prefix 2 and rehashed changed traces/worlds, and do not pretend graph equality
alone proves the HQ draw count. There are 24 Python test methods across clock,
trace, native and replay verification. All 4682 archive files remain unchanged.

[Recovery, executable patch contracts, provenance and remaining boundaries](../research/yt-rng-seeding/RECOVERY.md).
Full port random consumption, other RND argument variants, complete MBF arithmetic,
a general production compatibility profile and native BBS acceptance remain open.
Hosted CI includes these checks; local results do not claim hosted green status.


## Exact port stream replay — 2026-11-03

The research model matches six retained DOS clock worlds: 108,000 graph cells,
822,000 raw port-record bytes and 18,000 sector links. Twelve fresh native state
hooks at four clocks match graph/placement/port endpoints and preserve every
complete unhooked world byte. The +2-second raw seed is checked independently.
The target, seed, state and replay suites pass 22 test methods, including
rehashed corruptions and numeric-zero residue that selected-field checks miss.
The original sector-7 overwrite remains an explicit research control.

[Report and limits](../research/yt-port-replay/RECOVERY.md). No production Go
behavior or schema changes; full initializer records, general MBF arithmetic,
DOS import/export and a production compatibility profile remain separate.
Hosted CI runs these checks; local verification does not imply hosted success.


## Complete pre-maintenance initializer replay — 2026-11-03

All ten retained worlds reproduce all 4,151 records and 568,687 bytes each
(5,686,870 total), including configuration, inactive players, complete sectors,
ports and inherited inactive planet records. Four fresh controls cover default
repeat, alternate scoreboard path, January 1 and leap day, each bound to its own
raw seed trace and complete output hash. Native checks pin 23 original-byte
contracts; they are archived/static evidence, not new REA provider observations.

The four new suites pass 25 test methods. Corruption controls reject rehashed
world, native-range, seed, clock, recipe, auxiliary and raw-zero changes; replay
tests forbid target-template reads and implicit report rewriting. Existing port
and graph regressions and all 4,682 archive hashes also pass.

[Recovery and exact boundaries](../research/yt-initializer-replay/RECOVERY.md).
No production Go, dependency, initialization profile or save-format-34 change.
Initial maintenance, general MBF, DOS interoperability and target-host acceptance
remain separate. Hosted CI is configured to run these checks; local results do
not claim a hosted CI run for this milestone.


## Pure Go initializer source generator — 2026-11-03

`internal/qbinit` matches the complete-world and five record-block hashes of all
ten native initializer controls (5,686,870 bytes), along with RNG stage/final
states, draw counts and placement rejection counts. It preserves source defects
and raw FIELD/FAC residues, with a bounded one-million-draw maximum. Tests cover
empty-result budget failures in multiple phases, an exact successful budget,
original sector-7 overwrite, January/raw-zero inheritance, invalid inputs and
independent result ownership/concurrent generation.

The compact fixture is verified against observed DOS outputs, raw seed/phase
evidence, complete replay reports and original weighted DATA. Two Python fixture
tests reject altered fingerprints, seed provenance, counters and coverage.
Full race-enabled Go tests and vet pass; a separate minimal Go module containing
only qbinit/qbrng and their fixtures also passes race-enabled tests without the
research tree, Python, original executables, emulator or GoDoors dependency.

[Implementation and limits](../research/yt-initializer-replay/GO_IMPLEMENTATION.md).
No production profile/CLI, modern save projection or schema change. Save 34,
existing maps and ports, reset/export/restore behavior and game streams remain
unchanged. Hosted CI includes fixture provenance/corruption checks; local results
do not claim a hosted run for this commit.


## Release packaging and sysop cheat sheet — 2026-11-03

The release builder creates standalone Linux amd64/arm64 tarballs and Windows
amd64 ZIPs, with a binary hash manifest, archive SHA-256 list, bundled operations
guides, credits and available third-party license texts. All three targets were
cross-built against the same pinned GoDoors revision as CI. Archive checks verify
complete matrix coverage, checksums, executable format/architecture, Linux file
mode, safe single-root paths, required guides and absence of saves/source extras.
Three packaging tests cover deterministic packaging, contents/modes, unsafe names
and official/Homebrew Go license layouts. CLI setup/overwrite-refusal/maintenance/
export/guarded-reset checks pass on the native development host; packaged Linux amd64 execution
is included in Linux CI. Windows and Linux ARM64 builds are format-checked, not
claimed as native transport/host acceptance.

PR CI builds/verifies packages without creating a Release. Version-tag builds run
Go race tests/vet and packaging validation, then attach all assets/checksums to a
draft GitHub Release. Draft reruns may replace assets; published releases are not
overwritten. No tag, published release, save schema or gameplay change is made
by implementing this tooling. See [release procedures](../docs/RELEASING.md) and
the [sysop cheat sheet](../docs/SYSOP_CHEAT_SHEET.md).


## Internal safe QB projection/admission — 2026-11-03

The internal candidate pipeline admits three distinct native source states and
validates current UTC clocks/stocks, ordered Earth exits, exact baseline Earth
economy, source HQ force and all required modern faction homes. Source bytes,
fingerprint and RNG statistics remain independent of modern bootstrap randomness.
The retained port-overwrite control, generated protected HQ and source-work
exhaustion return no partial candidate. Fourteen malformed-source variants plus
zero-clock and one-way-connectivity controls are rejected without input mutation.
Repeatable candidates and independent mutable storage are checked.

Five focused Go test groups pass under the race detector; full race-enabled Go
tests and vet pass alongside retained native fixture provenance checks.
[Projection behavior and boundaries](../research/yt-initializer-replay/PROJECTION.md).
The pipeline remains unexported and unused by active CLI/store constructors.
Typed saved recipe, schema/CLI selection and complete guarded reset integration
are prerequisites to enabling the playable profile; save format stays 34.

## Playable QB profile integration — 2026-11-03

Save 35 adds the opt-in `qb36-v1` profile using the previously verified pure Go
source generator and safe projection. Typed recipes retain versioned profile,
explicit raw 24-bit state/source date and complete source SHA-256. Loader validation
checks syntax/geometry/rule consistency without regenerating an evolved world.
Old worlds upgrade with no recipe or reroll; pre-35 recipe fields are rejected.

Validation performed:

- Full `go test -race -count=1 ./...` and `go vet ./...` passed.
- Focused QB tests cover recipe round trips, invalid/missing/unknown inputs,
  unchanged old-world geometry/economy, both repeat-layout resets, copied recipes,
  stale Genesis confirmations and source-fingerprint mismatch rejection.
- Store tests exercise both resets with success, pre-replacement failure,
  provenance change and injected post-replacement directory-sync failure.
  Committed warnings retain receipts/history/recipe, invalidate old sessions and
  reject reset replay. Private archive checksums and stopped-node restoration
  preserve recipes and evolved world data.
- `scripts/smoke_qb_profile.py` passed headless admission/conflict/collision controls,
  actual compact PTY navigation and a commodity purchase, classic port display,
  CLI admin reset, repeated source layout, archive extraction/restore and stale
  season rejection. CI now invokes this smoke check.
- Linux amd64 and Windows amd64 cross-builds passed. These are build checks,
  not native Windows runtime acceptance.
- Existing season-admin, DOS port and DOS warp CLI/PTY smoke checks passed.
  Active smoke assertions expect schema 35; historical migration inputs stay intact.
- Portable native fixture provenance and release-package unit checks remain part
  of validation; source goldens are unchanged by playable integration.

These local checks use the existing local GoDoors review modfile. They do not
establish native Windows socket/durability behavior, live BBS acceptance, exact
DOS maintenance, arbitrary MBF arithmetic or DOS save interoperability. Published
v0.1.0 packages predate this source-build feature; no new release was published.


## Full QB world acceptance — 2026-11-03

The [full campaign report](QB_FULL_WORLD_CAMPAIGN.md) and retained
[summary](qb-full-world/summary.json) establish a bounded production session/store
acceptance run on `qb36-v1`: 3,000 sectors, 1,000 ports, normal starting assets,
111 trade cycles and 300 separately confirmed purchases. The default Genesis
threshold was not overridden. Three simulated UTC maintenance transitions
advanced every port economy, NPC defenses and Wanderer state; same-date retries
were exact no-ops. The captain parked at Earth between dates, replanned changed
trade classes and used one confirmed non-HQ battle to reopen an NPC-blocked
frontier, purchasing fighters with earned credits.

The run passed the 299-port denial, fresh 300-port confirmation, recipe/source-map/
source-economy/HQ reset, current injected-date watermarks, reconnect preservation
and stale-login write rejection after player-ID reuse. Its 1,147 sessions and
3,510 input lines use the real Session handlers with scripted line input and a
controlled game clock; this is distinct from real TCP/PTY transport and native
Windows/BBS acceptance. Known disruption locations are avoided deliberately.
No production gameplay, save schema or CLI behavior changed in this milestone.

Validation passed: the complete sequential campaign (269.77 seconds), current
race-enabled door suite, vet, three planner regressions, independent artifact
verification and six Python verification tests with 22 corruption controls.
Local tests used Go 1.27.3 and the existing GoDoors review modfile. CI adds a
separate full-world job with the pinned minimum GoDoors checkout, normal long
campaign plus race-enabled planner checks and retained diagnostic artifacts.

## January 10 source-date admission — 2026-11-04

[Ten fresh original controls](../research/yt-initializer-replay/JANUARY10.md)
cover January 9/10/11 across 2026–2028 and an independent January 10 repeat.
Copied original initializer/runtime binaries ran in disposable DOSBox directories
with the declared maintenance exit stub. Independent raw-seed probes retained
TIMER residue `00004800` and post-RANDOMIZE state `c805`. All auxiliary, clock,
normal-return and complete-world identities pass independent verification.

January 10 port dates are numeric zero with class-specific bytes: class 1
`06004000`, class 2 `05002000`, class 3 `04000000`. Preserving the preceding
`7-class` index/FAC residue reproduces all observed records. January 9 and 11
remain canonical -1/+1 controls. Go and Python match all twenty retained complete
worlds (11,373,740 bytes), and all ten previous golden cases remain unchanged.
Three added original-byte contracts extend native coverage from 23 to 26 ranges.

Validation passed: full race-enabled Go suite and vet; focused January 10
creation/save/load/Genesis/admin-reset regressions for each admitted year; QB
CLI/PTY smoke including January 10 creation with the pinned native fingerprint;
complete replay checks; portable golden provenance/corruption tests; native byte
contract tests; historical target/control tests; and new January evidence
corruption tests. CI verifies the new controls without needing an emulator.
Local Go checks used the existing GoDoors review modfile.

This extends `qb36-v1` date admission without changing schema 35, old worlds or
previously admitted hashes. Older save-35 builds reject January 10 recipes;
upgrade every node before using them. The evidence remains bounded to selected
dates/classes/seed controls. No general MBF engine, DOS maintenance parity or
DOS save conversion is claimed. The REA Ghidra provider still lacked its configured
JDK; no new successful REA decompilation is attributed to these observations.

## Original initial-maintenance transition — 2026-11-04

Research-only `codex/dos-initial-maintenance`: eight copied-original DOS controls
retain integrated initializer/real-child launches, split before/after snapshots,
repeat/date/clock variations and complete auxiliary outputs. The baseline,
repeat and New Year controls use original binary hashes; split initialization
explicitly uses the declared exit stub before launching original maintenance.
No game code, save format or source fingerprints changed.

- `python3 scripts/verify_initial_maintenance.py`: eight controls passed,
  including fixed raw world/auxiliary hashes, phase boundaries, clocks, complete
  returns, unchanged map/names and bounded placement/economy relationships.
- `python3 scripts/test_verify_initial_maintenance.py`: four methods and 12
  corruption/missing/identity rejection controls passed.
- `python3 scripts/verify_archive.py`: all 4,682 original archive hashes passed.
- Scoped whitespace check passed. Nine unrelated pre-existing smoke captures
  remain untouched; the global whitespace check reports existing trailing space
  in `evidence/missiles-smoke.txt`, outside this milestone.

[Native findings, exact scope and reproduction](../research/yt-maint/INITIAL_MAINTENANCE.md).
Maintenance RNG state/draw tracing and bit-exact Go post-maintenance replay are
not established by these captures. No live BBS/native Windows acceptance claimed.


### PR #85 launch provenance review fix

The verifier now independently parses both phase launch logs and requires the
recorded command sequence/options, isolated control mount, DOSBox 0.83.0,
headless video/sound settings and exactly one applied fixed-200,000 CPU setting.
Mutable manifest hashes alone cannot authenticate these claims. Eight added
rehashed-log controls cover empty logs, contradictory requested/applied cycles
and a missing configuration-isolation flag in both phases. All eight native
controls and four test methods/20 rejection controls pass. Original native
observations and hashes are unchanged; README and research instructions updated.

## Initial-maintenance RNG first-hit boundaries — 2026-11-04

Research on `feat/maintenance-rng-research`, based on published initial-handoff
research PR #85. No Go source, `qb36-v1`, schema-35, dependency or original archive
changes. The capture writer changes only same-size disposable executable copies;
its terminating probes are not normal-maintenance completion claims.

- `python3 scripts/verify_maintenance_rng.py`: 151 probes passed (108 selected
  hits, nine baseline inventory hits, 34 guarded misses), two exact native reads
  and six freshly paired untouched completed runs.
- `python3 scripts/test_verify_maintenance_rng.py`: 35 corruption tests passed.
  Rehashed altered states/FACs/worlds, missing/forged hit/return witnesses,
  phase/site/source/executable substitution, contradictory launch clocks/options,
  rewritten pins, native truncation/address/bytes and independent seed/draw
  semantics are rejected. Untouched-oracle completion/input forgery is rejected.
- `python3 scripts/verify_initial_maintenance.py` and
  `python3 scripts/test_verify_initial_maintenance.py`: all eight earlier native
  controls and four test methods/20 rejection controls passed unchanged.
- `python3 scripts/verify_rng_native.py`: 13 existing native RNG contracts passed.
  `python3 scripts/verify_rng_trace.py`: all 16 raw traces/4,096 state-FAC pairs
  passed unchanged.
- `python3 scripts/verify_archive.py`: all 4,682 archived hashes passed.
- Script compilation and a fresh NASM assembly of the retained probe source
  matched the exact capture patch bytes. Scoped whitespace checks passed.
- CI now runs the new portable verifier and corruption suite. DOSBox, NASM,
  Ghidra and Java are capture/research tools, not CI or gameplay dependencies.

The measured main/helper reseeds and selected first Wanderer draw chain close
only that precision slice. All 34 guarded-miss worlds match the new untouched
baseline exactly; the new untouched repeat matches too. Their 97-byte difference
from the older launch recipe is retained and documented, with no automatic
expected-hash refresh. Exact full dynamic draw counts/rejection chronology,
post-maintenance/auxiliary replay, general MBF arithmetic and native target-host
acceptance remain open. The Go suite and terminal gameplay tests were not rerun
for this research-only addition; no new gameplay validation is claimed.

[Findings, native evidence, scope and reproduction](../research/yt-maint/RNG_FIRST_HITS.md).

## Maintenance repeated reseeds and occupied-candidate sequencing — 2026-11-04

Local research on `feat/maintenance-rng-sequencing`, based on merged PR #86
(`52ee648`). No Go source, dependency, save-35, release package or original archive
changes. README and the reconstruction plan distinguish measured research from
playable production behavior.

- Captured 463 returned DOS controls: four untouched completed comparisons,
  78 main-body-end counters and 381 terminating nth-hit reads. The diagnostic is
  a declared same-size 46-byte copied-executable patch, with flags/displaced
  instructions preserved until the selected boundary. It bypasses the original
  cleanup footer; instrumented return is not called untouched completion.
- `python3 scripts/verify_maintenance_sequence.py`: all 463 controls, all raw
  decoded artifact pins and four fresh relocated native byte observations pass.
  All 78 counter runs match every decoded DAT/ASC output from their own untouched
  control. Baseline and repeat untouched outputs match exactly.
- `python3 scripts/test_verify_maintenance_sequence.py`: 49 corruption tests
  pass. These include rehashed states/FACs/worlds, source/site/threshold/copied
  executable substitutions, missing/forged clock/return/completion witnesses,
  contradictory launch options, changed pins/native observations and direct
  semantic seed/LCG/caller/count mutations.
- All 43 literal RND sites are counted in the baseline: nine execute, 34 do not,
  totaling 25,891 draws. Forty-one single-draw helper reseeds and nineteen
  four-draw helper reseeds match measured TIMER/low-byte transforms; all 117
  helper draw states match LCG steps and eight raw FACs match exact fractions.
  Sixty caller snapshots distinguish observed paths from unused literal callers.
- A declared synthetic positive planet-link at sector 1095 forces a retry.
  Wanderer candidates 1095 then 1792, two seed/draw pairs and the accepted raw
  sector distinguish rejection from the original optimistic success text.
- Both retained NASM diagnostic variants assemble to exactly the independently
  reconstructed/captured 46-byte patch. Script compilation passes.
- Earlier first-hit controls (151 probes, two native reads, six untouched runs),
  their 35 corruption tests, initial-maintenance controls (eight runs and four
  test methods/20 rejected variants), 13 native RNG contracts, 16 raw RNG traces
  with 4,096 state/FAC pairs, and all 4,682 archive hashes pass unchanged.
- CI adds the new portable verifier and corruption suite while retaining all
  earlier commands. Python standard library suffices for these checks; DOSBox,
  NASM and Ghidra/Java remain acquisition/research tools.

The new baseline world equals the earlier initial-handoff world and differs by
97 bytes from PR #86's separately captured oracle. Both historical recipes/pins
remain unchanged; no single timing/filename cause is claimed. Full global
phase/interception chronology, exact post-maintenance record/auxiliary replay,
arbitrary worlds/clocks and general MBF parity remain open. Full Go tests,
terminal gameplay and native-host durability acceptance were not rerun or claimed
for this research-only update.

## Initial-maintenance group/player phase ledger — 2026-11-04

Local follow-up on `feat/maintenance-phase-chronology`, based on research commit
`3489442` published in PR #87. No production Go, dependency, source archive or
save-35 changes; the later research remains separate from that published branch.
README, the current plan and CI are updated in this milestone.

- Captured 332 returned controls: one untouched completed run, four complete
  main-body-end counters and 327 terminating nth-hit observations. These reuse
  the reviewed same-size 46-byte diagnostic and independent patch/witness checks;
  an instrumented main-body end is not untouched cleanup completion.
- `python3 scripts/verify_maintenance_chronology.py`: all 332 controls, three new
  exact relocated REA byte reads and all source/site/clock/exit/raw pins pass.
  The prior 463-control sequence corpus is independently verified before its
  seed/caller states can serve as anchors.
- `python3 scripts/test_verify_maintenance_chronology.py`: all 51 negative tests
  pass, including rehashed world/trace/provenance substitutions, missing witnesses,
  contradictory options, rewritten pins/native records and direct phase-state,
  group/player, graph-edge, force ownership and desertion/lottery mutations.
- Four fresh counters match the entire decoded DAT/ASC output inventory and bytes
  of their untouched control. The new untouched run matches the prior pinned
  baseline outputs, so the state bridges compare the same measured recipe.
- Nineteen group phases decode to original groups 2–20; each candidate scan spans
  cached player slots 2–51. The candidate/interception states close exact LCG
  distances totaling 950 candidate and 24,800 interception draws. These partition
  into 496 fifty-player scan blocks, including group 20's eager excluded scan.
- All 38 sampled old/next-sector argument pairs form directed edges in the
  immutable source graph. The nineteen sampled last destinations retain positive
  Xannor forces in the untouched final records. The sample does not claim all 496
  intermediate edges or successful attacks under arbitrary worlds.
- Every group joins the prior four-draw allocator, fallback and candidate helper
  states. All twenty eager desertion before-states and the last after-state join
  the single lottery before/after pair without filler LCG steps. This accounts
  for the selected baseline's 25,891 literal RND executions across the measured families,
  not a simultaneous trace of every instruction or general MBF replay.
- The previous 49 sequence corruption tests and all 4,682 archive hashes pass unchanged.
  New Python scripts compile, relative research links and scoped diff checks pass.
- CI adds the new portable checker and test suite, retaining every existing lane
  and command. DOSBox/REA are acquisition tools; Python standard library suffices
  for verification. Full Go/terminal gameplay/native-host acceptance was not rerun
  or claimed for this research-only update.

Next recover exact post-maintenance record/auxiliary synthesis from these measured
phase/seed anchors. Arbitrary-world dynamic behavior, unobserved indirect paths,
general MBF arithmetic and production BBS/Windows durability remain separate.

## Bounded maintenance record model and retained clock gap — 2026-11-04

Local research on `feat/maintenance-record-replay`, based on the published phase
chronology commit `7b8bef0`/PR #88. Core synthesis takes the three pre-maintenance
files, original executable constants and explicit measured clock inputs. It
accepts no target world or per-record output patch table. No Go, dependency,
source archive, playable profile or save-format 35 changes.

- Independently modeled all 4,151 records and five auxiliary files. Against both
  paired instrumented main-body-end outputs, all 570,059 bytes match exactly.
  Against four untouched runs, all configuration/player/sector/planet bytes and
  all 1,372 auxiliary bytes match; port bytes match 136,996 of 137,000.
- The only untouched differences remain port 606/record 3657, offsets 101–104:
  raw `00004800` versus the diagnostic profile's `0e745a76`. A counter and a
  separate flags-preserving read-only 386 comparison both move this clock edge.
  No timestamp masking, target-derived correction, CPU tuning or expected-hash
  refresh hides it. This is not exact untouched replay completion.
- `python3 scripts/verify_maintenance_record_inputs.py`: all 28 retained controls,
  three named diagnostic profiles, four untouched runs and 14 fresh relocated
  native reads pass. Prior helper TIMER samples are verified by the independent
  463-control sequence checker before use.
- `python3 scripts/test_verify_maintenance_record_inputs.py`: 48 corruption and
  provenance tests pass, including rehashed launch/witness/native changes,
  raw startup/Xannoron input mutations, the 605/606 transition, complete output
  inventories and attempted hiding/relocation of the four-byte gap.
- `python3 scripts/test_replay_maintenance_ports.py`: 10 property tests pass for
  ten-day stock/class/sign logic, first-maximum ties, raw zero mantissas,
  inherited bytes, finite inputs and prohibition of target-file reads.
- `python3 scripts/test_replay_maintenance_records.py`: 21 whole-file/model-guard
  tests pass. These cover all six file extents/hashes, exact remaining mismatch
  locations/values, original-only file access during synthesis, derived RNG/
  routes, inherited-field propagation and unsupported fixture/clock inputs.
- `replay_maintenance_records.py --output ...` regenerates the complete report
  without masking any bytes. Its `--require-untouched-exact` mode correctly
  returns failure while the known gap remains. Passing research tests explicitly
  do not equate to meeting that stronger parity condition.
- Fresh source evidence corrects the old Wanderer restoration offset-81-clear
  statement: the writer preserves that inherited offset, numerically 305 in this
  fixture. It also establishes the inactive score-cache initializer as eight-byte
  MBF double −1, not a four-byte single zero inferred from its prefix.
- Retained readonly diagnostic NASM source matches the capture/reconstruction
  byte-for-byte for the never-hit and port 606 targets. All 11 new Python scripts
  compile; research links, byte-preserving attributes and scoped diff checks pass.
- Earlier chronology verification (332 controls/three native reads), 51 chronology
  negative tests, 49 sequence negative tests, 57 Wanderer controls/two diagnostics/
  14 native reads and all 4,682 archive hashes pass unchanged.
- README and the current plan now make the four-byte clock limit the next genuine
  research task. CI adds the independent input verifier and all 79 new tests while
  preserving every existing validation lane/command. Python standard library
  suffices for portable checks; DOSBox/REA/NASM/Java remain research tools.

No new Go-suite/terminal gameplay, native Windows durability or live BBS acceptance
is claimed. Next obtain a clock-neutral TIMER boundary observation or independent
timing model, require full untouched equality, and extend to independently measured
dates/clocks before any production compatibility change.


### PR #90 entry-capture reproducibility fix

Both reviews identified the same valid omission: the documented entry capture
command did not emit `startup-timer`, although the fixed input contract and seed
loader require it. Added site `007d`, hit 1, source `001a` to that command.
The new contract regression failed before the fix and passes afterward, checking
the complete dispatch inventory against the independent verifier matrix.

A real pre-fix DOS capture reproduced the three-control directory; a fresh
post-fix capture produced all four controls and passed the independent launch,
input, output and cross-profile semantic checks. The 28 retained controls and
all 14 native reads remain unchanged; no raw captures or expected pins were
refreshed. The input suite now has 49 tests, with 21 composed-model and 10 port tests
also passing (80 new tests total). README and the current reproduction notes are
updated. The four-byte untouched port-clock limitation is unchanged.


### Clock-neutral maintenance TIMER research — 2026-11-05

The bounded four-byte untouched port timestamp gap is closed by a separate
host-observed profile; the historical diagnostic profile/report/pins are retained
unchanged. This research changes no Go gameplay, dependency, original archive,
`qb36-v1` fingerprint or save35 format.

- Six final runs use unmodified original guest binaries and identical three-file
  inputs at DOS11/02/2026 midnight, fixed200000cycles: two unobserved controls,
  one Frida attach-only control and three paired host DOS-time observations.
  Every run exits naturally with status0; no forced stop or observer error/drop.
- All six resulting files (570,059bytes) are byte-identical across all six final
  controls and four independently authenticated historical untouched controls.
  Each host trace independently supplies every TIMER input; all30 complete
  before-to-after replay comparisons have zero differing bytes.
- All1,000 port calls are source/frame/index qualified. The original boundary is
  port607, not606; all41/19helper calls, startup seed and Xannoron TIMER come
  from the same observation. Exact rational conversion preserves two distinct
  single-rounding stages and original zero residue, not a target-derived patch.
- Independent verification pins the installed macOSARM64 DOSBox0.83.0 binary,
  loaded UUID/prologue, original guest code/frame signatures, complete raw paired
  registers, exact launch/actual CPU logs, capture sources, Frida17.23.2 identity,
  natural PID cleanup and every retained raw artifact. Fourteen primary host
  source files and native static evidence explain the observer layout.
- All63 independent regressions pass, covering arithmetic, paired events,
  source attribution and24 capture-provenance checks (23 corruption cases). A valid606 clock
  substitution reproduces exactly four real byte differences and is rejected
  against the saved timestamp before immutable pin checking: no field is masked.
- Eight new profile tests pass, including no file reads during input derivation,
  no target/prior-probe reads in core synthesis, unchanged-byte propagation and
  all30 full comparisons. Historical49 input,21 composed-model,10 port,
  51 chronology and49 sequence regressions pass; original verifiers and all4,682
  archive hashes pass unchanged. Python/JavaScript syntax and relative links pass.
- The superseded REA pilot and client/logger diagnostics are explicitly separated
  from the accepted six-case matrix. Host instrumentation is not passive: the
  neutrality claim is limited to this exact recipe and complete output evidence.

README, reconstruction plan, retained comparison report and CI are updated in
this milestone. Portable checks require Python standard library only. No new
Go-suite, gameplay terminal, native Windows durability or live BBS acceptance is
claimed. Next independently recover additional dates/clocks and bounded worlds;
arbitrary-world maintenance prediction and production compatibility remain open.


### Maintenance clock/date matrix research — 2026-11-05

Eight declared recipes extend the midnight-only research with nonzero and noon
clocks, literal24:00:00 text rounding, actual midnight rollover, additional dates
and Jan1,2027 against the same saved-base-year26 before-world. Original executables,
three before inputs, source fingerprints and save35 remain unchanged.

- All48 native controls passed: eight recipes × two unobserved runs, one
  attach-only control and three host traces. Every process exited naturally with
  status0; original guest hashes, completion/error markers and cleanup verified.
  All288 complete output-file comparisons agree within recipe (six files,
  570,059bytes per run), without timestamp masks or target correction.
- All24 observed traces authenticate49,809DOS events:49,713source-qualified
  DATE$/TIME$/TIMER returns and96external shell calls. Frame/code/BP bindings,
  physical segment caches, fixed CPU budgets and source-backed interpreter
  refill accounting are independently verified. Two focused original native
  reads and pinned official BIOS source corroborate the new contracts.
- Seven recipes replay all six files exactly:21observations × six controls =126
  complete before-only comparisons with zero differing bytes. Every `late`
  observation remains one of three explicit unsupported rows in the report:
  the modeled prefix reaches neutral Wanderer slot1 in sector658 with group2.
  No battle result is inferred, target bytes copied or route sector skipped.
- Native TIME$ rounds at50hundredths without wrapping carried hour24. The100k
  profile's scoreboard preserves24:00:00 on Nov2. The10000-cycle recipe really
  crosses midnight:668portDATE samples are Nov2 and332are Nov3; news and score
  dates/clocks differ. Jan1,2027 uses legacyday366 from savedbase26, notDOY1.
- Nonzero seeds can take a42nd single-range lottery helper call, select an
  inactive player and abort without an award. Per-port dates, NPC creation days,
  final watermark and independent news/score date/clock inputs are modeled.
  The old strict entrypoints and all PR91 acquisition artifacts/pins are retained.
- All60new tests pass:44independent verifier checks (34corruption/rejection
  controls) and16model/property tests. The251selected historical regressions
  also pass:63midnight verifier,49record inputs,21record model,10ports,
  eight midnight model,51chronology and49sequence. All4,682archive hashes pass.
  Syntax, links and exact-byte diff checks pass; optional strict-all replay fails
  as expected for the documented encounter gap rather than hiding it.

README, reconstruction plan, reproducible acquisition, immutable provenance,
complete comparison report and portable CI checks are included. New pure-writer
entrypoints are opt-in research extensions; no Go-suite, live BBS gameplay,
release validation or native Windows durability acceptance is claimed.
Next recover the original maintenance Xannor/Wanderer interaction and its RNG,
record and side-file aftermath. Uncapped production, other encounters/worlds,
multi-year/leap/century behavior and general MBF remain separate research.

### PR #91 initialization deadline review fix

A single 30-second deadline now covers dynamic import, device discovery, spawn,
attach, script creation/load/readiness, resume and execution. Error cleanup kills
the owned PID directly and waits for exit (bounded to two seconds), before the
Python 40-second outer timeout. Six real spawned-process regressions use a fake
Frida adapter stalled at attach/create/load/ready/resume/execution; all confirm
failure metadata and target termination. The original acquisition controller is
retained under `clock-neutral-acquisition/` and verified through the unchanged
original manifest digest. Original observations and source hash claims are not
retroactively assigned to the fixed controller. README updated.

## Supplemental historical runtime streams — published 2026-11-05

Five full-stream experiments captured 2026-11-04 are retained separately under
`runtime-stream-controls`, with uniquely named capture/verifier/test scripts.
They check 127,618 seed/draw events and exact measured probe-induced boundaries;
no native observations or hashes were changed. This preserves the earlier
experiment without overwriting merged PRs #86–90, their newer controls or their
record-model claims. No gameplay/save/release changes.

`verify_maintenance_runtime_streams.py` and its four-method / 17-rejection suite
pass after integration with current main. Existing first-hit and sequencing
verifiers also pass. README and plan distinguish supplemental history from
newer implemented research. Unrelated smoke captures remain unstaged.


### PR #92 paired native reference integrity

The standalone full-stream verifier now validates each decompressed paired native
world against the existing independent initial-maintenance pin before computing
the perturbation boundary. A new regression alters an already differing byte
while preserving the exact differing-byte positions/count; it is rejected by the
native pin. No retained reference bytes or hashes changed. Five test methods /
18 rejection controls and all five full streams pass; README updated.


### PR #93 review wording and prerequisite integration

Corrected the four reviewed spacing issues in README, the reconstruction plan,
and the hand-authored text-clock contract's comment and success message. The
clock function's parsed AST is unchanged; only the derived helper's native-packet
digest and enclosing manifest digest are refreshed. Original binary/source,
all 48 raw control captures and replay target hashes remain untouched.

Integrated PR #91's already-validated initialization-deadline fix and current-main
supplemental runtime streams. Resolving the two append-only conflicts preserves
both validation histories and byte-preserving artifact rules. The matrix verifier
initially reproduced an acquisition-source mismatch against the now-hardened live
controller; it now authenticates the preserved original controller used by the
immutable observations, matching the prerequisite's source-binding policy.
Historical capture/source identities are not reassigned to new code.


Validation after the review fixes and prerequisite merge: all 44 matrix verifier,
16 matrix model, 63 midnight verifier and eight midnight model tests pass. The
six stalled-process cases in the deadline regression pass, as do all five
supplemental runtime-stream tests and all 4,682 archive hashes. The four static
rounding examples pass with readable output; raw captured controls are unchanged.


### Preserved acquisition source checkout integrity

A disposable `git -c core.autocrlf=true checkout-index` export reproduced a real
provenance failure: the unprotected historical controller acquired 57 CRLF line
endings, changing its SHA from `01cb319f697c40888d66fe313763b5e879a85e640ee99a488a5b6adb0ecda5eb`
to `caa17b2cffd95a3aa3438bf38d2fc97faa9684c4cfdbe162598a7711e2b46b5a`.
The recorded source is now explicitly `-text`, like the other immutable evidence.
The same export then preserves the exact original bytes and SHA. Both midnight
and clock/date corpus verifiers pass; no captured observations, original source,
manifest expectations, model behavior or production code changed. README updated.

## Independent maintenance dates/clocks — 2026-11-05

Twelve original-DOS runs cover next-day, New Year, leap-day and noon initial
worlds. One untouched and two host-observed runs per profile agree completely.
Eight independent traces drive 24 six-file comparisons / 13,681,416 bytes with
zero mismatches, including all timestamps/auxiliary files. No after-target bytes
enter synthesis. Original guest binaries and all 4,682 archive hashes remain
unchanged. Actual acquisition sources and complete native artifacts are pinned.

Five new test methods cover all four before-only profiles, eight direct
refill/caller/port corruptions, four invalid-input/inventory cases and four pinned
artifact mutations. Existing 63 clock-observation, 21 composed-model and eight
clock-neutral replay tests pass. Noon adds positive INT-minute and unnamed
lottery-candidate paths; New Year/noon require exact zero-budget CPU refill
witnesses, not a relaxed arbitrary-cycle rule. Default baseline checks remain
strict. No Go, save35, source fingerprints, release or live BBS claims changed.

[Capture method, results and remaining bounded state work](../research/yt-maint/CALENDAR_CONTROLS.md).


### PR #93 integration with merged calendar controls (#94)

Current main added four independently initialized calendar profiles while this
PR was validating. Integration preserves that separate corpus and verifier,
the eight same-saved-world matrix profiles, all recorded hashes and both
validation histories. The shared NPC writer now retains the calendar profile's
41/42-helper admission, nonzero integer timestamp and inactive lottery-candidate
statistics, while keeping explicit matrix creation dates, zero residue and the
structured unsupported Wanderer encounter. No source/capture data is regenerated.


Calendar integration validation passes: five fresh-world calendar tests and its
12-control/24-comparison verifier; all 16 matrix model and 44 matrix verifier
tests; historical 21 record-model, eight midnight-model and 63 midnight verifier
tests; six deadline-stall cases, five runtime-stream tests and 4,682 archive
hashes. The retained matrix report regenerates identically (126 exact complete
comparisons plus three explicit late encounter gaps). Both raw corpora are
unchanged; no production Go or dependency changes were introduced.


## Initial Xannor/Wanderer maintenance-stream integration — 2026-11-05

Research-only opt-in replay closes the late-night clock-matrix encounter without
changing the historical strict APIs/reports, Go gameplay, dependencies, source
recipes or save 35. All eight recipes yield 144 complete comparisons / 864 files
with zero mismatches. Six fresh unchanged-executable controls add 18 complete
comparisons / 108 files, also exact. Two unobserved, one attach-only and three
clock-observed runs all exit naturally and agree on every output byte.

Fourteen separately labelled guest-probe diagnostics verify zero ground draws,
53 production gates, 27 damage draws per commodity, 50 candidate-player draws,
23700 entered-sector player draws, two desertion draws, one lottery gate, first
seed transitions, the actual preferred-target output and group index. Nine are
complete counters; five stop at declared sites. They are timing-perturbing
source diagnostics, not untouched output goldens. Two complete REA native reads
are independently checked against relocated original bytes. The independent
verifier reconciles 18 public attack/death pairs, 6923 casualties, 3077 surviving
fighters and score 307700; private messages remain empty and raw zero residues
remain unnormalized. Immutable pins include every accepted file and frozen
acquisition sources. A later acquisition with a missing Frida flush notification
was rejected, not counted as success.

Focused model/semantic/provenance regressions and affected historical replay,
clock-neutral, calendar and archive checks are the applicable validation for
this research-only change; no new gameplay/PTY/native-Windows/live-BBS acceptance
is claimed. Reproduction, exact scopes and unfinished branches are in
[the encounter report](../research/yt-maint/WANDERER_ENCOUNTER.md).

Final local checks passed: 18 new model tests and 63 verifier tests (including
60 negative verifier controls); 16 historical matrix, five calendar, 21 composed
record, eight clock-neutral replay, 44 matrix-verifier and 63 clock-neutral
verifier tests; matrix/calendar/clock-neutral evidence verification and all 4682
archive hashes. The historical complete matrix report regenerated byte-for-byte
unchanged. Empty/partial corpora and falsely disabled observed modes cannot
produce a vacuous zero-comparison success. The finalized acquisition command
also completed all twenty controls in a separate fresh directory; their outputs
and diagnostics independently match the retained accepted corpus.
All 368 pinned corpus files also passed independent verification after an index
export with `core.autocrlf=true`; checkout cannot normalize the raw evidence.


## Bounded occupied placement and faction-cache research — 2026-11-05

Twelve a-priori initial-world recipes retain 72 unchanged-executable full DOS
runs and twelve separately patched early cache exits. Each recipe pairs two
unobserved, one attach-only and three host-observed full runs; every one of the
six outputs is byte-identical within that recipe. All children exit naturally
with status zero, intact original binary identities and checked DOS witnesses.
The early cache probe is independently reconstructed at source `29b7`, outputs 168
DS bytes and terminates before full maintenance; it is not a full-run golden.

The before-only cache primitive matches 480 raw location/force fields. The
source-qualified placement primitive matches 432 target checks from declared
TIMER/old-RNG-state witnesses and before links. Multiple rejection/reseeding,
fractional/negative/raw-zero occupancy, duplicate pointers, foreign-owner
non-consumption and unpointed friendly-force addition are separately checked.
All 40 modeled cache cells, raw consumed-sector zeros and cleared stored pointers
are verified; the two unused packet cells stay retained without invented model
values. Four fresh complete REA reads independently match relocated original
bytes. Input recipes, actual sources, host frames/logs, output identities and
all 1773 retained corpus files are pinned rather than automatically approved.

This research does not synthesize all final bytes for the twelve new worlds.
Measured Base old RNG states are explicit midstream inputs, not reconstruction
of all prior faction movement. The original complete clock/Wanderer replay
remains available. No Go gameplay/dependency change, save 35 migration, original
archive modification, live BBS acceptance or native Windows acceptance is
claimed. See [scopes and reproduction](../research/yt-maint/PLACEMENT_COLLISIONS.md).

Final local validation passed: 37 primitive/model tests and 69 independent
verifier tests; 18 prior Wanderer model tests, 63 Wanderer verifier tests, 16
historical matrix model tests, complete matrix/Wanderer evidence verification,
and all 4682 original archive hashes. The six-mode output equality and all 480
cache fields / 432 placement checks pass for every accepted recipe. Production Go,
terminal gameplay and platform builds were not rerun for this research-only
change; those checks remain enabled in CI.
All 1773 pinned corpus files additionally pass independent verification after
an index export with `core.autocrlf=true`; no raw observation or acquisition
source is normalized by checkout.


## Complete initial collision-fixture record replay — 2026-11-05

The selected twelve placement/cache fixtures now have complete before-only
six-file synthesis, rather than only primitive/phase predictions. All 36 source
observations compare against six paired untouched/attach-only/observed targets:
216 complete comparisons / 1296 individual files, zero byte mismatches. The raw
84-control corpus, original archive and historical strict replay reports remain
unchanged. Per-port timestamps and all raw zero residues are compared without
masks or target-derived corrections.

Every RNG state is derived from startup and explicit source-labelled TIMERs.
Captured old RNG states and cache probes are excluded from synthesis; 2265 helper
and final-score raw-state checks independently agree afterward. Poisoned raw
witnesses leave modeled outputs unchanged and fail the separate audit. Dynamic
helper inventories, repeated placement, normalized/existing groups, shared
preference, source-order route actions and the selected zero-tax Mercenary tail
now continue through the lottery and auxiliary writers. The 37-force Mercenary
case derives two descending-scan activations and preserves departure raw zero
`00002800`; public/private receipts and actual faction scores remain exact.

An additional complete REA original-byte read at `0x14600`, length 3462, is
independently verified against relocated original bytes and immutable packet
identity. Eleven native provenance/byte corruption tests pass. The new model
suite has 25 tests, auxiliary suite 22 and Mercenary suite 18: 76 new methods
pass in total. Original-only file-read guards, immutable typed clocks, unknown
before-world rejection, source chronology/consumption, independent state audits,
casualty conservation and explicit unsupported branches are covered. A separate
regression matches all six outputs for each of the earlier eight clock/date
recipes, and the historical strict late profile keeps its original rejection.

Current main's merged cursor fix was integrated cleanly; this research changes
no Go gameplay, dependency, save 35 or `qb36-v1` fingerprint. New mines, foreign
combat, stock pickup, evolved worlds, arbitrary MBF and general DOS maintenance
remain unsupported unless separately recovered. No new terminal/live BBS/native
Windows acceptance is claimed. Reproduction and source boundaries are in
[the complete replay report](../research/yt-maint/COLLISION_RECORD_REPLAY.md).

Final affected historical regressions passed: 37 placement replay tests, 69
placement verifier tests, 18 Wanderer replay tests, 63 Wanderer verifier tests
and 16 clock-matrix tests. All 4682 archive hashes remain valid. The new native
packet also verifies after an index export with `core.autocrlf=true`; its raw
bytes are preserved across checkout. All 76 new tests passed again at the final
staged source state. Production Go, terminal smokes and platform builds were
not rerun for this research-only update; their existing CI checks remain enabled.

## Active-planet and foreign-route controls — 2026-11-05

The next maintenance research slice retains ten declared contexts / 60 complete
original-DOS runs / 360 output files. Each case has two unobserved controls, one
attach-only and three observed controls; all six complete outputs agree in every
mode. Active ordinary-slot planets have real names, prior-day timestamps and
sector links. Three bounded pre-placement RNG advances per active planet agree
with authentic first-helper state witnesses. Follow-up controls actually reject
occupied Wanderer/Base candidates; old-candidate reference controls are retained
and distinguished from successful rejections.

Friendly and neutral planetary contexts separate earlier one-day economic growth
(1000 rates to 1010; 500000 ground to 505000) from subsequent combat. The neutral
planet spends 25 ground and destroys 5978 Xannor in 19 public attack/death pairs.
Actual Mercenary defenses at sector 854 exercise small and large foreign-force
encounters, later Mercenary movement and faction scores; saved physical losses
reconcile with original public literals, including their misleading lost/dstrd
columns and Plyr label. Owner-zero 37-force control remains unchanged. Private
message files remain empty. These are witness-assisted original controls, not
complete before-only synthesis of the new worlds or new Go features.

Independent verification covers all 1290 immutable corpus files, actual launch
and controller provenance, all source clock frames, full fixture reconstruction,
untouched original guests, active name/link/owner/ground aftermath, public losses,
faction force/scores and six-mode equality. All 56 provenance/semantic tests pass. One
complete REA/Ghidra read authenticates 720 original bytes and the three event RND
sites. The manifest SHA is 7c01a0ef401f3df96f413e4aefd046c7f8a57499a1dfa537c83ea950d0dc7a3a.

The forward-dated pilot contexts remain external diagnostics. A prior-day
observed capture that lacked the required Frida flush notification was rejected
despite natural process exit; its partial artifacts remain external. A fresh
complete six-mode set passed every unchanged controller requirement. No failed
capture is included in accepted counts and no automatic retry was added.

All ten new before-worlds are explicitly rejected by the historical bounded
collision-replay profile; its admission boundary was not broadened. Current
main's merged smoke-evidence PR #96 was integrated without changing its captures.
All 309 local Markdown targets in the changed README/plan/reports exist. README,
plan and portable CI evidence checks are updated in this research milestone.
Production Go, dependencies, archive originals, save 35 and generation fingerprints
are unchanged; no new Go/terminal/platform/live acceptance is claimed.

Final checks also passed the historical 84-control placement/cache verifier,
25 complete collision-record replay tests and all 4682 archive hashes. All 1290
new corpus files independently verify after index export with `core.autocrlf=true`;
checkout does not normalize raw captures or acquisition sources. No old corpus
pin, archive or historical report was rewritten to fit these results.

## Complete active-planet/foreign-route record replay — 2026-11-05

The separate bounded occupied-record profile now synthesizes all six files for
the ten retained active-planet/foreign-route before-worlds. Thirty authentic
source observations compare against six paired targets each: 180 complete
comparisons / 1080 individual files, zero byte mismatches. All 1872 independent
helper-entry/final-score RNG witnesses agree with states calculated from startup.
Captured raw states are discarded during input extraction; poisoning them leaves
synthesis unchanged and fails the separate comparison audit. Read guards exclude
all targets, captured states, recipes and manifests from core synthesis.

Ordinary one-day active-planet economy reproduces every raw field, including
fractional cargo/fighter/missile inventories, source TIMER-minute bytes and three
eager event draws per planet. Strong neutral ground consumes 25 units across 19
calculated fatal attacks; actual public Xannor losses total 5978. Foreign defense
uses source batch/tie order, derives actual raw loss counters and original labels,
clears shared pursuit when defenders die, and reproduces all later destinations.
The surviving 97525 Mercenaries move from 854 to 2689 in their own tail; per-owner
physical force, scores and public/private separation remain exact.

All 116 new tests pass: 42 active-economy, 28 full-record, 25 auxiliary, 15 direct
synthetic combat/tail and six native integrity methods. Unknown before-worlds,
clock types/order/inventories and unsupported economy/combat branches fail closed.
The historic collision replay still rejects these new worlds and retains its
own validated results. No old model or captured output was broadened/rewritten.

Two complete additional REA/Ghidra reads fill source gaps: 0x11111/699 bytes and
0x17691/229 bytes. All 928 relocated bytes independently match immutable original
YTMAINT; the packet has SHA-256 107dd59cca0e57ade5f590df37b178621abc999f086574de97ad6d83332d0fd7.
Existing event, battle and aftermath observations are reused. Static source
reads are not new DOS execution traces; no new runtime captures were needed.

README, reconstruction plan, linked control reports and portable CI checks are
updated. All 319 local Markdown targets in changed documentation exist. Go,
dependencies, save 35, generation fingerprints and raw retained control corpora
are unchanged. Go tests, terminal smokes, platform builds and live/native BBS
acceptance were not rerun or newly claimed for this research-only update.
Final-pointer convergence and exact evolved-world chaining remain next.

Final regressions passed: all 25 historical collision-record tests; the untouched
60-run occupied-control verifier; 47 mobile Xannor controls and 22 native reads;
56 plague/civil-war controls and 18 native reads; and all 4682 original archive
hashes. The additional 928-byte packet also verifies after an index export with
`core.autocrlf=true`. Its raw bytes survive checkout unchanged. No historical
capture/pin or production source was modified by these checks.

## Final-pointer convergence and exact evolved-world chain — 2026-11-05

Eighteen full original-DOS maintenance runs carry one declared world through
November 2/3/4, with two unobserved, one attach-only and three observed modes per
day. All six complete outputs agree per day (108 full-run files). Every child
and separately patched early-cache probe inherits all six output files from its
own parent mode without resetting or patching them: all 144 input-file links
match byte-for-byte. Twelve early probes are phase observations, not full runs.

The initial named friendly planet makes groups 2–19 finish at sector 2802, whose
single physical force is 6552; HQ retains 3095 and group 20 retains 353. Next-day
cache normalization consumes only those three physical sectors and loads that
shared force once. Groups 3–19 normalize to zero and require seventeen new
allocations. Day three starts with twenty distinct groups and makes zero new
shrinking-bound allocations. All 480 source-owned cache cells agree, stored
pointers clear canonically, and consumed force/title zeros retain raw `00008000`.
Physical force remains 10000 through all full runs; names, rotated news, private
files and actual scores are checked separately. No old scoreboard inherited by
an early probe is mistaken for a completed new writer.

All 39 new provenance/semantic tests pass. Independent checks bind actual guest
and host identity, complete launch/CPU/date/controller provenance, every source
clock frame, text receipts to source clocks, dynamic helper inventories, exact
input inheritance, unchanged full guests, exact early-probe patch, unique force
and raw cache fields. Rebound metadata and hashes cannot disguise a guest patch,
wrong parent, fabricated clock, duplicate force or premature scoreboard.

The frozen 794-file corpus has manifest SHA-256
164cc9d62bef6b213226ca8e125e39d282e6b851a9b6ffaf048e933a290d1f8c.
All thirty captures completed naturally without a retry. Existing complete cache
and final-writeback REA observations are reused; no new native query, installation
or configuration change was needed. All three new before-worlds remain explicitly
rejected by the historical active-world replay; their separate before-only
integration remains next. This milestone establishes observations and exact
chaining rather than evolved-world synthesis.

README, current plan, linked reports and portable CI checks are updated; 317 local
Markdown targets in changed documentation exist. Production Go, dependencies,
save 35, generation fingerprints, archive originals and earlier corpora remain
unchanged. Go/terminal/platform/live BBS and native Windows acceptance were not
rerun or newly claimed for this research-only update.

Final checks passed the earlier 84-control placement/cache corpus (including its
existing native reads), the 60-control active-planet corpus and all 4682 original
archive hashes. All 794 new corpus files also independently verify after an index
export with `core.autocrlf=true`; no raw capture or frozen acquisition source is
normalized by checkout.

## Before-only evolved three-day maintenance chain — 2026-11-05

The new separate profile takes only the original three before files and three
frozen source-clock inputs, then feeds each day's own modeled six files to the
next day. No native child before/after world, cache probe or captured RNG state
enters synthesis. All three days are calculated before expected output files are
opened. Across three source-observation chains and six paired targets per day,
all 54 complete comparisons / 324 files are byte-exact, without masks, output
fingerprint selection or target-derived record repairs.

Every source helper state and final-score RNG witness agrees: 501 independent
checks. Poisoning raw witnesses leaves extracted inputs and outputs unchanged,
then fails the separate audit. Actual planet loop indices bind their DATE/TIMER
pairs; source clocks cannot silently migrate to another physical record.
Modeled parents additionally predict all 480 captured cache fields, repeated
across the three observation chains for 1440 comparisons. The probes remain
comparison-only and never seed the modeled normalization.

One-day nonempty port stock arithmetic/rate promotion, four heterogeneous planet
banks/inventories, source floors, fractional weapons, surplus growth and eager
event draws now integrate with the existing-home paths. Wanderer unlinks its old
reference; existing Xannoron/Base skip creation clocks. Xannoron's common later
ground draw still adds 4/3 after ordinary economy on days two/three. Cache-derived
allocation counts are 19/17/0, computed physical force remains 10000, old mines
persist and actual inherited ranks/side files publish correctly. Day one's
scoreboard 00:00:01 stays distinct from its news clock 00:00:00.

All 100 new tests pass: 18 port, 22 planet, 24 auxiliary, 30 full-chain and six
native integrity methods. Full-chain read guards allow only original YTMAINT;
actual handoff spies and modeled marker checks reject a hidden native-child path.
Unknown initial bytes, malformed/fabricated/reordered clocks, wrong source record
indices, optional creation-clock mismatches, unsupported economics/combat and
incorrect conservation/publication fail closed. Historical replay APIs and
admission boundaries remain unchanged.

One complete additional REA/Ghidra read covers existing-Base search/skip bytes at
0x14128, length 153, through 0x141c1 exclusive. Every relocated byte matches the
immutable original. Packet SHA-256:
d63718fd9f35e8a04fa7e12b51cb40eb179319e513db2f6c0525d556072c337b.
Existing port/economy, Wanderer, Xannoron and cache evidence is reused. The static
read is not a new runtime trace; no new DOS capture was acquired or rewritten.
The existing JDK was selected per-process without installation/config changes.

Final regressions passed the 18-full/12-probe chain verifier, all 28 historical
active-world record tests, 57 returned Wanderer controls/14 native reads, 41
Mercenary maintenance controls/11 native reads and all 4682 archive hashes. The
Mercenary verifier's separately classified bounded hiring-capacity timeout is
historical evidence, not a newly passing full run. All raw 794 chain-corpus files
and prior pins remain unchanged.

README, plan, linked scope reports and portable CI checks are updated. All 325
local Markdown targets in changed docs exist. Go, dependencies, save 35 and source
generation fingerprints are unchanged; Go/terminal/build/live/native acceptance
was not rerun or newly claimed. Next collect evolved-chain clock/date controls
before broader admission; general MBF and arbitrary-world compatibility remain
separate.

The new 153-byte packet also passed independent verification after index export
with `core.autocrlf=true`; its raw source bytes remain unchanged on checkout.


## Evolved maintenance clock/date controls (2026-11-05)

Captured 48 full original-DOS runs: second-two, noon, eleven-day catchup and
New Year, each with two inherited children and six observation modes. All eight
stages agree across modes for all six files; 288 before-file inheritance links
and 288 complete after files are authenticated. The independent verifier and
47 regression/negative controls pass, as do all 4682 immutable archive hashes.

The clocks select a fatal six-fighter mine encounter, fourteen fatal Wanderer
attacks totaling 1700 fighters and four fatal Base attacks totaling 362 fighters.
Ground losses are nineteen and five respectively. Source clocks expose actual
BIOS quantization and New Year serial days 366/367; ten-day economic capping
does not collapse distinct helper TIMER values. These are native observations,
not yet a complete before-only replay of the new profiles. Existing replay
guards reject their selected combat or unadmitted dates/clocks.

README, plan, CI and the linked scope report are updated. Capture sources are
frozen exactly as executed; no historical capture is rewritten. Go, dependencies
and save compatibility are unchanged. Full Go/terminal/build/live acceptance was
not rerun for this research-only milestone. The published PR97 tip remains
3d1b9969cbbfcd2e25e1450629ac30d3ccbc6a4e; follow-up work remains local.


## Before-only evolved clock/date replay (2026-11-05)

A separate bounded profile now computes the original convergence parent and both
children from one original three-file before-world plus source-qualified clocks.
All 144 full comparisons / 864 files match byte-for-byte across four recipes,
three observed streams and six native target modes; all 1278 child helper/final
RNG-state witnesses agree. No child-before/after payload, transcript or captured
RNG state participates in synthesis. All targets are first opened after the
complete modeled chain exists. Exact object handoff and marker/read-ban tests
verify this boundary.

All 69 new tests pass: six port, seven planet, nine auxiliary, nineteen NPC and
28 full-chain tests. Port fractional/capped growth, source floors, New Year
serial dates 366/367 and actual raw timestamps compose with fatal mine/planet
combat. Noon loses 1700 Xannor / 19 Wanderer ground; New Year loses 362 Xannor / 5 Base
ground; second-two child 2 derives roll 223 but caps damage/loss at 6. Physical
casualties back actual public receipts and survivor-based scores. Subsequent
losses are not repaid. Names, previous news, private emptiness and separate
score/news clocks remain byte-exact.

A new no-hop branch exposed the old copied tail's unconditional mine increment.
The original 39d4..3a00 BFS-successor guard skips its movement/deposition block,
so an unchanged group 20 endpoint 439 retains one mine. The new profile models that
source guard; genuine travel still increments mines. The consumed mine 980 zero
is derived from the source FAC record-I/O calculation and exponent-only exact
cancellation, not an after-file literal. Both details have direct regressions.
Historical profile APIs, guards and raw captures remain unchanged.

The 30 historical full-chain tests and 40 historical port/planet tests pass.
Reused source evidence passes 26 initializer byte contracts, 332 chronology controls
and 47 returned mobile controls / 22 REA observations. The independent new-corpus
verifier and 47 provenance tests previously passed in the controls commit, including
export with core.autocrlf=true; all 4682 archive hashes remain valid. No new REA
query or emulator acquisition was needed for replay integration. README, plan,
linked reports and CI are updated; Go, dependencies, save 35 and generation
fingerprints are unchanged. Go/terminal/build/live/native acceptance was not
rerun or newly claimed. Both follow-up milestones stay local, separate from PR #97.


## Evolved foreign-force and surviving-combat controls (2026-11-06)

Captured 48 full original-DOS runs across four two-child recipes, using the
corresponding occupied-route parent's complete six-file output without edits.
All 288 inherited-file links match; all six output files agree across all six
modes at each of eight stages. Each run exited naturally on the first acquisition.
No failed, timed-out or forced-stop run is counted. Frozen corpus: 1318 files,
11,229,698 bytes; manifest SHA-256
fd794dccfda332ab79c2d5a693d2649ebbc32c607863fbf2f10801ec4e0ecef5.

The surviving Mercenary control retains 97525 fighters after the first child.
On the second, its public attack destroys 182 Xannor; actual saved Mercenary
force decreases by 188 to 97337. That unprinted loss is explicitly classified as
an observed physical delta, not a published count or a before-only RNG prediction.
Both children demonstrate descending-scan reactivation. The later Mercenary
victim's group-8 pointer remains 109 despite zero physical force at that sector;
verification preserves this authentic stale state. Route Haven survives eighteen
fatal Xannor assaults each child, accounting for losses 2614 and 792 and actual
ground 504975→510002→515083. Extinct-Mercenary and neutral-owner controls retain
their expected physical totals; neutral assimilation is not demonstrated.

All 43 provenance, outcome and source-width tests pass. They cover actual launch,
CPU/date/clock identity, exact parent/mode/file inheritance, observer/lifecycle
integrity, raw saved port/active-planet timestamps, public/console agreement,
physical score accounting, winner/phase/force corruption, stale pointers and
complete immutable inventory. Separate eight-byte MBF decoding verifies the
source fight threshold 200 despite its zero four-byte prefix; batch size is 150.
The reused original Mercenary source packet's complete 3462 relocated bytes
match the immutable binary. All 4682 archive hashes pass. No new native byte
query, provider installation or historical capture rewrite was needed.

README, plan, scope reports, byte-preserving Git attributes and portable CI
checks are updated. All new acquisition sources are frozen exactly as executed.
Go, dependencies, save 35 and generation fingerprints are unchanged. Full Go,
terminal, build, live BBS and native Windows acceptance were not rerun or claimed
for this research-only change. PR #97 and the earlier local follow-up branches
remain unchanged. Next compose these exact occupied-input chains before-only;
current convergence-only admission rejects their different initial contexts.


## Before-only evolved foreign-force combat replay (2026-11-06)

The new bounded profile computes each original occupied parent, then both
children through exact modeled six-file handoffs. All 144 new-child comparisons /
864 files match byte-for-byte across four cases, three observed clock streams
and six native target modes. All 1242 independent child helper/final RNG-state
witnesses agree; the original prefix witnesses agree as well. No captured child
file, transcript, probe or old RNG state is read during synthesis. Source
extraction explicitly admits actual parent zero/one and evolved three/four
active-planet clock inventories, with strict measured dates/publication clocks.

The surviving Mercenary offense derives the eager gate and 370 combat draws,
182 Xannor / 188 Mercenary casualties, continued movement, repeated descending
activation and authentic stale group-8 pointer 109. Source threshold DOUBLE 200
and batch 150 are bound to original executable bytes; captured offense 182 tests
unit damage, while source-derived batch/tie boundaries have synthetic tests.
Neutral Route Haven economy 510024/515102 followed by 22/19 ground losses gives
exact saved 510002/515083. Physical owners separately conserve all casualties;
original public literals print initial forces/winner without inventing a public
188-loss counter. Final score columns derive from physical survivors, not stale
pointers. Names/private/yesterday news and all five auxiliary files are exact.

All 56 new tests pass: five planet, six auxiliary, eighteen NPC/Mercenary and
27 full-chain tests. Direct tests ban target reads, check actual object and marker
handoffs, poison observed RNG witnesses, corrupt helper/final states, reject
unknown initial worlds and unmeasured clock/caller inputs, and retain stale
pointers. The 28 historical occupied-record and 28 clock-chain tests pass. The
complete reused Mercenary source read's 3462 relocated bytes match the immutable
original. No new emulator run, native byte query, provider installation or capture
rewrite was needed for model integration; raw control corpora remain unchanged.

README, plan, linked reports and portable CI are updated. Go, dependencies,
save 35 and generation fingerprints are unchanged. Full Go/terminal/build, live
BBS and native Windows acceptance are not newly claimed by these research-only
checks. The completed follow-up is prepared separately from prerequisite PR #97,
including the two control/replay pairs. Next acquire mixed-hazard/resource-pickup
or longer surviving-force handoffs before broader research admission.


## Longer survivor and foreign-defense handoffs (2026-11-06)

Acquired 48 complete original-DOS runs: four actual November 4 output states, each
followed by two unchanged six-file children on November 5/6. All 288 input-file
inheritance links match. All six output files agree across six modes at all
eight stages. Every process exited naturally on the first acquisition; no
failed/forced/timeout run is counted. Corpus: 1318 files / 11,442,647 bytes; manifest
2ce91ff7798d4da83f9ca5966fc999958b7a038808c4da4ed4c26889b3b2cc5e.

Mercenary-survivor November 6 selects 18 earlier Xannor-phase defensive battles.
Public counter columns sum 2533 Xannor / 3491 Mercenary losses and reconcile actual
physical 4966→2433 / 97337→93846. A legitimate 1/0 casualty summary is retained;
0/0 fiction is rejected. The later first Mercenary movement already has 93846,
and four descending activations retain that force. Planet-survivor loses 146
then 70 Xannor in 18 fatal Route Haven attacks each day. Neutral-survivor loses 1425
in 5 fatal Wanderer attacks on November 6 while neutral 37 remains at 854. Mine-survivor
loses 818 in 4 fatal Wanderer attacks on November 5 and none on November 6. Mines persist
and new deposits remain visible; no selected mine damage or stock pickup is claimed.

The actual stale/duplicate pointer fields are retained without canonicalization.
The known before-cache rule derives an empty group 8 from inherited pointer 109;
the new final pointer 328 / physical 2 are observations after reallocation, not a new
captured cache array or input patch. Neutral-survivor November 5 has NEWS 00:00:00
and SCORE 00:00:01, each bound to its own actual source call. Replacing the score
clock with the news clock fails verification.

All 47 independent provenance/semantic tests pass. They cover both pinned parent
corpora and lineage rebinding, exact mode/stage/input/output identity, actual
launch/CPU/date/time/controller/observer evidence, raw port/planet timestamps,
zero-column/public phase/console disagreement, physical/score conservation,
persistent mines and raw pointers. All 4682 archive hashes and 47 completed mobile
controls / 22 REA observations verify. No new helper caller, native byte query or
provider installation was required. Both historical parent corpora are unchanged.

README, plan, evidence report, byte-preserving attributes and portable CI are
updated. This is acquisition research, not a new before-only model. Production
Go, dependencies, save 35 and generation fingerprints are unchanged. Full Go,
terminal/build/live BBS/native Windows acceptance is not newly claimed. The
follow-up is prepared separately from PR #98; the branches for PRs #97/#98 remain
unchanged. Next compose the two added children before-only with measured days 309/310
and their selected foreign-defense/publication contexts.


## Before-only replay of both added survivor days (2026-11-06)

The five-day API now accepts one exact original three-file world and five typed
source-clock inputs, computes the November 2–4 prefix with its established
combat/clock profile, then passes that modeled six-file object into November 5
and its modeled result into November 6. All 144 new-child comparisons / 864 files
match byte-for-byte; all 1182 independent new-stage helper/final RNG witnesses agree.
Prefix witnesses also agree, without counting their targets again. Core synthesis
opens only immutable original YTMAINT; target files are first read after all five
days exist. Captured child files, raw RNG states and cache arrays are not inputs.

The new selected fatal sector-defense path composes the original shared-pursuit
write at 788c–788f already recovered by the occupied caller. It derives eighteen
November 6 battles and 2533 Xannor / 3491 Mercenary casualties, followed by four Mercenary
activations preserving 93846 without invented second loss. Raw printed 1/0 casualty
columns remain separate from capped physical losses. Earlier stale pointer 109
normalizes from modeled physical ownership, reallocates to 328 / 2, and later raw
aliases 1436 (groups 2/19) and 2369 (groups 13/15) remain authentic. Persistent mines are
not erased or deposited again on no-hop paths. Neutral November 5 NEWS 00:00:00 and
SCORE 00:00:01 are separate explicit admitted calls. All five auxiliary files,
physical score columns, inactive ranks and journal rotations match completely.

All 63 new tests pass: four port, four planet, seven auxiliary, nineteen NPC and
29 five-day properties. Tests enforce complete-chain-before-target ordering,
actual object/marker handoffs, all helper/final witness corruption checks,
poisoned captured-RNG independence, unknown world/array/date/caller admission,
exact mixed-prefix selection, distinct clocks, fatal pursuit and phase accounting.
The historical combat 27 and clock 28 chain tests pass; reused chronology evidence
verifies 332 controls / three native reads. No runtime capture, provider installation,
native byte query or historical corpus rewrite was needed for this model step.

README, plan, linked reports and portable CI are updated. Production Go,
dependencies, save 35 and generation fingerprints are unchanged. Full Go,
terminal/build/live BBS/native Windows acceptance is not newly claimed for this
research-only update. The follow-up is prepared separately from PR #99. Selected
mixed hazards/resource pickup and general MBF remain separate admission work.

## Gateway mine, defense and pickup acquisition (2026-11-06)

Six explicitly edited copied-world fixtures now select Mercenary mine damage,
planetary fighter pickup, guarded offense and fatal mine aftermath. All 72 original
DOS runs naturally completed on the first acquisition. Twelve stage groups agree
across six modes: 360 nonreference file comparisons, zero differences, with 432
complete output files. An indexed Git export with automatic line-ending conversion
also passes the complete pinned audit. The exact lineage audit distinguishes 396 unchanged input
links (180 first-stage side files and 216 complete second-stage files) from 36
explicit fifteen-edit YTDATA transformations. No second-day fixture edits occur.

Independent verification reconstructs each transformation, proves the gateway's
strong connectivity and sole predecessor, authenticates launch/controller/CPU and
source clocks, qualifies all 36 observed streams and checks public/console order,
physical/score conservation, mine residue, stock and zero-bank ground economy.
The fatal three-mine case still calls source helper2/4aa4 three times after its
first mine kills M1. Zero starting production rates become one after day one;
day-two production adds three fighters. Offensive losses inferred from stamps are
labeled observed rather than independently predicted RNG results. Exact raw zeros
and original receipt typos remain unchanged.

All 34 independent regressions pass, including forged fixture/graph/handoff,
source callback counts, public/physical disagreement, hidden ground changes and
zero-survivor offensive winners. The winner regression failed with the prior
non-strict admission and passes with the positive-survivor guard. The reused
complete 3462-byte original Mercenary source packet and all 4682 archive hashes
verify. The frozen corpus has 1974 files / 17257301 bytes, manifest
fff8758c16f18302ceda4115c1960f4bc859a3bd5333a29df1b5da3b70aa8e90.

README, plan, report, portable CI and byte-preserving attributes are updated.
This is research acquisition, not before-only integration: next compose these
declared fixtures from a modeled November 4 parent. No production Go, dependency,
save-35 or generation-fingerprint change is included. Full Go/terminal/build,
live BBS and native Windows durability acceptance are not newly claimed.

## Before-only gateway hazards and fighter pickup (2026-11-06)

All six explicit gateway fixtures now synthesize from the original Mercenary100000
three-file before-world, five immutable source-clock inputs and a declared case.
The established three-day combat model returns the actual November 4 parent;
a pure function applies exactly fifteen declared data edits once. The first new
child consumes that object, and the second consumes its complete returned six
files without further fixture intervention. All five days are modeled before
comparison reads targets. Only immutable original YTMAINT may be opened by core
synthesis; observation, parent/child capture and target reads are forbidden there.

All 216 complete new-child comparisons / 1296 files match, with 1962 independent
helper/final RNG-state witnesses checked across three observed streams per case.
Prefix witnesses also agree and are not counted as new targets. Poisoned captured
RNG fields cannot change typed inputs or outputs. Raw zeros, mine residue,
pre-pickup force stamps, public text and separate publication clocks are unmasked.
Original helper2/4aa4 count-two shrinking draws derive mine losses 712/518 and the
fatal first hit; all three initial mines still call the helper after M1 dies,
leaving two unspent mines. Guard victories derive losses 34/40 and continue the
route without pickup. Neutral pickup grants exactly 37 or zero, preserves ground
and title, and stops at the physical gateway. No second-day pickup is invented.

The source minimum-rate clamp runs after production/growth and before eager
planet event draws. Initial rates zero preserve day-one stock, then clamp to one;
next-day production adds three. The auxiliary audit independently derives stock
production from modeled before rates/date/minute values. Both guarded November 5
scores use their measured 00:00:01 call while NEWS uses 00:00:00. Other new
publication clocks remain midnight. All physical scores and journal rotations
match and private mail remains empty.

All 51 new tests pass: four port, eight planet, thirteen Mercenary, thirteen
auxiliary and thirteen complete-chain properties. They cover exact records,
source arithmetic/order and mine callback count, malformed/unmeasured inputs,
positive combat winners, stock/physical ledgers, object-identity/marker handoffs,
fixture purity, source caller/clock validation, core read bans and every helper
and final RNG witness. The prior combat 27 and survivor 29 tests pass unchanged.
The reused complete 3462-byte native source packet and all 4682 archive hashes
verify. No new native query, emulator capture, provider installation or historical
corpus modification was needed.

README, current plan, linked report and portable CI are updated in this milestone.
Production Go, dependencies, save 35 and generation fingerprints are unchanged.
General MBF, arbitrary inputs, occupied-origin departure and friendly-force
merging remain separate bounded research. Full Go/terminal/build, live BBS and
native Windows acceptance are not newly claimed. This replay follow-up is
separate from open PR101's acquisition milestone.




## Surviving defender receipt review fix (2026-11-06)

PR #100 review finding 4493758440 was reproduced: increasing each of eighteen
surviving Mercenary defender counters by one or by 5000 passed the old receipt
validation (36 erroneous admissions). The new regression fails before the fix
and passes after requiring the printed surviving-defender counter to equal
initial minus remaining force. Only the defeated attackers retain capped raw
losses. The complete survivor auxiliary suite and five-day native replay pass;
README is updated. No captured evidence, production Go or save format changes.


## Expanded maintenance CI budget (2026-11-06)

PR #99 job 127946431806 and PR #100 job 127958832764 explicitly exceeded the
40-minute whole-job limit. Both completed race/vet, season CLI and all preserved
research evidence checks; the terminal step was cancelled and release packaging
was skipped, so neither run is counted as passing. The complete validation job
now permits 60 minutes. Only that budget changes: all commands, actions, pinned
dependencies and the independent 10/20-minute campaign budgets remain unchanged.
README's current CI limits are aligned. New-head CI must pass before merging.


## Gateway pickup rejection review fix (2026-11-06)

PR #102 finding 4494354410 was reproduced for three unsupported force/stock
combinations: the old direct pickup helper raised after clearing caller-owned
stock. The new regression fails before the fix and passes after calculating
and validating the final force before any world write. An exact 100000-fighter
result still transfers stock successfully with the original raw zero. The
complete gateway Mercenary/auxiliary suites and 216-comparison/1296-file replay
pass; README is updated. No captured evidence or production Go/save changes.

## Occupied-origin departure and friendly Mercenary routes (2026-11-06)

The primary acquisition contains 96 completed original-DOS runs / 576 outputs,
eight explicit two-day fixtures with six modes per stage. Independent verification
reconstructs all 48 sixteen-edit YTDATA interventions and distinguishes them from
528 unchanged input links (240 first-stage side files, 288 exact same-mode child
handoffs). Original guests and all historical corpora remain unchanged. The graph
preserves all-sector reachability, the source's forced first successor and sole
predecessor. No second-stage repair or hidden data mutation is admitted.

Actual occupied-origin holds and departures, silent friendly merging and a larger
Wanderer-stock transfer are selected. The successful friendly case moves97337,
absorbs37 without a public merge receipt and saves97374; source8472 clears the
consumed successor while distinct859e clears departure. Next-day actual combat
loses one. Other friendly37 cases lose that group to the earlier Xannor phase;
those are interference controls, not successful merges. The four-second single
force takes189528 whole Wanderer fighters from source-grown189528.296875, clears
the entire stock and saves286865. The fractional0.296875 discard is disclosed as
a bounded observed conversion. The two-second second day reconciles2837 earlier
Mercenary losses, then5973 mine losses and9 offensive losses, saving88518.
Source-clock, public/console, stock/physical and scoreboard ledgers all verify.

Fourteen of sixteen stage groups have exact six-mode outputs. The occupied-friendly
second-two profile retains89 world-byte differences on day one and94 on day two,
only in source-clock/derived supply fields of the disclosed port records. Both
cohorts agree internally; other five files and all NPC outcomes match. All480
nonreference file comparisons are retained,474 equal and6 unequal; normalized
bytes=0. Direct source clocks and saved-clock corroboration are labeled separately.
This is not a claim of full observer neutrality or zero overall mismatches.

Two incomplete observed attempts are retained separately: attempt-a lacks its
asynchronous flush acknowledgement; attempt-b has a matching acknowledgement but
fails the immediate post-detach liveness check, then records exited=true without
forced termination. Neither is counted as a completed observed control. Six valid
partial-case runs remain supplementary, with all36 outputs matching the final
first-child controls. A new exit-only synchronous receipt checks actual trace
UTF8 byte count, canonical schemas, event/error/drop counts, natural exit and
fresh paths. Optional delivered acknowledgements must agree. DOS acquisition
prefix and exit-hook suffix remain byte-identical, and original deadlines/owned
cleanup remain enabled. This addresses acknowledgement persistence; no general
liveness-race repair is claimed. The entire final two-day case completed twelve
fresh runs under that protocol. Total retained acquisition:102 completed runs and
two invalid observer diagnostics.

All 30 independent evidence regressions and17 portable receipt-protocol tests pass.
They cover fixture/graph reconstruction, unchanged inheritance, clocks/callers,
physical/public accounting, raw departure/merge/pickup zeros, actual casualty
splits and stock conversion, explicit nonneutral-byte disclosure, missing/partial
receipts, conflicting messages, failed controllers and explicit diagnostic paths.
Both frozen corpora also pass the complete audit after indexed Git export with
automatic line-ending conversion. The reused3462-byte original native packet,
41 completed primitive Mercenary controls (plus their separately classified
capacity timeout),11 REA observations and all4682 archive hashes verify.

Primary manifest7a54595bfed7291f09e0f249a87023bce449fd1d16bcd30f77b3fca1cea1c129
pins2641files/23051965bytes. Diagnostic manifest
0bc0e2d64b84741e0821fab41fbe553dc29861677ab22b24082828ed7db0306e pins214files/
1798197bytes. The authored failure classification was corrected before publication
to distinguish the two actual controller errors; raw captures were unchanged.
Executed old/new source snapshots are retained. README, current plan, report,
byte-preserving attributes and CI are updated. This is research acquisition;
before-only integration with actual nonneutral clock admission remains next.
No production Go, dependency, save35 or generation-fingerprint change is included.
Full Go/terminal/build, live BBS and native Windows acceptance are not newly claimed.


## Verified maintenance prerequisite merges (2026-11-06)

PRs #97–102 were merged in order after current-head checks and review feedback
were clear. Actual GitHub merged states and all six merge commits are verified
ancestors of fetched `origin/main`:

- #97: `0b21842b60d5d8b248dd05562b24795f7666ca27`
- #98: `6d15f9d79b2fd690a19c38dd43521f01521eafda`
- #99: `1977e1d25cec946b3becdc3a4f6b77c2ba99e2e0`
- #100: `003d325a9d10a1a53363eabba4e34060d726dbd3`
- #101: `c8fba0c4f2c46c334abb7c3a1f588de355e8a76c`
- #102: `72777884f1e87cba739c162323645c16df272570`

The final main tree is byte-identical to validated prerequisite head3ba39f65.
The departure/merge research branch integrates that ancestry and updates only
README/plan/validation status; its capture, verifier and protocol code is unchanged.
PR103 now targets main and remains a separate open research change.

## Before-only occupied-origin departure and friendly merging (2026-11-06)

Eight measured departure fixtures now synthesize from the original occupied
Mercenary100000 three-file before-world, five typed source-clock structures and
one declared case. The established November2–4 prefix returns the actual modeled
six-file parent. A pure sixteen-edit transformation applies once, preserving the
other five files; both new children then use complete modeled handoffs. All five
days exist before expected targets are first opened. Core file-read bans permit
only original YTMAINT constants/literals; no captured handoff, transcript, recipe,
cache array or observed RNG state enters synthesis. Poisoning rng_raw witnesses
cannot change source inputs or results.

All48 direct observed-source comparisons /288 files match exactly and all2505
independent new-stage helper/final RNG-state witnesses agree. Prefix witnesses
also agree without being counted as new targets. The complete all-mode report
retains288 comparisons /1728 files:270 complete comparisons are exact;18 cross-
cohort comparisons preserve the existing89/94-byte port-clock/supply differences.
There are1710 equal files,18 unequal YTDATA files and1647 differing byte
comparisons across those targets. The full raw inventory is retained, normalized
bytes=0. Complete matrix, unique difference positions, observed-cohort equality,
all other files and every byte outside disclosed port writer fields are required.
No target-saved unobserved time is substituted into the model.

Derived source behavior includes occupied-origin holds/departures, silent
friendly37 absorption, mutable descending reactivation, actual empty Union1/4
route transit, earlier Xannor/Mercenary defense and later mine/offense ordering.
The successful merge saves97374, then next-day offense costs1. The two-second
second day starts97337, loses2837 earlier,5973 to mines and9 in offense, saving88518.
The Wanderer economy produces189528.296875 stock; bounded whole conversion grants
189528 and full stock clear discards0.296875, saving286865. Half-or-larger fractions
remain explicitly rejected pending runtime qualification; general floor-versus-
nearest behavior is not claimed. New physical/score bounds400000 are isolated
from historical APIs. Empty Union transit and the larger score denominator were
independently reproduced as integration admission failures before their narrow
new-profile corrections. Depart/merge/stock zeros, literal casualty branches,
strict surviving-defender counters, physical score totals, separate NEWS/SCORE
clocks and complete journal rotation all match.

All67 new tests pass:6 port,9 planet,19 Mercenary,18 auxiliary and15 complete-chain
properties. They cover actual object/marker handoffs, exact independent fixture
reconstruction, read bans, raw clocks/callers, poisoned captured RNG independence,
every helper/final witness, source arithmetic and unknown-context rejection,
no writes on rejected transfers, bounded fractional discard, silent merge/public
ledger conservation and explicit nonneutral comparison integrity. Historical
13 gateway and29 survivor record tests pass. The complete3462-byte original
native source packet and all4682 archive hashes verify. No new emulator capture,
native byte query, provider installation or historical corpus rewrite was needed.

README, plan, linked reports and portable CI are updated. Production Go,
dependencies, save35 and generation fingerprints are unchanged. Remaining work
includes ambiguous whole-number runtime conversion, friendly-plus-planet-stock
composition, general MBF and other unmeasured branches. Full Go/terminal/build,
live BBS and native Windows durability acceptance are not newly claimed.

## Positive fighter-stock whole conversion (2026-11-06)

Twelve exact binary stock fixtures now isolate the Mercenary planet-pickup
conversion from the verified November 4 evolved parent. All 72 original-DOS runs
completed naturally on their first attempt, yielding 432 complete six-file outputs;
all 12 fixture groups are six-mode byte-equal. Independent reconstruction binds
360 unchanged first-input links and 72 explicit YTDATA transformations, all fifteen
ordered edits (including no-op assignments), the reachable forced gateway graph,
per-mode parents, launch/CPU/date/time, guest/host identities and complete source
clocks. No byte is normalized and no failed attempt or retry is omitted.

Native pickup converts positive SINGLE stock using INT/floor. Subunit values
clear without taking-zero text; 1.5 gives 1 and 2.5 gives 2. The single values on both
sides of 189528.5 all give 189528; 189529.5 gives 189529. The single below 1 gives 0,
the single above 1 gives 1, and 32767.5 gives 32767. All transfers agree with physical
force, public/console receipts, exact full-stock clear `00008000`, minimum-rate clamp,
ground production, journals and scores. Fractions are discarded. Source force
97337 remains the receipt's actor stamp, while the actual saved force includes the
whole transfer. Whole-stock clear/save precedes amount addition and positive-only
receipt construction.

The independent static audit reuses four existing native reads in three pinned
packets, totaling 3932 retained overlapping bytes. It binds the actual `3D/03` pickup
call, dispatch to SINGLE INT, backward positive branch and exponent-scaled mask,
plus clear/save/add/receipt order, against complete original MZ LOAD images. No
new REA query or provider installation was needed. The new capture controller
waits at most two seconds for natural PID disappearance inside the existing
30-second deadline, then requires complete persisted zero-exit receipt evidence;
forced or still-live processes fail. All 48 observed/attach-only runs completed on
the first liveness probe; the historical observer and controllers are unchanged.

All 60 new portable tests pass: 25 independent fixture/clock/ledger corruptions,
27 receipt/natural-reap controls and eight native-byte corruption tests. A
coherent nearest-rounded force/receipt/score forgery passes conservation checks
but fails the independently qualified floor classification. The full corpus and
native-byte verifiers pass, as do all 4682 original archive hashes. An indexed
checkout with `core.autocrlf=true` preserves all 2022 corpus artifacts and passes
the complete corpus audit again. Edited relative links and diff checks pass.

README, plan, report, pinned raw corpus, frozen acquisition sources and portable
CI are updated together. The plan's current-main baseline and obsolete mixed-
hazard/resource-pickup deferral were corrected against merged PRs #97–104; historical
validation entries remain dated evidence. This research leaves the replay's
half-or-larger guard unchanged pending separate integration. The separate
friendly-force-plus-planet-stock path remains unmeasured. Production Go,
dependencies, generation fingerprints and save 35 are unchanged. New full Go,
terminal/build, live BBS and native Windows durability acceptance are not claimed.


## Before-only positive-stock conversion replay (2026-11-07)

The twelve qualified stock fixtures now replay from the original three-file
before-world, four typed source-clock inputs and one declared case. The original
November 2–4 prefix creates the complete modeled November 4 parent. A pure fifteen-
edit fixture applies once, retaining the five side-file objects; the complete
November 5 result exists before the comparison loader opens any native target.
Read-ban and marker tests prove that captured handoffs, recipe metadata, cache
arrays, transcripts and observed RNG states cannot supply synthesis data.

All 216 complete comparisons / 1296 files match without normalized bytes. The 36
direct observed-source comparisons account for 216 files; all cross-mode targets
also agree. All 1656 new-stage helper/final RNG-state witnesses agree; prefix
witnesses agree separately. Negative tests poison observed rng_raw values without
changing parsed inputs or results, while the independent witness audit rejects
the poison. The complete comparison inventory and every file's length/hash must
agree; an omitted, duplicated or altered comparison cannot claim success.

Derived behavior includes positive SINGLE INT/floor, full stock clear `00008000`,
entering actor 97337 in public receipts, no taking-zero line, exact fractional
discard and physical force/score conservation. Before-pickup economy preserves
all twelve raw stocks with zero initial rates, then clamps to 1 and grows ground
to 505000. All 36 ordered port clock sets reproduce all 1000 complete records.
New bounded profiles isolate admission expansion; historical gateway/departure
modules and all captured corpora remain unchanged. The old gateway rejects the
same 0.5 input before writes; the new pickup transfers 0 and clears the full stock.
The old Wanderer half-fraction guard still rejects its old unsupported context.

All 54 new tests pass: 11 economy, 17 Mercenary, 15 auxiliary and 11 complete-chain
properties. They exercise unknown stock/force/title/capacity/original-identity
rejection without partial writes, one eager source activation, exact RNG calls,
source-grown ledger derivation, coherent nearest-round forgery rejection, raw
zeros, private/public separation, journal rotation, independent publication
clocks, source-only reads and actual modeled object handoffs. The complete
corpus audit, retained native-byte audit and all 4682 archive hashes pass.
All 28 historical gateway/departure complete-record tests pass as well.

README, plan, linked acquisition/replay reports and CI are updated in the same
change. PR #105 is verified merged as a2f28be8eb6d8b264128964c31623abc959e0828 before
this dependent work. No new capture, native query, provider, production Go,
dependency, generation fingerprint or save 35 change is introduced. General MBF,
arbitrary worlds, friendly-force-plus-planet-stock composition, full Go/terminal/
build and live/native durability acceptance remain separate.


## Friendly-force and planet-stock composition controls (2026-11-07)

Eight explicit fixtures isolate a same-faction physical garrison at the forced
Gateway Cache pickup. All 48 original-DOS runs completed naturally on their first
attempt; all 288 output files are six-mode equal within each fixture. Independent
lineage binds 240 unchanged side-file links and 48 declared data transformations,
all fifteen ordered edits, mode-specific November 4 parents, connected gateway,
unchanged guests, pinned host, actual launch/CPU and complete source clocks.
Thirty-two observed/attach-only captures pass full persisted flush receipts.
No byte is normalized; no failure, retry or forced completion is suppressed.

The local garrison at 3000 is scanned first and holds in every retained case.
No earlier Mercenary casualty or local movement appears. The moving 97337 force
then combines the held 1/37/97337 friendly fighters with INT(stock). It saves
97338, 97374, 97411, 97375, 286902 or 194711 as declared by each exact input. Empty and
half stock clear silently; positive amounts print the combined pre-stock actor
97374 or 194674, not the moving-only count or final post-stock count. No capture
line prints because entering local force is positive. Stock always clears with
source8472 raw `00008000`; the departure force/owner retain source859e raw `00002800`.
Governors 0 and -2 are preserved. Title, link, ordinary economy and public/private
files reconcile with physical force and scoreboard totals.

One retained 3462-byte native observation authenticates 16 code spans and four
original literals against immutable YTMAINT bytes. It binds descending scan,
eager .66 hold gate, entering force cache `7b90`, sector owner/link pickup priority,
full stock clear/save, actor-plus-local-plus-whole save, combined taking stamp,
zero-local capture condition (with its source `7b68` comparison), positive-only
taking and bypass of the ordinary friendly merge. No new native query/provider
was needed. Source behavior is conditional on the garrison still being present;
this recipe selects that condition rather than claiming every clock would hold.

All 33 new tests pass: 24 independent corpus/clock/ledger controls and nine native
contract controls. They reject coherent overwrite/double-count amounts, wrong
pre-stock actors, invented capture/loss events, altered governors/raw zeros,
wrong clocks/callers, incomplete or forced exits and changed source gates. Both
verifiers and all 4682 archive hashes pass. An indexed autocrlf=true checkout
preserves all 1350 artifacts and passes the full corpus audit. Relative links,
compilation and diff checks pass. Historical corpora/controllers/observers remain
unchanged; frozen executed sources are retained separately from validators.

README, plan, linked reports and CI are updated. Prerequisite PR #106 is verified
merged as `c4ef395ea41b86f3097798897e0c49ea4f4d921d` and integrated into fetched
main; its tree exactly matches validated head `7c9c6d5`. Production Go, dependencies,
generation fingerprints and save 35 are unchanged. The current stock replay's
occupied-sector guard still rejects the composition before changing any world
bytes; separate before-only integration of the held activation and combined
receipt is next. Hostile/neutral garrisons, mines, other clocks, negative/nonfinite/
overflow stock and arbitrary-world MBF remain separate. Full Go/terminal/build,
live BBS and native Windows durability acceptance are not newly claimed.

## Departed-garrison stock controls (2026-11-07)

See [bounded native outcomes](../research/yt-maint/DEPARTED_STOCK_CONTROLS.md).
48 original-DOS runs retain 288 six-mode-equal output files across eight fixtures,
including held counter-controls and a separately frozen empty/subunit supplement.
The independent verifier checks pinned originals, fifteen fixture edits, clocks,
observer/flush provenance, receipts, total and per-sector force inventory, stock
clears and later repeated activations. Twelve new corruption/acceptance tests
cover missing activations, wrong actors/capture, double counting, lost groups,
stock clear, altered public output and manifests. This is acquisition acceptance,
not before-only replay, production DOS maintenance, or live BBS acceptance.



## Before-only friendly-force and planet-stock composition — 2026-11-07

Checked acquisition-only PR #107 at d9bfdbfc before implementation. Its native
corpus, source manifests and original observations are unchanged. The separate
explicit profile models November2–4, applies fifteen declared fixture edits to
the actual modeled six-file parent, then derives November5 and every writer.
All 144 complete comparisons / 864 files and 1104 new-stage RNG witnesses agree,
with no target-derived seed, captured-state handoff, normalized byte or omitted
output. The original three prefix days are independently RNG-audited as well.

28 new tests cover core read boundaries, object/marker handoffs, exact fixture
reconstruction, witness-only RNG, joint profile guards, combined actors, coherent
overwrite/double-count rejection, governors, zero/subunit receipts, raw source
clears and atomic failure. All 54 historical stock tests and the 33 acquisition/
native-audit tests pass. All 4682 archive hashes remain unchanged. CI and README/
plan are updated. Production Go, dependencies, QB fingerprints and save35 are
unchanged; no new live BBS or native Windows acceptance is claimed.

[Model, reproduction and remaining boundaries](../research/yt-maint/FRIENDLY_STOCK_REPLAY.md).

## Before-only departed-garrison stock replay (2026-11-07)

The [replay](../research/yt-maint/DEPARTED_STOCK_REPLAY.md) synthesizes a modeled
three-day prefix, applies the fifteen declared edits to its actual six-file
handoff and derives the new day before target reads. All 144 comparisons / 864
files match without normalization; 1152 new-stage RNG witnesses agree. Thirty-three
new tests cover before-only input boundaries, held/departed composition, repeated
activations, derived routes, capture/receipt actors, physical distribution,
coherent duplication/loss rejection, original zeros and atomic failure. Retained
native observations, manifests and frozen acquisition sources are unchanged.
Production Go, dependencies, source fingerprints and save 35 remain unchanged.

Verification: all 115 stock replay tests pass (33 new, 28 held-garrison and
54 historical stock tests), and all 4,682 archived files retain their hashes.
README/plan links and scoped whitespace checks pass. Native acquisition bytes
and nine unrelated local smoke captures are excluded from this replay commit.

## Native neutral-owner and mine-stock controls (2026-11-07)

The [new controls](../research/yt-maint/NEUTRAL_OWNER_STOCK_CONTROLS.md) retain
36 full original-DOS runs / 216 complete six-mode-equal output files. Fifteen
independently reconstructed edits per world account for 36 transformed data
links and 180 unchanged side-file links. Positive neutral fighters transfer once;
mine losses precede entering-force absorption and stock. The four-second fixture
retains earlier Xannor losses and its separate local group at sector 356.

Twenty new tests check provenance and composition, including rehashed metadata/
artifact substitutions and ignored or duplicated faction transfer. The initial
fixture assertion failure occurred before native launch and is retained with its
actual frozen source separately from the completed native matrix. No native
observations were retried or changed. This is acquisition acceptance, not new
before-only replay or production/native BBS acceptance. README/plan and CI are
updated; production Go, dependencies, source fingerprints and save 35 unchanged.

Verification: all 98 stock acquisition/verifier tests pass, including the 20 new
controls; the reused original-byte pickup audit and 4,682 archive hashes pass.
Scoped whitespace and local documentation links pass. Unrelated regenerated
smoke captures and ignored local release candidates remain excluded.

PR #110 ledger review fix: require the next occupied sector below the scan cursor
and reject lower groups left unvisited at completion. The coherent omitted final
activation regression passes (15 auxiliary tests total); the final replay still
matches all 144 comparisons / 864 files and 1152 RNG witnesses. Native observations
and hashes are unchanged.

## Before-only neutral-owner and mine-stock replay (2026-11-07)

The [new replay](../research/yt-maint/NEUTRAL_OWNER_STOCK_REPLAY.md) reuses all six
captured cases without new acquisition or changed hashes. It derives a three-day
modeled parent, fifteen pure edits and the child before reading any after-target.
All 108 comparisons / 648 files and 855 new-stage RNG witnesses agree without
normalization. Neutral transfer, incoming-only mines, stock, earlier Xannor changes
and repeated local activation are source-derived. Thirty-eight new tests cover
before-only boundaries, independent recipe reconstruction, clock/RNG witnesses,
helper calls, owner-transfer accounting, coherent physical-ledger corruption and
atomic failure. README/plan and CI are updated. Production Go, dependencies,
source fingerprints and save 35 are unchanged; this remains bounded research.

Verification: all 154 stock replay tests pass (38 new and 116 historical); the
complete six-case replay, independent pinned native-corpus verification and all
4,682 original archive hashes pass. Scoped whitespace, Python compilation and
local documentation-link checks pass. No native capture or manifest changed,
and unrelated regenerated smoke captures remain excluded.

PR #112 raw-byte review fixes: the independent publisher preserves all four
original governor bytes and requires canonical `00000000` after spent-mine
subtraction. Two new regressions reject numeric-zero aliases across all governor
contexts and the three mine cases. All 20 auxiliary tests pass; complete replay
still matches 108 comparisons / 648 files and 855 RNG witnesses. No native
observation or manifest changed.

## Native defender-survival and uncollected stock controls (2026-11-07)

The [new controls](../research/yt-maint/DEFENDER_STOCK_CONTROLS.md) retain 48 native
runs / 288 full output files across four declared fixtures and two days, all
six-mode equal. Fifteen first-stage edits account for 24 transformed and 120
unchanged links; all 144 next-stage six-file links are exactly inherited. The
balanced control retains its observed one-fighter Xannor survivor. Losing
Mercenaries do not pick up stock; stock produces normally on the untouched next
day and no Mercenary resurrection is invented. The independent audit binds the
exact loss receipt, pinned original literals, physical inventories, governor and
stock bytes, source clocks, flush/lifecycle provenance, scores and full handoffs.
Seventeen new corruption/acceptance tests pass. README/plan and CI are updated.
This is acquisition evidence, not new before-only combat integration or live BBS
acceptance. Original observations/hashes, Go, dependencies and save 35 unchanged.

Verification: all 115 stock evidence-verifier tests pass (17 new and 98 existing),
and all 4,682 archived originals retain their hashes. Complete native controls,
Python compilation, local documentation paths and scoped whitespace checks pass.
Unrelated smoke captures and ignored release candidates remain excluded.

## Before-only surviving-defender stock replay (2026-11-07)

The [new replay](../research/yt-maint/DEFENDER_STOCK_REPLAY.md) reuses all four
existing two-day controls without new native acquisition or changed hashes.
It derives a three-day modeled prefix, fifteen pure edits and both subsequent
six-file days before any target is opened. All 144 comparisons / 864 files and
1074 new-stage RNG witnesses agree without normalization. Thirty-four new tests
check target-read separation, exact object handoffs, independent fixtures,
source clocks/RNG poisoning, casualty/route/winner corruption, resurrection,
raw governor/stock/departure bytes and atomic failure. The public ledger also
independently replays the unit-damage battle RNG, rejecting coherent forged
survivor totals. README/plan and CI are updated; original evidence, production
Go, dependencies, source fingerprints and save 35 are unchanged.

Verification: all 190 stock replay tests pass (34 new and 156 historical), the
complete five-day defender model and independent retained-corpus verification
pass, and all 4,682 original archive hashes match. Python compilation, scoped
whitespace and local documentation paths pass. Existing native captures,
manifests and unrelated regenerated smoke captures remain untouched.

PR #114 review fixes bind battle entry/exit to a source-operation audit and a
separate immutable source-clock/helper/final-state context. The publisher derives
physical-field draws, movement gate and target-helper reseeding before selecting
the battle seed; helper/final witness validation independently binds that context
to the source clocks and surrounding runtime progression. A coherently changed
entry state, gate, casualties, rounds and exit state plus matching forged defender
inventory is rejected. The extinct output also preserves the admitted eight-byte
departure pair exactly; all four second-day canonical-zero substitutions fail.
All 195 stock replay tests pass (39 defender tests), including altered audit,
phase-marker, clock-context and coherent casualty regressions. Complete replay
remains 144 exact comparisons / 864 files with 1074 new-stage RNG witnesses; all
4,682 archive hashes, compilation, documentation paths and scoped whitespace
checks pass. Native observations, frozen sources and manifests are unchanged.

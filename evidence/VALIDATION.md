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

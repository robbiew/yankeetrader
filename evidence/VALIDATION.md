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
reserved slot100 refusal and Wanderer's separate planet/ship destinations. Mines
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

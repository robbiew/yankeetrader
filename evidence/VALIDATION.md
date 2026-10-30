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

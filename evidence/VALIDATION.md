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

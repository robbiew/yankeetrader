# Genesis endgame and safe season reset — bounded research follow-up

This extends the [original Genesis recovery](RECOVERY.md). It adds **24 returned
DOS controls, 48 before/after worlds, two exact parent-world/auxiliary follow-ups
and 13 native byte observations**. It is research and an implementation contract:
**Genesis is not implemented in the Go door, and save version 22 is unchanged.**
No active game or original archive was reset. Every executable ran against copied
fixtures mounted in its own disposable DOSBox directory.

## Questions and evidence boundary

| Question | Status | Evidence |
|---|---|---|
| Eligibility, equality, default/minimum/disabled settings | Answered within tested bounds | `owned-*`, `threshold-20`, `fallback-*`, `disabled-301` |
| Cached versus actual ownership | Answered | `cached-only`, `records-only`; admission and published count use the cache |
| Default/No cancellation | Answered | `cancel-*`, `standalone-*` |
| Scope of successful reset and initial maintenance | Answered for these worlds | Thirteen reset outputs and `first-maintenance` |
| Configuration retention and normalization | Answered for tested fields/values | `custom-defaults`, `lottery-zero`, `cargo-*`, standalone threshold 301 |
| Missing initializer and malformed handoff | Answered for these injected faults | `missing-initializer`, `malformed-marker`, `marker-resume` |
| Winner name and persistent winner history | Partial | Tested LOCAL mappings still announce an empty name; bounded file inventory creates no durable season archive |
| Crash during destructive file rewriting or concurrent DOS callers | Unresolved | No such runtime control; native ordering is static evidence |
| Safe modern reset/session contract | Specified, not implemented | Current Go source audit and requirements below |

The frozen baseline is `fixture-trade-earth`, SHA-256
`faf2c99341bcaceaa37770831d1548e5ebb066642ed146c2c665d679e27d65ca`.
Player record 2 is Q. Each independent recipe explicitly clears native port
ownership, assigns the declared number of **non-Earth** ports to Q, and sets the
cached count and Genesis threshold. It preserves an unrelated `KEEPME.DAT`
sentinel. Other optional declarations cover alias mappings, a scoreboard
sentinel, configuration fields, an omitted initializer and an invalid marker.

The corpus separates thirteen successful resets, six in-game refusals or
cancellations, two standalone cancellations, two deliberately faulted runs and
one maintenance follow-up. All return to a batch-written DOS completion marker
without timing out. A returned fault is not counted as a successful reset.
Compressed raw logs and decoded transcripts, keyboard bytes, date/time, exact
input/output worlds and auxiliary bytes, binary hashes and metadata are retained.
The two follow-ups consume their exact parent's final world and auxiliary files.

Preparatory uppercase-only alias replacements made YT enter new-player
registration instead of reaching Genesis; those incomplete probes are excluded.
The retained case-paired mapping keeps the main game's original entry and adds
its uppercase variant, reaches Genesis, and still produces a blank winner. This
is a bounded negative result, not confirmation of a case-only explanation.

## Admission and published ownership trust a cache

The normal default is **300 ports**, not the initializer's historical printed
450. In-game `G` asks for confirmation and compares player offset 117 with the
effective threshold from configuration offset 105. At 299 it reports one short;
300 and 301 satisfy a requirement of 300. No wealth, score, location or Xannor
victory prerequisite appears in this audited handler.

A configured 19 becomes 200 in memory: cached 199 fails by one, while 200 resets
and writes the normalized setting. A configured 20 permits a reset at 20. Setting
301 disables in-game Genesis even with cached/actual ownership 999. No and blank
cancel without resetting the universe.

The paired controls distinguish two moments:

- `cached-only`: cache 300, actual owned ports zero; Genesis resets anyway.
- `records-only`: cache zero, actual non-Earth ownership 300; Genesis says 300
  short. Normal logout keeps the saved count at zero; its published score also
  reflects that cached count, despite the 300 actual owned ports.

These deliberately inconsistent fixtures establish the missing recount, not a
player-accessible method to forge ownership. The Go implementation must count
current non-Earth port records under the same lock that authorizes a reset.

## Reset contents and configuration

The initializer rewrites the entire 4,151-record, 568,687-byte world: fifty human
slots clear, port owners and treasuries clear, warps regenerate, Earth links to
sector 1, an HQ is selected, and all planet records become inactive. Player
records are byte-exact blank names and zero numeric storage. Inactive planets
reuse the reset header buffer with inactive fields cleared; they are not blank
records. Some native zero cells retain nonzero mantissa bytes with exponent zero.
The verifier retains those bytes and checks semantic layouts rather than falsely
assuming a canonical modern zero encoding.

The regenerated directed map reaches all 3,000 sectors in these controls. Native
port placement can assign more than one port record to a sector; do not infer
unique port placement or perfect reciprocal port links from successful native
initialization. A modern candidate must satisfy its own stronger world validator.

`custom-defaults` confirms retention of 777 daily turns, 31 starting fighters,
4,321 starting credits, 17 starting holds, a nine-day deletion delay, seven daily
lottery plays, and an 850-hold maximum. World geometry and scoreboard path also
retain their configured values in this slice. The old year 7000 becomes **6324**.
Maintenance is backdated to day 296, and ports start with zero stocks and production
timestamps ten days behind the fixed DOS date, day 297.

Retention is not universal:

| Setting/control | Observed initializer outcome |
|---|---|
| Positive daily lottery limit 7 | Retained |
| Daily lottery limit 0 | Changed to 1; a previously disabled lottery is enabled |
| Cargo maximum 4 or 1001 | Changed to 50 |
| Standalone Genesis threshold 301 | Changed to 200, unlike the in-game disabled branch |
| In-game threshold 19 followed by successful reset at 200 | Stored as 200 |

The standalone initializer has its own confirmation: only Y/y continues, while
No and blank preserve the world. It can leave an empty `RMTINIT.TMP` file. This
route is not the same admission policy as the in-game `G` handler.

## Handoff, failure and winner reporting

The exact in-game handoff observed after the missing-initializer fault is:

```text
DORINFO1.DEF\r\n\x1a
```

It contains the command-line dropfile path, not a captured winner record. YT closes
its files and chains to `RMT-INIT.EXE`. The initializer reads and removes the marker
before interpreting that path or rebuilding the world.

With the initializer omitted, YT reports error 53 and returns; the world remains
byte-identical, but the handoff marker and normal login news remain. A linked
`marker-resume` run restores the original initializer and runs it separately.
It resets without a fresh standalone confirmation, despite a scripted No. A marker
is therefore not suitable authorization or a modern transaction/replay guard.
With a marker naming a missing dropfile, RMT reports path-not-found, consumes the
marker and leaves the world unchanged. This proves the tested failure ordering,
not recovery from a crash after truncation has begun.

Native alias code reconstructs the winner through the dropfile and four-column
alias mapping. Neither the original LOCAL fixture nor the retained case-paired
mapping restored Q in the announcement: both news and radio say the prophecy was
fulfilled by an empty name. The original cause remains unresolved for these
fixtures, and native BBS dropfile mappings were not exercised. The modern design
must snapshot the current authenticated player directly, without delegating
identity recovery to a post-reset alias lookup.

The reset replaces today's/yesterday's news, alias mappings and radio messages.
Its aliases become `Dummy,Dummy,Dummy,Dummy`; radio contains initialization
announcements. No winner-history file is created in the retained directory
inventory. `winner-mapping` demonstrates that a scoreboard sentinel remains
**byte-identical** even though its players have been deleted. The unrelated
sentinel remains unchanged. Thus the original reset is neither a durable season
archive nor a complete clearing of public presentation state.

The linked `first-maintenance` advances day 296 to 297, fills Earth's stock to ten
days of production and creates The Wanderer, Mercenary Base and Xannoron. RMT itself
does not perform this maintenance. Native creation of The Wanderer is an observed
fact; the Go source currently reserves its name but has no corresponding active
lifecycle implementation.

## Native byte evidence

YT.EXE SHA-256 is
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`;
RMT-INIT.EXE is
`05f639fe5249ac6ae8e28d8656f4c5e668e40ff08bf66524b109ad31a2217dac`.
Three YT and ten RMT observations were exported from Ghidra and the sessions closed.
The verifier reconstructs each original MZ image and its observed load-segment
relocations, then compares every retained byte. QuickBASIC-aware listings remain
interpretive aids; generic C decompilation can misread runtime inline arguments.

| Target | Loaded address | Bytes | Question |
|---|---|---:|---|
| YT | `0x12728` | 312 | G admission, confirmation and handoff |
| YT | `0x2b25e` | 120 | Configured threshold and fallback |
| YT | `0x29941` | 36 | Cached player count loading |
| RMT | `0x10044` | 294 | Marker, standalone input and early deletion |
| RMT | `0x10702` | 232 | Dropfile/alias winner reconstruction |
| RMT | `0x10888` | 92 | Main-file truncation and year |
| RMT | `0x10918` | 326 | Defaults and maintenance date |
| RMT | `0x12831` | 543 | Header loading and normalization |
| RMT | `0x10bc4` | 419 | Clearing human slots |
| RMT | `0x11cf4` | 265 | Inactive planets and HQ |
| RMT | `0x11dfd` | 92 | Winner news |
| RMT | `0x12017` | 610 | Yesterday news, aliases and radio |
| RMT | `0x12279` | 192 | Completion and program end |

## Modern source audit: why a reset needs new invariants

These are source observations and risk inferences, not a demonstrated attack
against a running reset. There is no Go Genesis/reset implementation yet.

- `internal/store/store.go` binds a login through `ForShip` to player ID and ship
  generation. `internal/game/game.go` starts a new world's IDs at one and ships
  at generation zero. Reusing those values after reset could make an obsolete
  login match an unrelated new player unless a season/epoch is also checked.
- `Store.View` and generic updates call `checkShip`, but spy acknowledgements and
  login-local visibility/spy caches also have direct ID/generation checks. Adding
  an epoch check only to ordinary updates would leave gaps.
- `Store.save` already atomically replaces one `world.json`; a second winner file
  would create a separate commit boundary. Never replace the `world.lock` inode,
  because old and new processes must continue locking the same file.
- `New` sets maintenance to today, so `New(...); Maintain(now)` immediately does
  nothing. It does not bootstrap required faction homes through that call.
- `New` selects unique extra warps through rejection sampling without a strict
  maximum draw count. A reset advertised as finite needs a finite candidate
  permutation/partial shuffle or an explicit bounded fallback.
- News is pruned to today/yesterday and cannot predate the current world's
  creation. It cannot be the permanent winner archive. Current rankings already
  recount actual non-Earth port owners and supply a suitable ownership model.
- The CLI's `-init` refuses overwrite. Starting resources/daily turns are current
  code constants; there is no general saved settings object or persisted old
  generation seed to claim can be carried across seasons.

## Proposed implementation contract

The following choices are explicit modern policy, not recovered DOS behavior.
They define the next implementation milestone without changing gameplay now.

1. Add a monotonic persisted **season epoch**, stable initial value one on legacy
   migration, and reject exhaustion. Capture epoch, player ID and ship generation
   **inside** both authenticated login transactions. Every bound read/mutation,
   logout publication, acknowledgement, cache and pending intent must check it.
   Old IDs may be reused only behind that guard; no attempt should lock all live
   callers to invalidate them.
2. Default to 300 actual non-Earth ports. Proposed configuration uses omission for
   300, explicit zero to disable, and explicit 20–300 thresholds; reject other
   values rather than copying hidden fallbacks. Existing small test universes may
   have an unreachable default; migration must not silently lower it or award a
   win. Recount current owners under the reset lock, never trust a cached count or
   stored score. Keep normal living-ship/encounter mutation guards.
3. Quote the old epoch, authenticated winner incarnation, effective threshold,
   sorted owned-port set, live public score and clock/deadline. Clearly explain
   that Genesis replaces the current universe and removes its players/assets.
   Require a fresh literal **GENESIS**, discarding queued input. Cancellation,
   expiry, ownership/configuration changes or a concurrent reset invalidate it.
4. Archive the winner before discarding the old world: season number, start/end,
   display alias, season-scoped player number, actual port count, threshold and
   live public score. Store bounded `SeasonResults` **inside the candidate
   world.json**. A proposed 128-result capacity must refuse safely when full;
   never silently drop winners. Do not archive identities, passwords, private
   balances/inventories or message contents as public results.
5. Generate a complete unpublished candidate with bounded work. Preserve universe
   size and supported explicit configuration, including omission versus zero for
   `LotteryDailyLimit`. Generate and record a new seed for the new season; older
   worlds' seed is unknown, so do not invent historical seed provenance. Do not
   claim configurable native starting assets/daily turns that Go does not support.
6. Initialize fresh economy and the **implemented** faction homes/state before
   admitting a caller. Complete an explicit bootstrap once, validate every world
   invariant, then set today's maintenance watermark. A same-date maintenance run
   must not repeat bootstrap. Native Wanderer lifecycle and exact DOS generation
   remain separate scope; do not label the existing Go generator fully equivalent.
7. Clear all season-specific accounts, teams, titles, treasuries, cargo, planets,
   mines/defenses, faction/revenge state, radio, battle reports, score caches and
   paid-lottery quotas/sequences. Reinitialize the required fresh faction state.
   Preserve only explicit configuration and bounded prior season results. Every
   new cache/report/confirmation is bound to the new epoch.
8. Under the existing OS world lock, revalidate admission and post-wait clock,
   construct and validate the candidate, append the result and advance the epoch
   in **one** atomic world replacement. Do not shell out to RMT-INIT, remove the
   lock file or use a marker as authority. Any pre-replacement failure preserves
   the old world/history byte-for-byte. Fail closed on invalid candidates.
9. A post-replacement directory-sync warning means the new season and result are
   committed. Return a receipt from that transaction directly: winner, old/new
   season, actual ownership/threshold and reset outcome. Preserve joined terminal
   errors and end the invoking login. An ordinary bound `View` afterward should
   reject that old session; never query it to manufacture the saved receipt.
10. Upgrade all nodes together with a stopped-world backup. Migration establishes
    the new guard/configuration without winning, resetting or inventing history;
    read-only loads do not rewrite. A separate explicit archive export or reset
    administration command is future work and must share these transaction rules.

### Required implementation validation

Cover threshold minus/equal/above, disabled/invalid/unreachable configuration,
forged caches versus real owners, fresh destructive confirmation, cancellation,
post-lock expiry, altered/stale quotes, changed ownership/threshold and two
concurrent eligible callers yielding exactly one archived result and epoch advance.

Reuse the same `(player ID, ship generation)` in a new season and prove that every
old session read/mutation, score publication, radio/battle/spy acknowledgement,
visibility grant and pending confirmation rejects. Pause a login between its
transaction and session binding while another process resets to catch epoch
capture races. New-session access must succeed.

Inject generation/bootstrap/validation/archive/epoch exhaustion, save failure,
post-rename durability failure and joined terminal-output errors. Verify byte-exact
rollback before replacement, committed result/epoch after it, reload/replay,
process interruption and the first new login seeing fully initialized state.
Exercise bounded generation at minimum and maximum supported sizes, both real
terminal interfaces, migration and same-day maintenance idempotence. Native Windows
crash durability and live BBS gameplay remain distinct acceptance work.

## Reproduction and verification

```sh
python3 scripts/recover_genesis_reset.py /private/tmp/yt-genesis-reset-fresh
python3 scripts/verify_genesis_reset.py
python3 scripts/test_genesis_reset_verifier.py
```

Capture requires the existing DOSBox Staging installation; verification is
standard-library Python. The independent verifier reconstructs the declared
inputs and exact parent chains, checks hashes/clock/keyboard/completion/native
bytes, evaluates admission and configuration, validates reset record patterns and
map reachability, and bounds every non-reset world/auxiliary change. Rehashed
semantic corruption controls (42 rehashed attacks) challenge those claims. Frozen
whole-world hashes and complete news/scoreboard witnesses for the single
maintenance follow-up preserve native bytes, including noncanonical MBF zeros
and effects outside the recovered formulas. They supplement rather than replace
semantic checks; this does not establish full maintenance formula parity.

[Fresh DOS corpus](dos/) · [YT native evidence](rea/yt.json) ·
[RMT native evidence](rea/rmt-init.json). The original eight Genesis sessions and
one maintenance run remain historical evidence under the archive and are not
counted among these 24 controls. No Go gameplay/schema change or live reset is
included in this milestone.

# Multi-caller Door32 campaign

## Result

Two retained final campaigns reached a real Genesis victory: Atlas acquired
20 personally owned non-Earth ports by playing commands, confirmed Genesis,
and entered season 2. No credits, turns, cargo, titles or saved world fields were
edited after production initialization. The supported initializer settings were
32 sectors and a 20-port Genesis threshold. This is a bounded campaign, not the
default 300-port endgame or a long-running production BBS acceptance claim.

Six BBS callers were connected concurrently before victory, mixing compact and
classic interfaces with ASCII and ANSI emulation. The identity-reuse run used
10 caller sessions and peaked at 7 live door processes while old and new seasons'
callers overlapped. Each caller connected through a localhost TCP client to a
simulated BBS relay, its own Door32 drop directory, and an independent real door
process over a PTY. All processes shared one save/lock directory. The race-enabled
binary ran on native macOS; this exercises the POSIX Door32 stdio path.

| Retained campaign | Recorded command transactions | Read-only core-state audits | Result |
| --- | ---: | ---: | --- |
| Team victory, seed 145 | 182 | 1014 | Atlas wins at 20 ports; no race logs |
| Identity reuse, seed 146 | 176 | 1032 | Atlas wins; old callers cannot act on recreated IDs |

Universe seeds do not fix login-local disruption or other runtime RNG. The
runner learns observed black-hole entry sectors and replans routes instead of
repeatedly spending all turns on the same hazard. Legitimate forced-warp costs
are retained. Earlier pilots corrected two driver assumptions: blind hazard
routing and assuming every caller reached sector 2 despite a forced warp. Those
were harness errors, not demonstrated game defects.

The current runner permits at most three fresh-world attempts only when an exact
committed black-hole receipt reports zero remaining turns and agrees with the
validated save. Each attempt retains its own complete evidence under `attempt-N`;
the outer `summary.json` records every outcome and identifies the winning attempt.
All three exhausted attempts fail. Timeouts, invariant failures, unexplained nonzero exits,
race logs and forced process cleanup are never retryable. A carrier-loss process
must exit naturally within five seconds. Status zero or status one with only the
CI-observed Linux PTY hangup diagnostic `write /dev/stdout: input/output error`
is accepted; arbitrary errors, signals and joined storage warnings fail. Termination is cleanup
and makes the campaign fail, including during an otherwise exhausted attempt.
The focused Python regressions run in the campaign CI job.

## Confirmed product issue and fix

The pre-fix one-minute Door32 session reached its allowance and closed with
`godoors: no reply from terminal`, misleadingly describing expiry as a terminal
probe failure. The [original terminal capture](multicaller-campaign/expiry-before.txt)
and [failed campaign summary](multicaller-campaign/expiry-before-summary.json)
retain that observation. It had already legitimately acquired 20 ports before
stopping at the expiry assertion.

The input loop checked time before blocking, but did not recheck when a key or
input timeout returned. A focused regression also reproduced acceptance of an
Enter arriving after the deadline. The fix checks the real deadline immediately
after the read, before accepting keys, replaying a saved command or refreshing
an idle clock. Expired normal/secret reads now report session expiry and return
no command. The regression covers timeout, a late completed COLLECT command,
secret input and idle clock behavior. Existing prompt-clock preservation tests
continue to pass. This changes no saved fields or dependency versions.

## Campaign assertions

- Concurrent previews of one unowned port yield exactly one purchase. The
  initial credit ledger loses exactly its 31-credit purchase price.
- A later owner's quote becomes stale when another caller buys the port; stale
  confirmation spends no credits and creates no notice.
- Owned buyouts retain seller-only old-name notices. Other callers cannot read
  them. Ordinary cargo buying/selling occurs through the real port interface.
- Abrupt TCP carrier loss during multiline entry publishes no draft. Reconnect
  uses the same BBS user-record identity rather than a second account.
- Private direct and team text stays out of another caller's history; confirmed
  ALL text is public. Team creation/join uses separately entered masked secrets.
- Nineteen personal titles plus a teammate's title do not qualify. The twentieth
  personally acquired title does. A separate exact GENESIS confirmation resets.
- A real one-minute Door32 allowance expires while a partial equipment command
  is pending. Ship state remains unchanged by expiry; the partial command is not
  executed. (The earlier retained team run tested idle expiry without partial input.)
- Old callers hold a buyout quote and radio draft across reset. After new callers
  recreate player IDs 2/3 and initial ship generations 0, the old nodes still reject
  the ended epoch; the new save is byte-identical before/after stale attempts.
- Fresh players can read the winner history and cannot replay Genesis with zero
  titles. Reset clears old players, teams, messages, public news and ownership.
- Repeated concurrent reads check money/turn/cargo bounds, owner references,
  planet-sector links, bounded journals and monotonic unique message/event IDs.
  No race detector logs, unexplained exits or torn JSON reads were found in the
  retained final campaigns.

## Reproduce and inspect

From the repository, with the supported sibling GoDoors checkout:

```sh
go build -race -buildvcs=false -o bin/yt ./cmd/yt
python3 scripts/simulate_bbs_campaign.py --out /tmp/yt-campaign-new-run --seed 146
```

The output path must not exist. The driver writes drop files and evidence; only
`yt -init` and callers write the game world. It creates no network listener beyond
127.0.0.1 and does not connect to a real BBS or touch existing game data. Every run
waits for the actual one-minute allowance; no clock or session-budget patch is used.

[Team capture archive](multicaller-campaign/team-victory.tar.gz),
[identity-reuse archive](multicaller-campaign/identity-reuse.tar.gz),
[team summary](multicaller-campaign/team-victory-summary.json),
[identity summary](multicaller-campaign/identity-reuse-summary.json) and
[outer hashes](multicaller-campaign/SHA256.json).

Each retained archive contains the frozen executed driver, per-node raw/text
terminal output and input bytes, Door32 files, milestone saves, final world,
command log, source patch, binary hash/build metadata, exit/race outcomes and a
file-hash manifest. The source baseline is private-port-sale commit 91e4c1c plus
the captured deadline patch. The local GoDoors checkout was clean at audit at
`a9ef30d0083a7f00c40b27a273e9f5d49785ed18`; the recorded build metadata identifies
its local module replacement. These are synthetic accounts and team credentials.
The pilot expiry capture predates the frozen-driver manifest and is diagnostic
evidence, not a separate fully pinned replay recipe.

Full Go race tests and vet passed. The strengthened input tests passed again;
Existing startup and idle-clock PTY checks also passed; their incidental captures
were restored. Linux/amd64 and Windows/amd64 cross-builds passed. The new CI job runs the campaign
separately with minimum supported Go/GoDoors and a race-enabled binary, keeping it
out of the existing near-30-minute terminal job. That Linux CI run is not yet
verified locally. Native Windows inherited sockets, production BBS behavior,
Telnet negotiation, WAN conditions, multi-day NPC economy, default 300-port victory,
and all combat/season strategies remain outside this bounded simulation.

## Review follow-up validation

The carrier-loss regression failed before the fix because a timed-out child could
be terminated without failing acceptance. The zero-turn receipt regression also
failed before the fix. Ten focused Python tests now pass, covering natural exit,
forced/abnormal exit in successful and exhausted attempts, exact receipt/save
agreement, invariant failures, bounded retries and non-retryable cleanup failures.
A fresh native macOS race-enabled campaign completed on its first attempt with
177 command transactions, 1,037 state audits, 10 sessions and seven peak live
processes. Atlas earned 20 ports and reset to season 2. No forced stops, race logs
or findings were reported; the executed-driver hash and every attempt-manifest
hash were verified. Focused race-enabled deadline/prompt-clock tests and door
package vet also passed. The follow-up changes only the campaign driver, its tests,
CI invocation and documentation; production gameplay/save format remain unchanged.
New-head hosted CI and production/native Windows acceptance are separate checks.

Linux CI exposed an overstrict status-zero assumption in the first follow-up.
[Separate child stderr capture](https://github.com/robbiew/yankeetrader/actions/runs/41486776920/job/125419120774) confirmed status one was exactly a PTY output EIO
after deliberate carrier loss. The runner now recognizes only that complete
diagnostic, requires natural exit, and retains all other exit/race checks. Ten
Python regressions include rejection of unexplained status one, signals, forced
stops and a hangup diagnostic joined to a storage warning. Repository dependencies
and production transport behavior are unchanged.

With separate stderr capture, the one-minute expiry assertion checks the exact
`session time expired` diagnostic and exit status one after waiting for natural
termination; it no longer expects stderr text on the TCP stdout stream. The
unchanged save assertion still rejects execution of the pending partial command.

Ended-season errors are also asserted on captured stderr with exact status one
and no extra warning text, preserving the byte-identical new-season save check.

The final driver, including separate stderr and exact error-exit checks, also
passed a fresh race-enabled macOS campaign on its first attempt: 174 command
transactions, 995 state audits, 10 sessions and seven peak processes.
The final driver and all attempt-manifest hashes matched; no forced stops,
race logs or findings occurred. New-head Linux CI remains required before merge.

## CI duration follow-up

On head `b9d248e`, Linux campaign check 125422667990 passed. The full validation
job 125422667264 was cancelled by its 30-minute job limit. GitHub's annotation
explicitly reports that limit; every individual step, including formatting,
uncached race tests/vet, preserved evidence, all terminal sessions, cross-builds
and cleanup, reports success, with completion just beyond the allowance.
The full job now allows 40 minutes. The workflow diff was checked to preserve
every command, dependency pin, action and the separate 10-minute campaign budget.
This changes no Go, Python, save, evidence capture or gameplay behavior. Current
new-head CI must pass before merge; the prior cancellation is not a green check.

## Login arrival audit follow-up — PR #73

[Campaign job 125599445595](https://github.com/robbiew/yankeetrader/actions/runs/41539409849/job/125599445595)
failed on head `1794a3e`: Broker reached the team-port planner with zero turns
after reconnect. Production startup calls `StartDisruption` and prints committed
arrival receipts before the first main prompt, but the driver previously only
audited command output. A startup exhaustion receipt could therefore be discarded
and surface later as an unclassified daily-turn assertion.

`Caller.login` now collects startup dialogue through the first main prompt and
records it through the same authoritative receipt/save checks as movement. Only
a committed forced-warp exhaustion receipt matching both saved zero turns and
final sector permits the existing bounded whole-world retry. A zero balance alone,
inconsistent receipt, timeout, world invariant failure or abnormal exit still fails.
No turns are granted, gameplay random draws disabled, or active saves rewound.

Thirteen campaign-driver tests pass. New regressions first reproduced the missing
startup check in both compact/classic prompts, including a receipt before a startup
key pause, and then passed with the fix. Mismatched saves are rejected and an
unexplained zero balance retains the planner assertion. Existing retry bounds,
whole-attempt retention and cleanup/error-exit tests remain enforced.

A fresh native macOS race-enabled run of the corrected driver passed on its
first attempt: 181 recorded actions including all ten logins, 1,000 saved-world
audits, ten sessions and seven peak processes. Atlas reached a 20-port victory
and season 2; no findings, forced stops or race logs occurred. Attempt manifest
hashes and the captured driver hash match the retained files/current driver.
[Full capture](multicaller-campaign/login-arrival-fix.tar.gz) and
[summary with archive SHA256](multicaller-campaign/login-arrival-fix-summary.json)
retain startup output, inputs, exit audits and world snapshots. Linux CI on the
new PR head remains required before merge.

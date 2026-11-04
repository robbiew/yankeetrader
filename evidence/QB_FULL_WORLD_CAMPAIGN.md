# Full QB world: multi-day session acceptance

This campaign exercises the playable `qb36-v1` profile on its full 3,000-sector,
1,000-port world with the **omitted/default 300-port Genesis threshold**. It uses
production `door.Session`, transactional store operations and `RunMaintenance`;
the driver supplies line-oriented terminal input, a controlled UTC game clock and
fixed known login-local disruption locations. Wall-clock deadlines remain real.
It is complementary to the [TCP/PTY Door32 campaign](MULTICALLER_DOOR_CAMPAIGN.md),
not a new native BBS, Windows, carrier-loss or live multi-day transport claim.

The captain starts through normal registration with 1,005 credits and ten holds.
Only session commands buy/sell commodities, buy Earth equipment, navigate and
confirm individual port purchases. The driver never edits saved world files or
grants credits, turns, equipment or ownership. It reads authoritative snapshots
for path/economy planning. When NPCs close the reachable frontier, it purchases
fighters with earned credits and confirms ordinary non-HQ defense combat to
reopen a route; the driver does not remove defenses. Maintenance runs once per simulated UTC date with a
seeded random stream; a second invocation on that date must consume no randomness
and change no game state. Every transition retains before/after/repeat snapshots.

## Verified local result — 2026-11-03

Production base: merged `main` at `e6093d1`; this milestone changes acceptance
code/evidence/docs/CI only. Local Go 1.27.3 used the existing GoDoors review
modfile. The complete campaign passed in 269.77 seconds; the race-enabled door
regression suite and vet also passed. Dedicated CI replay is configured, not
claimed as already completed for this unpublished branch.

| Observation | Retained result |
| --- | --- |
| Source recipe | State `0xc805`, source date `2027-01-01`, verified native source fingerprint |
| Geometry / victory setting | 3,000 sectors / 1,000 ports; Genesis threshold omitted, default 300 |
| Game dates | 2032-06-13 through 2032-06-16; three maintenance transitions |
| Session/command inputs | 1,147 production session logins; 3,510 input lines |
| Earned economy | 111 commodity trading cycles; holds purchased up to 1,000 |
| Ownership | 300 separately confirmed purchases; no granted port titles |
| NPC frontier | One confirmed non-HQ battle; fighters bought with earned credits |
| Daily behavior | All 1,000 port supply snapshots changed on each date; same-date repeats were identical; NPC defenses changed and Wanderer relocated |
| Endgame | Visible 299-port refusal, 300/300 winner receipt, season 2 and source-layout reset |
| Reconnect protection | Same-date asset preservation; old-session write rejected after numeric ID reuse |

The independent verifier passed its positive retained-evidence check and **17
corruption controls**, including rehashed false summaries, altered ownership,
source recipe/history/economy/watermarks, changed daily state, forged driver/
action/receipt evidence and missing manifest entries.

## Acceptance requirements

- Earn the acquisition budget by trading, upgrading to 1,000 holds with earned
  money, then buy 300 non-Earth ports using separate purchase confirmations.
- Replan trade classes after maintenance; the economy can change what ports buy
  and sell. Reserve sufficient turns to park at protected Earth before advancing
  the day, because NPC maintenance can fortify the current sector.
- Use the real 500-turn daily allowance across at least three date transitions;
  observe port economy changes, daily receipts, NPC/Wanderer results and
  same-day idempotence. No direct turn refill is used.
- Reconnect through production session login throughout the campaign, including
  an EOF disconnect/reconnect that preserves identity, credits, holds, cargo and
  remaining turns on the same date.
- At 299 owned ports, require the visible one-short denial; at 300, require fresh
  literal `GENESIS` confirmation and the actual 300/300 winning receipt.
- Require season 2, no old players/assets/ownership, one winner history entry,
  the identical source recipe, source map/port economy/initial HQ and current
  injected-UTC watermarks. Maintenance-altered port classes/rates must reset to
  the source economy, rather than leak into the new season.
- Reject the old bound login, including a write after the same numeric player ID
  is reused by reconnect; the rejected write must leave the new save unchanged.

The fixed disruption draws place both login-local hazards in sector 2999, which
the planner avoids along with mines. It routes around defenses until no unowned
port is reachable, then fights the weakest eligible non-HQ boundary through
normal session confirmations. This lane isolates
maintenance/economy/endgame behavior; it does not establish random hazard balance,
all raw QB seeds, every admitted source date or general DOS numeric parity.

## Evidence and reproduction

The retained [summary](qb-full-world/summary.json) contains actual day/session/
trade/purchase counts and daily receipts. The [manifest](qb-full-world/manifest.json)
pins compressed snapshots, the complete action/receipt transcript and the exact
Go driver embedded into the compiled test. The independent verifier checks hashes,
source provenance, all daily deltas/idempotence and the full before/after reset.
Rehashed corruption tests must reject false ownership, altered recipes/history,
changed reset economy, missing artifacts and repeated maintenance changes.

```sh
python3 scripts/verify_qb_campaign.py evidence/qb-full-world
python3 scripts/test_verify_qb_campaign.py
go test -race -count=1 ./internal/door -run '^TestQBCampaign'
YT_QB_CAMPAIGN_OUT=/tmp/yt-qb-new-run go test -count=1 -timeout 15m -v ./internal/door -run '^TestQBFullWorldAcceptanceCampaign$'
python3 scripts/verify_qb_campaign.py /tmp/yt-qb-new-run
```

Use a new output directory. Ordinary `go test ./...` runs planner regressions but
skips the opt-in long campaign. The dedicated CI job runs the sequential campaign against the pinned minimum
GoDoors checkout, runs planner regressions under the race detector and retains the complete
runtime output as a 14-day artifact, including diagnostics on failure.
The game binary gains no clock override, debug grant or campaign runtime option.

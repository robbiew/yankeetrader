# Before-only replay of the evolved three-day maintenance chain

The measured [convergence chain](CONVERGENCE_CHAIN.md) now has complete before-only
replay. Three independent observation chains each calculate all three days, then
compare each prediction against six paired native targets: **54 complete
comparisons / 324 individual files, zero byte mismatches**. All 4151 records and
five auxiliary files match on every day, including timestamps, fractional assets,
raw zero residues, retained mines and exact public/private output.

This closes the prior three-day integration task. It changes no Go gameplay,
dependencies, `qb36-v1` fingerprint or save **35**. Earlier strict initial,
collision and active-world replay APIs remain unchanged. It is a separate bounded
research profile, not arbitrary evolved-world or general MBF compatibility.

## The modeled handoff is the only continuation input

`synthesize_chain(initial_before, inputs)` accepts exactly the three original
before files and a frozen tuple of three typed clock inputs. The single admitted
initial-world SHA-256 is
`7e470653aabe81d1d3402d8810aca8e2c745e800d0295abcf575d5d7e2a309d3`.
The name/old-news files have their own fixed input identities. Unknown initial
bytes, altered side files, nonconsecutive dates or malformed clock inventories
fail closed.

After day one, the API passes its own **modeled six files** to day two; day two's
modeled six files go to day three. No native child before-world or after-world is
opened, selected by fingerprint, or substituted into this continuation. Expected
files and early-cache probes are first opened only after the entire three-day
prediction exists. A read guard permits only immutable original YTMAINT during
core synthesis; marker/handoff tests separately prove that both children receive
the actual modeled objects.

Clock extraction authenticates original source frames while discarding every
captured `rng_raw`. Inputs carry separate per-port and per-planet dates/raw
TIMER-minute samples, optional home-creation clocks, text clocks and chronological
source-labelled helper TIMERs. Actual captured loop indices bind each planet's
DATE/TIMER pair to its physical record. Missing, reordered or falsely attributed
clocks fail. An absent creation clock remains explicit `None`; it is not filled
from another date or used to decide whether a home exists.

Every RNG advance and reseed is calculated from startup. All **501 independent
helper-entry/final-score raw RNG witnesses** agree afterward. Poisoning those
witnesses leaves the extracted inputs and outputs unchanged and makes the audit
fail. The modeled parents also predict all **480 captured source-owned cache
fields**, checked against each of the three observation chains (**1440 field
comparisons**). Cache probes never seed, patch or guide the calculation.

## Evolved port and planetary economy

The new port writer retains the original wider stock sum and single-precision
production product. Surplus rate promotion uses that wider sum before the final
record stock conversion. Rounding the sum early can change raw output bytes.

The first day remains the initial ten-day capped update. On each following day,
all **3000 commodity rates** promote from one-day nonempty stocks. The source's
first-maximum class rule and coefficient magnitudes remain intact; classes stay
346/336/318. The small-rate port event gate consumes no RNG. Only the measured
consecutive-day, zero-treasury/asking-price context is admitted; arbitrary owned
ports, rollback recipes or selected port plague are rejected.

Four heterogeneous planets now receive ordinary economy before NPC processing:
Wanderer, Convergence Haven, Mercenary Base and Xannoron. Their prior inventories,
banks and source time fields remain inputs. The source details needed for exact
bytes include:

- base fighter production truncates the sum of old cargo rates;
- bank bonuses use the old bank, before interest;
- individual bonus/rate/stock assignments retain their single-precision order;
- interest and ground apply integer floor after the source single conversion;
- surplus stock can replace a cargo rate before natural growth;
- negative/over-ten-day elapsed intervals take the original ten-day catch-up cap;
- three eager event draws occur per active planet, even when no event is selected.

These recover selected inherited home records and bank/stock paths, including
fractional weapons/inventories. Unknown active planets, human assets, inherited
field layouts, unbounded numeric contexts and selected event damage fail closed.
This is not a replacement for general MBF arithmetic or a claim that every
rounding boundary has been recovered.

## Existing homes, convergence and persistent state

Wanderer movement clears its actual old link before searching. Existing slot 1
retains its post-economy record; restoration runs only when no reference exists.
The common owner/bank aftermath remains outside that conditional branch.

Xannoron likewise skips construction and its creation clocks when its HQ link
already exists. **Its later ground-increment draw still runs.** Ordinary economy
produces ground 520/807 on days two/three; the source's common RND increment adds
4/3, giving the actual 524/810. Treating all three initial home draws as a single
creation-only block would shift every later helper state. Existing Base lookup
also bypasses restoration/placement clocks and preserves the evolved record.

Before-only cache normalization loads the first day's actual 6552-fighter
converged force once. Seventeen emptied duplicate entries need allocation the
next day; none need it on day three. These counts arise from modeled pointers
and physical forces, not from the observed helper inventory. That inventory is
checked as calls occur. The third day's same-origin fallback rejection naturally
requires one additional helper call.

Mines deposited at 1169, 439 and 474 are carried forward unchanged unless a
source writer acts. The measured routes do not enter a damaging mine encounter;
new mine/foreign-defense/planetary combat remains outside this peaceful chain
profile. Physical Xannor force stays 10000 and scoreboard score stays 1000000.
Eager desertion draws count physical deployments, not duplicate pointers.

News uses actual modeled creation flags: the first day publishes restoration
messages, and the children do not repeat them. Names retain their exact bytes,
yesterday's news is the current input public journal, private mail remains empty,
and inactive rank -1 is inherited normally. News and scoreboard each use their
own text clock: day one's scoreboard is **00:00:01** while its news says
**00:00:00**. No common display time is substituted for those distinct samples.

| Day | Helper 1 / helper 2 | Calculated draws | Final RNG | Home creation |
|---|---:|---:|---|---|
| November 2 | 42 / 19 | 26678 | `dba78b` | Wanderer, Xannoron, Base |
| November 3 | 41 / 17 | 25693 | `e62250` | None |
| November 4 | 42 / 0 | 26976 | `2d47e5` | None |

These values are calculated outcomes, not configured budgets or captured seeds.

## Source evidence and validation

Existing original-byte observations cover port/economy writers, Wanderer
movement, the common Xannoron ground increment and cache/writeback. The new
[153-byte REA/Ghidra read](evolved-replay-native/rea.json) fills the existing-Base
lookup/skip gap at **0x14128–0x141c1 exclusive**:
`ev_595cbc661571a691b968d1ba600ce81bc7c08cc8a34003ed98062abfaf0bda63`.
Packet SHA-256:
`d63718fd9f35e8a04fa7e12b51cb40eb179319e513db2f6c0525d556072c337b`.
An independent verifier reconstructs every relocated byte from original YTMAINT
SHA-256 `8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6`.
This static read is not a new execution trace. CLI analysis used an existing JDK
via per-process environment and closed normally; no installation/configuration
was changed. All 794 retained chain-corpus files and prior pins remain unchanged.

All **100 new tests** pass: 18 ports, 22 planets, 24 auxiliary, 30 full-chain and
six native provenance/byte methods. They cover exact repeated predictions,
modeled-only handoffs, target/cache read exclusion, witness poisoning, precise
fractional writers, source record attribution, unknown inputs/branches, immutable
clock order, optional creation paths, physical conservation, inherited fields and
accurate side-file publication. README, plan and portable CI checks accompany
the completed research profile.

```sh
python3 scripts/verify_maintenance_convergence.py
python3 scripts/verify_maintenance_evolved_replay.py
python3 scripts/test_verify_maintenance_evolved_replay.py
python3 scripts/test_replay_maintenance_evolved_ports.py
python3 scripts/test_replay_maintenance_evolved_planets.py
python3 scripts/test_replay_maintenance_evolved_aux.py
python3 scripts/test_replay_maintenance_evolved_records.py
python3 scripts/replay_maintenance_evolved_records.py \
  --output /tmp/evolved-chain-replay.json
```

Portable replay launches no emulator, Frida, Go application or network operation.
No runtime capture was rewritten or newly acquired to make the model fit. Next
integrate the separately captured [evolved clock/date controls](EVOLVED_CLOCK_CONTROLS.md),
then admit only their verified new branches. This three-day midnight recipe does not establish arbitrary
calendar/economy combinations, active-player maintenance, general MBF, DOS save
conversion, live BBS acceptance or native Windows durability. Research work guards
are not claims that the original program had finite combat or retry budgets.

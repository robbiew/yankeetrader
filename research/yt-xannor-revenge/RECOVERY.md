# Xannor revenge and cloak candidate-search research

This slice preserves **53 completed original-DOS maintenance controls**, **three
normally exited player-command controls**, paired before/after worlds, an exact
next-day chain, private/public side files and **23 complete REA byte observations**
from YTMAINT, YT and BRUN30. It recovers the revenge producer/consumer, candidate
search and top-player overrides. This research introduced no Go gameplay or schema changes. The subsequent
[bounded implementation](IMPLEMENTATION.md) now enables revenge in save version 17.

## Finding ledger

| Question | Recovered result | Evidence and limits |
|---|---|---|
| What queues revenge? | Defeating HQ sector fighters writes the victor's player-record ID to sector 21 field 105. | Three player-command controls; YT HQ reward writer and fighter/missile/plasma call sites. Missile/plasma callers are static-derived. |
| Is it a victim list? | One slot; a later write overwrites the previous ID. | Direct assignment/PUT, not a multi-victim queue. Overwrite ordering is static-derived. |
| Does any Xannor kill queue it? | A non-HQ sector victory does not in the new control; an HQ loss does not either. | Ordinary fighter commands; no recovered mine/mobile-casualty trigger. |
| When is it activated/consumed? | A positive pointer is read; live sector>7 activates. Positive pointers clear even if activation fails. Zero/negative pointers skip the clear. | Sector0/7/8, negative, dead and unnamed victim controls. No out-of-range GET experiments. |
| Which position seeds revenge? | Live sector controls the flag; cached victim position initializes preferred target. | Named/unnamed worlds distinguish live flag from missing cache. |
| How many candidates? | One ordinarily, at most25 in revenge mode; existing preferred state can terminate after one. | Native control flow and model draw accounting; native RNG call counts were not instrumented. |
| What qualifies? | `(fighters>1 && owner!=-1) || planet_ref>1`; otherwise scan cached players. | Force1/2, owners0/-1/-2/human diagnostics plus static predicate. Dense planet-reference controls have earlier-phase interference. |
| Which cloak comparison? | Candidate discovery is strict `RND>cached_cloak`, or revenge bypass. Top hunting and ordinary interception allow `RND>=cached_cloak-.33`. | BRUN operand/flag tracing establishes exact ties; no captured native exact-tie execution is claimed. |
| Does revenge ignore combat cloak? | No. Selection bypass and later ordinary interception are separate. | Cloak0 arrivals fight; diagnostic cloak10 arrivals do not. |
| Who do groups16–20 pursue? | During revenge16–19 use the preselected top/fallback sector;20 always uses it. HQ-return override runs last. | Distinct victim 250/top 260, protected/hidden/dead top, low-HQ and clock controls. |
| How is the top chosen? | Greatest positive named stored score, strict improvement; earlier equal-score record wins. | Equal/unnamed/no-score/dead top controls plus byte evidence. |
| Are all loops bounded? | Player scanning and1/25 attempts are finite; initial same-location fallback rejection and protected-sector reactivation have no recovered cap. | Static back edges; the new completed matrix avoids protected-sector retry stalls. |

## Artifact and fixture identity

The executables are unchanged:

- YTMAINT.EXE SHA-256 `8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6`.
- YT.EXE SHA-256 `c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
- BRUN30.EXE SHA-256 `3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8`.

The maintenance fixture derives independently from the preserved mobile baseline.
Its SHA-256 is `bf34079e27215d2c086ec750fc2b4fd30d90d4c869eb0bb26227d654a0292bc9`.
Q occupies player record 2/sector 250; HQ is 1114 with1,000,000 fighters, and all 19
mobile slots have 100 fighters in distinct sectors 100/203–220. Non-Union outgoing
warps are removed so printed missing-path destinations expose selection without
ordinary movement, combat or helper pursuit writes. Two arrival controls restore
routes to250. Initial stored score 4000 prevents allocation/low-HQ interference;
selected cases explicitly change it. Every world mutation is declared and rebuilt
by the verifier. Actual maintenance RNG remains native, not replaced.

Maintenance controls set DOS date 10/25/2026 and time 00:00,04:00 or08:00, recording
both clocks before running. The child uses the parent's exact saved world on
10/26. Stored score publication changes the next day's score, so that child is
not an identical-score RNG replay: it also demonstrates pointer consumption
surviving an ordinary subsequent daily run.

Player-command controls copy the archived surrender fixture's **before** world,
original LOCAL/YT/BRUN binaries, XANNORHQ.TXT and the research keyboard feeder
into fresh mounts. They set 10/24/2026 midnight, run ordinary attacks and answer
both HQ and exit pauses. Initial exploratory sessions that timed out before a
normal exit are excluded. All three retained sessions return to LOCAL normally.
Original archives and live BBS worlds are never executed in place.

## Revenge creation, persistence and consumption

The YT reward helper `1f42:a7de–a9b5` displays XANNORHQ.TXT, awards the million-credit
HQ bonus, then writes the current player ID to record `playerBoundary+21`, field 105
(`a978–a9af`). In the standard layout that is record 72/offset105. It is a single
pending victim, not a saved target-sector cache or a list. Victory text alone can
precede the write: the original HQ text pause comes first. Later
[reward research](../yt-xannor-hq-reward/RECOVERY.md) confirms that the pause can
finish on a key or timer expiry; a key is not strictly required.

The new `xannor-hq-win` control defeats a one-fighter HQ in sector 100, receives
the bonus and saves pointer 2. `ordinary-xannor-win` defeats the same force at100
while HQ remains 1114 and saves 0. `xannor-hq-loss` commits one fighter against a
million at HQ 100, leaves the defenders and saves 0. These distinguish location
and actual victory without inventing revenge from every Xannor casualty.

Fighter call site `main:1248–1272` and missile site `sub:72e3–731b` require zero
remaining sector fighters, the HQ sector and prior Xannor owner. The plasma site
`sub:b05f–b083` checks zero force and HQ but has **no recovered owner==-1 guard**.
That looks capable of rewarding/queuing after another faction's HQ-sector force
is destroyed. This is static-derived, not a newly executed plasma exploit.
Modern code must keep actual faction ownership authoritative. No producer was
found for planetary title/ground destruction or attributed mine kills. The
bounded search covered the three annotated YT modules and literal field 105
writers; dynamic/bulk writes and all action variants remain outside that claim.

YTMAINT `2fab–30ea` clears run-local revenge flag `7ba8` and shared preferred
value `7bac`, then reads the pending victim. A positive ID is GET without a
local upper-bound/name/death check. Its **live** sector must exceed 7 to set the
flag; preferred instead receives that victim's **cached** position. Positive
pointers clear/persist afterward even for sector 0/7. Zero and negative pointers
skip the block and remain unchanged in these controls.

The diagnostic dead record retains a positive sector and activates. An unnamed
slot with stale positive sector also activates while its missing cached position
leaves preferred 0. This does not authorize targeting modern dead/unnamed players.
No invalid-record or out-of-range-sector read is claimed safe or fully recovered.

Revenge flag persists for the rest of the run; helpers can change preferred but
do not reset the flag after victim death. The pending slot has already cleared.
These run-local and persisted states must not be conflated.

## Candidate search and eager random draws

For each group, first choose a random fallback1..N until it differs from the
current location (`31e6–3227`). It is not restricted to sectors>7 in DOS.
Then candidate search (`3234–33eb`) permits 1 attempt, or 25 if revenge flag is
nonzero. Candidate selection itself does not reject current or protected sectors.

A foreign force stronger than one, or raw planet reference greater than one,
sets shared preferred. Owner 0 qualifies when force>1; this is not an ownership
validity check. No active planet object is loaded by this predicate. A nonzero
preferred value—new **or retained from a previous group/result**—then ends the
search, even when the new candidate was unqualified. Thus a named revenge victim
normally seeds a preference that makes the first attempt enough;25 is a maximum.

Only when preferred remains zero does the code scan cached player records 2 through
the configured player boundary. For **each visited record**, it calls RND before
combining sector match with `(RND>cached_cloak OR revenge)`. Mismatching positions
and revenge bypass still consume that draw. There is no live/name/death/team
validation in this local scan; earlier cache construction limits some entries.
An accepted player sets preferred to the candidate sector and stops scanning.

A protected raw candidate can set preferred 1–7 and stop search, but the subsequent
adoption test requires preferred>7. In that case the original fallback wins.
Failed candidate search also retains fallback. These are separate decisions.

## Cloak thresholds and the earlier equality correction

The loader uses the nonzero name indicator, caches position and subtracts .05
from positive cloak, clamping at 0. Negative legacy input is first normalized to 1,
then reduced to approximately .95. Controls at 0,.025,.05,.1,1,10 and−1 check the
saved result. Diagnostic10 is outside the modern valid0–1 range.

Candidate discovery compares RND directly with cached cloak and **rejects equality**.
Top hunting and ordinary route interception first form the single-precision
`cached_cloak-.33` threshold and permit equality. Initial1 therefore produces
approximately .95 for candidate discovery and approximately.62 for the other gate.
The three top-hunt samples at initial 1 fail at midnight and pass at 04/08; initial 10
fails all three. These are observations, not a measured probability or fixed seed
contract for other runs.

BRUN's QB71 handler (`1e5b`) saves a four-byte threshold expression. QB_A5
(`a831`) resolves that saved operand into SI and points DI at the RND accumulator;
the compare core and register-restoring wrapper preserve flags. Equality yields
CF0/ZF1. At YTMAINT `25ae`/`3c1c`, JBE leaves the rejection mask zero, so hunting
or ordinary battle proceeds. Candidate `335e–3379` instead builds an acceptance
mask from strict RND>cloak. This runtime-aware trace corrects the prior ordinary
interception interpretation. At research completion the Go ship implementation used strict `>`. The
[subsequent implementation](IMPLEMENTATION.md) now corrects that equality boundary;
this evidence slice itself introduced no gameplay changes.

The arrival pair separates selection from combat: with revenge active, groups 2–15
reach sector 250 in both cases. At cloak 0 all 14 fight and lose their 100 fighters;
private messages match the transcript's human casualties and recipient 2/sender −1.
At diagnostic 10 no ship battle/private casualty mail occurs; the 1400 attackers
combine at250 without duplication. Revenge has not granted cloak immunity to
combat or guaranteed an interception.

## Top player, final overrides and special group 20

Top selection uses greatest positive **named stored** score with strict greater-
than updates; ties keep the earlier record. It does not locally filter death.
The top-dead and equal-score controls corroborate those legacy gaps/boundaries.
An unnamed larger score is ignored; no positive named score yields no top ID.

With a top ID, the detection draw is consumed even below the2,500,000 score
threshold. Successful hunt selection starts from the just-read live sector; a
separate RND>.25 selects cached position. **Equality .25 keeps live position.**
Quiescent fixtures do not create an ordinary live/cache position divergence, so
that distinction is static/model-derived, not a captured concurrent movement.
Missing/protected/out-of-range targets receive random 8..N and clear top ID; the
hunt announcement can precede replacement, as the sector 7 control shows.

After candidate adoption, groups 16–19 use preselected top/fallback sector when
revenge is active. Group 20 always does so. Revenge does **not** replace this top
sector with its victim. The victim 250/top 260 controls show 2–15→250 and16–20→260
at all three sampled times. When top hunting fails or no top exists, the latter
groups can instead use the same random fallback. Finally HQ force below
`topStoredScore/2000` overrides everything to HQ (`345c–347a`).

Group 20 is also excluded by the ordinary interception mask, though that path
still eagerly consumes its draw. At its endpoint it can call the ship helper
using the retained top ID (`3caf–3d15`), without another ordinary cloak draw. The
helper's live-position checks remain separate. This branch is static-derived in
this matrix; endpoint destination is not proof of a successful live target or
battle. The modern implementation should explicitly state whether it retains
its uniform, living-ship cloak policy rather than inheriting this legacy bypass.

## Diagnostic phase boundaries and remaining unknowns

Dense synthetic planet-reference 1/2 controls cause repeated earlier Wanderer
placement messages and change RNG consumption before Xannor selection. They are
retained as diagnostics, not isolated causal proof of the planet>1 predicate;
that boundary is established by exact code/runtime interpretation and the model.
Dense Mercenary/human force2 screens can alter Xannor force in **later Mercenary
maintenance**, including failed-route behavior. Their Xannor-phase target logs
and19 unchanged activation sizes are checked separately; whole-run force
conservation is not claimed for those two controls. Other no-arrival controls do
verify unique-sector force conservation. Original public news and private mail
are preserved as legacy evidence, not proposed modern privacy rules.

The [model](recovered_rules.py) checks1/25 attempt bounds, eager record draws,
shared preference, protected candidates, threshold equality, score ties and
position/override order. It deliberately limits its diagnostic fallback test;
DOS's initial rejection and protected-sector retry loops remain unbounded.
It is not a BRUN emulator or bit-exact RNG/MBF replay. Native exact-tie execution,
precise native draw counts, concurrent writers/live-cache divergence, malformed
pointers, every HQ weapon producer variant and native/live BBS acceptance remain
unverified. No live external player was contacted by these fixtures.

## Next implementation contract

Implement a persistent single pending revenge target from **verified defeats of
Xannor-owned HQ sector fighters**, settled atomically with combat; ordinary mobile
kills, neutral/human HQ garrisons and planet destruction must not create it merely
by location. Define last-write behavior, target lifetime across ship replacement,
and no-valid-target consumption explicitly. Require current living modern players
and protect Union sectors; do not import legacy name/death/GET defects.

Add finite 1/25 candidate selection with documented RNG order and uniform safe
fallbacks, retaining shared pursuit and final top/HQ override ordering. Keep
world locks, generation checks, replay guards and force conservation. Decide and
document cache/live and group 20 policies; reuse current authoritative state rather
than emulating stale caches. Correct ordinary `.33` equality to the recovered
boundary, and test strict candidate equality separately. Define whether daily
cloak subtraction joins existing turn-based decay; do not silently add it during
research or migration. Keep recipient-private aftermath and public news bounded.

## Reproduce and validate

```sh
python3 scripts/recover_xannor_revenge.py /tmp/yt-revenge-new
python3 scripts/recover_xannor_revenge_queue.py /tmp/yt-revenge-queue-new
python3 scripts/verify_xannor_revenge.py
python3 scripts/test_xannor_revenge_verifier.py
python3 scripts/verify_archive.py
```

Destinations must be new disposable directories. DOSBox Staging is needed only
for new runs; preserved-world verification needs Python and original archive
bytes. `--only`/`--parent-world` select maintenance controls and exact child input.
The ten negative controls rehash altered files/manifests yet reject semantic
corruptions in pointers, cloak, force, overrides, interception, private recipients,
clock capture, world chaining, HQ queue creation and normal exits.

Local validation passed: all 56 preserved original-DOS runs completed normally;
the independent verifier and ten rehashed semantic negative controls passed;
planetary, ship, mobile and lifecycle evidence verifiers passed; all 4682 archive
hashes remained intact; changed Python syntax, relative documentation links and
whitespace checks passed. REA targets were closed after retaining complete
records. No Go code changed, so no new Go gameplay validation is claimed.

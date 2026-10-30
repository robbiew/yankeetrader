# Port plague and planetary plague/civil-war research

This milestone preserves **56 normally completed original-DOS maintenance runs**,
exact before/after worlds and auxiliary-file chains, **18 complete REA byte
observations**, an executable static model and an independent verifier with
**16 deliberately rehashed corruption controls**. It recovers event selection,
damage, caps, ownership and reporting, with explicit economic/NPC boundaries.

**Research only:** no Go gameplay or schema changes are included. Plague and
civil-war events were unimplemented at this research commit (save version 18).
The subsequent [bounded implementation](IMPLEMENTATION.md) adds them with save version 19.

## Finding ledger

| Question | Recovered rule | Evidence and limits |
|---|---|---|
| What triggers port plague? | Updated/promoted production sum strictly greater than 1,000,000; no random outbreak gate. | Exact 999,999/1,000,000/1,000,001 controls; `0b38–0b7a`. |
| Does large cargo directly trigger it? | No. Cargo first grows, then can promote production to cargo/10. The resulting production is tested. | Cargo-only diagnostic remains below the production threshold; `09ae–0a3f`. |
| Can port plague increase a rate? | Yes: each rate>500 becomes `RND*rate+500`; rates<=500 do not draw or change. | 499/500/501 controls; `0b91–0c3b`. |
| Does a port retry until cured? | No: one pass, at most three rate draws, then cap/select/save. | One-pass control ends above 1,000,000 with one public count. |
| Is Earth exempt? | No. Port maintenance includes port 1; Earth contracts plague. | Earth and three-port controls; separate later tax loop is not this event gate. |
| Which commodity is sold? | First strictly greatest positive internal cargo, after event caps; its coefficient becomes positive and others negative. | Exact dedicated tie/winner controls. Saved-single cargo can hide internal-double distinctions. |
| What about zero stocks? | A prior port's selected index can persist. | Following Earth winner 1 versus winner 3 produces different type/signs for the same zero-stock port. Diagnostic zero-rate inputs are not modern-valid port defaults. |
| How is planetary plague chosen? | `R1*sum(updated rates) > R2*1,000,000 +100,000`. | Strict runtime comparison and high-rate controls; not a measured outbreak frequency. |
| How is civil war chosen? | A third draw tests `R3*updated ground >1,000,000` and overrides plague. | Civil-only/dual-candidate controls at three clocks; strictness is static/model-derived at exact ties. |
| What is damaged? | Each production rate gets its own multiplier; positive ground becomes `G-G*R4*R5`; cargo is capped at 10 times damaged rates. Civil war alone debits `floor(RND*bank)`. | Native bounds, stocks, fractional ground, rich-bank controls and BRUN arithmetic traces. |
| Do events transfer title or kill planets? | No local owner/name/link deletion; no direct weapon-stock loss. | Owners 0/human 2/Xannor −1/Mercenary −2, active/inactive and protected/unprotected probes. Later NPC/home work is separate. |
| Are messages private? | Event announcements and detailed summaries are public. No private event helper is called. | Console and newly rotated public journal; named human-owner control. |
| Can public spending text be wrong? | Yes. A later plague can repeat a prior civil-war expense without a corresponding debit. | Ordered civil→plague, civil→quiet→plague, zero-bank reset and reverse-order controls. |

## Artifact identity and controlled setup

Original files are copied into fresh DOSBox Staging mounts; neither the archive
nor a live BBS world is executed in place. No executable patching or random-source
replacement is used. All 56 retained runs return `Daily Maintenance Completed OK`
within the 45-second limit; pilot runs are outside the retained corpus.

- `YTMAINT.EXE` SHA-256 `8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6`.
- `BRUN30.EXE` SHA-256 `3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8`.
- The canonical fixture independently derives from the preserved lifecycle world.
  Its SHA-256 is `ad34a8f17e91395a5456f797f27fff4d4d636159b3257314ca4a2f4fa2f83ac7`.
- The frozen [recipe](dos/recipe.json) has SHA-256
  `38dc23bbf48d83e2da8e1271d31e5adae3e2ccb3a414fbb5b82aff2d6a45023b`.

All 1,000 ports start with small cargo/production and zero treasury, preventing
unrelated port outbreaks and tax-funded Mercenary hiring. Probe planet 2 is linked
to protected sector 2, with ordinary stocks/timestamps and existing faction homes
retained. Non-Union outgoing warps are removed. Only the declared ownership
control adds a named protected human player. Other scenarios vary the isolated
port, ordinary planets 2/3/4, timestamps and explicit links. A separate sector 8
probe checks that the local event is not restricted to the Union.

DOS DATE/TIME are set and captured for October 25, 2026 at 00:00, 04:00 or 08:00.
Two children inherit their parent's exact world **and auxiliary files**: one on
October 26 and one on the same date. The runner keeps compressed before/after
worlds, full public/private side-file payloads and hashes, clock captures,
completion transcripts and original executable identities. The independent
verifier rebuilds every input rather than trusting the capture manifest alone.

These are controlled binary experiments, not ordinary playable universes.
Economic/event assertions target ordinary probe slots 2–4. Wanderer and faction
home slots have later relocation/reserve repairs; their final ground counts
cannot establish event damage.

## Port growth, threshold and one-pass effects

The main port loop starts with port 1, including Earth (`07dd–07e8`). Before each
update its coefficients become negative absolute values (`08ca–0912`).
Elapsed time uses the saved day/minute and a single-precision day fraction.
Negative elapsed time or more than ten days becomes ten days (`093b–099e`).

For each commodity, using its old production:

```text
cargo = cargo + production * elapsed_days
if cargo / 10 > production:
    production = cargo / 10
```

The multiplication is single precision; cargo lives temporarily in a double
array. Production is promoted back to a single when surplus requires it. There
is **no 1% natural production multiplier in this port path**. In the one-day
control, rates 100/200/300 remain 100/200/300 while cargo grows 100/200/300 to
200/400/600. Planetary growth follows different rules.

`0b38–0b7a` loads the **production array** and adds its three singles, rounding
after each addition. Only a sum strictly greater than 1,000,000 enters plague.
The 999,999 and exact 1,000,000 controls do not; 1,000,001 does. A cargo-only world
with 1,000,001 units promotes one rate to about 100,000.10, remains below the
production threshold, and does not contract plague.

During plague (`0b7f–0de2`):

1. Increment the run's affected-port count once.
2. Visit commodities in order. Only a rate strictly greater than 500 consumes a
   draw and becomes `single(single(RND*rate)+500)`.
3. Cap cargo at ten times the resulting rate when it exceeds that amount.
4. Continue to commodity selection and saving. There is no cure/retry loop.

A 501 rate becomes about 642.09 in the captured control: “lost productivity” is
not a reliable description of every individual rate. A separate one-pass world
ends with total production **1,577,064** while the aggregate report counts that
port once. Model draw-count checks enforce zero outbreak-gate draws and at most
one damage draw per eligible commodity. Native RNG call counts were not instrumented.

No-event `0b7c` jumps over the event damage/cap block. A pilot initially confused
cargo and production because a retained register points to the production array;
large-cargo native controls contradicted that reading. The corrected pointer
trace and native production-threshold controls are the basis of this report.

### Commodity selection and public count

After event handling, the code scans internal cargo 1→3 with a strict improvement
test and an initial maximum of 0 (`0de7–0e7f`). The selected index determines type
`4-index`; that coefficient becomes positive, the others remain negative.
Dedicated equal-positive and distinct-winner controls verify the first tie and
all three commodity outcomes. All coefficient magnitudes are retained.

The selected-index variable itself is not reset for each port. Identical zero
stocks/rates after a preceding winner 1 versus winner 3 inherit different type
and coefficient signs. These diagnostic zero-rate worlds establish stale state;
they do not define a safe modern fallback for valid ports.

The work array's double values can differ while their saved MBF singles compare
equal. The verifier requires the selected commodity to be maximal within its
explicit rounding tolerance, then checks exact type/sign consistency. It does
not fabricate internal exact ties from equal persisted stocks. Dedicated native
tie controls and injected model boundaries remain distinct.

At `0f47–0fad`, a nonzero aggregate count is printed and appended publicly before
planet maintenance. The corpus demonstrates Earth alone and three ports including
Earth. No per-port plague announcement or private mail is produced here. Port
ownership/treasury are not altered by this block; ordinary taxes happen later.

## Planet selection, damage and persistence

Economic growth, bank interest, weapons and ground production happen before event
selection. The legacy minimum-one rate repair at `15e2–164e` also precedes damage.
Let S be the sum of those updated production rates, and G updated ground:

```text
flag = none
if single(R1*S) > single(single(R2*1,000,000)+100,000):
    flag = plague
if single(R3*G) > 1,000,000:
    flag = civil_war
```

Every active planet takes those three gate draws, even if both events are
mathematically impossible. Both comparisons are strict. Civil war overrides
plague (`169e–1705`). S<=100,000 cannot pass the first gate; G<=1,000,000 cannot
pass the second, **when measured after growth**. An input just above a threshold
is not a guaranteed event: the 1,000,001-ground native control has none.

Both events then:

- Replace each cargo production rate with its own `RND*rate` (`1719–1771`).
- For positive ground, use two more draws: `G = G - G*R4*R5` (`1776–17c3`).
- Cap each cargo stock at ten times its reduced rate (`17c8–1891`).

Ground remains fractional; an ordinary plague probe saves about 27.1999 ground
from 100. Display-only floor calls do not change the saved array. There is no
post-event minimum-one repair, title change or logical planet deletion in this
block. Weapon stock changes belong to the earlier production pass, not event
casualties. The inactive-name probe skips the entire planetary update.

Civil war alone additionally spends `floor(single(RND*bank))` from the
**post-interest** bank (`18cc–1915`). The loss is kept as a double for reporting;
the updated bank is stored as a single. Plague does not debit its bank. Large
native balances have MBF spacing, so these are not modern exact-integer credit
arithmetic guarantees. Controls cover bank 0, 1, 1 million, 1 billion and a one-day
rich world. Model tests cover exact gate equality, override ordering, zero rates,
fractional ground, cap boundaries and conditional draw counts.

### Public announcements and the stale expense defect

Each event publishes its label, planet name, productivity summary, optional
ground summary and optional expenditure to console and `YTNEWS.DAT` through
`57d1` (`191a–1b1d`). A ground notice is emitted only when positive floored ground
actually changes. No private-event helper call occurs, including for the named
human-owner control. This original public detail is not a modern privacy policy.

Civil war assigns the expense temporary `7b58`. Plague and no-event planets do
not reset it. Thus a civil war followed by a plague can print the same expense
twice while deducting it from only the first planet. The direct and quiet-middle
controls show the same **771,511,168** expense twice; the later plague planet's
bank stays **12,345**. A zero-bank civil war between them resets the temporary,
and the later plague does not print the stale expense. Reversing the order also
removes the spurious earlier charge. This is process-local stale state, not debt
saved across program executions.

The verifier compares each event with its own planet and current public body,
not the position of a similar old line. It also verifies that the original
current journal rotates exactly into yesterday's journal, and that the new
journal contains this invocation's expected event bodies/count. Rehashed stale
public text and missing required ground notices are rejected.

## Ordering and the 08:00 clock trap

The original sequence is port growth/plague/commodity selection, aggregate port
news, planet economics/events, Wanderer/faction/NPC actions, tax collection,
Mercenary actions, lottery and score publication. Only the local event phase is
covered here; prior research supplies the later detailed faction algorithms.

At the 08:00 fixture's nominal prior minute 480, maintenance saves
**479.9993591308594**. That tiny negative interval triggers the legacy ten-day
catch-up rule before events. The civil-only control therefore grows ground from
100 million to **110 million**, then reduces it to **107,989,992**. The apparent
increase over the raw before world is not a negative loss or signed-RNG defect.
Its transcript reports the correct pre-event 110 million and productivity 3300.
The verifier reconstructs growth from actual saved timestamps before checking
event damage. The 00:00/04:00 controls do not cross that negative-time boundary.

An exact same-day child prints `Maintenance not needed!` and still executes the
phases. The next-day child inherits its prior bank/rates/ground and journal.
Modern saved-day replay and clock-rollback guards must remain; the observed
clock behavior must not be copied as an overproduction feature.

## Next bounded implementation contract

The next milestone can add these events without changing the recovered research:

- Run a finite per-port/per-planet pass in the existing locked daily update,
  after the object's ordinary growth and before NPC actions. Keep once-per-day,
  missed-day and clock-rollback policies explicit; do not reroll until cured.
- Use the recovered strict gates, civil override and separate conditional draws.
  Preserve current zero-rate planet support, quantity bounds and whole-credit
  banking. Choose/document the conversion of fractional legacy ground into the
  modern integer representation rather than silently changing ownership.
- Cap cargo after event damage and make port commodity switching stable. Supply
  a deterministic fallback for a zero-positive-stock case instead of stale state.
  Include Earth in recovered economic event rules while retaining its separate
  ownership, mine, combat and tax protections.
- Keep owner/title, name/link and weapon stocks unchanged by the event itself.
  Captured faction-home identity and later reserve repairs remain separate.
  Confirm existing phase order and landing/docking invalidation when integrating.
- Publish typed public news without exposing sensitive ground/bank figures.
  Scope any owner-only details separately. Expense reporting must use this
  planet's actual debit, with no stale temporary or duplicate charge.
- Validate thresholds/equality, full-capacity work, simultaneous events, no-event
  eager draws, caps, safe numerical limits, fresh notices, replay, rollback,
  concurrency, committed durability and migration if new saved event state is
  introduced. Update README and the plan with actual playable status.

Exact native RNG streams/distributions, complete bit-for-bit MBF arithmetic,
all possible hidden-double ties and malformed negative economic states remain
outside this bounded recovery. Live BBS/native platform acceptance is separate.
No modern gameplay, event privacy policy or save format has been changed here.

## Verification and reproduction

```sh
python3 scripts/verify_plague_civil_war.py
python3 scripts/test_plague_civil_war_verifier.py
python3 scripts/verify_archive.py
# Requires the already-installed DOSBox Staging; destination must not exist:
python3 scripts/recover_plague_civil_war.py /private/tmp/yt-events-new
```

The independent verifier checks canonical input reconstruction, declared patches,
all world/auxiliary parent chains, original binaries, real clocks/completion,
post-economic semantics, event/title/resource/report constraints and native MZ
mapping with relocation fixups. Its tolerances are explicit and do not establish
bit-exact MBF parity. All 4,682 original archive hashes remain unchanged. This
research-only change does not claim new Go gameplay or operational acceptance.

## Native evidence index

The linked [complete REA records](rea/target-paths.json) retain subject hashes,
provider/profile, raw and normalized bytes, coverage and limitations. These are
**static byte observations**, not observations of execution. The 56 DOS runs are
the runtime evidence. Addresses below are Ghidra's linear loaded-image addresses;
the annotated maintenance listing uses CS 1000 offsets (add 0x10000).

| Range | Address / bytes | Evidence ID |
|---|---|---|
| port-load-growth | `0x107b2` / 902 | `ev_1af942c6c4cd24ba1e87c584e063b6b78d436b6a1f2e3d8a0ae3c06bad69aaf7` |
| port-plague-cap-selection | `0x10b38` / 1039 | `ev_1086dd145838ea69d2c3cfbf44117bfc8604b280f4b6b5b18e2664654733acfd` |
| port-public-count | `0x10f47` / 126 | `ev_7b39a9f8d275942f909e21fb5d9d09e784ca57a8bc3916ab7e6f7c3fb285e99a` |
| planet-input | `0x10fc5` / 332 | `ev_0b24708ed2c0939e41e952ff280d041eea27fc8e3c2bb3e3a24eecb08a6209e4` |
| planet-production-event-gates | `0x113cc` / 845 | `ev_f9a7adc0ab947d299c252b6d5dadf11af9c847334e89599fa00c949e644b7b9e` |
| planet-event-damage-bank | `0x11719` / 513 | `ev_367d477d925d8ae72673176228133258e665cce0480ffd6ba48666c2edb5ad05` |
| planet-public-private-reports | `0x1191a` / 552 | `ev_5908e242a24b38deb29980c6a2760a9d97df35aafeddd05a86fe3feaf089d1a8` |
| planet-save | `0x11b42` / 382 | `ev_dd9e446826d42b7311c3790863a4505cace7b3426ace72a997fca47b5c0e6147` |
| runtime-single-subtract | `0x1b359` / 65 | `ev_0c88703837ef1a04c92a7c5c1d5c36c278e802229adea197a07f5dfb6d5c684c` |
| runtime-double-subtract | `0x1ad81` / 90 | `ev_e12ba0779b3cef76b32a1b3126aa1f4f5c4489c30c32f52764d749175a37834c` |
| runtime-comparison | `0x1a818` / 180 | `ev_f85dd9d3290438449fc290e8755a1080b2dcc7c45b4bcdafaa754ff3de1a725f` |
| runtime-floor | `0x1acb2` / 180 | `ev_567123d41857df939d326c9daf676249df6b745ddf6c8bd7b563373a125605f5` |
| runtime-multiply | `0x1b440` / 220 | `ev_bb97aa592ebc8ca6355e6a094ce31baee8b0a981ac9939aa52dd7c857ab6b455` |
| runtime-sign-tests | `0x1ac1e` / 70 | `ev_9db975e4cc86dd209b9576ca16c60ee501ade5a250cbd1a4654a3d6529d09dd6` |
| runtime-single-stack | `0x11e5b` / 60 | `ev_130ec2966d0a290c2c572662c894fc2bb2b95e9740b418c9826c8ce41408d19d` |
| runtime-array-load | `0x1c324` / 190 | `ev_34031866b91c96f5fec3c5d42fded12de815df64918cdcf789eb90b60b770102` |
| port-constants | `0x18086` / 24 | `ev_95fa75ae242928a64f50929d699014dc8d6c61a0e8016fa7caabb219f49cd7d5` |
| phase-start | `0x10389` / 368 | `ev_0ccff675f7db56d162dd0137830715584d90b75f7837e807a0e80c83812035cc` |

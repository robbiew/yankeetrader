# Xannor planetary assault and destruction research

This slice preserves **71 completed original-DOS maintenance runs**, 142 world
snapshots, paired economic-phase controls, an exact next-day world chain and
**20 complete REA byte observations** from YTMAINT and BRUN30. It establishes
planetary eligibility, ground/production battle rules, warehouse capping,
neutralization, logical deletion and route ordering. This is research only: Go
mobile groups still hold before foreign planets, and save version remains 15.

The original executable SHA-256 is
`8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6`;
BRUN30 is
`3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8`.
Unmodified executables run only in fresh disposable DOSBox mounts. The archive
and live BBS saves are never mounted for execution.

## Finding ledger

| Question | Recovered answer and boundary |
|---|---|
| Which arrivals attack? | Positive moving force, a sector planet reference, active planet name and foreign owner; surviving positive sector force can suppress the helper. Static + skip/screen controls. |
| Do neutral and Mercenary planets qualify? | Yes; owner -1 is skipped. Owner 0, -2, 1 and human 2 controls are distinguished. Owner 1 is a legacy diagnostic, not a claim that original record 1 is an ordinary player. |
| Which resource defends first? | Ground forces. Each ground unit is consumed and destroys **floor(RND × 1000) + 1 Xannor**, or 1–1000 fighters. Static register/runtime trace + one-ground and large-group controls. |
| How is production damaged? | With surviving attackers, RND < .5 damages all three rates using independent draws × batch / 3; RND >= .5 spends the batch from Xannor. Exact equality is static/model evidence. |
| What chooses batch 450 rather than 1? | Any rate >500 plus a nonzero group **location**, through a mistaken subscript. It does not require a large remaining force. One-attacker controls corroborate large production damage. |
| What happens to warehouses? | Clamp negative rates to zero, then cap each stock to 10 × its corresponding final rate. Smaller stocks are not increased. Paired stocks and mixed-rate controls. |
| Does ground victory capture a planet for Xannor? | No. Exactly zero remaining ground sets owner to 0, even if the planet survives. Positive remaining ground retains its title. |
| What destroys the planet? | All three post-clamp rates at zero clear sector reference 93 and planet active-name length 85. This is logical deletion; bank and weapon fields remain stale. |
| Do planet fighters defend or become loot? | No. The 100000-unit weapon-stock control retains them in the inactive record; no force is harvested into the returning group. |
| Is the attack protected from earlier phases? | No. Earlier maintenance floors ground, repairs rates below 1 and can raise rates from surplus warehouses. Paired non-arrival controls are required. |
| Does a planet explosion kill nearby ships? | The planetary helper does not call ship death or estate settlement. A hidden overlapping ship survives deletion unchanged; visible ship combat happens afterward. |
| What reports the result? | Public attack/destruction lines, with no private planet report in this helper. A static simultaneous-deletion branch can overwrite the planet message with the group-death message; raw links remain authoritative. |
| Can this happen in the Union? | DOS attacks the controlled planet in sector 7. The Go protected-sector policy must remain explicit. |

## Controlled worlds and phase isolation

The baseline derives from the independently verified [mobile world](../yt-xannor-mobile/RECOVERY.md):
3000 sectors, 1000 ports, 100 planet slots, Q in player record 2, stored score
4000, diagnostic cloak 10 and protected sector 7. HQ 1114 holds one fighter;
group 2 starts in sector 100 with 100 fighters and follows 100 → 101 → 1114.
Planet slot 2, Probe Planet, is linked to 101 and starts owner 2, zero ground,
zero bank, production 1000/2000/3000 and empty cargo warehouses. Weapon stocks
are fighters37/missiles11/plasma5/mines3.

A separate **pointed parked group 3** has 10000 fighters in sector 200 with no
outgoing warps. This prevents regeneration even when group 2 is reduced to one
fighter, while HQ 1 remains below score/2000 and cannot split. The parked group
logs a bounded path failure, remains intact and cannot revisit the probe. Every
independent run verifies exactly the declared group-2 activation, if nonzero,
and group 3; no extra mobile groups or regeneration confound the assault.

The raw baseline SHA-256 is
`c3e432bb8aef6e094a42fed4f2a22dabbd6c306079d19d455eb0d7b832619716`.
The [frozen recipe](dos/recipe.json) and [manifest](dos/results.json) declare every
field override. The verifier reconstructs the baseline and each before-world
without importing the runner's fixture construction, then checks full raw bytes,
binary/runtime identities, DOS clocks, side files and after-state semantics.

All independent runs request 10/25/2026, normally at midnight; paired clock
controls request 04:00 and 08:00. Captured time must be within one second.
After-state fractions are recorded MBF observations, not guaranteed RNG replay.
Every process has a 45-second bound; all 71 preserved runs completed normally.
Initial warehouse-heavy exploratory probes remain in temporary workspaces but
are not added to this count; their phase interference is reproduced by the
explicit surplus/non-arrival pair in the final suite.

The child dated 10/26/2026 consumes the **exact complete final world bytes** of
`weapons-retained`, without reset or patches. Its inactive planet remains
inactive with zero production and stale weapon stocks. Later top-score-driven
NPC activity is not described as a second isolated attack. Side files are
freshly copied, so this is an exact world-state chain, not a message-history chain.

## Eligibility, screens and ordering

Helper `5efd–6727` is called after mine/sector-defense resolution at `3b33`.
Before loading the planet, it checks the current sector's reference 93 and force
81: nonzero sector force other than legacy sentinel -1 suppresses the attack.
It also requires moving force >=1. After loading the referenced record, inactive
name-length 85 or owner -1 suppresses it.

The unpointed friendly-garrison control leaves 50 Xannor fighters in sector 101.
The moving group passes, but the foreign planet is not attacked. A diagnostic
owner-zero garrison also suppresses it. These are actual sector-force predicates,
not proof of a general planetary immunity rule. A one-fighter human garrison is
first defeated, clearing that screen, then the planet is attacked.

Origin planets are ignored. Fatal mines and strong sector defenses prevent any
planet attack or title change. A winning group destroys the planet and reaches
later mines; a group killed by ground leaves those later mines intact. In the
visible-ship control, the public planet-destruction line precedes ordinary ship
combat; in the hidden-overlap control the ship's defenses and position survive.
The controlled sector-7 planet is destroyed, corroborating the absence of a
protected-sector check in this DOS helper.

## Ground defense: one unit buys a random volley

The decisive loop is:

```text
while ground > 0 and Xannor > 0:
    ground -= 1
    Xannor -= floor(RND * 1000) + 1
ground = max(ground, 0)
```

At `6160–6175`, AX receives the ground descriptor; `6197–61a2` therefore
subtracts one from **ground**, not from Xannor. AX then preserves the -1 constant
across the runtime calls. `61a7–61d8` loads group force, subtracts INT(RND × 1000)
and adds that -1. BRUN's register-saving wrapper, array load and INT path confirm
the preserved operand. Reading just the nearby -1 without this register trace
would reverse the casualty rule.

A 100-fighter group is killed by the first ground volley: ground499/500/999/1000/
500000 become 498/499/998/999/499999. The one-ground/one-attacker control spends
both units. A 100000-fighter group against ground500000 is destroyed after 201
ground units are consumed. With only one ground unit, that large group survives,
then destroys production and returns to HQ. These samples establish direction,
order and bounded accounting; they are not a measured uniform-distribution test.

The live cache can become negative after a fatal volley; final group cleanup
writes zero force/location. A modern implementation must cap each casualty at
available force and preserve nonnegative state.

## Production attack and the location-subscript defect

With positive remaining force and any positive rate:

```text
batch = 450 if any rate > 500 and integer(group_location) != 0 else 1
if RND < .5:
    for each of the three production types:
        rate -= independent_RND * batch / 3
else:
    Xannor -= batch
```

Rates are local floating arrays. All three damage draws occur, including for an
already nonpositive component; clamping waits until the loop ends. There is no
recovered per-round cap on this original loop. Exact tie behavior is checked in
the injectable model, not claimed as a forced draw in the unmodified executable.

The batch selector at `62e5–6310` literally compares 1 with 500. Its false value
becomes array subscript zero, selecting the group's location row rather than its
force row. With a valid positive location, any rate above500 therefore selects
450 even for one attacker. The rate501/one-attacker sample reduces ore to
378.6458435 before the group dies. Paired non-arrival controls preserve exact
499, 500 and 501 rate inputs; the rate500/one-attacker sample instead uses the
small-batch path. A separate one-attacker 08:00 control loses the group without
changing the pre-assault rates.

The reconstructed helper can overshoot a small force below zero on a 450-cost
round. The settled DOS record clears that negative cache; the model explicitly
retains both raw and published force to distinguish the defect. The likely
intended force threshold is **not established** by the broken expression.
Corrected force-aware batch policy belongs in the implementation contract.

## Earlier economics, warehouse caps and deletion

Non-arrival pairs show that ordinary maintenance first:

- Floors the tested fractional ground .25/.5/.75 to zero.
- Repairs zero or fractional rates below1 to rates1/1/1.
- Reconstructs zero rates as 1000/2000/3000 when warehouses contain
  10000/20000/30000.

Those are earlier economic effects. They are not planet-assault repairs. The
helper's MBF exponent test would recognize nonzero fractional ground, but these
whole-maintenance runs do not deliver those fractions to it. The empty-warehouse
baseline avoids surplus restoration and permits meaningful rate-threshold probes.
Paired 04:00/08:00 runs distinguish elapsed economic growth from assault damage.

After combat, negative rates clamp to zero and warehouses cap independently to
ten times their corresponding final rates. `warehouse-damage` falls to roughly
6664.657/17444.629/28206.799 stocks, versus the undamaged pair near10000/20000/30000.
Below-cap stock is retained apart from earlier tiny elapsed production/MBF
rounding. Zero components of `mixed-rates` have zero corresponding cargo.

Ground exactly zero neutralizes owner73, even when production survives. Positive
ground retains the original title. No planet becomes Xannor-owned through this
assault helper. Bank117 and weapons69/113/125/129 are not assault inputs or loot.
The bank1234 destruction control leaves1234 in the inactive record; the armed
planet retains all four 100000-unit stocks after logical deletion. Returning
Xannor force does not include those stocks.

All three final rates zero clear the sector's planet link and planet name-length.
Other raw fields are not wholesale erased. The next-day child proves those
inactive weapon fields are not ordinary active production or harvested force.
The helper contains no ship-death, estate or private-message call. Public news
records the observed attack and outcome; only the explicit subsequent ship battle
creates private YTRMSG in this suite.

A static edge deserves care: if the helper receives already-zero production and
ground kills the last attacker, its deletion test can still clear the planet.
Its message buffer then says only “Xannor fighters destroyed!” because the group
outcome overwrites the planet message. The readable model verifies this branch,
but **no preserved whole-maintenance run demonstrates simultaneous deletion**:
ordinary maintenance repairs initial zero rates to1 first. The current Go world
supports legitimate zero-rate planets, so directly copying this helper would
introduce a new bad outcome into otherwise valid modern state.

## Evidence and remaining boundaries

[Complete REA records](rea/assault-paths.json) cover the full helper, route
dispatch and constants, plus BRUN dispatch tables, register preservation, array
loads, nonzero/INT tests and arithmetic. The verifier independently applies MZ
relocations at load segment0x1000 and compares every retained byte. Code CS
offsets map to file offset CS +0x200 in these images; runtime/data coordinates
are kept distinct. Ghidra bytes are static evidence, not execution traces.

The [reference model](recovered_rules.py) is executable branch documentation,
not a full maintenance or BRUN/MBF emulator. Exact random streams, fractional/
large-value rounding, concurrent DOS writers, all malformed pointers and
home-specific restoration/retitling interactions remain unverified. In particular,
[earlier Xannoron restoration](../yt-xannor-lifecycle/RECOVERY.md) can overwrite
foreign ownership before this helper; ordinary probe planets do not prove a
captured-home policy.

## Next implementation contract

Enable foreign planetary encounters only after current mine and sector-defense
resolution, within the existing bounded daily route budget. Keep Union sectors
protected, explicit faction-home identity and current ownership authoritative,
and do not grant immunity merely because a separate friendly garrison happens
to occupy the sector.

Implement the recovered one-ground/1–1000-fighter exchanges with checked,
nonnegative accounting. Require surviving attackers to reach production damage:
a successful ground defense must not lose a zero-rate planet or suffer invented
warehouse capping/destruction. Choose and document a corrected force-aware
production-batch rule; do not infer an intended threshold solely from the buggy
subscript. Preserve independent commodity damage, final clamping and actual
post-impact stock caps.

Settle ground/title changes, production, cargo, route force, news and private
owner reports atomically under the world lock. Logical deletion must remove the
modern planet object and sector link, invalidate every landing/confirmation token
and retain ship-generation safeguards. Do not resurrect stale bank/weapons as
salvage, and do not invent collateral ship death. Reuse existing ship encounters
only after the planetary action, with finite work, replay/rollback and concurrent
login/landing coverage. Apply captured-home policy explicitly rather than copying
DOS's earlier forced-retitling side effects.

Planetary assault/destruction implementation is the next milestone; remaining
revenge/cloak candidate searches, exact RNG/MBF parity and native/live BBS
acceptance stay separate.

## Reproduce and verify

From the repository root, with a new destination:

```sh
python3 scripts/recover_xannor_planets.py /tmp/yt-xannor-planets-new
python3 scripts/verify_xannor_planets.py
python3 scripts/test_xannor_planets_verifier.py
python3 scripts/verify_archive.py
```

DOSBox Staging is required only for new runtime runs. Verification requires
Python and preserved bytes, not DOSBox or REA. `--only` selects controls;
child-only replay additionally needs `--parent-world` pointing to the parent's
compressed after-world. Replays may yield new random samples: retain new results
rather than overwriting the recorded evidence. Ten rehashed negative controls
reject incorrect ground losses, caps, links, titles, stale fields, route order,
world chaining, clock capture, phase normalization and force creation.

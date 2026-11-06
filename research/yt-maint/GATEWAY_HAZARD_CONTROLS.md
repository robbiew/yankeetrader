# Gateway mine, defense and fighter-pickup controls

Six explicit fixtures in copied evolved worlds now select Mercenary mine damage,
planetary fighter pickup and defense-before-pickup ordering. **72 complete original
DOS runs** retain **432 complete output files**. All twelve case/day groups agree
across six observation modes (360 nonreference file comparisons, zero differences).
This is acquisition research; before-only model integration remains the next step.
Production Go, dependencies, save 35 and generation fingerprints are unchanged.

## Declared fixture and exact inheritance

The common parent is the actual November 4 result of
[evolved combat controls](EVOLVED_COMBAT_CONTROLS.md), profile
`route-mercenary-100000/child-2`, with manifest
`fd794dccfda332ab79c2d5a693d2649ebbc32c607863fbf2f10801ec4e0ecef5`.
Its physical Mercenary force is 97337 at sector 2368 and Xannor force is 4966.
Each mode uses its own corresponding parent files.

Before November 5 only, fifteen ordered, recorded YTDATA edits install a neutral
ordinary planet, Gateway Cache, in slot 3 / sector 3000. Ground starts at 500000,
bank and all three production rates at zero. Six origin warp fields lead to the
gateway; the three other incoming edges (2996/45, 2998/49, 2999/53) are redirected
to the origin. The verifier reconstructs every edit independently, including
no-op assignments. It proves all 3000 vertices remain reachable both to and from
the gateway, whose sole predecessor is the Mercenary origin. The gateway has
already passed in the descending scan when the origin acts, preventing same-day
reactivation there. No original executable is patched.

| Case | Planet stock | Gateway mines | Gateway Xannor defense | Initial Mercenaries |
|---|---:|---:|---:|---:|
| empty | 0 | 0 | 0 | 97337 |
| pickup | 37 | 0 | 0 | 97337 |
| mine-pickup | 37 | 1 | 0 | 97337 |
| guarded-pickup | 37 | 0 | 37 | 97337 |
| mine-guarded | 37 | 1 | 37 | 97337 |
| fatal-before-pickup | 37 | 3 | 0 | 1 |

Every run naturally completed on the first acquisition. Both dates use midnight:
November 5 and November 6, 2026. Modes are two unobserved runs, attach-only and
three independently observed runs. Of 432 input relations, **396 are unchanged
file links**: 180 first-stage side files and 216 second-stage files. The remaining
**36 are explicitly audited YTDATA transformations**, not unchanged inheritance.
All six November 6 inputs exactly equal their own mode's November 5 outputs;
there are no second-day fixture edits or repairs.

## Selected outcomes and ordering

| Case | November 5 observed Mercenary result | Planet stock after Nov 5 / Nov 6 |
|---|---|---:|
| empty | 97337; capture message, no taking-zero line | 0 / 3 |
| pickup | 97337 + 37 = 97374 | 0 / 3 |
| mine-pickup | 97337 − 712 + 37 = 96662 | 0 / 3 |
| guarded-pickup | wins against X37, loses 34, retains 97303; no pickup | 37 / 40 |
| mine-guarded | mine loss 518, then offense loss 40, retains 96779; no pickup | 37 / 40 |
| fatal-before-pickup | M1 dies at first mine; two mines remain; no pickup | 37 / 40 |

Unprinted offensive losses in this table are observations inferred from force
stamps and physical conservation, not independently predicted RNG combat results.
Earlier Xannor actions lose 2696 fighters in eighteen fatal planetary attacks;
none attacks Gateway Cache. Added gateway X37 dies only in the guarded cases.
Ground grows to 505000 then 510050 through normal economy. Pickup neither changes
the planet title nor transfers ground. Guarded routes leave the gateway and do
not revisit it on day two; the first three cases hold there without a second
pickup. The fatal case remains extinct and retains its two unspent mines.

Zero starting rates do not disable future production. Original `15e2–1649`
clamps each rate below one after first-day production. All rates finish day one
at one, producing three fighters on day two, then grow to approximately
1.00999999046. The independent zero-bank economy calculation checks the resulting
stock and ground, using authenticated source clocks; unobserved saved-clock
corroboration is labeled separately from direct clock observation.

## Exact source and receipts

The existing [complete native read](collision-replay-native/rea.json), relocated
address `0x14600`, length 3462, authenticates the Mercenary source window
(Evidence `ev_c92656dd4a34f4605e434c81cbd3e9f730962d0373f2a3fecfce72256fbfcd2f`).
Mine setup/loop `4a78–4b8e`, fatal output `4c0c–4c7a`, pickup gate
`4c7f–4ec0`, stock clear `4d09–4d34` and defense `4ec3–5318` explain the
selected ordering. The minimum-rate rule is from the original annotated listing,
corroborated by these actual rate transitions; no new native read is claimed.
Earlier [primitive controls](../yt-mercenary-maintenance/RECOVERY.md) remain
separate from these full evolved-world runs.

Helper2 caller `0x4aa4` is an already qualified site. Its source supplies count two
and bound 10000. Each initial mine invokes the helper even after the force dies:
the fatal three-mine case has three callbacks although only one mine is spent.
All 36 observed streams qualify; this audit does not predict the full RNG stream.

NEWS and TRACE both preserve pickup receipts. Capture and taking lines stamp the
**pre-pickup** force: mine-pickup prints 96625 taking 37, while the actual saved
force is 96662. Empty pickup prints capture but no taking-zero line. Fatal output
retains the original typo `The mercenariers were killed!`. Public and console
ordering, physical totals and scores are checked together. Raw numeric zeros
remain distinct: pickup stock clear `00008000`, spent mine count `00000000`,
Mercenary departure `00002800`; two remaining mines encode as `00000082`.

## Provenance, verification and limits

The [frozen corpus](gateway-hazard-controls/) contains 1974 files / 17257301 bytes.
Its manifest SHA-256 is
`fff8758c16f18302ceda4115c1960f4bc859a3bd5333a29df1b5da3b70aa8e90`.
Four executed source snapshots are retained separately from the evolving verifier.
The verifier imports neither the capture writer nor a maintenance replay model.
All 34 independent regression tests pass. It audits exact fixture bytes, graph proofs, original launch/CPU/controller evidence,
all files, handoffs, clocks, helper caller counts and selected semantic outcomes.

```sh
python3 scripts/verify_maintenance_gateway_hazards.py
python3 scripts/test_verify_maintenance_gateway_hazards.py
python3 scripts/verify_maintenance_collision_replay.py
python3 scripts/verify_archive.py
```

Next integrate the declared fixture transformation into a **modeled** November 4
parent and synthesize both days before opening targets. This requires the
zero-rate clamp, mine helper's initial-count loop, defense-versus-pickup ordering
and exact raw writers. Existing model admission guards deliberately reject these
new fixtures; this is a scope boundary, not a masked numerical mismatch. General
MBF, arbitrary worlds and other unmeasured paths remain separate. This research
does not establish live BBS acceptance or native Windows crash durability.

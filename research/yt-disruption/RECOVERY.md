# Disruption and black-hole arrival recovery

Research completed 2026-10-31. This milestone changes evidence, tooling and
interpretation only. **Go gameplay and save version 25 are unchanged; disruption
arrivals are not implemented.** The next milestone is the bounded, atomic arrival
resolver described in the [candidate implementation contract](CONTRACT.md).

## Evidence and reproducibility

The retained [DOS corpus](dos/recipe.json) contains **61 normally returned
controls, 122 complete before/after world snapshots and four exact world/auxiliary
reload chains**. A [separate diagnostic](diagnostics/recipe.json) is an unsupported
one-sector fixture that did not return within 40 seconds; it is excluded from
those counts. Each control retains exact input, DOS date/time output, raw CP437
log, rendered transcript, program-return marker, full auxiliary bytes, hashes and
result metadata. No incomplete pilot is counted as a successful control.

[Native analysis](NATIVE.md) retains **15 complete byte observations and one
independently reconstructed DOS MZ load-image observation**, including all 870
relocations. Twelve byte reads are targeted/supporting; three exploratory reads
are explicitly classified. One exploratory data read contains text, not the
intended numeric constant, and supports no arithmetic claim.

The source world is the preserved planet-transfer fixture at
`archive/analysis/yt-combat/experiments/fixture-planet-transfer/YTDATA.DAT`, SHA-256
`2a63d12af095a59227840946be57fd4b7e4dafb5724d4019de694da7c4194b19`.
The unmodified original `YT.EXE` has SHA-256
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
The harness copies this executable, BRUN30, LOCAL and KEYFEED into disposable
fixtures and runs them under DOSBox Staging. It never mounts the archive for
execution, patches executable bytes, injects runtime memory, or invents a
persistent black-hole flag. All archived originals remain unchanged.

Recipe `disruption-arrival-v1` deliberately separates two geometries:

- Narrow 2-, 3- and 8-sector controls retain the player base at record 51, move the
  declared sector/port/planet boundaries consistently, and remap the actual planet
  records after the declared sector interval. These force branches efficiently;
  they are not ordinary generated worlds or distribution samples. Clearing
  sector fields is limited to the declared sector rows, preserving the remapped
  planet activity and garrison fields.
- Full-width controls retain the original 3000-sector header ranges and 100-planet
  table. Routes, hazards and occupancy are still controlled. Original sensors
  identify actual session holes 592 and 1051 at the selected clock, and targeted
  movement/transport/startup controls exercise both. These are full-header
  fixtures, not untouched worlds or samples of normal gameplay frequency.

The four reloads use the exact parent's complete saved world and auxiliary
bytes, without reapplying setup patches, at DOS00:01:00. The other controls use
10/24/2026 and an explicitly declared clock, usually 00:00:00. The final corpus
reuses 50 previously completed canonical cases and captures the remaining 11;
reuse checks declarations, source identity, normal return and retained hashes.
No outcome was synthesized from the native interpretation.

Run the portable retained-evidence checks without a DOS emulator:

```sh
python3 scripts/verify_disruption.py
python3 scripts/test_disruption_verifier.py
```

The verifier independently decodes MBF, reconstructs setup and the relocated MZ
image, checks complete world/auxiliary witnesses and permitted mutations, and
checks receipts, turn/heat arithmetic, privacy, score/news effects, exact reload
chains and diagnostic classification. Its corruption suite rewrites hashes and
metadata where appropriate, so a self-consistent altered artifact must still
fail the independent contract. All **65 rehashed corruption controls** pass
(58 complete-control mutations and seven diagnostic mutations). The verifier does not import the capture harness.

To create new disposable runtime evidence (requires local DOSBox Staging):

```sh
python3 scripts/recover_disruption.py /tmp/yt-disruption-new --workers 6
python3 scripts/recover_disruption.py /tmp/yt-disruption-diagnostic-new --diagnostic --workers 1
```

Each destination must be new. `--only quiet-origin` offers a small capture-writer
check. Fresh clock-sensitive outcomes are additional observations, not permission
to overwrite the reviewed corpus or claim exact random-sequence reproduction.

## Recovered session and arrival rules

The native initialization draws two independent locations using the interpreted
formula **`INT(RND*(N-2))+2`**. For ordinary N=3000 the mathematical interval is
2..2999; Earth 1 and upper sector 3000 are excluded. Duplicate holes are allowed.
There is no distinctness, reachability, mines, fighters or planet-occupancy filter.
Both locations exist in login-local variables, not saved sector flags. Repeated
sensor calls in one login are stable; reconnecting with a different clock gives
a new session picture. Raw sector field 133 remains unmapped: setting it in an
otherwise safe sector does not create a hole.

The main arrival shell prints `A *-BLACK HOLE-* grabs you!`, invokes the shared
emergency-warp helper, and rechecks arrival unconditionally. This precedes mines
and hostile fighter admission. It applies at startup as well as after a command
returns to the shell. Forced warp needs neither a scanner nor manual consent nor
a positive turn balance. The original code has no finite reentry cap.

The destination helper models **`INT(RND*N)+1`**, including Earth, the current
sector and another hole. It does not select only safe or reachable destinations.
The helper's direct saved changes are the ship sector and turns; it updates its
position cache too. It does not directly move a planet, debit money/cargo, change
cloak, award a killer or destroy a ship. Subsequent arrival hazards can do damage.

The interpreted heat model uses two eager budget draws, then increments heat
when a heat draw is strictly greater than .75. At 31 heat the meltdown path consumes
the remaining turn balance. Ordinary recharge is bounded by available turns and
models `min(turns,4*heat+INT(4*RND))`. A further eager post-destination draw does not
establish a destination override: its temporary result is overwritten by recharge
handling. These are native arithmetic interpretations corroborated by retained
receipts, not a full reproduction of BRUN30 random state or extreme MBF rounding.
Text about disabled engines for a solar day does not establish a persisted damage
flag or prove a next-day repair rule.

## Returned controls and actual saved outcomes

Unless indicated, these selected controls begin with 500 turns. Counts distinguish
black-hole encounters from all calls to the shared emergency-warp helper.

| Control | Observed result |
|---|---|
| Quiet origin 1, upper 3, upper 3 with raw 133=1 | No black hole or forced warp; 500 turns remain. |
| Startup at 2 | One hole/warp; ship 3, 442 turns after 58 recharge. |
| Ordinary move 1→2 | One movement turn, then two hole/warp encounters 2→2→3; 373 turns after 55+71 recharge. |
| Scanner acceptance / refusal | Acceptance reaches the same 373 result; refusal stays 1/500. Combined mine/fighter warnings retain the same decision boundary. |
| Startup with zero turns | Still warps 2→3, charging zero; remains at zero turns. |
| One-turn movement into 2 | Movement exhausts the turn, then two forced warps still complete with zero recharge debit. |
| Startup with 7 turns | Forced warp consumes at most 7; ship 3/0. |
| Startup cloak 0 or 0.5 | Cloak remains exactly 0 or 0.5 while 58 recharge turns are spent. Forced recharge is distinct from ordinary movement's cloak threshold. |
| Startup clock 02:00 | Two hole/warp events, ship 3/298. Different selected clocks produce different realized chains. |
| Two-sector geometry | Three hole/warp events return at 1/262. |
| Manual warp | One manual warp followed by one black-hole warp; ship 3/375. |
| Autopilot 1→2→3 | Stops after the first move and a forced warp to 1; 444 turns remain. It does not finish the queued route. Scanner refusal cancels before movement. |

Mines 3 and fighters 100 placed in hole 2 are untouched when startup immediately
warps away. At a later safe-sector landing, mines damage shields and hostile
fighters reach normal admission. In `startup-landing-mines`, shields 10000→8419
after the 58-turn forced warp. In `startup-landing-lethal`, one black-hole warp is
followed by a distinct automatic mine-escape warp; mines 30→27, turns 500→386,
player death marker 45=2 and ship sector/holds/mines become zero. The retained
self-attribution is native aftermath, not evidence that disruption directly
kills, or a policy for modern enemy credit, loot or account identity.

### Planetary helper return and independent ship position

| Control | Planet / ship / turns |
|---|---|
| Ordinary thrusters finish at hole 2 | Planet2, ship forced to 1,435 turns:10 transport +55 recharge. |
| Ordinary thrusters1→2→3 with bare intermediate hole 2 | Planet and ship 3/480; no intermediate disruption check. |
| Same route stopped at 2 by mines or fighters | Planet stays 2; returned-shell disruption sends ship 1/435 before those local hazards resolve. |
| Collision at planned2 | Moving planet destroyed on failed edge; stationary planet preserved; ship 1/500 and no disruption warp. |
| Ten-turn thruster balance | Transport spends the last10, then forced warp still acts at zero turns. |
| Cancelled thrusters | No transport, charge or warp. |
| Wanderer at default clock | Planet1, final ship 1/400;10 transport +90 recharge. Matching coordinates do not imply that forced warp carried the planet. |
| Wanderer at 02:00 | Planet3, ship 1/0 with actual meltdown text. |
| Wanderer at 03:00 | Planet1, ship 3/413. |

Thus disruption is checked on returning to the arrival shell, rather than after
every safe internal planetary edge. A hazard stop returns earlier. A ship-only
forced warp leaves the transported ordinary planet or Wanderer at its own already
committed position.

### Larger-geometry controls

The 8-sector sensor control identifies holes 3/4. Separate moves to either end at
ship 6/407. In the full 3000-sector header, repeated original sensor views identify
holes 592/1051. Moves from 3000 to either end at 1981/407. Ordinary transport to 592
leaves the planet 592 and ship 1981/398. The Wanderer transport leaves its random
planet 2368 while the ship ends1810/435. Startup at 592 forces a warp to 2665/442;
Earth 1 and upper 3000 remain safe. The exact saved-world reconnect shows the old
592/1051 pair is not a persistent map hazard. These corroborate the narrow-control
interpretation without claiming a probability, distribution or exact RNG match.

Local sector displays and scanners can reveal disruption at the observed sector.
They do not justify publishing both hidden session locations in generic reports.
Transport news adds only the ordinary login notice: there is no public black-hole
or Wanderer-coordinate disclosure. The Wanderer's private disappearance receipt
also conceals its independent random planet position.

## Separate diagnostic and remaining scope

The unsupported one-sector diagnostic starts at 1 with zero turns. It observed two
black-hole/warp iterations, remained at 1/0 and timed out after 40 seconds without
a program-return marker. It establishes only bounded nonreturn in that invalid
geometry, interpreted alongside the native unconditional loop. It is neither a
completed control nor a requirement to permit one-sector modern worlds. A modern
implementation needs a declared finite chain budget and an atomic exhaustion
policy; silently committing a free partial escape would not satisfy that policy.

The [contract](CONTRACT.md) covers session lifetime, startup/command-return seams,
finite work, exact authority across prompts, one atomic save for origin movement
and reached aftermath, distinct movement/recharge charges, independent planets,
death attribution, committed warnings and private receipts. Existing Go mine
escape has a source-level heat-budget discrepancy to audit during that work; no
incidental gameplay fix is included in this research milestone.

Exact BRUN30 state, MBF extreme boundaries and full random/numeric parity remain
open. Plasma/missile deflection, spy disruption intelligence, all unrelated
command combinations and long-running balance need separate evidence. The
historical [CHANGES.TXT](../../archive/dos-original/CHANGES.TXT) corroborates
black-hole automatic warp and a startup-arrival fix, but is not runtime proof.
The prior [planetary](../yt-planet-mobility/RECOVERY.md),
[Wanderer](../yt-wanderer/RECOVERY.md) and
[scanner/warp](../yt-scanner-warp/RECOVERY.md) milestones retain their original
provenance. Native Windows durability and live BBS acceptance remain separate
from DOS research, retained-evidence verification and future Go/PTY validation.

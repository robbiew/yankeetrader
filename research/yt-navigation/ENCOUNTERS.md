# Danger scanner and emergency warp — bounded DOS recovery

Recovered 2026-10-26 from original Yankee Trader 3.6. This is a historical
research slice: combat/mine hazards and automatic escape are now implemented.
The purchasable danger scanner and manual emergency-warp command remain pending;
[the later integration research](../yt-scanner-warp/RECOVERY.md) closes their
purchase, queue and arrival gaps. Original binaries and archived experiments
remain unchanged.

## Controlled results

Thirteen completed DOSBox Staging sessions retain 26 compressed full saves,
keyboard streams, readable transcripts and emulator logs in the
[manifest](encounter-dos/results.json). Each starts in sector 100 using the
navigation graph and archived `fixture-team-captain` world, with explicit patches
recorded in the manifest. The player occupies record/slot 2; Enemy is slot 3.
Sector 101 is record 152. Original executable SHA-256:
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.

| Probe | Observed outcome |
|---|---|
| `danger-clear` | Installed scanner, clear destination: move 100 → 101, 500 → 499 turns, no warning. |
| `danger-mines-no` | Reports ten mines and disables warp. Separately answering N preserves sector 100 and all 500 turns. |
| `danger-mines-yes` | Reports one mine. Separately answering Y enters 101 and spends one turn. One mine explodes, disappears, and shields fall from 10,000 to 9,270. |
| `danger-stacked-yes` | `M;101;Y` does not approve danger. Warning discards queued Y; subsequent blank response cancels, preserving position and turns. |
| `danger-fighters-no` | Reports 100 fighters belonging to Enemy. N cancels without moving or spending turns. |
| `danger-own-fighters` | Own 100 fighters do not trigger a warning; movement costs one turn. |
| `danger-no-scanner` | Entering the one-mine sector offers no scanner confirmation. Movement costs one turn; mine/shield transitions match the accepted case. |
| `danger-autopilot-no` | Confirming the course, then separately declining its first dangerous hop, preserves sector/turns at 100/500. The course does not continue to 110. |
| `warp-cancel` | W warns about recharge and meltdown; N preserves sector 100 and 500 turns. |
| `warp-default` | Blank confirmation also cancels. |
| `warp-yes` | W;Y reaches sector 60 and charges 55 turns, leaving 445. Sector 60 is not an outgoing neighbor of 100. |
| `warp-one` | W;Y works with one turn: reaches sector 60 and consumes the remaining turn. |
| `warp-zero` | No engagement or movement at zero turns. |

Mine damage and warp destination/cost above are recorded outcomes, not universal
constants or probability estimates. Exact RNG/MBF parity is not established.
Warnings themselves cost no turn. Confirmed entry pays normal movement cost and
then runs the encounter; a scanner does not make accepted travel safe.

## Static cross-checks

Runtime-aware annotated listing anchors:

- Main `1000:1c3e..1cae`: installed-scanner check, danger call, queued-command
  clearing and `Move into sector …? [y/N]` confirmation.
- Sub2 `2e79:194e..1d34`: destination validation, disruption/mine/fighter
  warnings, owner/team checks and warp deactivation. Sector mines are at record
  offset 129, fighter count/owner at 81/85. Player scanner flag is at 93
  (`-1` installed, `0` absent in these fixtures).
- Main `1000:15a9..161a`: manual emergency-warp warning and affirmative gate.
- Sub `1f42:9fc4..a400`: temperature animation, random destination/recharge
  work, meltdown path, turn clamp and committed position/turn changes.

[REA evidence](encounter-rea/evidence.json) retains Ghidra 12.1.4 observations:
`ev_66cbaa8cb9f56563dc9c38be2cb7c7f43a2aecc92762b37695b758ee79746b24`
finds scanner strings; byte reads at linear `0x300de` (danger entry) and
`0x293e4` (emergency-warp entry) match the annotated listings. These use REA's
DOS load segment `0x1000`; linear addresses are not file offsets. The ephemeral
session was closed. QuickBASIC runtime calls make ordinary decompiler control
flow insufficient to prove gameplay; save/transcript comparisons establish the
specific outcomes above.

## Reproduction and verification

```sh
python3 scripts/recover_navigation.py /tmp/yt-encounters-new --only \
  danger-clear danger-mines-no danger-mines-yes danger-stacked-yes \
  danger-fighters-no danger-own-fighters danger-no-scanner danger-autopilot-no \
  warp-cancel warp-default warp-yes warp-one warp-zero
python3 scripts/verify_encounter_evidence.py
```

Destination must not exist. The runner resolves DOSBox Staging on PATH;
`--dosbox` selects another executable. It mounts copied fixtures only and fixes
DOS date/time to 2026-10-24 00:00:00. `~` is a keyboard-feeder delay, not a game
command. Responses must arrive after scanner warnings clear stacked input.
The verifier needs no emulator: it checks source/executable/feeder identity,
snapshot/input/transcript hashes, patched fields, graph, completion and outcomes.
Randomized replays may produce different damage, destinations and recharge costs;
inspect new transcripts/saves before changing recorded expectations.

Validation on 2026-10-26 passed the encounter, navigation and avoid-list evidence
verifiers, archive verification (4,682 files), and `git diff --check`. Negative
controls separately corrupted a transcript and changed a declared turn outcome;
the encounter verifier rejected both. No Go gameplay code changed in this slice.

## Remaining research and implementation constraints

- [Disruption, mine scanner damage and automatic escape](HAZARDS.md) now add
  46 completed sessions. Other weapon damage and fighter escape remain separate.
  Team passage, sensor cloak visibility and manual-warp
  accounting are covered by the follow-up below. Exact MBF/RNG boundary parity
  and live encounter acceptance remain separate.
- Hostile fighter escape remains separate; automatic mine escape and black-hole
  warp are now covered in the hazard follow-up. Prior Earth mine/respawn evidence is in
  [ship recovery](../yt-ships/RECOVERY.md).
- Establish combat/death and session invalidation before enabling hazards in Go.
  Confirmation must revalidate live position, hazards, defenses, ownership and
  turns. Autopilot must stop for a new danger decision and preserve completed
  moves on interruption.

The user's live BBS test on 2026-10-26 confirms the Go door loads. Encounter
acceptance remains separate because these features are not implemented.

## Cloak, teams and warp follow-up — 2026-10-26

[Follow-up evidence](followup-dos/results.json) adds **42 completed DOS sessions
and 84 full save snapshots**. The combined encounter research now has 55 sessions
and 110 snapshots. No executable was patched to force a random result.

### Sensor visibility and team passage

- `cloak-none`: Enemy appears on sensors without a shimmer message.
- `cloak-full`: cloak energy 1 hides Enemy completely in the adjacent scan.
- `cloak-weak`: approximately 0.000001 cloak reveals Enemy on the first scan;
  the second scan still shows it, without another shimmer.
- `cloak-half`: 0.5 cloak hides Enemy on the first scan, reveals it with a shimmer
  on the second, and keeps it visible without a shimmer on the third.
- All four cases preserve Enemy's **stored** cloak energy exactly and spend no
  turns. Detection changes the current session's cached visibility.
- `danger-team`: both humans are members of team 1; player 2 passes player 3's
  100 sector fighters without a scanner warning, spending one turn. Neither
  the ship fighters nor the deployed fighters change; owner stays player 3.
- `danger-other-team`: the players are on different valid teams. The scanner
  warns and a fresh N preserves the original position, turns and fighter counts.

Sub `1f42:5e71..5f29` compares a random draw with the cached cloak fraction:
positive cloak is revealed when `RND > cloak`; equality stays hidden. On reveal,
the cached entry is cleared, not the ship's saved energy. This interpretation
is modeled in [encounter_rules.py](encounter_rules.py). It does not establish
reconnect cache rebuilding, every anti-cloak path or a measured detection rate.
Direct attack and anti-cloak recovery remain in [ship research](../yt-ships/RECOVERY.md).

### Emergency-warp rules

The varied warp series includes 16 scan counts, 12 starting DOS clock hours,
and eight current-sector redisplay inputs with Enemy present. They exercise the
normal random stream through original game inputs. The clock series records its
starting time explicitly; other cases start at 00:00:00 on 2026-10-24. These are
branch probes, not an unbiased statistical sample.

The runtime-aware interpretation of `1f42:a0a2..a3fd` is:

1. Set a loop budget from `70 * (RND + RND)`, using independent draws.
2. Each iteration increases the temperature gauge if a new draw exceeds 0.75.
   Stop at 31 marks, or at the loop budget.
3. Choose a destination using the integer part of `RND * sector_count`, plus 1.
   This helper does not search the warp graph. The earlier sector-60 result
   already demonstrates escaping the fixture's closed 100–110 route graph.
4. Normal recharge costs `4 * gauge_marks + integer_part(4 * RND)`, capped at
   remaining turns. Every normal follow-up result matches the resulting 0–3
   jitter. The earlier one-turn case confirms the cap.
5. At 31 marks, **meltdown consumes all remaining turns**, while still moving
   the ship to the chosen destination.

`warp-clock-02`, starting at DOS 02:00:00, naturally reaches 31 marks and prints
MELT DOWN, engines disabled and the solar-day repair message. Its completed save
moves sector **100 → 219** and turns **500 → 0**. It then quits normally. This
establishes the actual branch and saved accounting, not a meltdown probability
or next-day repair test.

There is an ineffective-looking >0.95 random branch at `a1e9..a1fd`: destination
has already been copied from temporary `5c1a` into `5c1e`; the branch then writes
`5c1a`, which recharge calculation overwrites. The research model preserves this
extra draw but does not turn it into a destination override. This is a static
observation, not a separately instrumented branch outcome.

The original linear decoder missed the inline exponent byte after runtime
selectors `3f/ab` and `3f/ad`, making `a20f`/`a21a` look like x86 instructions.
[YT bytes](encounter-rea/followup-yt.json) and the
[BRUN30 handler](encounter-rea/followup-runtime.json) show those selectors consume
an inline byte; here `02` scales by four. The original BRUN30 SHA-256 remains
`3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8`.
REA sessions were closed. The model uses mathematical integer parts and injected
random values; it is not an MBF emulator or a reconstruction of the exact RNG.
Zero-cost recharge is possible in the mathematical model but was not observed
in these DOS runs. No modern balance policy is chosen here.

### Follow-up reproduction and checks

```sh
python3 scripts/recover_navigation.py /tmp/yt-encounter-followup-new --followup
python3 scripts/verify_encounter_followup.py
```

The feeder retries normal quit commands after delays because display and warp
animation routines consume typeahead. Only completed sessions are packaged.
Failed timing probes were excluded. The verifier checks hashes and provenance,
clock metadata, cloak persistence, team conservation, gauge/recharge relations,
the completed meltdown and injected model branches. Randomized replay need not
reproduce every recorded destination or damage value.

Validation on 2026-10-26 passed both encounter verifiers, the navigation and
avoid-list verifiers, all 4,682 archive checksums and `git diff --check`. Negative
controls rewrote stored cloak energy and meltdown turn accounting, recomputing
their snapshot hashes; the follow-up verifier still rejected both semantic
changes. No Go gameplay code changed and no publication was performed.

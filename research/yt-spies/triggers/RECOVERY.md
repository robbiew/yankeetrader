# Spy triggers, shared detection and target notifications

This is original-DOS research, not a Go gameplay update. The existing Go spy
network remains playable with its documented policies; implementation of the
newly recovered differences requires a separate milestone.

## Evidence and reproduction

The unmodified DOS 3.6 `YT.EXE` is identified by SHA-256
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
The runner copies synthetic fixture worlds and binaries into disposable
execution directories. It never mounts or changes the archive or live BBS data.

```
python3 scripts/recover_spy_triggers.py /private/tmp/yt-spy-triggers-new --workers 6
python3 scripts/verify_spy_triggers.py --dos /private/tmp/yt-spy-triggers-new
python3 scripts/test_spy_triggers_verifier.py
```

The 36 normally returned controls and three exact target-relogin chains are
retained under [dos](dos/recipe.json). Every successful control
retains exact keys, raw/normalized logs, DOS date/time reports, an explicit
program-return marker (the reused engine emits `BROADCAST_PROGRAM_RETURNED`),
full compressed before/after worlds and before/after
auxiliary files. Child target logins start from the parent's exact final world
and all auxiliary outputs, without patches. Date is 10/24/2026 and each DOS
session explicitly starts at 00:00:00; this is not a claim of a monotonically
advancing clock across reloads. Fixed clocks/key feeds do not prove identical
random sequences across hosts. The verifier requires the stated positive/negative
witnesses; a different branch on recapture is a diagnostic to investigate, not a
reason to relabel or weaken the evidence.

The runner reuses the hardened copied-world capture engine from
`recover_broadcast_lifetime.py`. Its declared root patches clear an otherwise
unrelated planet pointer at sector 102 and port pointer at 101. The three-sector
spy route is 101→102→103→101; caller movement uses 1↔100. There are no injected
spy arrays: one or three spies are hired through Earth's ordinary shop.

Pilot captures outside the retained corpus exposed the inherited sector-102
planet pointer. Those runs cannot establish traversal through empty sectors.
The final suppression controls explicitly clear it, and separately introduce
mines in sector 102 for the alternate-finding comparison. This distinction is
checked by the verifier, not inferred from a run's name.

The original looting plasma pilot struck unrelated baseline ships in sector 100.
It is not used for resource-conservation claims. The retained positive-plasma
control instead targets one declared three-million-shield ship in sector 2, which
absorbs the bolt without death or loot. A separate unreachable-course control
records that accepted positive input can consume the launch and advance spies
before targeting later fails; it does not claim a projectile hit.

## Command-trigger results

Spies scan their current sector before selecting the next warp. They do not
advance on every command or every resource transfer.

| Tested action after hiring | Observed spy progression |
| --- | --- |
| List, ship information, sensors, help, ordinary port report | None |
| Own planet's full report; ordinary foreign planet's name/ground report | None |
| Accepted ordinary move | One step |
| Dock where a port exists | One step |
| Dock where there is no port | None beyond any earlier move |
| Accepted fighter transfer, zero transfer, excessive request | No additional step |
| Drop one mine | No additional step |
| Positive cruise-missile/plasma launch | One step before the integrated launch aftermath |
| Accepted positive plasma input, later unreachable course | One step; launch turn and bolt consumed despite no impact |
| Zero/negative/excessive tested launch quantities | No additional step |
| Computer 9 unavailable planet information: no planet or hostile sector defenses | One step and one additional turn consumed |

A foreign planet's ground troops alone do not make information unavailable:
the control reports `Planet: Test Planet -*- Ground Forces: 12` without a spy
step. The protected-sector control separately installs hostile sector fighters.
The no-planet query also takes the unavailable-information path. These failed
information queries are consequential actions in DOS, unlike ordinary successful
report reads.

[Native evidence](NATIVE.md) anchors four direct BASIC GOSUB encodings in the
complete main code region: movement, the shared missile/plasma launch path,
docking and unavailable Planet Report. Earlier notes mistakenly classified the
launch site as fighter deployment. The byte search is complete for that exact
encoding and region; it is not an exhaustive proof about indirect dispatch,
every command alias or all failed-action branches.

## Report suppression and multiple spies

`last reported sector` differs from `last visited sector`. An empty scan does
not replace the last report location. A spy can traverse empty sectors and
return to the last reported sector without reporting it again. A finding in a
different sector changes that remembered location and allows the original
sector to be reported on a later revisit.

Three spies hired at the same location report independently in spy-number
order. One spy's report does not consume another spy's report or movement.
The routes and complete ordered headers/locations are verified, including
intermediate positions rather than only the final sector.

## Detection sharing and saved cloak

A successful partial-cloak spy report prints
`The spy detected the shimmering of a cloaking device!` before the ship details.
A subsequent sensor report in the same login displays that ship without a second
`You detect the shimmering...` notice. The no-spy partial-cloak sensor control
provides the corresponding independent detection notice. A full-cloak control
supplies the negative visibility comparison, and an uncloaked control supplies
the positive ship-report comparison.

The static result is stronger than spy-only memory: spy detection clears the
same observer-local cached cloak slot used by adjacent sensors and ship attack
eligibility. It does not clear the target's saved cloak. The attack-choice
controls show `Attack Enemy (Y/N)` after a spy shimmer, with no ordinary detection
notice; the no-spy control also eventually offers the attack after its own ordinary
shimmer notice. The full-cloak comparison offers no such candidate. Both offered
attacks are declined with N. These are visibility/eligibility witnesses, not a
claim that spies are the only way to expose a target or that the sampled random
sequences are equivalent.
No battle, target damage or target warning is inferred from an attack prompt.
The full-hidden attack branch clears queued input before its final requested spy
list, so only the actually displayed intermediate locations are claimed there.

This is visibility within the observer login, not a reveal to all players.
Runtime and native evidence are kept separate: selected successful controls
corroborate the tested cache consumers, while broader indirect cache writers,
concurrent DOS sessions and exact RNG/tie behavior remain unknown.

## Target-notification boundary

The successful spy-detection path does not create a radio packet in the tested
world. Its ordinary login newspaper append is distinct from a spy notification.
Exact target reloads retain an empty radio mailbox and show ordinary login/
history, without a new spy or cloak-detection warning. Target saved cloak and
ship assets are checked separately from normal login/score bookkeeping. The
positive-plasma control has an ordinary public weapon-hit notice; its text and
shield amount are checked as launch aftermath, not misclassified as a spy warning.

Native review identifies the apparent detection helper as sound/presentation
selector 4, not a target-message sender. The complete bounded spy body contains
no direct BASIC PUT or explicit foreign-target mailbox write. Together with the
runtime chains, this supports **no persistent target notification on the tested
spy-detection route**. It does not prove that no other game event, future login
condition or concurrently running process could notify a target.

Do not turn the former “target notifications pending” backlog into an invented
notification feature. Any notification beyond the recovered path would require
separate evidence or an explicit modern design choice.

## Validation and remaining work

The independent verifier anchors the recipe, fixture identity, actor and alias,
exact keys/clocks/return, full starting snapshots, exact auxiliary parent edges,
ordered report/ship fields and action-specific resource effects. It checks
semantic outcomes and allowable bookkeeping footprints rather than accepting
refreshed self-reported hashes as proof. Rehashed corruption controls exercise
both meaning and provenance. [Native byte verification](NATIVE.md) independently
reconstructs all 870 relocations, the 20 complete observed ranges and the bounded
four-match search.

This milestone changes no Go source, saved-world fields or dependencies. The
current version-27 format and independent radio read flags remain unchanged.
The follow-up [implementation contract](CONTRACT.md) separates recovered rules,
current Go differences and deliberate safety policies. Exact DOS RNG/MBF parity,
all command aliases, online simultaneous-writer behavior and live BBS/native
Windows acceptance remain separate.

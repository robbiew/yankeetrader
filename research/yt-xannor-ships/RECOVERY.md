# Xannor ship battles and maintenance aftermath

This research preserves **42 completed original-DOS maintenance runs**, 84 world
snapshots, an exact next-day world chain, changed private/public side files and
**11 complete REA byte observations**. It recovers ordinary mobile ship
interception, fighter/shield rounds and the maintenance death path. No Go
encounter is enabled and no save schema changes in this milestone. The bounded
[mobile implementation](../yt-xannor-mobile/IMPLEMENTATION.md) still holds before
live ships and foreign planets.

Target: original `YTMAINT.EXE`, SHA-256
`8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6`;
BRUN30 SHA-256
`3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8`.
Experiments copy unmodified binaries and archived side files into new disposable
DOSBox mounts. Archive and live BBS data are never mounted for execution.

## Finding ledger

| Question | Answer and evidence boundary |
|---|---|
| What makes a normal encounter eligible? | Cached player sector must match the arriving group and `RND > cached_cloak - .33`. Group 20 has separate dispatch. Static bytes; low/full-cloak and protected/origin/endpoint controls. |
| Does the helper trust cached location? | It rereads the player's live sector and compares it with the group location. Static-derived; no concurrent DOS writer was introduced. |
| Are dead players excluded? | The cache uses the nonempty-name indicator, not death marker 45. Diagnostic dead records retaining positive sector 101 are still attacked. This is a defect, not a valid modern target rule. |
| What fights first? | Ship fighters, then shields if Xannor remain. Separate fighter-only, shield-only and staged controls. |
| Which casualty batches? | 5000 only when both remaining forces exceed 5000; otherwise 500, reduced to 1 if either is below 500. Static + 499/500/5000/5001 controls. |
| Which side loses at an exact tie? | Fighters: `RND <= .5` kills humans. Shields: `RND >= .5` damages shields. Equality is established statically and in the injectable model, not by claiming a forced DOS random draw. |
| Do missiles return fire? | No missile access in these helper paths; 0, 7 and 100000 carried missiles produce the same fighter/shield outcome in paired midnight runs and remain unspent. |
| Can one group attack several ships? | Yes, in ascending record order while force survives. Two-ship controls distinguish loss on the first ship, first-ship death and two deaths. |
| Does a survivor continue its route? | Yes. A winning group reaches later mines; a group destroyed by the ship leaves later mines untouched. |
| What is the killer/death state? | Killer marker -1, sector 0 and human fighters 0. Dead records retain credits, cargo/equipment and carried mines in these controls. Exhausted shields can incorrectly retain their old saved value. |
| What happens to estates? | Personal ports are released and their treasury cleared; sector fighters become Mercenary; planetary titles remain; team membership is removed while the captain field can remain stale. Runtime + shared helper bytes. |
| Is salvage or a wreck minefield created? | Neither occurs in this maintenance ship-death path. Carried mines remain on the dead record and no new sector mines appear. This differs from direct player kills. |
| How are events delivered? | Private casualty/shield/death messages use 86-byte YTRMSG records. Battle summaries also enter YTNEWS, including surviving shield values. These are DOS observations, not a modern privacy policy. |

## Isolation and provenance

The baseline is the independently verified [mobile isolation world](../yt-xannor-mobile/RECOVERY.md):
3000 sectors, 1000 ports, 100 planet slots, HQ 1114 with one fighter, mobile group
2 at sector 100 with 100 fighters, path 100 → 101 → 1114, Q in player record 2 and
stored score 4000. The new baseline changes only Q's sector to 101, cloak to 0,
credits to 12345 and carried mines to 5. Q starts with 1000 fighters and 10000
shields. Initial Xannor strength 101 exceeds score/100, while HQ 1 is below
score/2000, so regeneration and later missing-slot allocations are suppressed.
Every independent preserved run verifies zero regeneration and exactly one
mobile group activation. Cases using larger groups preserve that isolation.

The baseline's raw SHA-256 is
`ffa58f171db5efe4e325846346fa826daee4e35c0193a3ba666546ec9fd666ef`.
[Frozen recipe](dos/recipe.json), [manifest](dos/results.json) and the verifier
bind every modified field and raw text copy. A second ship is a declared copy of
Q into record 3, renamed R before explicit patches. No out-of-range pointer or
undeclared player is needed to produce the battles.

The team captain case changes team fields in sector record 52 while preserving
its overlaid HQ pointer at offset 105. Team captain is field 77; it remains 2
after victim 2 is removed from member field 109, with member 3 retained in field
117. The coincident sector offset 105 must not be mistaken for the team captain.

`kill-assets` seeds an ordinary port owner at **97**, treasury at 89, cached
personal port count at player 117, a victim-owned planet at planet 73, and 37
human sector fighters in sector 300. Sector 300 is outside early Union cleanup.
The death helper's Mercenary conversion is followed by an actual later
Mercenary phase: the transcript shows 37 Mercenaries departing sector 300 and
subsequently losing a battle. Therefore their final absence is not evidence
that conversion failed. The controlled disconnected two-sector graph also
produces a bounded path-error report before those later Mercenary actions;
this run does not establish new Mercenary routing semantics.

Most runs request DOS date 10/25/2026 at midnight. Cloak controls additionally
sample 04:00, 08:00, 12:00, 16:00 and 20:00. Captured clocks are checked within
one second. The next-day child starts from `strong-ship`'s **exact final world**
at 10/26/2026, without reset or field patches. It exercises the saved post-battle
world and later score-driven maintenance; it is not a second isolated attack.
Side files are freshly copied, so the chain is a world-state chain, not a claim
that private message files or scoreboard history were chained.

Each process has a 45-second deadline; all 42 preserved runs completed normally.
Earlier exploratory 1/10-fighter cases allowed score-driven regeneration, and
initial asset/team probes overlapped earlier Union cleanup or the HQ pointer.
They are excluded from this isolated suite. Their temporary directories are not
counted as evidence for the conclusions here.

## Eligibility and order

The initial maintenance cache (`052e–0636`) uses active-name field 85. Positive
cloak loses .05 and is clamped at zero before being saved/cached. Normal route
interception (`3baa–3c66`) compares cached position and the `.33` detection
adjustment. Full cloak therefore becomes approximately .95, with a threshold
near .62. At 00/04/08/12/16 the captured full-cloak runs skip the ship; at 20:00
the ship is intercepted and loses 115 fighters. These are samples, not a
measured probability or bit-exact RNG guarantee. Diagnostic cloak 10 isolates a
skip; it is explicitly outside the modern valid 0–1 range.

Battle helper `5811` checks target record range, positive group force/location,
valid sector bounds and the player's reread sector. It does not check death,
team or missiles. The deliberately inconsistent dead-record cases keep positive
sector and test only that missing death predicate; ordinary deaths from this
same helper clear sector/cache and prevent a second encounter that day.

Origin ships are ignored because dispatch runs after a hop. Endpoint ships at
HQ are attacked before return/merge. Mines and sector defenses precede ship
interception: a strong sector garrison can destroy the group without damaging
the ship. Group 20's separate hunt and revenge selection remain described by
the [previous research](../yt-xannor-mobile/RECOVERY.md); this suite does not
claim to recover all candidate-search behavior.

## Battle arithmetic and persistence

Let G be remaining Xannor, F human fighters, S shields. All runtime controls use
whole units. For either battle phase:

```text
batch = 5000 if both remaining sides > 5000 else 500
batch = 1 if either remaining side < 500
```

First, while G > 0 and F > 0: draw RND; if R > .5 subtract batch from G,
otherwise subtract batch from F. Only if G remains do shields fight: if R >= .5
subtract batch from S, otherwise subtract batch from G. Cloak does not enter
these casualty loops. Both batch thresholds are strict at the large boundary;
499 uses unit rounds, 500 and 5000 use 500, and 5001 starts with 5000 before
possibly reaching unit rounds. Valid whole-unit batches cannot overshoot.

The helper tracks cumulative Xannor losses and human fighter losses separately.
The public `lost N, dstrd M` line means Xannor lost N and human fighters lost M;
shield damage is not included in M. In `shields-only`, Xannor lose 100 and human
fighter losses are zero, while shields fall from 10000 to 9897.

Human fighters are written after their phase. Shields are written **only if
still positive**. Consequently the weak ship's private message says shields
became 0 and its death is saved, yet shield field 53 retains 1; the killed
500/5001-shield controls retain 500/5001. Modern code must save actual zero
shields and settle death once, never treat those stale values as surviving force.

A destroyed group saves zero force and zero location and leaves the encounter
sector as shared pursuit output. A victorious group subtracts its casualties,
clears the defeated target's cached position/cloak and continues the ordered
ship scan and remaining route. These output rules extend the prior mobile
research rather than creating new independent group activations.

## Death, ownership and messages

Shared helper `6924–6c07` clears the victim's sector and cached position/cloak,
stores killer -1 and clears its cached owned-port count. It walks ordinary ports
and clears owner 97 and treasury 89. It scans sector defenses, replacing the
victim's owner ID with Mercenary -2 while retaining force at that point. It
removes matching team roster entries and clears the victim's team ID. It does
not retitle planets, distribute salvage or create a wreck minefield.

The team captain remains the dead player's ID in the saved control; later
visiting-member succession is a separate login behavior. Existing modern team
and estate safeguards should remain authoritative.

The preserved `sidefiles.json` files contain exact changed-file bytes and source
hashes for YTRMSG, current/prior newspaper and scoreboard. Private records contain
sender, recipient and cause MBF values followed by the message. The verifier
checks exact victim delivery of casualty and death messages, public battle
publication and post-death inventory retention. No real caller data is involved:
all players are the declared copied Q/R fixtures.

## Static evidence and limits

[Complete REA records](rea/ship-paths.json) bind the shipped executable digest,
Ghidra 12.1.4 profile, returned bytes and explicit limitations. The verifier
independently applies MZ relocations at load segment 0x1000 and checks every
retained byte. Code CS offsets map to file offset CS + 0x200 for this image;
REA addresses are linear load coordinates. Data segment addressing must not be
confused with code offsets: double constants 5000/500/1 reside at image offsets
9850/9858/9892, and the single .5 constant at 92f0.

The 11 records cover initial cache, dispatch, complete ship/ownership helpers,
field context and constants. Static equality rules are tested in the
[injectable reference model](recovered_rules.py). The model is not a BRUN/MBF
emulator; exact RNG sequence, fractional/large-number rounding, asynchronous DOS
writes, full group-20/revenge selection and NPC planetary assault remain limits.
The original loops do not establish a modern bounded-round or atomicity policy.

## Next implementation contract

Implement Xannor ship encounters in the bounded route phase using current,
living, generation-bound players, outside protected Union sectors. Revalidate
sector and ownership under the world transaction; copied cached position alone
must not grant attack eligibility. Retain the separate detection gate and
fighter-before-shield order, with a finite work budget shared with route work.
Never reschedule a receiving/returning group in the same maintenance pass.

Extend the existing one-time death/estate machinery with explicit Xannor
attribution, zero spent force, safe team cleanup, checked capacities and atomic
rollback. Define how NPC port/defense/planet ownership follows the supported
modern estate policy; do not copy stale captain/retained-shield defects or assume
that direct-player salvage/mined wreck rules apply to this distinct death path.
Deliver battle details privately and deliberately choose any public journal
summary rather than exposing exact surviving defenses by accident. Test
same-date replay, concurrent maintenance/login, stale sessions, multiple victims,
route continuation and save failure/reload before enabling these encounters.

Planetary assault/destruction and remaining revenge/cloak search follow this
ship milestone. Live BBS acceptance remains separate from local research.

## Reproduce and validate

From the repository root, in a fresh destination:

```sh
python3 scripts/recover_xannor_ships.py /tmp/yt-xannor-ships-new
python3 scripts/verify_xannor_ships.py
python3 scripts/test_xannor_ships_verifier.py
python3 scripts/verify_archive.py
```

The runner requires DOSBox Staging; evidence verification requires only Python.
Use `--only` to select cases; child-only replay requires `--parent-world` pointing
to the exact parent's compressed after-world. Replays may draw different random
results and require preserving a new observation set rather than overwriting
these captures. Nine rehashed negative controls reject incorrect casualties,
shield persistence, planetary/team cleanup, later mines, record order, force
creation, broken world chain and private-message delivery.


The [bounded Go implementation](IMPLEMENTATION.md) now enables these ship
encounters with explicit corrections for stale lifecycle state. The original
research above describes DOS observations; implementation policies and current
save version 15 are documented separately.

# Super-planet lottery, inactivity deletion and maintenance ordering

This research preserves **41 normally completed original-DOS maintenance runs**,
exact before/after worlds and auxiliary-file chains, and **18 complete REA byte
observations** from the original maintenance executable and BASIC runtime. It
adds an executable static rule model and independent semantic verification,
including eleven deliberately rehashed corruptions that must fail verification.
**No Go gameplay or save-schema change is included; save version remains 17.**

## Recovered rules

| Question | Result | Evidence boundary |
|---|---|---|
| Who can be deleted? | A named slot whose last-play day is at or before `today-delay`, with a nonzero death marker. Old living players stay. | Ages13/14/15 at delay14; positive/negative death markers. |
| Does zero disable deletion? | No: delay0 can delete a dead player last seen today. Negative delay is not a disable sentinel either. | Delay0/−1/30 controls. |
| What happens on cloak expiry? | Named cloak decays by .05; expiry skips that player's age test for that run. Negative cloak normalizes to1, then decays. Unnamed slots skip the whole block. | .01/.05/.1/−1 controls and an exact next-day expiry chain. Unnamed nonzero cloak is static/model-derived. |
| Does age survive New Year? | Yes: the configured starting year feeds a cumulative day counter; December31 day365 advances to January1 day366. | Exact year-boundary world/auxiliary chain. Century/leap limitations below. |
| What triggers an award? | Gate `RND>=.5`, then one player slot, one planet slot, one sector. Failed eligibility ends the draw. | Static control flow, lazy-draw model, three clocks and occupied/missing controls. No measured RNG distribution. |
| Is the winner necessarily living? | No. The local test is only nonzero name length after earlier cleanup. | All recent-dead players remain named and one wins; all old-dead players are removed before the lottery and nobody wins. |
| Is a new planet completely initialized? | No. Rates/name/owner/ground/bank and several stocks change, but date/time, fighters and plasma can survive from an inactive slot. | Diagnostic free-slot control plus next-day catch-up. |
| Are protected sectors and reserved slots excluded? | No such local test exists. Selection spans sectors1–3000 and planet slots1–100. | Static/model-derived. No native Union award or reserved-slot overwrite is claimed. |
| Is an occupied sector skipped by retrying? | No. A positive planet reference aborts the draw. Mines are not checked by that predicate. | Occupied selected-sector control; the same selected sector with five mines receives an award and retains its mines. |
| Is a same-day run a no-op? | No. “Maintenance not needed!” is printed, then execution falls through. | Exact same-day world/auxiliary chain completes and changes the world. |

## Fixture and artifact identity

Original executables are copied into disposable DOSBox Staging mounts. The
preserved archive and live BBS world are never executed in place or modified.

- `YTMAINT.EXE` SHA-256 `8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6`.
- `BRUN30.EXE` SHA-256 `3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8`.
- Canonical input is independently rebuilt from the preserved lifecycle baseline
  and archived player template. The resulting baseline SHA-256 is
  `f33c07c40113b4c89b73acf9892fdeb54abb04d1c9694885d8fd4e54b920f339`.
- The frozen [recipe](dos/recipe.json) declares all mutations and has SHA-256
  `7134e217504933ceaa27014e3685be305ed2706985de3122f6adb5f28d0f0fd7`.

Ordinary controls use October25,2026 and midnight,04:00 or08:00 DOS time.
The saved chains include October26 and December31→January1. Each run retains
actual DOS DATE/TIME captures, its normal-completion transcript, compressed
world snapshots, original auxiliary payloads, changed auxiliary payloads and
hashes. All five child runs inherit their parent's exact world **and auxiliary
files**. The fixture uses synthetic account/password strings only.

Q is a named, protected-sector player; the lottery controls fill all50 player
slots with fresh aliases. Stored scores initially zero suppress unrelated
regeneration; later chains inherit genuine published scores, so some activate
mobile Xannor groups. Non-Union outgoing paths are removed; those groups print
missing-path diagnostics rather than reaching players or planets. Existing
faction homes remain present. These are deliberately controlled worlds, not
normal playable universes or native live-BBS acceptance tests.

## Inactivity predicate and cleanup

Annotated maintenance code `1000:052e–079b` first checks name indicator85. It
normalizes negative cloak to1, subtracts the single-precision .05 constant from
positive cloak and clamps at0. The precise `.05` input reaches zero; a host
float64 subtraction without the BASIC single rounding can misclassify it.
A newly expired cloak sends an expiry notice and jumps directly to the next
player at `06dd`, bypassing deletion. Already-zero or still-positive cloak
reaches the ordinary age test.

The deletion predicate at `06e0–0714` is:

```text
named AND last_play_day <= current_game_day - configuration[77]
      AND death_marker != 0
```

This is retirement of old **dead** slots, not indiscriminate inactivity expiry.
The last-play date itself is unchanged. A positive or negative death marker
qualifies. A zero delay deletes qualifying same-day dead players. In the zero
and negative delay fixtures both Q and the second recent dead record qualify;
the verifier checks their combined roster/radio/name cleanup.

Cleanup `6c0d–7033` performs these writes:

- Clears the victim's name indicator85, team89 and raw auxiliary field105,
  together with run-local cached position/cloak. Raw alias, sector, death marker,
  equipment and money remain stale in the inactive record. Later scoreboard
  publication sets its stored score to−1.
- Clears matching entries in the four team roster fields. The raw captain77
  remains the deleted ID. Our synthetic team record has no active name, so this
  proves roster/captain field behavior, not active-team presentation or password
  handling.
- Releases all planets with owner73 equal to the victim and clears their
  ground77. Names, links, banks and stocks remain. Subsequent ordinary production
  can immediately regrow neutral ground: the million-credit, one-day fixture
  ends with100 ground after the cleanup's zeroing.
- Clears matching sector defense owner85 and fighters81.
- Rewrites another player's death attribution equal to the deleted ID to−98.
- Marks radio records with the deleted sender or recipient read; it does not
  erase their payload at this point.

Ordinary port ownership is **not** released. Both the living and deleted control
retain active non-Earth port3053 owner97=2 and treasury89=9. This orphan title is
a legacy defect, not a safe modern transfer policy. Port101 is the last-production
minute timestamp; its midnight reset is not a treasury or ownership write.
Historical descriptions of101 as a paired owner must not override these fields.

The `YTNAME.DAT` filter (`7039–714f`) compares the deleted alias with CSV field3
plus a literal blank plus field4. Both synthetic duplicate Q alias rows are
removed, while R and Other User remain. Standard one-word Q includes its
separator blank in name indicator85. Comparison uses exact bytes/length, not an
account ID. This does not establish modern duplicate-account deletion behavior.

### Radio compression happens first

At `048f`, helper `672d–68d6` copies only records with a nonzero unread marker.
Deleted-player messages are marked read **later** during player cleanup. The
next run therefore physically removes those records. The exact deleted-next-day
chain starts with three messages, leaves the two Q-related messages marked read,
then retains only the unrelated third message on the following run. The expiry
chain retains its private expiry mail before deletion suppresses it.

The original86-byte record has three MBF singles (marker, recipient, raw sender)
and72 text bytes plus two trailing bytes. Compression rebuilds the trailing two
bytes as zero. Original daily compression can remove already-read history even
without deletion; it is not an immutable historical journal.

### Day calculation and rollover

Caller `0307–034a` reads the starting year from config45 and inactivity delay
from77. Helper `79e3–7d05` computes month/day offsets, adds elapsed years and uses
a divisible-by-four leap rule. The new native chain retains last-play day352
on December31 day365, then deletes it at the inclusive14-day boundary on
January1 day366.

Century exceptions are absent. A current two-digit year below the starting year
gets100 added; a backward clock crossing that boundary can look like a century
advance. Those century/rollback cases remain static-derived and were not run.
Modern code should use its authoritative saved date and existing replay policy.

## One-shot super-planet award

The local code at `5371–576e` executes these stages:

1. A gate draw below.5 ends with no winner; equality enters.
2. Choose one player record2–51. A zero name indicator ends the draw.
3. Choose one planet record4052–4151, including nominal reserved slots. A nonzero
   name indicator ends the draw.
4. Choose one sector1–3000. A positive planet reference ends the draw. The exact
   local acceptance predicate is `planet_reference<=0`, without mine, defense,
   owner or Union checks.
5. Reuse that planet record and publish its sector link and success notices.

There is no search/retry after these failed tests. The bound helper `78f3–7933`
uses the BASIC random/seed machinery before constructing `INT(RND*bound)+1`.
The injected-draw model describes control flow and endpoints, not the original
RNG stream, independent sampling or a measured50% award frequency. A successful
model path uses12 draw values; those are not instrumented native RNG counts.

The reused planet receives alias + `"'s Planet"`; three production rates each use
`RND*RND*3000`; cargo, missiles and mines reset to0; owner becomes the selected
player record; ground is `INT(RND*100+1)` (1–100); bank is `RND*1,000,000` without
integer truncation. Date41, time89, fighters129 and plasma113 are **not written**.
The sector's reference93 is set to the planet slot; no separate planet-sector
field is updated.

The dirty-slot award retains date111, time222,37 fighters and5 plasma. Its exact
next-day chain runs the existing ten-day catch-up limit and ends with more than
40,000 fighters. This demonstrates stale-slot contamination, not intended fresh
planet defaults. Normal award controls also preserve date0 until the next update.

The positive mined-sector control awards a planet without clearing the five
mines already there. The selected-player-empty and selected-sector-occupied
controls terminate without an award despite many other available choices.
Changing an active planet slot changes **earlier maintenance/RNG consumption**: the selected-slot-occupied control awards a
*different* planet to a different player. It is not evidence of a lottery retry.
The Xannor-defense diagnostic's no-award result likewise does not establish a
local defense exclusion. Those local rules come from control flow, not naive
matched-seed assumptions. A Union-only-free-sector control uses synthetic duplicate planet links and
completes without an award; it does not demonstrate a native award in the Union
or establish a Union placement restriction.

Success adds public `won a PLANET in the SUPER LOTTERY` news without the sector,
and private mail with recipient=winner, raw sender−2 and the sector number.
Failure prints `No one won a planet today.` only to the console. This daily
planet award is separate from the player-facing credit lottery mentioned in the
original change history; that credit feature is not recovered by this slice.

## Maintenance phase order

The captured console sequence and native call/writer ranges establish:

1. Compute game day/cutoff; print a same-day warning without returning.
2. Clear Union mines (`0419–0488`).
3. Compact radio, then rotate newspaper files (`048f`, `672d–6914`).
4. Publish the dated maintenance-run event (`0497–04d8`).
5. Load players, decay named cloak, perform qualifying deletion/name filtering.
6. Ordinary port production, then ordinary planet production/events.
7. Wanderer movement and Xannor home/HQ restoration, regeneration and actions.
8. Port-tax collection and Mercenary restoration/hiring/actions.
9. Super-planet lottery.
10. Persist maintenance day (`5773–57ab`), then generate/publish the scoreboard.

Deletion precedes planet growth and lottery eligibility. Lottery precedes the
scoreboard and gets no immediate ordinary production pass in that run. The
same-day child prints the warning and still executes every phase; later NPC
activity also changes its saved world. The modern replay guard must remain.
The DOS path writes files sequentially; these observations do not imply atomic
original transactions or crash safety.

## Bounded implementation contract for the next milestone

Research is complete for this slice; these are recommended modern boundaries,
not implemented or shipped behavior:

- Add daily super-planet awards and old-dead-player retirement to the existing
  locked, atomic maintenance update, once per saved day. Keep normal account
  identity/history and ship generations authoritative.
- Keep retirement before economic/NPC phases and lottery after NPC actions.
  Use real saved dates and a clearly documented delay; old living players stay.
  Keep current turn-based cloak policy, rather than introducing a daily cloak
  tick or copying the expiry-dependent retirement loophole silently.
- Release **all** current-generation ownership safely, including ports; maintain
  valid teams/captains, pending revenge, mines, score publication and other
  references. Preserve private/public histories under their original identity
  instead of inheriting DOS alias filtering or unread-based erasure. Verify
  actual store/identity invariants before selecting a retirement representation.
- Permit only current living, eligible players to win. Keep selection finite and
  explicitly state one-shot/no-award behavior. Never overwrite an existing
  planet, faction home, reserved resource or protected sector. Initialize all
  new planet stocks and timestamps; do not inherit stale record contents.
- Publish owner, sector link, private award mail, public news and score effects
  together. Keep the location private. Test full capacity, no eligible players,
  replay/concurrency, rollback and committed durability without partial awards
  or cleanup. Preserve save migration explicitly if new state/config is needed.

Exact BASIC RNG/MBF parity, native clock-tie execution, native Union awards,
century rollover, full active-team cleanup UI and complete account-deletion
reference coverage remain outside the captured evidence. Live BBS and native
Windows durability acceptance remain separate. Plague/civil-war scope, the HQ
credit reward and other equipment still require their own milestones.

## Validation and reproduction

```sh
python3 scripts/verify_maintenance_lottery.py
python3 scripts/test_maintenance_lottery_verifier.py
python3 scripts/verify_archive.py
# Requires locally installed DOSBox Staging; destination must not exist:
python3 scripts/recover_maintenance_lottery.py /private/tmp/yt-maintenance-new
```

The verifier independently rebuilds all declared worlds and original auxiliary
payloads, verifies every parent link, native clock/completion, deletion/lottery
semantics, messages, phase order, executable hashes and relocated MZ bytes. It
also runs the static model. Eleven rehashed corruptions exercise incorrect
retirement, ownership/roster cleanup, reused-slot retention, occupied award
placement, radio suppression and broken world/auxiliary chains. All 4682 original
archive hashes pass. No Go source changed, so no new gameplay test result or
live acceptance is claimed by this research commit.

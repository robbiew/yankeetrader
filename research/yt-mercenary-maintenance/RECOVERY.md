# Mercenary daily maintenance — recovered rules and bounded DOS evidence

This research extends [the earlier maintenance recovery](../yt-maint/RECOVERY.md)
and [player-facing bribery](../yt-mercenaries/IMPLEMENTATION.md). It preserves
**41 completed original-DOS maintenance runs and 82 before/after snapshots**, plus
**one separate eight-second hiring-capacity timeout with two snapshots**. Eleven
Ghidra/REA byte observations cross-check the relevant code. This slice changes
research, verifiers and documentation. The subsequent
[hiring implementation](IMPLEMENTATION.md) enables a bounded subset; the
original-DOS evidence below remains unchanged.

Target: original `YTMAINT.EXE`, SHA-256
`8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6`.
All experiments execute copied, unmodified EXEs in disposable DOSBox mounts. The
original archive is neither mounted nor patched; all 4,682 archived hashes pass.

## Method and phase isolation

The starting world is `archive/analysis/dos-validation/evidence/YTDATA.DAT`.
A declared `mercenary-maintenance-isolation-v1` recipe removes active players,
sector defenses/mines and old planet references, clears port treasuries/titles,
and establishes four controlled planets. Warps and ordinary port contents stay
from the original fixture unless a case explicitly overrides them. All runs use
DOS date 10/25/2026 at 00:00:00 except the exact chained next-day run, dated
10/26/2026. The actual DOS date/time outputs, emulator log, transcript, exact
fixture overrides and hashes accompany each pair of compressed worlds.

Mercenary Base occupies reserved slot 99 at sector 2000 with ground/bank 1;
Xannoron is slot 100 at the configured HQ and The Wanderer is slot 1. Planet
production starts at the current maintenance timestamp, preventing a deliberately
old rich planet from supplying the tested groups. The engine still executes its
**whole** maintenance path: Xannor HQ recovery creates a 1,475-fighter group in
these ordinary fixtures, which some new Mercenary groups subsequently encounter.
The verifier separates reported hiring from those later losses rather than
claiming that final Mercenary strength alone measures hiring.

The active human controls copy one archived player record, then declare its
login/death/location/team/stored-score changes. The fixture's public alias is `Q`.
Two dense-world controls fill all non-Earth sectors with 1,000 human defenders,
except an occupied Xannor HQ. One leaves only home sectors 2–7 free; the other
leaves no eligible empty sector. No fake mutation command is added to the game.

## Tax-funded hiring and discarded remainders

The government sums individual ordinary-port taxes:

```text
T = sum(floor(port_treasury / 10)) for ports 2..1000
Earth (port 1) is excluded.
N = floor(T / 10)

if N < 1: no new group
if 1 <= N < 10: one new group of N fighters
if N >= 10: ten new groups of floor(N / 10) fighters each
```

| Tax collected T | Newly hired groups | Reported new fighters |
|---:|---|---:|
| 0, 9 | none | 0 |
| 10, 19 | one × 1 | 1 |
| 90, 99 | one × 9 | 9 |
| 100, 109, 110, 199 | ten × 1 | 10 |
| 200 | ten × 2 | 20 |
| 100,112 | ten × 1,001 | 10,010 |

Each tax case starts ordinary port 2 with `10*T` credits. Independent port
checks verify the exact debit from every ordinary treasury. Split controls show
that 95 and 5 credits produce taxes 9+0 (no hire), while 95 and 15 produce 9+1
(one hire). Taxing their combined balance would give the wrong first result.
An Earth-only million-credit treasury remains unchanged and funds no hiring.

Both integer divisions can discard a remainder. Taxes are already removed from
the ports; there is no saved carry budget. The `tax-next-day` process reads the
**exact final world** from `tax-199`, without resetting player/port/NPC state.
Its port balance 1,791 is taxed by 179, leaving 1,612, and it hires ten new
fighters. The first day's remainder does not increase that second hire. The
portable verifier checks the complete world-byte chain, not just the balance.

Static anchors: `1000:3f73..40d6` taxation; `4478..4502` rounding/group size;
`4528..464a` creation and actual hired-total reporting. The number printed as
hired is a new-force total, independent of later merging, combat or desertion.

## Placement, home sectors and capacity

New groups sample sector IDs **2..N** and retry while the selected sector has
positive fighters. Earth is excluded; sectors 2–7 are not. The placement branch
checks fighter count, not port/planet presence, ownership or outgoing warps.
Each new group immediately occupies its selected sector, so the initial hire
locations are distinct, although movement can merge them later.

The dense `union-only-spawn` world leaves only sectors 2–7 empty. Its one-fighter
hire starts at sector **4**, then joins a human defense at 12. This confirms home
sector eligibility at runtime, not just a range inferred from instructions.

The dense `capacity-blocked` world reaches Mercenary maintenance after collecting
100 credits in port taxes, but cannot place the first of ten requested groups.
The emulator is stopped after eight seconds; no hired-total or completion message
appears. Its world already contains the treasury debit. The static retry at
`4534..457b` has no exhaustion/capacity exit, corroborating the bounded stall.
This timeout is **not** counted as a completed maintenance run. A one-sector
world and a fully occupied planet map are additional static range/retry hazards;
they were not run and are not claimed as observed failures here.

Modern hiring must use a finite available-sector set, handle saturation explicitly
and commit with the daily economic transaction. A failed placement must never
leave half of a maintenance update visible. Home-sector eligibility must respect
the Go game's protected-spawn policy rather than silently adopting the DOS range.

## Existing human groups can become Mercenaries

Before movement, the game examines human defense groups. For the tested ordinary
player slot, it changes ownership to -2 when `RND*100 > fighters`. The fighter
count is unchanged by conversion. The exact owner predicate is `owner > 1` in
DOS, whose player records begin at 2; do not copy that literal ID cutoff into a
Go world where the first real account has ID 1.

- A one-fighter human group at 100 deserts, then moves, retaining one fighter.
- A 100-fighter human group does not desert and retains owner/count at 100.
- In `human-defense`, the 50-fighter target deserts **before** the other
  Mercenary group moves; the final 150 Mercenaries are two groups. This run is
  not evidence of a human group accepting reinforcement.
- The separate 1,000-fighter human target cannot satisfy this small-group test.
  It accepts the 100 incoming Mercenaries and ends with 1,100 human fighters.

Static anchors: `4664..47c6`. The sampled conversions do not establish empirical
probabilities or a particular QuickBASIC random sequence. The subsequent
[Go desertion phase](DESERTION.md) implements this strict comparison with modern
player IDs and protected-Union policy.

## Movement is a route walk, not one adjacent hop

A mobile group chooses a random different sector, obtains a path and walks that
route within this maintenance phase. Intermediate interactions can stop, merge,
destroy or change the force. A single `moving from sector` message does not mean
one warp was taken. In `move-empty`, sector 100's only outgoing warp is 101, yet
the force finishes intact at **1951**. The paired planet/mine/defense controls put
an interaction at the forced first hop, 101, to establish intermediate handling.

A group in a sector with any planet reference is held when `RND < .66`, regardless
of that planet's owner. `planet-held` and `planet-human-origin` both retain their
100-fighter group at 100 and leave the planet's 37 stored fighters untouched.
The precise .66 comparison is static evidence; two held samples do not measure
its frequency. Clearing the origin and following the path occur only on the
moving branch (`4804..4932`).

### Unreachable-path defect

`move-zero-warp` clears **all six** outgoing warps at 100. Maintenance prints
`Sector path not found - from sector 100 to sector 1951`, then nevertheless moves
the intact 100-fighter group to 1951. The saved before/after graphs and force
location verify this relocation; an error message alone would not establish it.
Modern movement must hold the group or choose another verified reachable target,
never turn a failed path lookup into teleportation.

### Descending scan can process relocated forces again

The outer sector loop descends and reads the changing data file. In `tax-100`,
ten initially hired one-fighter groups generate **18** movement-start messages,
with no other source of Mercenaries or planet-fighter pickup. One group loses to
Xannor; nine fighters survive in eight final groups, including a merged pair.
The extra starts and loop at `5318..5357` show why a final location processed
later in that same descending scan can receive another action. Modern maintenance
should snapshot/identify its phase participants to prevent accidental repeat
activation. Whether one legitimate activation walks a whole route or one hop is
a separate balance policy; this research does not silently choose a replacement.

## Mines, defenses and planets

### Mines on the route

Mines are processed before planetary pickup or defense encounters. One mine
kills the tested 100-fighter group and is spent. A three-mine field costs the
100,000-fighter group **2,807** fighters in the recorded run; all three mines are
spent and the remaining **97,193** reach 1951. Loss is capped to the remaining
force; a killed group stops. These are measured samples, not fixed damage values.
The `mine-kill-remainder` control loses its 100 fighters to the first mine and
leaves **two mines** intact. The helper at `7939` is called with parameters 2 and
10,000. For each mine it starts a bound at 10,000, draws
`floor(RND*bound)+1`, replaces the bound with that result and repeats once.
Damage is the second result, capped to the remaining force. These are nested
shrinking-bound rolls, not two independent dice summed together. The caller
resets the bound for every mine. Exact QuickBASIC RNG/MBF damage matching remains
a precision boundary. [Readable derived rules](recovered_rules.py) and synthetic
RNG boundary checks make the recovered control flow independently inspectable. Mine owner attribution and player-death
semantics require explicit Go integration rather than being inferred from these
NPC-only probes. Anchors: `49d4..4c7a`.

### Merging and battles

Friendly Mercenary groups merge without losing force: the 100/200 control ends
with one 300-fighter group. A foreign positive-owner defense usually receives
incoming Mercenaries as reinforcement; the static code instead attacks when the
owner is negative (Xannor), or a random draw is **greater than .95**. It consumes
the draw even for the Xannor branch (`4fb1..4fd8`). The 1,000-fighter human group
accepts 100 and retains its title; Xannor always fight in the controlled paths.

NPC-vs-defense combat uses a different batch algorithm from player sector fights:
when **both remaining forces exceed 200**, the batch is **150**; otherwise it is
one. A draw below .5 removes defenders; a draw at or above .5 removes
Mercenaries (`504e..50f7`). Thus the exact .5 tie favors the defender. The 200 constant
is an MBF **double** at DS:8916; interpreting its first four bytes as a single
incorrectly yields zero. Independent constant-byte checks protect this detail.
A 100-vs-50 Xannor sample leaves 31 Mercenaries, and a 20,000-vs-15,000 sample
leaves 3,360. Both clear the defeated defense and continue along their route.
Exact random distributions and mixed-precision parity are not claimed.

### The “captured planet” message does not transfer its title

When an encountered planet has no hostile sector fighters, Mercenaries take its
stored fighters and occupy that sector, ending this route activation. In the
neutral and human-owned controls, 100 incoming fighters plus 37 planetary fighters
become a 137-fighter Mercenary defense; the planetary stock becomes zero.
Despite the capture message, **planet owner and ground forces remain unchanged**.
A human planet with **500,000 ground forces** is plundered in the same way without
fighting or changing that ground count. “Captured” therefore describes the sector
occupation here, not a proven title transfer or planetary ground assault.

A human sector garrison intercepts the force: the 1,000-fighter group accepts
reinforcement and its planet keeps all 37 fighters. With 50 Xannor sector fighters,
Mercenaries fight and continue, but do not revisit that just-cleared planet to
pick up its fighters; its 37 remain. Ordering and accounting come from the paired
worlds, not the wording of the log. Anchors: `4c7f..4ec0` then `4ec3..5318`.

## Reserved Mercenary Base behavior

The phase searches sector references for the reserved penultimate planet slot
(default slot 99 / record 4150). The existence test does not check active name,
owner or referential consistency. Even with zero tax:

| Control | Observed result |
|---|---|
| Reference missing, old planet record still present | Rebuilds Mercenary Base: production 100,000 each, ground 150,000, bank 25,000,000, owner -2; assigns a new sector reference |
| Reference present, active-name length zero | Skips full rebuilding; the inactive record remains inactive |
| Existing base assigned to a human, ground 123, bank 1,234 | Owner becomes -2; positive ground/bank stay 123/1,234 |
| Existing ground/bank zero | Ground becomes 150,000 and bank 25,000,000 |
| Existing ground/bank one | Both remain one |

Ground restoration uses `<1`; the bank restoration check is exactly zero.
The reserved record identity and restoration bounds are static and dynamically
corroborated (`413a..4473`). A modern implementation must validate an active,
consistent planet reference. Automatic retitling of a captured base is a separate
faction-home policy, not permission to overwrite arbitrary human ownership.
The subsequent [Go base lifecycle](BASE.md) preserves captured ownership and
uses explicit identity with finite placement instead of inferring a home from
a legacy slot or name.

## Evidence, reproduction and verifier

- [Manifest](dos/results.json): 41 completed cases and one explicitly timed-out case.
- `baseline.dat.gz`: the common declared fixture, reconstructed independently.
- Per case: compressed before/after worlds, `transcript.txt`, actual DOS date/time,
  emulator log and `result.json` with input overrides, executable/runtime hashes,
  completion/timeout state and captured file hashes.
- [REA observations](rea/phase-paths.json): eleven byte ranges at linear addresses
  0x14478, 0x14534, 0x14804, 0x149d4, 0x14c7f, 0x14fb1, 0x1504e, 0x143e9,
  0x15318, 0x17939 and 0x14a78. The verifier reconstructs the MZ load image and relocations before
  comparing all bytes. Ghidra 12.1.4 was used and the session was closed.

```sh
python3 scripts/recover_mercenary_maintenance.py /tmp/yt-mercenary-new
python3 scripts/verify_mercenary_maintenance.py
python3 scripts/verify_archive.py
```

The destination must not exist. The runner executes the exact next-day child only
after `tax-199` completes. For an isolated child replay, use `--only tax-next-day
--parent-world /path/to/tax-199/after.dat.gz`. The timeout case is deliberately
bounded; no unresolved process remains. Replays can differ in random outcomes;
do not overwrite the preserved samples or call them deterministic fixtures.

The portable verifier independently reconstructs the baseline and every declared
input, checks the entire chained world, date/time, all file/executable hashes,
port debits, hiring/remainders, force/stock/owner accounting, the capacity stall,
no-route relocation and static constants. Rehashed false tax debits, title changes,
child worlds and no-route outcomes are rejected by semantic negative controls.
Validation passed: the new verifier, both existing bribery/hostility verifiers,
the utility evidence verifier, all 4,682 archive hashes, Python syntax checks and
`git diff --check`. All four rehashed semantic negative controls were rejected.
CI is configured to revalidate artifacts without DOSBox or REA. The research
commit itself enables no gameplay; subsequent hiring is documented separately.

## Implementation boundary and recommended next slice

The daily-maintenance questions in this slice are answered at the rule/accounting
level. Exact RNG/MBF correspondence, all human-defense combat random branches,
all NPC planet/home lifecycle combinations, ship/NPC encounters and live BBS
acceptance remain bounded work. The timeout does not prove elapsed-time behavior
on every host; its unbounded placement loop and absence of eligible slots explain
this specific stalled run.

The subsequent [implementation](IMPLEMENTATION.md) adds **tax-funded hiring with
finite placement**, within the existing
once-per-UTC-day locked transaction. Preserve integer accounting and define
unplaced-budget handling explicitly. Do not introduce arbitrary NPC owners or
world fields without validation/migration coverage. The subsequent
[route implementation](ROUTES.md) uses stable phase participants,
valid paths, conserved merges, current ownership and attributed mine layers.
NPC losses do not invent player deaths. Further faction lifecycle work remains.
Snapshotting eliminates repeated
activation; path failure must not relocate a force. Planet-fighter pickup must
not accidentally retitle planets or debit ground forces. Keep faction base
restoration and movement balance decisions explicit and independently tested.

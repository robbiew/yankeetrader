# Player/team rankings and score generation

Recovered 2026-10-28 from original Yankee Trader 3.6 in isolated DOSBox Staging
copies. This is a research milestone; the Go ranking command and score-cache
updates are not implemented by this branch.

## Scope and evidence

The suite retains 27 completed sessions, 54 compressed full before/after saves,
key streams, console transcripts, final scoreboard files, emulator logs and
hash/patch manifests under [dos](dos/results.json). The original executable
SHA-256 is `c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
Only disposable DAT copies were patched. No archived executable or fixture was
modified or mounted for writing. Each session logs in as TESTER/Q, inspects
computer option 4, and quits normally; the independently controlled target is
Enemy, player record 3, which does not log in during the experiment.

The baseline keeps fixture account metadata, gives Enemy ten holds and 1,000
credits, clears its other known scored inventory, and clears all deployed
ownership/strength and planet ownership. Target score is 26,000. Other named
players remain as positive-score ranking references. `expected.json` records
fixed outcomes and declared patches, independently checked against snapshots.

## Recovered score components

For the tested nonnegative inventory, the observed score is the sum below.
The quantities are not money prices; they are scoreboard points.

| Component | Points per unit | Controlled observation |
|---|---:|---|
| Ship shields | 50 | +100 shields gives +5,000 |
| Ship fighters | 100 | +100 fighters gives +10,000 |
| Holds | 2,500 | 10→11 gives +2,500; 10→20 gives +25,000 |
| Ore / organics / equipment cargo | 20 / 30 / 40 | +10 gives +200 / +300 / +400 |
| Ship credits | 1 | +100 credits gives +100 |
| Scanner | 250,000 bonus | DOS flag -1 adds 250,000; zero adds nothing |
| Missiles | 1,000 | +10 gives +10,000 |
| Plasma bolts | 1,000,000 | +10 gives +10,000,000 |
| Cached owned-port count | 50,000 | Counter 0→1 gives +50,000 without a title |
| Carried ground forces | 750 | +10 gives +7,500 |
| Carried mines | 2,500 | +10 gives +25,000 |
| Personally owned sector fighters | 100 | 100 at sector 101 gives +10,000 |

The original fixture's Q inventory independently reconciles to 9,990,250 points.
Changing Enemy's stored score to 12,345 is overwritten back to 26,000. Cloak
0→1 and raw player fields 101/105 set to 10 do not change the tested result.
These last probes establish no broader meaning or safety for those raw fields.
An owned planet with a 1,000,000-credit bank contributes no extra score in this
fixture, including its other unchanged inventory. Separate planetary-component
perturbations remain untested.

## Ranking and cache behavior

Computer `4` prompts for `O` to show the old scoreboard or Enter to generate an
updated one. A deliberately supplied `STALE SCOREBOARD PROBE` file appears on
the OLD path. Enter instead generates and displays actual rankings. Both paths
subsequently generate a fresh scoreboard on normal quit, so the final snapshots
do not establish that OLD is mutation-free for the whole session.

The generated board contains rank, percentage, score, team number, cached port
count and alias, then team and non-human sections. Scores descend. A five-way
tie at 9,990,250 keeps player-record order Q, Enemy, Third, Fourth, Fifth and
assigns ordinal ranks 1–5. A zero-score live player remains listed. A dead
player whose other assets remain populated also remains listed, with zero
score. Do not infer that retained inventory earns a dead ship points.

Percentages match score/leading-player score times 100 in the observed positive
leader cases, displayed to two decimals. Zero-score rows show 0.00%. Exact
halfway rounding, negative scores, all-zero leader behavior and different team
ties are not established by these tests.

Team Orion, containing Q and Enemy, receives 10,016,250 = 9,990,250 + 26,000.
Individual team numbers and the named team row appear correctly. With only one
team it displays 100.00%; this does not establish the percentage denominator
across multiple teams. The zero-strength NPC sections remain zero here;
nonzero NPC score aggregation and normalization are outside this slice.

Updated generation writes the new per-player score into offset 109. All tested
ship quantities, position and remaining turns are preserved. This is relevant
to missile retaliation, whose existing Go rule consumes the stored score; an
implementation must specify when a new cache becomes authoritative rather than
silently treating a ranking display as an unrelated pure read.

## Confirmed stale-count gap and Go implementation boundary

`cached-ports` awards 50,000 points and displays one owned port without a real
port title. Conversely, `port-title` grants Enemy an actual ordinary-port title
while leaving its count zero: score and displayed count remain unchanged. This
is a demonstrated consistency gap, not proof that a player can forge counters
through normal commands. Go should derive owned-port counts from current port
records in the score transaction, as already required for Genesis eligibility.
See BUG-007 in [the issues register](../ISSUES_AND_EXPLOITS.md).

The next implementation can use recovered weights for supported assets,
current personal sector defenses, current team membership, stable tie ordering,
and bounded pages. It must define safe zero/negative score percentages and
checked score arithmetic; omit unsupported scanner/NPC data rather than invent
it. Recalculate and publish score caches coherently under the world lock,
without altering credits, turns, combat state or private account fields.
Old-scoreboard persistence/retention and quit/maintenance timing need an explicit
modern policy; DOS's stale-counter behavior should not be copied.

## Static cross-check and reproduction

[REA evidence](rea.json) retains verified Ghidra 12.1.4 load-image facts and full
byte Evidence for the ranking dispatch at linear `0x19330` (annotated
`1000:9330..939e`) and score accumulation at `0x22c73` (annotated
`1f42:3853..3999`). Evidence IDs are
`ev_03514cdc41e9c75482e17cee3453202b476020e2c67335ece260857148a762e9`,
`ev_67f1e644e00a9a9ea1c374125df789397cfd759642a21e625bf1b4f4c5e14f5d`,
and `ev_a8a6764ebd283974b1cf32cc129a5abd6f8d9c67e5b9c21846d618d73b5f522e`.
The load report is a selected projection omitting its large relocation list;
byte query Evidence is retained completely. The verifier independently applies
the MZ relocation table and checks these exact loaded bytes. Static byte matches
corroborate the archived annotated listings, not runtime execution or original
source recovery. The REA session was closed without modifying executable bytes.

```sh
python3 scripts/recover_rankings.py /tmp/yt-rankings-new
python3 scripts/verify_rankings.py
```

Destinations must be new; `--only` selects named probes. DOS date/time are fixed
at 10/24/2026 00:00:00. Retries in the key stream let output finish before normal
quit; display routines can consume typeahead. Initial timing/fixture attempts
and a deployed-force probe that blocked the caller's current sector were
excluded. The retained deployment probe uses adjacent sector 101 so both the
ranking command and quit complete.

The verifier checks all artifact hashes, reconstructs the precise baseline and
each patch from the archived source, compares fixed score controls, checks
ship/turn preservation, old/updated report paths, dead/zero/tied rows, team sum
and REA byte identity. Negative controls change a saved score or team total and
recompute artifact hashes; semantic checks must still reject them. This evidence
does not validate Go gameplay, full DOS numeric equivalence or live-BBS behavior.

Validation passed the 27-session verifier, both rehashed negative controls,
Python syntax checks, all 4,682 archived-file integrity checks, the preserved
commerce/radio verifier and `git diff --check`. No Go gameplay files changed;
Go tests and live-BBS acceptance are not new evidence from this milestone.

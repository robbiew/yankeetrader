# Bounded Go evolved Mercenary/desertion and lottery tail

`qbmaint.ReplayEvolvedNPCTail` starts after Base lookup/placement. It takes a
complete modeled world, a 24-bit modeled RNG state and only the chronological
helper-one suffix for Mercenary targets and the conditional lottery candidate.
Family/caller labels and all four TIMER bytes are preserved; helper calls are
calculated from the world and gate results, not inferred from suffix length.

The admitted profile has default geometry, inactive human players, zero port
taxes, no pending revenge and an existing named Mercenary Base. Whole physical
forces have Xannor, neutral or Mercenary ownership. Mercenaries are absent or
one retained **37- or 97,525-fighter** deployment. This reuses both the evolved
convergence chain and the already recovered empty-route Mercenary controls.
Human desertion, tax-funded hiring, changed/merged Mercenary force, mine damage,
planet stock pickup and defense/merge combat remain excluded.

## Source behavior retained

Desertion consumes one eager draw for each positive **physical sector force**,
regardless of group-pointer aliases or an owner's ineligible desertion predicate.
The convergence phases contain 3/20/20 such sectors. Group cache entries never
supply a desertion count or a starting RNG state.

The Mercenary scan descends from sector 3000 and rereads the mutable world. An
arrival at a lower sector can activate again later that day. Every activation
consumes its movement gate, even without a planet. A positive origin link with
a gate below SINGLE `.66` holds the force; departure from an occupied origin is
excluded. Empty-origin departure clears force and owner with the original
`00002800` FAC residue, not cache-clear or canonical zero bytes. Each same-origin
target rejection consumes another caller `48cf` helper reseed/draw without
another movement gate. Original column-order directed BFS checks every entered
sector for mines, force and planets before writing the intact force/owner at the
endpoint. Force conservation is checked afterward. Guards of 16 activations and
64 target retries are research bounds, not claims about original DOS budgets.

The lottery draw follows movement. It consumes a `53b4` helper only when its gate
is at least `.5`, chooses a player record 2..51 and admits only an inactive
candidate. Unused, missing, reordered or wrong-family helper clocks fail. All
work and RNG are private: an error returns no world or statistics, including an
unsupported encounter discovered after clearing a departure locally. Inputs are
never modified. Existing strict initial and late-clock APIs stay unchanged.

## Evidence and tests

No captures or native hashes changed. The exporter authenticates the existing
convergence, occupied-route and placement/cache corpora, then instruments the
recovered Python tails. Its 15 phase inputs and outputs are **modeled worlds**;
intermediate hashes, movement gates and helper seeds are model receipts, not new
native phase observations. Initial worlds are independently reconstructed and
multi-day children come only from prior modeled outputs. Native after-files,
RNG witnesses and cache probes are validation only, never corrections or inputs.

| Retained phase | Runs | Mercenary force | Activations per run | Desertion draws | Total tail draws |
|---|---:|---:|---:|---:|---:|
| Convergence day one | 3 | 0 | 0 | 3 | 5 |
| Convergence day two | 3 | 0 | 0 | 20 | 22 |
| Convergence day three | 3 | 0 | 0 | 20 | 22 |
| Occupied-route survivor | 3 | 97525 | 1 | 2 | 5 |
| Placement/cache survivor | 3 | 37 | 2 | 21 | 27 |

The independent native qualification is **90 complete six-file comparisons /
540 files, 885 RNG witnesses and 1,440 modeled cache-field comparisons**. For the
convergence chain, all three modeled days exist before native oracles open. For
the two selected single-day controls, each complete modeled run exists first.
The source verifier separately authenticates the original departure-zero bytes.

Go tests match every complete phase-world hash, physical-sector inventory,
activation/candidate/route, gate, lottery, draw count, helper old/seeded state and
final state. Six cases feed actual Go planet output into existing-home/mobile
continuation and then directly into this tail, carrying the calculated RNG state
at both boundaries without substituting Python worlds. Day-one prefix and full
multi-day Go chaining are not established by that three-phase composition.

Additional synthetic tests check held/no-lottery gates, unexpected candidate
clocks, duplicate group-pointer immunity and same-origin reseeding. They are not
new native executions. Refusal tests check unknown inputs and late route hazards
without partial publication. Exporter controls reject altered inputs, results,
clocks, native files, cache probes and RNG witnesses, enforce oracle-read order,
and accept portable gzip recompression by comparing complete decompressed bytes.

```sh
python3 scripts/export_evolved_tail_fixture.py --check
python3 scripts/test_export_evolved_tail_fixture.py
go test ./internal/qbmaint -run 'TestEvolvedTail|TestGoEvolvedEconomyContinuationAndTail'
```

[Day-one convergence admission](GO_CONVERGENCE_DAY_ONE.md) now has its own
bounded Go API and composes with this tail. [Evolved auxiliary output](GO_EVOLVED_AUXILIARY.md),
[complete Go chaining](GO_CONVERGENCE_CHAIN.md) and [CLI v2](REPLAY_CLI.md)
are now qualified separately. Do not redo completed port, planet, continuation or tail recovery.
Research CLI v1 profiles, playable gameplay and save 35 remain unchanged. General
DOS loading, broader Mercenary combat, native Windows durability and live BBS
acceptance remain separate.

# Maintenance-chain composition audit — 2026-11-18

Audited main at `fa4c5968a4c01a49e8938881595d364e2aea17cb`, after PRs
184–186 merged. GitHub's open-PR collection was empty during this audit.
This is a source/contract and retained-fixture audit, not a new native capture,
full campaign run or production-maintenance qualification.

## Complete Go compositions already implemented

| Entry point | Completed scope | Existing recipe/CLI |
| --- | --- | --- |
| `ReplayInitialMaintenance` | Ordinary initial six-file replay | v1 `initial` |
| `ReplayInitialMaintenanceWithWanderer` | Separate late-clock Wanderer initial six-file replay | v1 `initial-wanderer` |
| `ReplayConvergenceChain` | Three consecutive days 306–308; only preceding Go six-file output supplies the next day | v2 `convergence-three-day` |
| `ReplayOccupiedFiles` | Ten pinned occupied initial worlds on day 306; economy, creation/mobile combat, tail, reports and metadata | v3 `occupied-day306` |

Sources: `internal/qbmaint/initial.go`, `convergence_chain.go`,
`occupied_records.go`, and `internal/qbreplay/{recipe,chain_recipe,occupied_recipe,run}.go`.
Do not rebuild these compositions or infer that the convergence input pin also
admits the distinct occupied-combat prefix. Modern playable maintenance is a
separate engine/policy, not a caller of these research recipes.

## Completed phases that are not complete chains

| Go API | Existing retained modeled phase coverage | Boundary still missing |
| --- | --- | --- |
| `ReplayFriendlyStockMercenary` | Eight held-garrison/stock cases, 24 phases | Prefix, child economy/home routing, lottery and public files |
| `ReplayDepartedStockMercenary` | Eight hold/departure cases, 24 phases | Same, including source-clock partition around later local activations |
| `ReplayNeutralOwnerStockMercenary` | Six owner/mine cases, 18 phases | Same, with distinct neutral transfer and incoming mine loss receipts |
| `ReplayDefenderStockMercenary` | Four fatal-offense contexts across two children, 24 phases | Both complete children, stock growth, extinct continuation and reports |
| `ReplayGatewayVictoryMercenary` | Two guarded contexts across two children, 12 phases | Both complete children, Xannor/home events and reports |
| `ReplayClearGatewayStockMercenary` | Twelve positive SINGLE stock cases, 36 phases | Complete four-day chain, stock economy, lottery and public files |

These APIs take a modeled pre-Mercenary world and calculated RNG state. They
stop before lottery/publication/final metadata. Their full-world hashes are
modeled intermediate oracles; their exporters separately verify existing whole
Python/native chains. Native-equal Python files are not proof that Go generated
the prefix or surrounding child phases. All six admissions remain independent.

## Concrete gaps in source order

1. **The occupied-combat three-day parent is not composed in Go.** Every selected
   stock/gateway Python chain first calls
   `replay_maintenance_evolved_combat_records.synthesize_chain`. Its day 306 is
   already covered by occupied Go replay. Its two children cover four profiles:
   `route-mercenary-37`, `route-mercenary-100000`, `route-neutral-37`,
   `route-planet-neutral`. `ReplayEvolvedPlanets` instead admits Convergence Haven
   with a fixed active inventory; it does not admit these absent-ordinary or
   neutral Route Haven contexts. `ReplayOccupiedPlanets` only admits clean day
   306. Existing-home routing similarly admits convergence names/days and excludes
   these later combat contexts. Existing raw arithmetic and combat primitives
   are reusable; new native controls are not the first dependency.
2. **Child-day economy is not admitted by current Go APIs.**
   `ReplayEvolvedPorts` stops at day 308; the gateway/stock children require days
   309 and sometimes 310. Reuse the retained Python survivor/gateway port writer
   and existing numeric primitives in a separately bounded profile, with exact
   source date/TIMER guards. Gateway planet economy needs slot 3, zero initial
   rates and selected stock inputs, distinct from named convergence and clean
   occupied profiles. Second-day grown stock 40/3 must be calculated once, not
   replaced by whole-day before values 37/0 or loaded from phase fixtures.
3. **Home/cache/mobile continuation needs the actual child profiles.** Reuse
   `replay_maintenance_*_npcs.py` through the Mercenary boundary: normalize loaded
   caches from the day's own world, derive living/dead groups, shared pursuit,
   eager/skipped scans and home assaults, and carry calculated state/events.
   Existing initial occupied routing and convergence continuation cannot simply
   be used with relaxed names or dates. Do not feed captured child worlds,
   expected endpoints or exporter phase snapshots into a public composition.
4. **Mercenary coverage is not the whole gateway matrix.** The gateway corpus
   has `empty`, `pickup`, `mine-pickup`, `guarded-pickup`, `mine-guarded`, and
   `fatal-before-pickup`. The victory API covers only the two guarded profiles.
   The twelve-value clear-stock API does not admit the gateway's stock 0/37;
   mine/neutral APIs with local physical defenders do not imply a clear gateway
   or three-mine fatal profile. Reuse these captures for missing outcomes only.
5. **Lottery must follow each computed phase exactly once.** The original
   `ReplayEvolvedNPCTail` includes physical scans, movement and lottery together;
   invoking it after a new Mercenary phase would repeat work and its force/route
   admission is narrower. Add a bounded post-Mercenary lottery continuation
   accepting calculated state and only the remaining /53b4 clocks. Preserve
   eager lottery draw, conditional helper call and no named-player admission.
6. **Report writers need new event/physical ledgers.** `ReplayEvolvedAux` is
   convergence-only: days 306–308 and conserved all-Xannor physical inventory.
   `ReplayOccupiedAux` requires three original before files, not six-file child
   handoffs. Neither is a general publisher for pickup/fraction discard,
   neutral transfer, mine loss, fatal/victorious Mercenary combat and later
   home assaults. Reuse the retained family-specific Python auxiliary writers;
   preserve pre-pickup actor stamps, source ordering, faction scores, DOS
   CRLF/EOF, yesterday-news rotation, raw counters and independent text clocks.
7. **Composition and recipe admission come last.** Add a pinned bounded parent
   chain, pure declared fixture edits over its Go-generated final files, then
   one or two internally chained children. Each DOS day has its own startup
   seed; state continues between phases within that day. Only original before
   files and source clocks enter. Late failures publish no partial bundle.
   Extend CLI schema only after full six-file Go chains pass; retain v1–v3
   compatibility and reject cross-profile fallback or caller-supplied endpoints.

## Ordered implementation queue

**Next: bounded Go evolved occupied-combat planet economy for days 307/308.**
Reuse `replay_maintenance_evolved_combat_planets.py` and the four existing
occupied-combat chains: 24 modeled child phases (four cases × two days × three
source observations). Keep `ReplayEvolvedPlanets` and `ReplayOccupiedPlanets`
strict. Validate complete worlds, active slots, inherited raw fields, fractional
elapsed time, production/ground/bank/rate changes, eager RNG draws and atomic
refusal. Retain the existing independent Python-chain audit: 144 six-file
comparisons /864 files and 1242 child RNG witnesses. This is existing
qualification to revalidate, not newly acquired evidence.

Then implement the corresponding evolved occupied-combat home/mobile
continuation, tail and auxiliary admission and compose its three-day Go parent.
Only afterward extend day-309/310 ports and gateway economy/home continuation,
complete the missing gateway outcomes and lottery/report ledgers, and compose
one carefully selected four-day stock chain before adding its CLI profile.
Five-day fatal/victory chains and the remaining stock families follow once their
actual dependency guards/receipts pass. Do not jump directly from a Mercenary
phase to a full-chain wrapper.

Reuse existing raw SINGLE/DOUBLE arithmetic, INT/comparison/sign tests,
initial/occupied combat primitives, acquisitions, exporters and corruption
controls. This audit does not authorize a broad numeric-runtime rewrite or new
captures where retained cases already qualify the requested behavior. Other
calendar/survivor/tax-hiring research profiles, active humans, arbitrary
interceptions, production maintenance, DOS save interoperability, native Windows
and live BBS acceptance remain separately scoped work.

## Audit verification

Source call sites, profile guards, recipe dispatch and complete Python parent/
child call graphs were inspected. Existing focused Go convergence-chain,
occupied-file, gateway-victory and clear-stock tests passed, as did the existing
recipe/CLI package tests. No full native
verifier, remote CI campaign, new executable or gameplay behavior was run or
changed for this documentation-only audit. Open PRs were checked live; that is a
point-in-time observation, not a permanent guarantee.

# Friendly-force and planet-stock composition controls

This acquisition isolates the remaining friendly-force-plus-planet-stock path.
The existing [stock replay](STOCK_CONVERSION_REPLAY.md) derives pickup into an
empty destination; [departure/merge replay](DEPARTURE_MERGE_REPLAY.md) derives
friendly force on a nonplanet route. Their composition requires separate evidence
because source pickup is selected before the ordinary friendly-merge branch.
The current stock replay rejects an occupied gateway before changing any world
bytes; it remains intentionally unchanged in this acquisition milestone.
Production Go, save 35, dependencies and replay admission are unchanged here.

The corpus retains **48 complete original-DOS runs / 288 output files**. All
**eight fixture groups are six-mode equal**, without normalized bytes. There are
**240 unchanged input links** and **48 declared YTDATA transformations**. Every
run completed naturally on its first attempt; no failed run or retry is omitted.
The frozen [recipe](friendly-stock-controls/recipe.json), raw six-file before/after
sets, launch/clock logs and executed acquisition sources are retained together.

## Declared fixture and selection boundary

Every case starts from its own mode's actual November 4 output in
`evolved-combat-controls/route-mercenary-100000/child-2`, pinned manifest
`fd794dccfda332ab79c2d5a693d2649ebbc32c607863fbf2f10801ec4e0ecef5`.
The established fifteen-edit gateway recipe forces the first hop from sector 2368
to 3000 and redirects all other incoming edges. The graph remains reachable in
both directions. Slot 3 Gateway Cache retains 500000 ground, zero rates
and bank, day 308 and minute 0. Its declared stock, governor and a same-faction
physical garrison at 3000 are the controlled variables. The main force remains
97337 at 2368. The other five input files are unchanged parent copies.

All cases use November 5, 2026 at 00:00:00, two unobserved controls, attach-only and
three observed controls. This is a single-day acquisition with fresh disposable
copies, unchanged guests, strict natural completion and persisted exit receipts;
no retry or forced exit is accepted. The already qualified capture controller and
DOS observer are reused unchanged, with executed source snapshots frozen before
launch. Historical corpora are not rewritten.

The descending mutable scan reaches the friendly garrison at 3000 before the
incoming main force at 2368. Therefore a declared friendly input alone does not
prove composition: the garrison could depart before pickup. Each retained outcome
must establish the actual hold/departure path and earlier combat effects. No
unselected case is silently relabeled as successful composition.

## Actual selected outcomes

All eight garrisons remain at 3000 until the main arrival. There is no console
movement from 3000 and no earlier Mercenary casualty; the main force moves 97337
from 2368. Final physical totals and scores account for both forces plus the whole
stock transfer. These outcomes select held-garrison composition, not a departure
of the garrison before pickup.

| Case | Friendly garrison | Governor | Raw stock | Saved fighters | Taking receipt actor / amount |
|---|---:|---:|---:|---:|---|
| friendly-one-empty | 1 | 0 | 0 | 97338 | none |
| friendly-empty | 37 | 0 | 0 | 97374 | none |
| friendly-half | 37 | 0 | 1/2 | 97374 | none |
| friendly-whole | 37 | 0 | 37 | 97411 | 97374 / 37 |
| friendly-odd-half | 37 | 0 | 3/2 | 97375 | 97374 / 1 |
| friendly-large | 37 | 0 | 189528 + 1/2 | 286902 | 97374 / 189528 |
| friendly-owned-whole | 37 | -2 | 37 | 97411 | 97374 / 37 |
| friendly-large-force | 97337 | 0 | 37 | 194711 | 194674 / 37 |

No case prints a capture line. Empty or subunit stock prints no taking line,
but all stock is cleared using the original raw zero `00008000`. Positive whole
stock prints the combined pre-stock actor, not the moving force 97337 and not the
final post-stock force. The planet title, link, governor and ground remain intact
apart from ordinary source economy. The source moving-origin clear retains its
distinct raw zero `00002800`.

## Why this is pickup, not a second friendly merge

The existing complete 3462-byte native source packet is reused
(`ev_c92656dd4a34f4605e434c81cbd3e9f730962d0373f2a3fecfce72256fbfcd2f`),
with whole-packet SHA and original YTMAINT MZ bytes authenticated. Original `4a01–4a11` caches
the entered sector's force in `7b90` before loading the planet. The `4c7f` pickup gate
uses entered sector owner/link and precedes the ordinary nonplanet friendly-merge
branch. The positive SINGLE INT result joins the moving force and cached local
force; the entire stock is cleared and saved first. The later capture gate requires
zero cached local force and its retained `7b68` route comparison; the taking gate
tests the converted stock.
Thus local force is included once, capture text is suppressed here, and taking
text uses moving-plus-local force. The planet governor does not select this
retained pickup gate. Sixteen machine-code spans and four original literals bind
the descending scan, eager hold draw, cached entering fields, pickup/merge
priority, saves and receipt conditions. The ordinary friendly merge's force/owner clear and route
continuation are not executed afterward.

This source reading is corroborated by native physical/public outcomes, not a
new claim of arbitrary-world runtime parity. Exact machine contracts, pinned
packet identities and original MZ bytes are checked by the independent native
verifier; no duplicate native query or provider installation was needed.

## Independent validation

The corpus audit reconstructs every fixture with an independent IEEE-single-to-
MBF encoder, binds all fifteen ordered edits to its actual parent, authenticates
launch/CPU/date/time and complete source clocks, and checks strict persisted
exit receipts. Measurement first retains any unexplained inventory difference;
only afterward does the qualified closed matrix require once-only held-force
absorption. Raw governor preservation, physical totals, public/console text,
whole transfer, scores, distinct zeros and complete file inventories are separate
checks. Coherent overwrite and double-count forgeries cannot claim success.

All 33 new tests pass: 24 corpus/clock/ledger corruption tests and nine native-byte
contract tests. The complete corpus and native verifiers, all 4682 archive hashes,
compilation, relative links and diff checks pass. An indexed Git export with
`core.autocrlf=true` preserves all 1350 corpus artifacts and passes the full audit.
These portable commands run in CI. The controller and observer themselves remain
byte-identical to the already qualified sources; their existing protocol tests
remain enabled.

## Before-only integration requirements

The next profile should start with the existing original three-file world and
model the three-day parent before applying the declared fifteen edits. Its next
Mercenary phase must retain both actual activations: held local force at 3000,
then the moving 97337 at 2368. Both eager gate draws and the additional physical-
force scan draw must follow source order, rather than being patched from observed
RNG state. Governing owner 0/-2 remains an actual fixture input throughout economy
and pickup, not a temporary neutralization used to bypass an old guard.

A pickup event needs distinct incoming force, entering local force, whole stock,
combined pre-stock receipt actor and final saved force. The publisher must debit
the moving origin and absorb the existing destination once; recording an ordinary
merge as well would double count it. A zero-whole pickup is still an actual stock
clear and absorption. Public capture suppression must not be replaced by a generic
"captured planet" flag. Complete modeled handoffs, source-only read bans, poisoned
RNG-witness independence, source literals and all six files should be validated
against every retained mode, with historical APIs unchanged.

## Scope and next step

The controls qualify only the retained garrisons, stocks, governors, graph and
clock recipe. Separate before-only integration must derive the held activation,
entering local force, combined receipt stamp and final saved totals without
reading native after-state. Negative/nonfinite/overflow stock, hostile or neutral
physical garrisons, mines and unrelated mixed encounters remain separate. Native
Windows durability, live BBS and new full Go/terminal/build acceptance are not
claimed by this research acquisition.


## Subsequent before-only integration — 2026-11-07

The separate [friendly-stock replay](FRIENDLY_STOCK_REPLAY.md) now derives all
eight jointly measured cases from a modeled three-day parent and pure fixture
transformation. All 144 complete comparisons / 864 files and 1104 new-stage RNG
witnesses match. This acquisition corpus, source snapshots and every hash remain
unchanged; historical stock replay admission remains strict.

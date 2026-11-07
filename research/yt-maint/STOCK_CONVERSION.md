# Maintenance fighter-stock conversion controls

This acquisition isolates the stock-to-whole-fighter conversion at the Mercenary
planet-pickup call site. The acquisition introduced no production Go, replay
admission, save 35, dependency or generation-fingerprint change. The prior
[departure replay](DEPARTURE_MERGE_REPLAY.md) already recovers its measured
189528.296875 transfer; this matrix addresses the previously unqualified half-unit
and adjacent-value boundaries instead of repeating that full feature.

The corpus contains **72 complete original-DOS runs  / 432 output files**. All
**12 fixture groups are six-mode equal** for every output byte. Independent
lineage accounting verifies **360 unchanged file links** and **72 declared data-only
transformations**. Every capture completed naturally on its first attempt; there
are no suppressed failures, retries or normalized bytes. The 48 observed/attach-only
runs all passed the persisted receipt and bounded natural-exit checks.

## Copied-world experiment

Each of twelve exact binary stock values starts from its observation mode's
verified November 4 output in
`evolved-combat-controls/route-mercenary-100000/child-2`, manifest
`fd794dccfda332ab79c2d5a693d2649ebbc32c607863fbf2f10801ec4e0ecef5`.
Fifteen declared YTDATA edits reuse the established gateway topology: six warps
from sector 2368 lead to 3000, three other incoming edges are redirected to 2368,
slot 3 becomes neutral Gateway Cache, sector 3000 links it, and the unchanged source
97337 force is explicitly restamped. The graph remains connected in both
directions. Gateway Cache has 500000 ground, zero bank and production rates, day 308,
minute 0, and the declared stock. The earlier production phase preserves that stock;
its later minimum-rate clamp is separately checked.

Every fixture runs on November 5, 2026 at 00:00:00, using fresh disposable copies and
unchanged original guests. There are two unobserved controls, one attach-only
control and three host-observed controls per value. The other five input files
are exact parent copies. This is a single-day experiment; no captured after-state
is fed into another case. The frozen recipe, executed acquisition sources,
complete six before/after files, launch/clock logs and controller receipts are
retained under [stock-conversion-controls](stock-conversion-controls/recipe.json).

## Measured whole-stock conversion

The selected call floors positive SINGLE stock before transfer. It does not round
half ties to nearest, and it clears the entire original stock rather than saving
the remainder. The stock clear retains the exact source zero `00008000`,
not a normalized zero. Positive stock below one therefore captures the planet, transfers
zero, and prints no taking-zero receipt. A positive whole transfer prints the
source force 97337 in both capture/taking text; the saved physical force includes
the transferred whole fighters. Receipt text is not a claim that the old force
remained unchanged after the transfer.

| Exact starting stock | Whole transfer | Saved Mercenaries | Discarded fraction |
|---|---:|---:|---:|
| 1/4 | 0 | 97337 | 1/4 |
| 1/2 | 0 | 97337 | 1/2 |
| 3/4 | 0 | 97337 | 3/4 |
| 3/2 | 1 | 97338 | 1/2 |
| 5/2 | 2 | 97339 | 1/2 |
| 189528 + 31/64 | 189528 | 286865 | 31/64 |
| 189528 + 1/2 | 189528 | 286865 | 1/2 |
| 189528 + 33/64 | 189528 | 286865 | 33/64 |
| 189529 + 1/2 | 189529 | 286866 | 1/2 |
| 16777215/16777216 (single below 1) | 0 | 97337 | 16777215/16777216 |
| 8388609/8388608 (single above 1) | 1 | 97338 | 1/8388608 |
| 32767 + 1/2 | 32767 | 130104 | 1/2 |

## Acquisition and source evidence

The new controller addresses the previously measured post-detach liveness race:
it yields to the host event loop and waits at most two seconds for the owned PID
to disappear, inside the existing 30-second capture deadline. It requires natural
process termination, zero exit, complete canonical UTF8 trace and persisted flush
receipt, exact byte/event counts, no drops/errors, and guest completion markers.
Persistent liveness or forced cleanup fails. The DOS observer and its event
collection are unchanged; no asynchronous acknowledgement is required when the
complete synchronous receipt proves the write. Historical acquisition sources
and captures remain untouched. Portable tests exercise actual short-child
termination, delayed disappearance, timeout/error rejection and receipt corruption.

Four retained byte observations in three existing native packets are reused;
no duplicate REA query or provider installation was needed. The complete
Mercenary packet (`ev_c92656dd4a34f4605e434c81cbd3e9f730962d0373f2a3fecfce72256fbfcd2f`)
binds stock decode at `4cd3` and the `QB_3d_03` call at `4cdb`. Existing BRUN30 dispatch
and positive-entry observations (`ev_4390e0214550c70e645826a190f8145dff501480374c0ed92fdb697c34198a9b`,
`ev_4888ae8d5fad919bf11ecf6e4461c59ac2011bdceeab000c71c7272060e18374`)
map opcode `03` to `ACB2` and the backward positive branch to `AC9D`. The retained runtime
floor observation (`ev_567123d41857df939d326c9daf676249df6b745ddf6c8bd7b563373a125605f5`)
covers the `AD17` fraction mask. Their 3932 retained bytes include an intentional
overlap, not 3932 unique bytes or new queries. The independent native verifier
pins whole packets and compares every selected byte against original MZ LOAD
images. It also binds whole-stock clear/save before amount addition and the
positive-amount receipt gate. This qualifies the positive SINGLE `INT` call site,
not every runtime conversion. The later `QB_3f_77` name-length conversion is a
different operation and supplies no rounding rule for fighter stock.

## Portable validation

The independent corpus audit authenticates every input, output, declared edit,
launch, clock and lifecycle receipt before classifying the physical transfer. It
reconstructs fixture MBF through IEEE-single bits, separately from the producer's
rational encoder, and rejects any rounded declaration. All 360 unchanged input
links and 72 transformations are explicit. A coherent nearest-rounded force,
receipt and score still fails the qualified floor classification; raw zeros,
subunit no-receipt behavior, source callers and complete six-mode equality are
separate checks.

The 60 new portable tests pass: 25 corpus/ledger/clock controls, 27 controller/receipt
controls and eight native-byte controls. Both evidence verifiers and all 4682
archive hashes pass. A staged Git checkout with `core.autocrlf=true` preserves all
2022 corpus artifacts and passes the full corpus verifier. This transport check
protects raw CRLF logs and frozen acquisition sources as well as compressed data.
The same commands run in CI; remote CI results remain a separate validation layer.

## Bounds and next work

The original-DOS outcomes and independent audit below qualify only these positive
binary stocks, this reachable gateway path and these controlled clocks. Negative
stock, nonfinite/overflow conversion, arbitrary-world MBF parity and the separate
friendly-force-plus-planet-stock composition remain unmeasured. The separate
[before-only integration](STOCK_CONVERSION_REPLAY.md) now derives
these measured values from a modeled parent. Historical gateway/departure APIs
retain their earlier narrower admissions; the new profile isolates this expansion.
Live BBS, native Windows durability and new full Go/terminal/build
acceptance are not claimed by this research milestone.

# Direct raw-SINGLE multiplication parity — 2026-11-11

## Result and entry contracts

All **115 first-attempt native controls** completed naturally: **106 returned
results** and **nine exact Overflow diagnostics**. `MultiplySingle` models
INT3F/91 FAC-times-memory; `MultiplySingleWithFAC` adds independent prior-FAC
state for 8f memory-times-memory and represents 93 memory-times-FAC by passing
right as the prior FAC. No arithmetic implementation existed for these entries
before this slice; existing addition/subtraction APIs and their evidence remain
unchanged. This is an isolated numeric API, not a production replay migration.

| Entry | Loaded offset | Inputs and prior FAC |
|---|---|---|
| 8f | b4ab | SI left memory, DI right memory; independent prior FAC |
| 91 | b4a0 | SI set to FAC, DI right memory; left is the prior FAC |
| 93 | b4a8 | SI left memory, DI set to FAC; right is the prior FAC |

Zero operands and underflow branch to the existing exponent-only zero exit:
clear the **original destination FAC exponent** and retain its first three bytes.
This differs from addition's directional zero-operand selection. For example,
entry 8f with zero aliases 12345600/ffffff00 and prior FAC 5aa5d592 returns 5aa5d500,
not either operand or canonical zero. The same mathematical zero need not have
the same raw encoding when the initial FAC changes.

Nonzero products use exact 24-bit significands. The native partial-product helper
retains guard/sticky information for both 47- and 48-bit product widths, then
joins the existing nearest/ties-to-even normalizer. Result sign is operand-sign
XOR. Underflow is checked **before rounding**: raw 01000040 times feff7f41 lies
just below the minimum normal and becomes 01000000, even though rounding first
could carry into the minimum binade. A product at/beyond the upper range or a
rounding carry out of range produces the complete native Overflow diagnostic.
The Go API returns a zero array and false on overflow as its own contract; no
native post-error FAC/register state is inferred from that array.

## Reused source, missing bytes and callers

Before acquiring controls, the audit reused:

- `yt-plague-civil-war/rea/target-paths.json`: complete retained runtime-multiply
  observation at 1b440/220 bytes, including normalizer/wrapper/partial products.
- `yt-xannor-planets/rea/assault-paths.json`: retained register-saving ABI helper
  at 11f6b/128 bytes (and existing direct dispatch observations).
- The qualified addition packet/normalizer, exponent-only zero and error exits,
  plus existing initializer contracts.

Only **four missing bytes** at 1b51c were newly queried: `E1 03 C7 C3`. They complete
the split `MUL CL`, `ADD AX,DI` and return at the end of the partial-product helper.
The new complete REA packet is retained at `rea/multiply-tail.json`. All selected
source ranges are fixed-hash authenticated and mapped to the immutable original
BRUN30 image. Previously retained packets and native observations are unchanged.

The fixed `maintenance-calls.json` inventory matches 60 annotated direct call
sites to original archived machine bytes: two 8f and 58 entry 91. There are no 93
matches in that listing; this is not proof that indirect or other-module calls
are absent. Entry 93 qualification comes from its source mapping and new declared
native dispatch controls. The same inventory separately retains twelve inline 95
call sites, explicitly excluded from this direct milestone. A listing-matched
inventory is static evidence, not observed normal execution or an exhaustive
indirect-call graph.

Existing positive production/RNG application captures remain bounded historical
application evidence. They are not relabeled as isolated signed/range/rounding
multiplication vectors. Current Go generation/replay policies and source recipe
fingerprints are not changed by this API.

## Native matrix and frozen acquisition

`native/` retains 109 controls from one frozen source/recipe:

- 61 FAC-times-memory cases exercise signed products, raw zero aliases, either
  zero operand, exponent sums 128–130/383–385, normalization, both even-tie widths,
  reversed factors, exact constants, carry, underflow and overflow boundaries.
- 16 focused input pairs each run through 8f and 93, testing actual operand/FAC
  roles without repeating every kernel pair for every wrapper.
- 16 controls vary four prior FAC encodings across zero and underflow cases in 8f,
  independently of both operand values. Initial RNG is also controlled at 5 or
  16777215; mode remains the bootstrap default 0.

After reviewing the main matrix, `sticky-native/` adds six separately frozen
entry 91 controls, three exact remainder boundaries with both result signs. The
47-bit below-half case has an odd kept significand; the 48-bit below-half case is
also odd; the 48-bit above-half case is even. Their remainders differ from half by
one exact product unit, so incorrectly treating them as ties changes the result.
The positive remainder cases use these normalized 24-bit significands:

| Product width | Left / right significands | Kept parity | Remainder versus half |
|---|---|---|---|
| 47 | 800007 / e49249 | odd | 3fffff versus 400000 |
| 48 | 80205b / fff02d | odd | 7fffff versus 800000 |
| 48 | 800c3d / ffeb15 | even | 800001 versus 800000 |

These inputs were selected by integer remainder/parity analysis. No primary
observation or executed acquisition source was changed or retried.

Every process uses its own disposable copy of the original initializer/runtime,
with both original startup calls preserved. The first initializer body call is
redirected to a diagnostic at loaded 006d; copied runtime **code is untouched**,
with only the declared initial RNG data seeded. No synthetic inline BP frame,
caller-header change, selector byte or runtime return stub is used. Left/right
memory blocks are actual operands for 8f; left is a trace shadow for 91 and right
is a trace shadow for 93. Successful returns check both memory blocks unchanged.

The host is fixed DOSBox Staging 0.83.0 at 200000 cycles, requested DOS date
2026-11-02/time zero. Exact command, host/version, clock and shell-return logs are
retained. A successful shell return does not classify arithmetic success.

## Independent verification and implementation

The `MUL1` protocol keeps 21 initial bytes: marker, initial RNG, prior FAC,
ordered memory blocks and mode. A success is a complete 42-byte frame with raw
result, unchanged memory blocks, RNG/mode and footer. A fatal outcome instead
retains the complete exact native diagnostic at 01A3:00F6 for 8f/91 or00F3 for 93;
post-error FAC, memory and RNG values remain unknown.

The verifier independently reconstructs payloads and entire copied images,
checks relocation exclusion, fixed prelaunch sources/recipes and complete
artifact inventories, validates native host/clock/return provenance, and compares
the portable fixture to all 115 original raw traces/digests. Its arithmetic
reference uses exact rational products, source-derived zero/pre-round-underflow
rules and even rounding. It computes results from inputs, not native answers.

Go separately multiplies two integer 24-bit significands into 48 bits, normalizes,
checks the exponent before rounding, applies integer remainder/even-tie rounding
and handles a final carry. Fourteen acceptance/corruption tests cover all traces,
independent acquisition payloads, original FAC residues, pre-round underflow,
both tie widths and sticky boundaries, actual FAC bindings, exact error sites,
fabricated success, caller scope, all four missing source bytes, source/fixture
substitution and preserved old evidence. Go compares both APIs against every
native outcome and adds a focused minimum-binade regression.

This is source-derived arithmetic with representative native qualification, not
an exhaustive operand-pair enumeration. Inline 95 addressing/error contexts,
DOUBLE multiplication, division, mode-dependent conversion admission, complete
normal maintenance and live BBS acceptance remain separate. Gameplay, initializer
fingerprints, save 35 and sysop procedures are unchanged. Next bounded work is
inline 95 multiplication, reusing the completed resolver and this product model;
do not repeat direct multiplication or prior addition/subtraction controls.

Local validation passed: all 115 native outcomes and fourteen verifier tests;
existing inline/direct addition/subtraction and overflow verifier suites;
race-enabled qbmbf/qbrng/qbinit tests and Go vet; twenty complete native
initializer goldens; and all 4,682 original archive hashes. PR CI and live BBS
acceptance remain separate validation.

The [inline multiplication supplement](../yt-mbf-inline-multiply/RECOVERY.md)
now qualifies declared 95 resolver/result/error contexts using these unchanged
product APIs. General machine-frame validity and broader unwind remain separate.

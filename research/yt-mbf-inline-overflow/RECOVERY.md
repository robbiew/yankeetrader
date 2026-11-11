# Bounded inline SINGLE overflow and error context — 2026-11-11

## Result and limits

All **twenty first-attempt controls** completed naturally: **twelve exact native
Overflow diagnostics** and **eight finite returns**. INT3F/85 addition and
INT3F/9d subtraction both reject the selected positive/negative overflowing pairs
in the controlled bootstrap frames. Their existing Go APIs already return false;
no arithmetic, production caller, gameplay, recipe fingerprint or save change is
needed. This supplement adds native evidence, portable fixtures and tests.

This admits the complete fatal diagnostic and absence of a return frame in these
declared contexts. It does **not** observe registers, FAC, operands or RNG after
a fatal exit, establish actual saved-BP restoration at runtime, or qualify
arbitrary frames, ON ERROR hooks, RESUME, cross-segment operands, complete normal
maintenance or live BBS behavior. The fixture uses null output for fatal cases;
it does not fabricate a zero FAC. Source-level error dispatch and observed fatal
output remain distinct evidence.

## Reuse and source observations

The completed [inline resolver](../yt-mbf-inline-add/RECOVERY.md),
[direct subtraction](../yt-mbf-sub/RECOVERY.md) and
[successful inline subtraction](../yt-mbf-inline-sub/RECOVERY.md) milestones
(PRs #128–130) are merged. Their capture/source packets and arithmetic oracles are
reused unchanged; successful addressing/arithmetic controls are not recaptured
as missing work.

The earlier 180-byte error-dispatch observation existed only in temporary
storage. Its recovered complete REA packet is now retained at
`rea/error-dispatch.json`, with the same content-addressed Evidence ID
`ev_f3da38b6cfd40e6a9b3c8d648c955c575b7aa5db077a4ca820725f8fee559340`.
It maps address 109a0 to the immutable original BRUN30 image. A new nine-byte read
at 10a54 completes the split instruction and default route jump. Both complete
packets are fixed-hash authenticated. The recovered dispatch envelope is a new
acquisition record with fresh metadata and its own digest, not the unavailable
temporary file; its normalized bytes and Evidence ID agree with the earlier
audit. Previously retained repository packets and native capture hashes are
unchanged.

The source selects BL=6 at 9a0 for Overflow. The common path checks the optional
hook at data 002b; absent that hook, a49 restores BP from data 0a06, calls a0fa and
jumps through the route at 0029. This is static control-flow evidence, not an
observed unwind-state trace. Existing resolver/ABI packets establish that one
inline selector byte is consumed and the advanced caller return IP is pushed.

## Frozen acquisition and admission context

`native/` retains twelve outcomes from one frozen acquisition source: both
opcodes, both descriptor tags (bm/bz) and positive overflow, negative overflow and
one finite control. `depth-native/` retains eight separately acquired outcomes:
each opcode at padding 16/bm and padding 32/bz, each with a positive overflow and a
finite control. These are explicit combinations, not an exhaustive or orthogonal
frame matrix. Both sources/recipes were frozen before their first launches; no
case was retried or rewritten.

The original initializer executes both startup calls untouched, then redirects
its first body call to the diagnostic. Runtime code is unchanged; only the
declared initial RNG word is seeded. As in the parent successful-inline probes,
the diagnostic builds an explicit BP local, sets ES=DS, places a descriptor at
DS:5000 and its paragraph alias at SS:[BP-2], and changes caller-CS base words
in memory after startup to safe 6000/6800. The original on-disk header remains
unchanged. Selected memory holds the left operand; alternate-base memory holds
a distinct finite poison operand. No resolver-only return stub is used here.
The four baseline and four depth finite returns are harness controls in this new
error-context protocol, not repeated qualification of the arithmetic kernel.

The depth source reserves 16 or 32 extra stack bytes **before** constructing its
BP local. It does not patch the module's startup error context. The observed
bootstrap admission is route 0a68, no hook, pre-entry saved-SP 0, saved BP equal to
the original BP on the stack, module stack equal to original BP minus 6 and the
synthetic BP equal to original BP minus 8 minus padding. These are admitted
observations for this bootstrap, not a general runtime ABI for arbitrary callers.
The current ABI invocation updates its own saved stack after this snapshot; no
post-error global values are claimed.

The host remains DOSBox Staging 0.83.0, fixed 200000 cycles, requested DOS date
2026-11-02/time zero, with exact host/clock/command/return logs. The program returns
to the native shell normally even for an arithmetic error; shell ERRORLEVEL or
host exit status alone never selects an arithmetic outcome.

## Protocol and independent validation

A new 46-byte `IOF1` prefix records initial RNG, raw FAC/left input, mode, selector,
descriptor/base/DS/ES/BP context, opcode, error route, optional hook, saved BP,
saved SP, module stack and original stack BP. A successful control then records
SI/DI/AX/DS/ES/BP, FAC, RNG/mode, selected/poison memory and `END!` (79 total bytes).
A fatal case instead has exactly the full 85-byte native diagnostic (131 total),
with no invented return fields or footer. The printed addresses are
`01A3:0194` for the baseline and `01A3:0197` for padded controls, derived from the
independently reconstructed call-site layout plus the consumed sixth selector
byte, not fitted by parsing the native message.

The verifier authenticates complete fixed artifact inventories, frozen actual
acquisition sources/recipes, whole copied images and relocation exclusion,
source packet mappings, controlled launch/clock logs and portable equality.
Existing independent addition/subtraction oracles predict error versus finite
outcome before inspecting native output. Finite controls check raw result,
registers, memory, RNG and mode. Fatal checks compare the entire diagnostic only.

Twelve acceptance/corruption tests cover independent payloads, every trace byte,
return-IP consumption, fake success/truncation/newline substitution, recipe-label
and opcode swapping, frame-depth/source/inventory/fixture damage and finite/fatal
confusion. Go compares the existing arithmetic APIs against all twenty raw native
frames without treating a Go return array as an observed post-error FAC. Parent
contracts and captured source fingerprints remain unchanged.

The next independent source-selected slice is direct SINGLE multiplication.
Inspect and reuse its existing wrapper/kernel/normal-caller observations first;
do not repeat the completed addition/subtraction or bounded inline fatal controls.
Hooked/resumable error handling and broader frame/unwind behavior remain separate.

Local validation passed: the new complete verifier and twelve tests; the prior
inline-addition, inline-subtraction and direct arithmetic verifier suites;
race-enabled qbmbf/qbrng/qbinit tests and Go vet; twenty native initializer
goldens; and all 4,682 original archive hashes. These local checks are distinct
from PR CI and live BBS acceptance.

The [direct multiplication supplement](../yt-mbf-multiply/RECOVERY.md) now
qualifies the next isolated arithmetic primitive. Its native inputs reuse source
observations and do not broaden this milestone into general error unwinding.

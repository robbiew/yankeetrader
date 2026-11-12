# Direct raw-DOUBLE multiplication

## Result and entry contracts

`MultiplyDouble` qualifies INT3F/92 FAC times memory;
`MultiplyDoubleWithFAC` qualifies /90 memory times memory with independent
initial FAC and /94 memory times FAC by passing right as initialFAC. The
implementation retains exact 56-bit significands using a 112-bit integer
product (`bits.Mul64`), with no float64 demotion or new dependency.

| Entry | Loaded offset | Inputs and initial FAC |
| --- | --- | --- |
| 90 | af46 | SI left memory, DI right memory; independent initial FAC |
| 92 | af3b | SI set to DOUBLE FAC; DI right memory; initial FAC is left |
| 94 | af43 | SI left memory, DI set to DOUBLE FAC; initial FAC is right |

Zero operands and underflow clear only the original FAC exponent, retaining all
seven residue bytes. This differs from addition's operand-selection zero rules.
Nonzero products normalize from 111 or 112 exact bits and round once to 56 bits,
nearest with ties to even, preserving the native guard/sticky information. Result
sign is operand-sign XOR. Underflow is tested before rounding: the retained
`flush-before-round` control lies below the minimum normal even though rounding
first would carry into that binade. Overflow, including rounding carry past the
upper range, returns a rejected Go result without claiming native post-error FAC.
This isolated numeric API selects no gameplay, save or generation policy.

## Evidence reuse and missing source

The plan, README, retained evidence, exported APIs and open PRs were checked
before acquisition. Completed SINGLE arithmetic, DOUBLE conversions, direct and
inline addition/subtraction, and initializer acceptance were not repeated.
No overlapping open PR or prior isolated DOUBLE multiplication corpus existed.
This branch starts from merged main after PR #141 (`c6c0a6e9`).

Retained DOUBLE addition source already authenticates the rounding normalizer,
exponent-only zero exit and Overflow path. Existing register-saving ABI and
startup evidence are also reused unchanged. The audit found two missing ranges:

- `rea/entries.json`: **78 bytes at analysis 1af3b**, through af88, containing
  direct/inline entry mappings, zero tests, sign/exponent setup, helper call and
  normalization join. Evidence
  `ev_574eb55ea083e08234cd13540a47f1c77af8e8afd115f70e960c55a9348d66ce`.
- `rea/partial-products.json`: **322 bytes at analysis 1b08c**, through b1cd,
  containing the complete multiword helper and return, including lower-product
  residue used for sticky information. Evidence
  `ev_8db9b1a3a4017154da3e0b7d69fb2026b7068adb520675de197269167ef9d5cb`.

Only those **400 missing bytes** were queried. Both complete REA records bind
to the original BRUN30 SHA, provider profile, requested/returned lengths and
mapped original bytes. Queries used the installed Ghidra and current installed
JDK through per-command environment paths; global configuration was unchanged.
Existing packets, binaries, native observations and manifests remain unchanged.
No division source in the intervening range was acquired or qualified.

The [fixed caller inventory](maintenance-calls.json) matches five /92 direct
maintenance slots to archived bytes at code offsets 13b8, 875c, 88ba, 89ae and
89d4. The bounded annotated listing has no /90, /94 or inline /96 matches. This
is static evidence, not normal-path runtime observation or exhaustive indirect
coverage. /90 and /94 are qualified by their entry source and declared native
controls; inline /96 frames remain separate.

## New native controls and provenance

All **118 first-attempt disposable processes** completed: **111 numeric returns
and seven exact Overflow diagnostics**. The matrix has 66 /92 controls, 34 /90
controls (including sixteen independent-FAC cases), and eighteen /94 controls.
It covers zero aliases, signs, both product widths, raw word-boundary partial
products, even/odd half ties, exact half-minus/plus-one product-bit sticky
controls at both widths, exponent boundaries, pre-round underflow and Overflow
including rounding carry. Low bits beyond float64 precision are explicit.
Four independent FAC encodings and two RNG seeds separate residue from input
binding. Previous SINGLE/application captures are not relabeled as these controls.

Each acquisition source and closed recipe was frozen before first launch.
Both original initializer startup calls remain; only copied diagnostic code,
operands/FAC and declared runtime RNG seed change. Runtime code is untouched.
Independent preflight reconstructed all payloads and excluded loader relocation
overlaps before launch. Every first process outcome is retained, without retry
or replacement. Immutable manifests pin every observed artifact and source.

The distinct `DMP1` prefix records all eight initial FAC bytes, both ordered
memory blocks, RNG and mode. Successful 66-byte frames preserve both memory
blocks, RNG/mode and complete raw result/footer. Each fatal frame retains its
full native diagnostic at 01A3:011A for /90-/92 or 01A3:0117 for /94, derived
from independently reconstructed five-byte call slots. No post-error state is
fabricated. These are original-startup diagnostic contexts, not arbitrary modules,
frames, error hooks, ON ERROR/RESUME or general unwind qualification.

The verifier authenticates full copied-image hashes, relocation boundaries,
exact inventories, pinned DOSBox Staging 0.83.0/fixed 200000-cycle headless launch,
raw 2026-11-02/time-zero controls and native shell returns. ERRORLEVEL alone
never classifies arithmetic success. Its independent exact-rational product
oracle applies source-qualified pre-round underflow and residue rules; it does
not use captured outputs or the Go implementation as expected answers.

Portable fixtures retain complete traces and source hashes; Go tests compare all
118 native outcomes without an emulator. Eighteen verifier/corruption tests
reject lost precision/residue, wrong ties/sticky handling, round-first underflow,
FAC rebinding, memory/RNG/mode mutations, wrong continuations, incomplete source,
changed frozen artifacts and invented error FAC. CI runs both new checks, and
Git attributes preserve exact native control bytes.

```sh
python3 scripts/verify_multiply_double.py
python3 scripts/test_verify_multiply_double.py
go test -race ./internal/qbmbf ./internal/qbrng ./internal/qbinit
go vet ./internal/qbmbf ./internal/qbrng ./internal/qbinit
```

Gameplay, source recipe fingerprints, save 35 and sysop behavior are unchanged.
Next: audit retained inline DOUBLE multiplication /96 resolver/entry evidence
before adding missing bounded controls. Do not repeat direct multiplication,
completed arithmetic/conversions or initializer acceptance. DOUBLE division,
general unwind, full maintenance, DOS save interoperability and native Windows/
live-BBS acceptance remain separate.

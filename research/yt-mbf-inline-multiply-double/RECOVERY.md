# Bounded inline DOUBLE multiplication

## Scope and existing evidence

INT3F/96 composes `SingleAddInlineOffset` with
`MultiplyDoubleWithFAC(selectedMemory,FAC,FAC)`. The historical offset-helper
name remains; no new arithmetic algorithm or production caller is introduced.
The README, plan, retained source, exported APIs and open PRs were checked first.
PR #142's direct multiplication milestone is merged as `56a61e94`; this branch
starts from that baseline. No overlapping open PR or existing inline /96 corpus
was found. Completed direct multiplication controls were not reacquired.

No source query was needed. The immutable
`yt-mbf-multiply-double/rea/entries.json` packet already includes analysis af40:
`CALL 1ec3; MOV DI,0016; CALL 1f6b`. The original file bytes b140..b148 are
`e8806fbf1600e82270`; the dispatch table maps /96 to af40. The same parent
milestone retains the complete partial-product helper, while existing packets
cover the shared resolver/frame, normalizer, zero exit, ABI and error path.
The verifier authenticates those source packets through the
[direct verifier](../../scripts/verify_multiply_double.py), then constrains the
inline dispatch and entry bytes separately.

The reused [original-byte caller inventory](../yt-mbf-multiply-double/maintenance-calls.json)
contains five direct /92 sites and **no inline /96 sites** in the bounded
annotated maintenance listing. New selectors and frames are synthetic controls,
not observed normal maintenance callers or an exhaustive indirect-call graph.
Actual caller-header controls from other arithmetic are not relabeled here.

## Two native profiles

All **153 first-attempt disposable processes** completed without retry or
replacement:

- **15 resolver-only controls**, marker `DM96`, 69 bytes each: bm/bz descriptor
  variants, selectors 00/80/7f/ff, wrapped offsets and a fallback descriptor.
  A copied-runtime `RETF; NOP; NOP` replaces only the post-resolver `MOV DI,0016`
  at file b143..b145. These compute offsets without operand reads or arithmetic.
- **138 full executions**, marker `DMF1`: **128 numeric returns** and **ten exact
  Overflow diagnostics**. Runtime code is unchanged. Both descriptors and safe
  synthetic selectors 80/8a cover signs, zero aliases, seven-byte FAC residue,
  both product widths, even/odd ties, exact half-minus/plus-one sticky controls,
  raw word-boundary products, pre-round underflow and Overflow/rounding carry.
  Separate 16/32-byte padded frames cover Overflow and two underflow cases.

Closed recipes and exact acquisition sources were frozen before first launch.
Both original initializer startup calls remain. Only copied diagnostic code,
explicit frame/header metadata, operand data and declared runtime RNG seed
change. Independent preflight reconstructed every payload, excluded loader
relocation overlaps and checked complete safe eight-byte read spans before
launch. Original binaries, earlier source packets, observations and manifests
remain unchanged. Every first process outcome is retained.

The resolver chooses caller-CS base12 for descriptor tag 7a62 and base10 otherwise,
masks the selector high bit, uses eight-byte slots and wraps at 16 bits. Wrapped
cases remain address-only. Successful 99-byte full traces retain all eight FAC
result bytes, unchanged selected and alternate-base poison blocks, RNG/mode,
AX and declared DS/ES/BP state. Zero operands and pre-round underflow clear only
the original right-FAC exponent, preserving its seven residue bytes instead of
choosing an operand or canonical zero. Raw ties and sticky boundaries retain the
full product precision qualified by the direct primitive.

## Error, provenance and qualification bounds

Every Overflow preserves its complete native diagnostic after a 54-byte
pre-entry prefix. The verifier derives the consumed-selector continuation from
its independently reconstructed six-byte call slot: 01A3:01C4 for baseline
frames and 01A3:01C7 for the declared padded frames. Original module BP/SP,
synthetic BP, default route 0a68 and absent error hook are checked separately.
No post-error FAC/register state is invented. General unwind, arbitrary frames/
modules, hooks and ON ERROR/RESUME remain unqualified.

Immutable manifests pin all artifacts, frozen source and recipes. The verifier
reconstructs complete copied-image hashes, exact inventories and relocation
bounds, and checks pinned DOSBox Staging 0.83.0/fixed 200000-cycle headless launch,
raw 2026-11-02/time-zero controls and native shell-return provenance. ERRORLEVEL
alone never classifies arithmetic success. The independent exact-rational product
oracle from direct multiplication supplies expectations, with source-qualified
pre-round underflow/residue rules; neither captured output nor Go is the oracle.

Portable fixtures retain separate address/execution schemas, full raw traces and
source hashes. Go tests compare all 153 controls against the shared resolver and
existing multiplication API without an emulator. Nineteen verifier/corruption
tests reject changed bytes, lost precision/residue, operand-selection zero,
round-first underflow, fake callers, SINGLE/profile substitution, unsafe-read
claims, changed error continuation/padding and frozen-source mutation. CI runs
both new checks and Git attributes preserve exact native bytes.

```sh
python3 scripts/verify_inline_multiply_double.py
python3 scripts/test_verify_inline_multiply_double.py
go test -race ./internal/qbmbf ./internal/qbrng ./internal/qbinit
go vet ./internal/qbmbf ./internal/qbrng ./internal/qbinit
```

Gameplay, source fingerprints, save 35 and sysop behavior are unchanged. Next:
audit retained direct DOUBLE division entry/kernel/caller evidence before adding
missing controls. Do not repeat completed SINGLE arithmetic, DOUBLE conversions,
direct/inline addition/subtraction/multiplication or initializer acceptance.
DOUBLE division, general unwind, complete maintenance, DOS save interoperability
and native Windows/live-BBS acceptance remain separate.

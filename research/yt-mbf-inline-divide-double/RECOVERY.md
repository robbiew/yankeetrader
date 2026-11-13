# Bounded inline DOUBLE division

## Retained source and composition

INT3F/8e composes `SingleAddInlineOffset` with
`DivideDoubleWithFAC(selectedMemory,FAC,FAC)`. The historical resolver name is
retained. No new arithmetic algorithm or source query was required. The
README, plan, retained source, APIs and open PRs were audited first. PR #144
owned the direct division dependency when this slice began stacked on its branch.
That parent is now merged as `ba4d27b0`, its ancestry is verified, and this slice
now includes the merged dependency and targets main. No direct controls are duplicated.

The parent's immutable `yt-mbf-divide-double/rea/division.json` already includes
analysis af8e: `CALL 1ec3; MOV DI,0016; CALL 1f6b`. Original file bytes
b18e..b196 are `e8326fbf1600e8d46f`; the dispatch table maps /8e to af8e.
The same source retains quotient/correction, divisor staging and error routing.
Existing packets cover the shared resolver/frame, normalizer, ABI and fatal
messages. The verifier authenticates this source through the direct division
verifier, then constrains the inline entry and dispatch separately.

The reused [caller inventory](../yt-mbf-divide-double/maintenance-calls.json)
contains nine direct /8a sites and **no inline /8e sites** in the bounded
annotated maintenance listing. The new selectors and frames are synthetic
controls, not observed normal maintenance callers or an exhaustive indirect-call
audit. Actual-header controls from other arithmetic are not relabeled here.

## Distinct eight-byte native profiles

All **163 first-attempt disposable processes** completed without retry or
replacement:

- **15 resolver-only controls**, marker `DV8E`, 69 bytes each: bm/bz descriptor
  variants, selectors 00/80/7f/ff, wrapped offsets and a fallback descriptor.
  A copied-runtime `RETF; NOP; NOP` replaces only post-resolver `MOV DI,0016`
  at file b191..b193. No operand is read and no arithmetic is claimed.
- **148 full executions**, marker `DVF1`: **120 numeric returns**, **ten exact
  Overflows** and **18 exact Division-by-zero diagnostics**. Runtime code is
  unchanged. Both descriptors and safe synthetic selectors 80/8a cover ordered/
  reversed division, all input sign pairs, zero aliases and 0/0 precedence,
  full-width guard/sticky brackets at both normalization paths and parities,
  range boundaries and early/late underflow. Three raw divisor shapes separately
  exercise late underflow, early underflow and adjacent minimum-normal returns.
  Declared 16/32-byte padded frames cover both error kinds and both zero-residue
  underflow paths.

The selected numerator and alternate-base poison remain unchanged on success.
Zero numerators and early range underflow retain the original right-FAC seven
residue bytes. Late normalization underflow at raw exponent difference -128
instead retains `00 + originalDivisor[0:6] + 00`, as qualified by the separate
parent finding and forty counter-controls. Inline traces verify this distinction
with the divisor bound to FAC; an operand-selected or canonical zero cannot
substitute for either raw residue. A zero divisor wins even for 0/0.

The resolver chooses caller-CS base12 only for descriptor tag 7a62, otherwise
base10; it masks the selector high bit, uses eight-byte slots and wraps at
16 bits. Wrapped controls remain offset-only. Full executions require complete
safe eight-byte spans for selected and alternate blocks. Successful 99-byte
frames retain all FAC/input/poison bytes, RNG/default mode, AX and declared
DS/ES/BP state.

## Provenance and errors

Each exact acquisition source and closed recipe was frozen before first launch.
Both original initializer startup calls remain. Only copied diagnostic code,
declared frame/header metadata, operands/FAC and runtime RNG data seed change.
Independent preflight reconstructed all payloads, excluded loader relocation
overlaps and checked safe reads. Original binaries, earlier packets, observations
and manifests are unchanged; every first process outcome is kept.

Both error types retain complete native messages after the 54-byte pre-entry
prefix. The verifier derives the consumed-selector continuation from its
independent six-byte call-slot model: 01A3:01C4 for baseline frames and
01A3:01C7 for the declared padded frames. Original module BP/SP, synthetic BP,
default route 0a68 and absent error hook are checked separately. No post-error
FAC/register state is invented. Arbitrary frames/modules, hooks, ON ERROR/RESUME
and general unwind remain outside this qualification.

Fixed immutable manifests pin every artifact, source and recipe. The verifier
reconstructs full copied-image hashes, exact inventories and relocation bounds,
and checks pinned DOSBox Staging 0.83.0/fixed 200000-cycle headless launch, raw
2026-11-02/time-zero controls and native shell returns. ERRORLEVEL alone never
classifies arithmetic success. The parent's independent exact-rational quotient
oracle supplies expected results and source-qualified early/late residue rules;
neither Go nor captured output is used as the expected-answer source.

Portable fixtures retain separate address/execution schemas, complete raw traces
and source hashes. Go tests compare all 163 controls through the shared resolver
and existing division API without an emulator. Twenty verifier/corruption tests
reject lost precision, wrong operand order, zero-divisor precedence/error
conflation, early/late residue substitution, unsafe-read claims, fake callers,
SINGLE/profile swaps, changed error continuations/padding and frozen-source
mutation. CI runs both new checks; Git attributes preserve raw native bytes.

```sh
python3 scripts/verify_inline_divide_double.py
python3 scripts/test_verify_inline_divide_double.py
go test -race ./internal/qbmbf ./internal/qbrng ./internal/qbinit
go vet ./internal/qbmbf ./internal/qbrng ./internal/qbinit
```

Gameplay, source fingerprints, save 35 and sysop behavior are unchanged. After this inline milestone merges, reconcile remaining runtime
and maintenance gaps against current APIs, retained evidence and open work;
do not reschedule completed binary arithmetic or conversions. General unwind,
production maintenance integration, DOS save interoperability and native Windows/
live-BBS acceptance remain separate. This slice does not qualify those boundaries.

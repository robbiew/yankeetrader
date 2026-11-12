# Bounded inline DOUBLE subtraction

## Existing evidence and composition

INT3F/9e composes `SingleAddInlineOffset` with
`SubtractDoubleWithFAC(selectedMemory,FAC,FAC)`. The historical offset-helper
name is retained; subtraction reuses the qualified direct primitive and addition
kernel. No new source query or arithmetic algorithm was required.

The README, current plan, retained sources, APIs and open PRs were audited first.
PR #140 merged as `3fc4ec74` after current-head CI and reviews were clear. Its
head and merge commit were verified on main before this branch began; merged
PR #138's separate inline-addition observations remain intact. No overlapping
inline DOUBLE subtraction implementation or open PR was found.

The [direct subtraction supplement](../yt-mbf-subtract-double/RECOVERY.md)
authenticates the original wrapper, full 56-bit kernel, ABI and error packets.
The immutable `yt-plague-civil-war/rea/target-paths.json` packet already retains
analysis ad86: `CALL 1ec3; MOV DI,0016; CALL 1f6b`. Original file bytes at
af86..af8e are `e83a71bf1600e8dc71`, and the dispatch table maps /9e to ad86.
The shared wrapper flips the right high-word sign in a register before entering
addition, including exponent-zero aliases. Operand memory stays unchanged.

The reused [original-byte caller inventory](../yt-mbf-subtract-double/maintenance-calls.json)
contains 21 direct subtraction sites and **no inline /9e sites** in the bounded
annotated maintenance listing. The new frames/selectors are synthetic controls,
not observed execution of a normal inline subtraction maintenance caller or an
exhaustive indirect-call audit. Actual-header controls from addition are not
relabeled as subtraction callers.

## Two eight-byte native profiles

All **117 first-attempt disposable processes** completed without retry or
replacement:

- **15 resolver-only controls**, marker `DS9E`, 69 bytes each: bm/bz descriptors,
  selectors 00/80/7f/ff, wrapped offsets and a fallback descriptor. A copied-runtime
  `RETF; NOP; NOP` replaces only `MOV DI,0016` at file af89..af8b. These compute
  offsets without reading operands or executing arithmetic.
- **102 full executions**, marker `DSF1`: **88 numeric returns** and **14 exact
  Overflows**. Runtime code is unchanged. Both descriptors and safe synthetic
  selectors 80/8a exercise directional/reversed subtraction, signs, zero aliases,
  cancellation/underflow, low significand bits, even/odd ties, native 56/57 gap
  behavior, word alignment and range boundaries. Separate 16/32-byte padded
  frames cover Overflow and raw cancellation/underflow residue.

Closed recipes and exact acquisition sources were frozen before first launch.
Both original initializer startup calls remain. Only copied initializer diagnostic
code, declared frame/header metadata, operand data and runtime RNG seed change.
Independent preflight reconstructed every payload, excluded loader relocation
overlaps and checked complete safe eight-byte read spans before launch.
Original binaries, historical source packets, observations and manifests are
unchanged. Every first process outcome is retained.

The resolver chooses caller-CS base12 for descriptor tag 7a62 and base10 otherwise,
masks the selector high bit, uses eight-byte slots and wraps at 16 bits. Wrapped
cases remain offset-only. Full executions preserve selected memory and alternate-
base poison, RNG, mode, AX and declared DS/ES/BP state in successful 99-byte
frames. All eight initial/result FAC bytes are retained. Zero aliases are chosen
after the register sign flip; cancellation/underflow clears only the original
right-FAC exponent and retains its seven residue bytes.

## Error and provenance boundaries

Every Overflow preserves its complete native diagnostic after a 54-byte
pre-entry prefix. The verifier derives the consumed-selector continuation from
its independent six-byte call-slot model: 01A3:01C4 for baseline frames,
01A3:01C7 for the declared padded frames. Original module BP/SP, synthetic BP,
default route 0a68 and absent hook are checked separately. No native post-error
FAC/register state is fabricated. Arbitrary frames/modules, hooks, ON ERROR/
RESUME and general unwind remain unqualified.

Fixed immutable manifests pin every artifact, source and recipe. The verifier
reconstructs full copied-image hashes, exact inventories, relocation boundaries,
pinned DOSBox Staging 0.83.0/fixed 200000-cycle headless launch, raw 2026-11-02/
time-zero controls and native shell-return provenance. ERRORLEVEL alone does
not prove arithmetic success. The independent exact-rational difference oracle
from direct subtraction supplies expected results, with source-qualified alias,
gap and residue rules; captured outputs and the Go result are not its oracle.

Portable fixtures retain distinct address/execution schemas, full raw traces and
source hashes. Go tests compare all 117 controls using the shared resolver and
existing subtraction API without an emulator. Nineteen verifier/corruption tests
reject changed bytes, lost precision/residue, addition or operand-order
substitutions, memory mutation, fake callers, SINGLE/profile swaps, unsafe-read
claims, changed continuation/padding and frozen-source changes. CI runs both new
checks; Git attributes preserve raw native bytes.

```sh
python3 scripts/verify_inline_subtract_double.py
python3 scripts/test_verify_inline_subtract_double.py
go test -race ./internal/qbmbf ./internal/qbrng ./internal/qbinit
go vet ./internal/qbmbf ./internal/qbrng ./internal/qbinit
```

Gameplay, source fingerprints, save 35 and sysop behavior are unchanged. Next:
audit retained direct DOUBLE multiplication source/callers and existing controls
before adding missing coverage. Do not repeat completed SINGLE arithmetic,
DOUBLE conversions, direct/inline addition/subtraction or initializer acceptance.
Other DOUBLE arithmetic, complete maintenance, DOS save interoperability and
native Windows/live-BBS acceptance remain separate.

# Bounded inline DOUBLE addition

## Retained evidence and composition

INT3F/86 composes `SingleAddInlineOffset` with
`AddDoubleWithFAC(selectedMemory,FAC,FAC)`. The existing offset helper also
serves this eight-byte operation; its historical name is retained. No new
arithmetic algorithm, production caller or source query was needed.

PR #137 merged as `8e711469` after current-head CI and reviews were clear;
both its head and merge commit were verified on main before this branch began.
The plan, README, original bytes and retained source were checked first.
The [direct DOUBLE addition supplement](../yt-mbf-double-add/RECOVERY.md)
already authenticates the shared 56-bit arithmetic, zero/gap behavior and ABI.
Its original-byte [caller inventory](../yt-mbf-double-add/maintenance-calls.json)
retains four separately listed inline /86 sites at code offsets 2541, 32965,
33287 and 33489, using selectors 80 and 8a. This is a static bounded inventory,
not observed execution of those normal maintenance paths or indirect coverage.

The existing `yt-plague-civil-war/rea/target-paths.json` packet retains the entry
at analysis ada7: `CALL 1ec3; MOV DI,0016; CALL 1f6b`. Its original file bytes
at afa7..afaf are `e81971bf1600e8bb71`; the dispatch table maps /86 to ada7.
The parent kernel tail and shared resolver/frame/error packets cover the rest.
The verifier reuses their fixed source authentication rather than duplicating
or relabeling earlier observations. Actual caller header words 7e00/08c3 and
both source selectors are covered by new offset controls.

## Distinct eight-byte native profiles

All **113 first-attempt disposable processes** completed without retry or
replacement:

- **19 resolver-only controls**, marker `DA86`, 69 bytes each: bm/bz descriptor
  variants, selectors 00/80/7f/ff, wrapped offsets, a fallback descriptor and
  actual caller-header/selector combinations. A copied-runtime `RETF; NOP; NOP`
  replaces only the post-resolver `MOV DI,0016` at file afaa..afac. This computes
  an offset without reading an operand or executing arithmetic.
- **94 full executions**, marker `DAF1`: **80 numeric returns** and **14 exact
  Overflow diagnostics**. Runtime code is unchanged. Both descriptor variants
  and source selectors exercise zero aliases, ordered inputs, signs,
  cancellation/underflow, low bits beyond float64 precision, even/odd ties,
  exponent gaps 56/57, word alignment and upper/lower range boundaries.
  Separately declared 16/32-byte stack-padding controls cover Overflow and
  noncanonical cancellation/underflow residue.

Every source and closed recipe was frozen before its first launch. Both
original initializer startup calls remain; only the copied initializer body,
explicit frame/module metadata, operand data and declared RNG seed change.
Original executables, earlier sources, native observations, manifests and
portable fixtures are unchanged. Preflight independently reconstructed every
payload and excluded loader relocation overlaps before any process launched.

The descriptor tag 7a62 chooses caller-CS base12; every other tag chooses base10.
The resolver masks the selector high bit, uses eight-byte slots and wraps at
16 bits. Wrapped controls remain offset-only. Full controls require complete
safe eight-byte spans for both selected and alternate-base memory.

Each full prefix records all eight initial FAC bytes, the selected memory
shadow, RNG, mode, descriptor/header values, synthetic BP and original runtime
error context. Successful 99-byte frames retain all eight result bytes,
unchanged selected and alternate-base poison blocks, RNG/mode and declared
AX/DS/ES/BP state. Cancellation/underflow clears only the exponent, preserving
all seven initial right-FAC residue bytes; explicit nonzero residue cases prevent
canonical zero or a copied left operand from passing as equivalent.

## Errors, provenance and qualification limits

Every Overflow retains its complete native diagnostic following the 54-byte
pre-entry prefix. The verifier derives the consumed-selector continuation from
the independently reconstructed six-byte call slot: 01A3:01C4 for baseline
frames, 01A3:01C7 for the declared padded frames. Saved module BP/SP, default
route 0a68 and absent error hook are checked separately from the synthetic BP.
No native post-error FAC/register state is fabricated. General unwind, arbitrary
frames/modules, ON ERROR/RESUME and hooks remain unqualified.

Immutable manifests pin all artifacts, including exact frozen acquisition
sources and recipes. The verifier reconstructs complete copied executable
hashes, validates relocation boundaries, exact inventories, pinned DOSBox
Staging 0.83.0/fixed 200000-cycle launch, raw 2026-11-02/time-zero controls and
native shell provenance. ERRORLEVEL alone never classifies arithmetic success.
The arithmetic oracle is the independent exact-rational model qualified with
the direct primitive; expectations are not copied from observed result bytes.

The portable fixture preserves separate address/execution schemas, complete raw
traces and source hashes. Go tests compare every trace with the shared resolver
and existing DOUBLE primitive without an emulator. Eighteen verifier/corruption
tests reject changed bytes, lost precision/residue, wrong source selectors,
profile/SINGLE substitution, unsafe-read claims, wrong continuation/padding,
forged success and frozen-source changes. CI runs both new checks.

```sh
python3 scripts/verify_inline_add_double.py
python3 scripts/test_verify_inline_add_double.py
go test -race ./internal/qbmbf ./internal/qbrng ./internal/qbinit
go vet ./internal/qbmbf ./internal/qbrng ./internal/qbinit
```

This qualifies bounded inline DOUBLE addition. Gameplay, source fingerprints,
save 35 and sysop policy are unchanged. Next: audit retained direct DOUBLE
subtraction entry/caller evidence before selecting missing controls. Do not
repeat addition, completed SINGLE arithmetic, DOUBLE INT/FIX/signed16 conversion
or initializer acceptance. Other DOUBLE arithmetic, complete maintenance, DOS
save interoperability and native Windows/live-BBS acceptance remain separate.

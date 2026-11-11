# Bounded inline SINGLE division

## Scope and evidence reuse

INT3F/8d composes the already qualified inline resolver with division of selected
memory by the initial raw SINGLE FAC. `SingleAddInlineOffset` selects the address;
`DivideSingleWithFAC(left,FAC,FAC)` computes the quotient, zero residue or distinct
error. No new arithmetic implementation or production caller is introduced.

PR #134 merged after two green observations and an immediate full review/CI
recheck, protected by its expected head; its ancestry was verified on main before
this branch began. The plan, README, retained evidence and open PRs were checked
first. No overlapping open work or completed inline /8d corpus was found.

No source query was needed. The immutable division entry packet in
`yt-xannor-planets/rea/assault-paths.json` includes analysis addresses b525..b52d:
`CALL 1ec3; MOV DI,001a; CALL 1f6b`. Existing resolver/frame, dispatch, quotient,
normalizer and fatal-error packets cover the rest. `verify_single_divide` and
`verify_inline_overflow` authenticate those packets against archived BRUN30;
this verifier additionally checks inline /8d's dispatch target b525 and complete
entry bytes at original file offsets b725..b72d.

The original-byte maintenance inventory remains 8 direct /87 and 16 direct /89
sites, with no direct /8b or inline /8d sites in the annotated listing. The new
controls are synthetic entry/frame controls, not observed execution of a normal
inline /8d maintenance caller or exhaustive indirect-call coverage. Actual-header
controls from other arithmetic operations are not relabeled as division callers.

## Two separate native profiles

All **93 first-attempt processes** completed without retry or replacement:

- **15 resolver-only controls**, marked `ID8D`: both bm/bz descriptor variants,
  selectors 00/80/7f/ff, wrapped offsets and a fallback descriptor. These compute
  an offset only, without dereferencing a potentially unsafe operand or doing
  arithmetic. A copied-runtime `RETF; NOP; NOP` at file b728 replaces exactly the
  post-resolver `MOV DI,001a`; its full image hash is independently reconstructed.
- **78 complete inline executions**, marked `IOF1`: 54 numeric returns, 10 exact
  Overflow diagnostics and 14 exact Division by zero diagnostics. The copied
  runtime code is unchanged. Both descriptors and safe selector slots exercise
  ordered/reversed division, signs, canonical and noncanonical zero divisors,
  zero numerators, prior-FAC underflow residue, four near-half guard/sticky pairs,
  and lower/upper range boundaries. Stack padding 16/32 adds finite underflow,
  Overflow and 0/0 controls in separately declared frame contexts.

Each frozen acquisition source and recipe is retained before its first launch.
The original two startup calls remain intact; only the copied initializer body,
explicit module/frame metadata, test operands and runtime RNG seed are changed.
Every first outcome is retained. Neither original DOS binaries nor previous
source packets, observations, manifests or portable profiles were changed.

The selected numerator and alternate-base poison remain unchanged on success.
FAC output preserves the initial right-FAC lower bytes when its exponent is
cleared, rather than copying the numerator or making a canonical zero. Divisor
exponent zero wins even for 0/0. RNG, default mode, AX and declared DS/ES/BP
state are checked. The descriptor chooses caller-CS base12 only for tag 7a62;
otherwise it chooses base10, masks the selector to 7 bits, uses eight-byte slots
and wraps at 16 bits. Wrapped resolver controls are never promoted to safe reads.

## Error and provenance boundaries

Both failure types retain their complete native diagnostics. The source-based
verifier derives the consumed-selector continuation from the reconstructed
six-byte call slot: 0194 for baseline frames and 0197 with the padding prologue.
It separately records the synthetic frame BP, original module BP, saved runtime
BP/SP, default route 0a68 and absent error hook. These checks do not admit arbitrary
frame depth, error hooks, ON ERROR/RESUME or a general unwind algorithm.
No post-error FAC/register state is invented; portable error outputs remain null.
The Go API's zero-array rejection result is not a claim about native state.

The immutable manifests pin every observed byte. The independent verifier checks
complete artifact inventory, exact copied-image reconstruction, loader relocation
boundaries, pinned DOSBox Staging 0.83.0 host, fixed 200000 cycles, headless mode,
raw 2026-11-02/time-zero controls, shell provenance, frozen actual acquisition
source and exact rational arithmetic. Native ERRORLEVEL alone never classifies
a numerical result. The portable fixture contains distinct address/execution
profiles and retains complete raw traces and hashes.

Seventeen verifier/corruption tests reject changed trace bytes, opcode or operand
order substitutions, error conflation, FAC residue loss, consumed-byte/address
changes, forged success, wrong padding, swapped profiles and source rewrites.
Go tests compare the shared resolver and division primitive against every trace.
The shared validators retain their closed operation choices and unchanged older
fixture schemas; division full/error frames cannot enter the resolver-only API.

```sh
python3 scripts/verify_inline_divide.py
python3 scripts/test_verify_inline_divide.py
go test -race ./internal/qbmbf ./internal/qbrng ./internal/qbinit
go vet ./internal/qbmbf ./internal/qbrng ./internal/qbinit
```

This qualifies bounded inline SINGLE division, not DOUBLE arithmetic, arbitrary
stack/unwind behavior, complete maintenance replay, or native BBS/Windows
acceptance. Gameplay, generator/replay source fingerprints, save 35 and sysop
policy remain unchanged. Audit remaining arithmetic/conversion evidence and
callers before choosing another numeric slice; do not repeat these controls.

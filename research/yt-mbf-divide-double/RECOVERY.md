# Direct raw-DOUBLE division

## Entry contracts and evidence reuse

`DivideDouble` qualifies BRUN30 INT3F/8a FAC divided by memory.
`DivideDoubleWithFAC` qualifies /88 memory divided by memory with independent
initial FAC, and /8c memory divided by FAC by passing right as initialFAC.
The implementation normalizes two exact 56-bit significands, scales the
numerator into at most 112 bits and uses `bits.Div64` plus the exact remainder
for rounding. It uses no float64 or external dependency.

| Entry | Loaded offset | Inputs and initial FAC |
| --- | --- | --- |
| 88 | af94 | SI numerator memory, DI divisor memory; independent initial FAC |
| 8a | af89 | SI set to DOUBLE FAC, DI divisor memory; initial FAC is numerator |
| 8c | af91 | SI numerator memory, DI set to DOUBLE FAC; initial FAC is divisor |

The README, plan, APIs, retained source and open PRs were audited first. No
competing PR or existing direct DOUBLE division API/corpus was found. PR #143's
inline multiplication is merged as `888b57df`; this branch starts there.
Completed SINGLE arithmetic, DOUBLE conversions, direct/inline addition,
subtraction and multiplication, and initializer acceptance were not repeated.

Existing DOUBLE multiplication/addition source authenticates the ABI, shared
normalizer, zero exit and range-error path. SINGLE division evidence retains
the shared code-11 dispatcher and exact `Division by zero` text; it is reused as
source authority, not relabeled as DOUBLE execution evidence. Only **259 missing
bytes**, analysis 1af89 through 1b08b, were queried. The complete immutable REA
record is `rea/division.json`, Evidence
`ev_cf48876215f6577e4344a3ea37863ceba46384066ad33b8b220ef78350aeb435`.
It includes direct/inline wrappers, divisor-first zero check, divisor staging,
quotient/correction helper, remainder/sticky join and fatal-error jump. Its fixed
hash, subject SHA, complete requested/returned length and loaded original bytes
are authenticated by the verifier. Earlier source packets remain unchanged.

The [original-byte caller inventory](maintenance-calls.json) matches nine /8a
maintenance sites. The bounded annotated listing has no /88, /8c or inline /8e
matches. This is static evidence, not observed normal-path execution or an
exhaustive indirect-call audit. /88 and /8c are qualified by source mappings and
new declared native controls. Inline /8e frames remain separate.

## Division-specific numeric behavior

An exponent-zero divisor raises `ErrDoubleDivisionByZero`, even for 0/0 or raw
zero aliases. A nonzero divisor with zero numerator clears only the original
initial FAC exponent. `ErrDoubleDivisionOverflow` separately denotes an out-of-
range quotient. Errors return a zero Go array as an API rejection convention;
that array makes no claim about native post-error FAC/register state.

Finite quotients use operand-sign XOR and the shared nearest/ties-even rounder.
Exact nonintegral half-way cases cannot arise at this precision: scaling by
2^55 or 2^56 absorbs the divisor significand's entire power-of-two factor, leaving
an odd denominator. Native guard controls instead bracket half by exact doubled-
remainder differences -1/+1, both normalization paths and both quotient parities.
Both signs and low bits beyond float64 precision are explicit.

**Underflow has two distinct raw residues.** Early range underflow (raw exponent
difference below -128) returns original initialFAC[:7] plus a zero exponent.
At raw exponent difference exactly -128, a smaller numerator significand reaches
normalization with exponent zero after the divisor has been staged in FAC.
Source afc8..afda copies the divisor backwards into scratch FAC with a zero low
byte. The subsequent zero exit therefore returns:

```
00 + originalDivisor[0:6] + 00
```

For example, numerator `0000000000000001`, divisor `cdab896745230181` and
independent FAC `5aa5d5c33c918092` return `00cdab8967452300`. Raising that divisor's
exponent to 82 takes early underflow and returns `5aa5d5c33c918000`. Matching the
numerator significand to the divisor at the late boundary returns the minimum
normal `0000000000000001`. This differs from SINGLE division and cannot be
modeled as unconditional original-FAC residue or canonical zero.

## Native controls and the retained boundary finding

All **178 first-attempt disposable processes** completed: **150 numeric returns,
12 exact Overflows and 16 exact Division-by-zero diagnostics**.

- The original **138-case corpus** covers operand order/signs, zero aliases,
  both quotient normalization paths, low-word boundaries, exact near-half
  brackets, exponent differences around both range boundaries and independent
  FAC encodings. Earlier SINGLE inputs are reused only as selected input values
  widened into DOUBLE; their old outputs are not expected DOUBLE answers.
- One original boundary observation disagreed with the initial all-underflow-
  preserves-FAC model. That observation, acquisition source and original fixed
  manifest were retained unchanged. Source inspection identified divisor staging.
  A separate frozen **40-case underflow supplement** checks four raw divisors,
  late/early/minimum-normal counter-controls through every direct entry, plus
  four independent prior-FAC states. All agree with the source-derived rule.

The combined entry coverage is 100 /8a, 49 /88 and 29 /8c controls. Exact raw
outputs, ordered memory shadows, RNG and default mode are retained. Both
original initializer startup calls remain; only copied diagnostic code,
operands/FAC and declared runtime RNG data seed change. Runtime code is untouched.
Each closed recipe and exact acquisition source was frozen before first launch.
Independent preflight reconstructed all payloads and excluded loader relocation
overlaps. No first outcome was retried, replaced or rehashed to redefine it.

The `DDP1` protocol records eight-byte initial FAC, numerator and divisor.
Successful frames are 66 bytes including full result, unchanged memory, RNG/mode
and footer. Every fatal frame preserves the complete native diagnostic at
01A3:011A for /88-/8a or 01A3:0117 for /8c, derived from independently modeled
five-byte call slots. No post-error state is invented. These are original-startup
diagnostic contexts, not arbitrary frames/modules, error hooks, ON ERROR/RESUME
or general unwind qualification.

Both immutable corpus manifests pin every artifact, frozen source and recipe.
The verifier reconstructs complete copied-image hashes, exact inventories,
relocation bounds, pinned DOSBox Staging 0.83.0/fixed 200000-cycle headless launch,
raw 2026-11-02/time-zero controls and native shell returns. ERRORLEVEL alone does
not classify arithmetic success. An independent exact-rational quotient oracle
applies the source-derived early/late residue rules; captured results and Go
are not its expected-answer source. Portable fixtures retain all raw traces and
source hashes, allowing Go tests without an emulator.

Twenty verifier/corruption tests reject wrong order, error conflation, zero-
divisor precedence changes, lost precision, wrong guard decisions, FAC rebinding,
late/early residue substitution, memory/RNG/mode mutation, altered continuations,
changed source/manifests and fabricated post-error FAC. CI runs both new checks,
and Git attributes preserve exact native bytes.

```sh
python3 scripts/verify_divide_double.py
python3 scripts/test_verify_divide_double.py
go test -race ./internal/qbmbf ./internal/qbrng ./internal/qbinit
go vet ./internal/qbmbf ./internal/qbrng ./internal/qbinit
```

Gameplay, source fingerprints, save 35 and sysop behavior are unchanged. Next:
audit retained inline DOUBLE division /8e entry/resolver/caller evidence before
adding missing bounded controls. Do not repeat completed arithmetic/conversions
or initializer acceptance. Inline /8e, general unwind, complete maintenance,
DOS save interoperability and native Windows/live-BBS acceptance remain separate.

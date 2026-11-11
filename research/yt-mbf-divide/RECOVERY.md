# Direct raw-SINGLE division

## Scope and reuse

This isolated numeric milestone qualifies direct BRUN30 INT3F/87 memory divided
by memory, /89 FAC divided by memory, and /8b memory divided by FAC. Numerator
and divisor order is significant. It introduces no production caller, gameplay
policy, generator/replay fingerprint, save-format change or sysop setting.
Inline /8d, DOUBLE division, general error/unwind behavior and complete DOS
maintenance remain separate research.

PR #133's inline multiplication was merged and its ancestry verified before this
branch began. The current plan, README and open PRs were checked first; division
had no completed implementation or competing PR. Existing source packets,
shared normalization, ABI and default fatal-error evidence were reused. Old
captures and hashes were not changed.

## Source authority

Original BRUN30.EXE SHA-256:
`3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8`.
The retained `yt-xannor-planets/rea/assault-paths.json` contains the first 48
bytes at analysis address `0x1b520`, plus dispatch and entry helpers. The existing
multiply/add packets retain the shared normalizer, range exits and ties-even
rounder. `yt-mbf-inline-overflow/rea/error-dispatch*.json` retains the fatal
error dispatcher, including the division error-code entry at `0x9ac`.

Only missing source was queried: 91 bytes at `0x1b550` through `0x1b5aa`,
completing the split instruction and quotient/correction helper, and 18 bytes at `0x135f8` for
code 11 plus the NUL-terminated `Division by zero` text. Both complete REA
packets are retained in `rea/`, pinned and compared byte-for-byte with the
original loaded image by `verify_single_divide.py`.

The static `maintenance-calls.json` independently matches every annotated
site to original YTMAINT bytes: 8 direct /87 sites, 16 /89 sites and no /8b
or inline /8d listing sites. This is a bounded static inventory, not exhaustive
indirect coverage or evidence that those callers executed.

## Arithmetic and entry state

The runtime tests the divisor exponent first. Any exponent-zero divisor,
including noncanonical residues and 0/0, raises Division by zero. A zero
numerator with nonzero divisor clears only the initial FAC exponent. Finite
underflow does the same before rounding. Independent prior FAC bytes must
survive; neither a canonical zero nor an operand's bytes substitute for FAC.

For nonzero operands the sign is XOR. Subtract exponents and normalize the
ratio of the two 24-bit significands. The quotient and exact remainder are
sufficient for the shared 24-bit nearest/ties-even rounder; the native helper
retains remainder information with a sticky bit. Compare the full remainder,
not a truncated guard bit. Range overflow and Division by zero have distinct
API errors. A returned zero array on error is an API rejection convention,
not an observation of native post-error FAC.

Exact nonintegral half-way rounding cases cannot arise from these 24-bit
significands at this precision: scaling by 2^23 or 2^24 absorbs the divisor's
entire power-of-two factor, leaving an odd denominator. The native common
rounder is ties-even; the division controls instead bracket half with exact
remainders above/below, both normalization paths and both relevant quotient
parities. This argument does not claim every native helper branch is covered.

## Acquisition and validation

`recover_single_divide.py` freezes itself and its closed 105-case recipe before
launching any disposable DOS process. Both original startup calls remain;
only the initializer diagnostic body and the copied runtime RNG data seed
are changed. Every first outcome is retained, with no retries or overwritten
observations. The original executables are never changed.

The corpus contains 75 numeric returns, 14 exact Overflow diagnostics and 16
exact Division by zero diagnostics. Inputs include operand order/signs, zero
aliases, four independent prior-FAC residues, finite/range extremes, exponent
differences around both boundaries and near-half guard/sticky brackets.
Each normal return preserves both memory shadows, RNG and the default mode.
Both error types retain exact original message bytes and entry-specific call
addresses; no post-error state is fabricated.

The pinned DOSBox Staging 0.83.0 host uses fixed 200000 cycles, headless video,
no sound and retained raw date/time controls. Prefixes and complete success or
fatal-message framing are independently reconstructed. The verifier uses exact
rational arithmetic, reconstructs every patched image and copied-runtime hash,
checks immutable observations/source attribution, then checks the portable Go
fixture against the complete corpus. Corruption controls reject changed bytes,
operand/FAC substitutions, error conflation, altered source and invented state.

Run:

```sh
python3 scripts/verify_single_divide.py
python3 scripts/test_verify_single_divide.py
go test -race ./internal/qbmbf ./internal/qbrng ./internal/qbinit
go vet ./internal/qbmbf ./internal/qbrng ./internal/qbinit
```

This is controlled direct-entry qualification. It does not establish arbitrary
inline frames, error hooks/ON ERROR/RESUME, native BBS/Windows acceptance, full
maintenance replay or new gameplay behavior. Next: audit existing inline /8d
evidence and callers before planning a separate bounded division-address slice.

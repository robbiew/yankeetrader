# BRUN30 SINGLE to signed 16-bit integer

This milestone qualifies the original runtime's INT3F/75 memory-input and
INT3F/77 FAC-input conversion entries, **in the measured default mode 0**.
The isolated `internal/qbmbf.Int16Single` implements their numeric result with
an explicit success/overflow boolean. It does not change gameplay arithmetic,
source recipes, twenty initializer goldens, save 35 or sysop procedures.

The earlier SINGLE/DOUBLE INT and FIX operations are already complete. Those
return MBF values and have different rounding rules; they are not substitutes
for this machine-integer conversion. Likewise, the recovered SINGLE addition
rounding controls do not qualify integer-cast rounding.

## Native source and dispatch

The original BRUN30 SHA-256 is
`3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8`.
Two retained REA/Ghidra 12.1.4 byte observations under `rea/` identify the
INT3F dispatch words and complete shared conversion window. MZ load segment
1000 maps observation address `10477` to file offset `677`, and `1a8c8` to
file offset `aac8`; the verifier checks identity, mapping and every byte.
Local ndisasm rendered those observed bytes; its rendering is not a separate
REA observation. Analysis used the already installed provider with process-local
Java/provider paths; original executables were not edited.

| Entry | Original code offset | Behavior |
| --- | --- | --- |
| INT3F/75 | `a8c8` | Read four raw SINGLE bytes through SI |
| INT3F/77 | `a911` | Read the same value from FAC `001a` |
| Shared kernel | `a91e` | Sign/exponent selection, integer shift and rounding |
| Return | `a955` | Write BX to FAC low word; retain FAC upper word |
| Overflow | `a971` | Jump to original runtime error path |

The default branch uses a right shift and carry addition, not ties-to-even.
A separate branch selected by DS byte `001f == 4` is visible in the original
bytes; it is **not measured or implemented by this API**. No assumption about
its normal callers or semantics is needed for this bounded mode-0 contract.

## Acquisition and observed outcomes

`native/recipe.json` and its frozen executed writer declare 48 distinct raw
SINGLE encodings for each entry: **96 independent, single-operation processes**.
Controls cover positive/negative subunits, adjacent encodings around 0.5 and
2.5, signed ties, zero aliases, signed-range boundaries, adjacent values around
positive 32767.5, negative 32768.5 and finite extremes. This does not claim an
exhaustive set of all 32-bit encodings or every adjacent negative-range input.

The disposable initializer redirects its entry into a fully declared diagnostic
payload; the copied runtime changes only the explicit unrelated RNG initial
state to 5. Conversion instructions and mode remain original. Before conversion,
the trace records the input, RNG state and actual mode byte (0 in every case).
On return, BX is stored before output can clobber it, followed by all four FAC
bytes, RNG state, mode and a footer. Successful traces are exactly 28 bytes.
Both entry variants produce identical numeric outcomes for the same inputs.

All 96 first attempts returned naturally without timeout, retry or missing
artifacts: **70 conversions succeeded and 26 emitted native Overflow**. Overflow
traces retain the complete 13-byte input prefix and exact CRLF runtime message,
including the operation-specific diagnostic call address. No result, preserved
post-error RNG state or successful-conversion footer is invented for an error.

Importantly, the runtime prints `Overflow ... Hit any key to return to system`
but DOSBox's shell then returns with **ERRORLEVEL 0**, just as in successful
controls. `PROGRAM_OK` therefore proves shell errorlevel only, not numeric
success. The audit requires exact successful framing or the complete native
error bytes; an exit code or error substring alone cannot qualify an outcome.

Each immutable case retains actual host launch/version/fixed CPU settings,
raw DOS date/time, stdout/stderr, shell return markers, trace, source/recipe and
complete reconstructed copied-image hashes. A fixed manifest covers the whole
corpus. Original evidence, old source profiles and other native captures remain
unchanged. Normal world generation/maintenance and live BBS sessions do not run.

## Recovered numeric contract

- Exponent-zero aliases all convert to integer zero, irrespective of residue.
- Other values round to nearest, with halves **away from zero**: +2.5 becomes
  +3; -2.5 becomes -3. This differs from INT flooring, FIX truncation and
  ties-to-even arithmetic.
- The rounded value must fit -32768 through +32767. Positive 32767.5 and
  negative -32768.5 overflow; -32768 succeeds. No wrap, clamp or saturation.
- On successful return, the FAC low word becomes the signed result and the
  upper two raw bytes remain unchanged. The Go API returns the numeric integer;
  it does not expose FAC state. Unrelated RNG state and mode remain unchanged.

Go uses the raw 24-bit significand, bounded integer shifts and sign-specific
range checks. The independent Python model uses exact rational rounding and
separately reconstructs payloads/images without importing the acquisition writer.
Portable vectors retain full traces, successful integers and explicit null error
outcomes, and must equal the entire verified corpus.

## Verification and remaining work

- `python3 scripts/verify_int16_single.py`: original source/REA identity, all 96
  outcomes, exact FAC bytes/errors, complete acquisition provenance and fixture.
- `python3 scripts/test_verify_int16_single.py`: nine tests for independent
  reconstruction, wrong tie policy, input/RNG/mode/FAC corruption, framing,
  fabricated/clamped error results, call-address substitution, immutable
  observation inventory and portable fixture replacement.
- `go test -race ./internal/qbmbf ./internal/qbrng ./internal/qbinit`: all new
  native vectors and existing numeric/initializer regressions. Explicit Go unit
  boundaries beyond the captured matrix are implementation tests, not additional
  native observations.

CI runs the new verifier and corruption controls. DOUBLE-to-integer, signed
32-bit casts, mode-4 conversion, other MBF arithmetic and arbitrary-world parity
remain separate work. Do not repeat the already completed RND, INT/FIX or this
mode-0 SINGLE-to-int16 slice as missing work.

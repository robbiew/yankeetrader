# BRUN30 raw-SINGLE INT boundaries

This milestone qualifies the raw-SINGLE `INT` path beyond the previously
recovered positive fighter-stock conversion. It reuses the original handler
packets and adds sixteen diagnostic runs: **1,024 raw input/output records over
51 distinct argument encodings**. `internal/qbmbf.IntSingle` implements the
recovered four-byte transformation. It is not wired into gameplay or generation;
source recipes, old fingerprints, save 35 and sysop procedures are unchanged.

## Existing evidence and the remaining question

[Positive stock conversion](../yt-maint/STOCK_CONVERSION.md) already established
that maintenance decodes SINGLE stock and calls INT3D/03 before adding the amount.
Its [native verifier](../../scripts/verify_maintenance_stock_conversion_native.py)
authenticates four existing reads across three original packets, including the
SINGLE entry `0x1acb2`, sign/exponent selection and positive mask helper `0x1ad17`.
This milestone does not repeat those reads or rewrite any historical packet.
Local `ndisasm` rendered retained bytes; no new REA observation is claimed.

The old controls admitted positive stock and did not qualify the negative branch,
integer boundaries across precision/byte transitions or all observed zero aliases.
The new runs exercise the runtime operation directly using declared raw inputs.
They do not widen historical maintenance replay admission or claim that negative
fighter stock is valid gameplay state.

## Diagnostic method and provenance

Original YT-INIT and BRUN30 hashes remain respectively
`601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2` and
`3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8`.
A copied initializer redirects startup to a fixed diagnostic payload. A copied
runtime changes only its explicit initial RNG state. No original is modified.
The probe invokes verified INT3D/03 with the raw SINGLE FAC, recording the input,
unrelated raw RNG state and all four resulting FAC bytes. It never executes the
normal universe generator or maintenance body.

`native/recipe.json` and `native/sources/recover_single_int.py` were frozen before
the first launch. Every first-attempt outcome is retained; all sixteen returned
normally, without retries, errors or missing diagnostic footers. The corpus
contains commands, actual host launch/version/fixed CPU evidence, raw DOS date/time,
console streams, exit/return markers, copied executable hashes and full traces.
The independent verifier reconstructs the complete payload and both copied image
hashes without importing the acquisition writer, then checks immutable manifest,
reused native contracts, all raw results and exact portable-fixture equality.
Original observation bytes, CRLF/control bytes and native hashes are unchanged.

## Observed and modeled behavior

- Exponent-zero inputs, including signed/mantissa residues, retain all four bytes.
- Positive values below one clear only the exponent. `INT(.75)` returns raw
  `00004000`, numerically zero; canonicalizing it to `00000000` is incorrect.
- Positive fractional values mask off the fractional significand bits.
- Negative fractional values floor toward negative infinity: `INT(-1.5) = -2`,
  not -1. Negative subunits become the canonical -1 encoding `00008081`.
- Negative rounding through a power of two normalizes the resulting magnitude:
  `INT(-255.5) = -256`, and `INT(-8388607.5) = -8388608`.
- Inputs at exponent 152 and above are already integral at SINGLE precision and
  retain their bytes, including the largest finite positive/negative encodings.
- INT leaves the unrelated 24-bit RNG state unchanged in every record.

The Go primitive uses bounded integer bit operations. The independent Python
reference instead uses exact rational arithmetic and integer floor, then
reconstructs MBF bytes, with separately stated raw-zero rules. Neither reads
native outputs to choose a branch. Numeric agreement alone cannot satisfy the
raw comparison.

The acquisition case label `positive-large` includes literal `fffffffe`, whose
sign bit makes it negative. That predeclared input and its actual outcome are
retained under their original label; classification always uses raw sign/exponent
bytes, never the label. This is not an additional positive-only observation.

## Verification and boundaries

- `python3 scripts/verify_single_int.py`: sixteen complete controls / 1,024 exact
  raw pairs, original image/dispatch identity and portable provenance.
- `python3 scripts/test_verify_single_int.py`: ten acceptance/corruption tests,
  including exact source payload, coherent numeric-zero normalization, negative
  truncation, nearest rounding, negative carry, input/RNG substitutions, framing
  and integral extreme preservation.
- `go test -race ./internal/qbmbf ./internal/qbrng ./internal/qbinit` and matching
  `go vet`: native Go vectors, raw-zero/carry regressions, existing RNG controls
  and all twenty unchanged initializer goldens.

The earlier stock-conversion native tests and 4,682 archive hashes also pass.
CI runs the independent native audit and new corruption tests. No full production
or live BBS acceptance is newly claimed. FIX, DOUBLE INT, machine-integer casts,
general MBF arithmetic and arbitrary-world maintenance remain separate work.
Do not repeat the positive stock recovery, argumented RND or these SINGLE INT
controls as missing work.

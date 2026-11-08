# Explicit BRUN30 mode-4 signed16 conversion

The earlier default-mode SINGLE/DOUBLE signed16 contracts are complete. This
separate slice qualifies the original branch selected by runtime DS byte `001f`
equal to 4. `qbmbf.Int16SingleMode4` and `Int16DoubleMode4` implement its measured
numeric behavior: **floor toward negative infinity**, with explicit signed16
range failure. Default-mode half-away rounding is unchanged.

**224 native first-attempt controls: 168 successful conversions and 56 exact
native Overflow outcomes** agree with independent rational verification and the
portable Go APIs. Mode 4 is selected by an explicit diagnostic instruction; these
observations do not establish a normal gameplay caller or change one.

## Reused original evidence and scope

No new static provider query is needed. The immutable [shared kernel
observations](../yt-mbf-int16/RECOVERY.md) and [DOUBLE helper/dispatch
observations](../yt-mbf-int16-double/RECOVERY.md) already cover all four entry
points and the complete mode-selected branch. The new verifier reauthenticates
those exact REA packets and their original BRUN30 SHA-256/file mappings.

At original code `a93b`, `cmp byte [001f],4` selects the separate branch `a8f0`.
Positive values shift without carry rounding. The negative path subtracts one
from the retained magnitude, shifts and complements it; subunit negative values
become -1. The exact lower-bound branch accepts -32768 but rejects a negative
fraction below it. This interpretation is checked against retained original bytes
and the independent execution controls; it is not borrowed from default-mode
results or the separate INT/FIX operations.

The withdrawn [signed32/LONG backlog](../yt-mbf-int16/CONVERSION_SCOPE.md) is not
revived here: QuickBASIC 3.0 does not provide that language type. Other MBF
arithmetic and internal/DOS multiword calculations are separate questions.

## Two independently frozen native acquisitions

The main `native/` recipe declares 200 one-operation cases: the same 48 SINGLE
and 52 DOUBLE raw encodings previously used to compare default-mode entries,
now executed through the actual mode-4 branch for both memory/FAC variants.
Reusing raw inputs is not reusing execution evidence. The source and recipe were
frozen before the matrix began; every first outcome is retained.

The separately frozen `precision-native/` supplement adds 24 DOUBLE controls
at exact predecessor/successor values around 1, 2 and 32768, signed in both
directions. They use the maximum 24-bit unrelated RNG state instead of 5.
These are distinct new cases, not retries or rewritten main-matrix evidence;
their actual executed writer and prelaunch recipe are retained independently.

Both diagnostic writers redirect only a copied initializer entry into a declared
payload. A copied runtime changes only its explicit initial RNG data, never its
conversion instructions. The diagnostic reads the original mode (0), executes
`mov byte [001f],4`, then records the applied mode before calling the original
entry. The complete copied payload/image and that intervention are independently
reconstructed by the verifier without importing either writer.

The 29-byte SINGLE and 37-byte DOUBLE success frames contain operation-specific
magic, RNG, raw input, original mode, applied mode, BX saved before output can
clobber it, full FAC, post-call RNG/mode and footer. On success, SINGLE replaces
FAC bytes 0–1; DOUBLE replaces bytes 4–5. Other FAC bytes retain exact input
residues. RNG and applied mode remain unchanged. Exponent-zero aliases yield
numeric integer zero while their unaffected FAC bytes remain authenticated.

Overflow traces retain the full input/mode prefix and complete original CRLF
error message with the distinct diagnostic call address for each entry. No
returned integer, successful footer, or post-error state is invented. Runtime
Overflow still returns DOS ERRORLEVEL 0; shell `PROGRAM_OK` alone cannot qualify
numeric success. No timeout, failed host launch, missing artifact or retry occurred.

Two fixed manifests authenticate every trace, raw DOS clock capture, actual
host argv/version/fixed CPU, stdout/stderr, return marker, executed source,
recipe and reconstructed copied-image hashes. Original guests and all older
observations remain unchanged. Normal world generation/maintenance does not run.

## Numeric and precision distinctions

| Input | Mode 4 | Default mode 0 |
| --- | --- | --- |
| +2.5 | 2 | 3 |
| -0.25 | -1 | 0 |
| +32767.5 | 32767 | Overflow |
| -32768.25 (DOUBLE control) | Overflow | -32768 |

The DOUBLE integer-boundary supplement preserves all 56 significand bits:
`1 - 2^-56` floors to 0, while float64 demotion produces 1; `-1 - 2^-55` floors
to -2, while demotion produces -1. At the range limits, `32768 - 2^-41` succeeds
as 32767, whereas demotion overflows. Conversely, `-32768 - 2^-40` overflows,
whereas demotion falsely permits -32768. These controls distinguish truncation,
nearest rounding, wrapping/clamping and premature floating-point conversion.

Go uses integer significands and floor/range checks without float64. The Python
reference independently uses exact fractions and signed integer floor. Numeric
output branches are not chosen from native results. Portable fixtures retain the
whole authenticated traces, input kind/entry, source trace digest and explicit
null error outcomes, and must equal both complete corpora.

## Verification and boundaries

- `python3 scripts/verify_int16_mode4.py`: both immutable corpora, all 224 native
  outcomes, existing static evidence, full image/source/launch/clock provenance,
  original/applied modes, FAC/RNG, exact errors and portable fixture equality.
- `python3 scripts/test_verify_int16_mode4.py`: twelve acceptance/corruption tests
  for independent source recipes/payloads, floor/default distinctions, original
  versus applied modes, residue/RNG/input damage, framing, fake/clamped success,
  exact error call sites, float64 substitution, immutable source/inventory and
  portable fixture replacement.
- Race-enabled Go tests and Go vet for qbmbf/qbrng/qbinit retain all existing
  numeric contracts and initializer goldens. CI runs the new audit and tests.

This is measured numeric behavior under a **declared mode-setting intervention**.
It does not establish when normal program code selects mode 4, add a sysop
setting, change gameplay/save policies, qualify every input encoding, or claim
arbitrary-world/native BBS acceptance. Other MBF arithmetic and any integration
require separate source/call-site evidence. Existing fingerprints and save 35
remain unchanged.

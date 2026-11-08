# BRUN30 raw-SINGLE FIX boundaries

This separate milestone qualifies `FIX`, which truncates toward zero, alongside
the already completed [SINGLE INT floor recovery](../yt-mbf-int/RECOVERY.md).
`internal/qbmbf.FixSingle` matches eight first-attempt diagnostic runs: **512 exact
raw input/output records over 28 distinct encodings**. No gameplay, generation
stream, source fingerprint, save format or sysop procedure changes.

## Existing work and source boundary

Positive stock conversion and SINGLE INT already establish the common fraction
mask. They do not establish negative FIX behavior: `INT(-1.5)` is -2, whereas
`FIX(-1.5)` is -1. Existing evidence is reused rather than reacquired.

The original BRUN30 SHA-256 remains
`3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8`.
The established stock-conversion native verifier authenticates the existing
original dispatch and common mask observations. Dispatch INT3D/01 selects code
`ac92`; its SINGLE load calls `ad69`, then the count-two fraction mask calls
`ad17`. The complete 16-byte FIX entry is additionally checked directly against
the original runtime file at `ae92`:
`87f3e8d20087f351b90200e8770059cb`.
This direct file-byte contract is not represented as a new REA observation.
The common mask bytes and dispatch are already covered by retained REA packets;
no old packet, evidence ID or observation hash is rewritten.

## New diagnostic controls

`native/recipe.json` and the frozen executed source predeclare eight cases:
zero aliases, positive subunits, negative subunits/fractions, negative byte and
precision boundaries, negative finite extremes and a mixed-history/max-RNG case.
Each executes 64 raw operations. They deliberately reuse relevant INT argument
encodings so the distinct runtime operations can be compared; no INT capture
is repeated or replaced.

The copied initializer redirects entry to a declared diagnostic payload and the
copied runtime changes only its explicit initial RNG state. The actual target is
INT3D/01, not a Python/Go substitute or the normal universe generator. Every
first attempt completed naturally with full framing and explicit DOS success/
return markers. No retries, discarded outcomes or evidence normalization.
Original executable bytes remain unchanged.

The independent verifier reconstructs both complete copied executable hashes,
checks frozen source/recipe and immutable corpus inventory, validates actual
host/version/fixed CPU/date/time/launch/return provenance, compares all raw FAC
bytes and requires the portable Go fixture to equal the entire native corpus.
The unrelated RNG state stays unchanged in every record. Runtime error outcomes
would have been retained explicitly; none occurred in this matrix.

## Native results

| Input | FIX result | Contrast with INT |
| --- | --- | --- |
| -1.5 | -1 | INT returns -2 |
| -255.5 | -255 | INT returns -256 |
| -8388607.5 | -8388607 | INT returns -8388608 |
| raw negative .75 `0000c080` | raw `0000c000`, numeric zero | INT returns canonical -1 |
| raw positive .75 `00004080` | raw `00004000`, numeric zero | Same positive truncation as INT |
| exponent-zero aliases | All four bytes unchanged | Same alias preservation as INT |
| integral large SINGLEs | All four bytes unchanged | Same integral preservation as INT |

The source path masks fractional bits without the sign-dependent floor
adjustment. Subunit results clear only the exponent; both sign and mantissa can
remain in a numeric zero. The Go primitive uses integer masks; the independent
reference uses exact rational truncation plus explicit zero-residue rules.
Numeric equivalence alone cannot pass the raw comparison.

## Verification and limits

- `python3 scripts/verify_single_fix.py`: eight native controls / 512 exact raw
  pairs, immutable source/launch/image provenance and portable fixture equality.
- `python3 scripts/test_verify_single_fix.py`: eight tests for complete corpus,
  independent payload reconstruction, erroneous INT substitution, zero-byte
  normalization, rounding away from zero, argument/RNG changes and framing.
- `go test -race ./internal/qbmbf ./internal/qbrng ./internal/qbinit` and matching
  `go vet`: FIX native vectors and explicit INT/FIX distinctions, previous INT/
  RNG vectors and twenty unchanged initializer goldens.

Existing INT/native stock tests and all 4,682 archive hashes remain valid. CI
runs the new audit and corruption controls. The separate [DOUBLE INT/FIX supplement](../yt-mbf-double/RECOVERY.md) now qualifies
those eight-byte operations. Machine-integer casts, general MBF arithmetic and
arbitrary-world replay remain outside this bounded milestone. Do not repeat the completed SINGLE FIX, SINGLE INT or
argumented RND controls as missing work. Live BBS acceptance is not newly claimed.

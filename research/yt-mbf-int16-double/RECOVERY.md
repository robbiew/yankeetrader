# BRUN30 raw-DOUBLE to signed16 conversion

This independently qualified supplement adds `qbmbf.Int16Double` for original
INT3F/76 memory and INT3F/78 FAC inputs in measured default mode 0. **104 native
single-operation controls over 52 distinct raw encodings** retain 74 successful
results and 30 exact runtime Overflow outcomes. Halves round away from zero;
rounded values outside -32768 through 32767 fail explicitly.

The earlier [SINGLE conversion](../yt-mbf-int16/RECOVERY.md), SINGLE/DOUBLE INT
and FIX operations and argumented RND are already qualified. No gameplay caller,
source recipe, initializer golden, save 35 or sysop procedure changes here.

## Existing evidence and new helper observation

The shared kernel and entry windows are reused directly from the immutable
SINGLE conversion REA packets; they are not recaptured or reattributed. Two new
REA/Ghidra 12.1.4 byte observations under `rea/` retain the DOUBLE dispatch words
and complete helper. The verifier checks each packet's fixed hash, original
BRUN30 identity, complete returned bytes and MZ mapping. Original BRUN30 SHA-256:
`3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8`.

| Path | Original code offset | Source mapping / role |
| --- | --- | --- |
| INT3F/76 | `a8d5` | SI points to eight-byte input; call `a9bc` |
| INT3F/78 | `a8e0` | Point SI at FAC `0016`; call `a9bc` |
| DOUBLE helper | `a9bc` | Read sign/exponent; compress lower words |
| Shared integer kernel | `a91e` | Default-mode rounding and range check |
| Dispatch observation | linear `10479` | File offset `679`, six bytes |
| Helper observation | linear `1a9bc` | File offset `abbc`, seventeen bytes |

The helper loads AX from input bytes 6–7. It ORs the two lowest words, replaces
their nonzero aggregate with 1, then ORs input word 4–5 into CX. This retains a
sticky indication below the high significand word. The shared mode-0 kernel
needs the integer bits and guard bit for half-away rounding, plus low-byte zero
and high-bit tests at the negative bound. The sticky reduction preserves those
tests; it is not a conversion to IEEE float64 or a rounded MBF SINGLE value.
Local ndisasm rendered original bytes to guide this interpretation; no additional
REA execution observation is claimed. The static provider used existing installed
tools with process-local paths and did not alter original executables.

## Native controls and precision

The frozen writer/recipe declare the complete 104-case matrix before launch.
Both entries use identical inputs in separate disposable processes: signed zeros
with residual bytes, subunits, ordinary ties, exact predecessor/successor values
around 0.5 and 2.5, values near positive 32767.5 and negative 32768.5, exact
-32768, signed-range fractions, larger integers and finite extremes.

DOUBLE has 56 significant bits. For example:

| Exact input | Native int16 outcome | If first demoted to float64 |
| --- | --- | --- |
| `2.5 - 2^-54` | 2 | 3 |
| `-2.5 + 2^-54` | -2 | -3 |
| `32767.5 - 2^-41` | 32767 | Overflow |
| `-32768.5 + 2^-40` | -32768 | Overflow |

The Go primitive uses a 56-bit integer significand, bounded shifts and explicit
signed limits. The independently written Python audit uses exact rational
rounding. Neither uses native outcomes to choose numeric branches or passes
through float64. Countertests deliberately demote selected inputs to demonstrate
why those results must be rejected.

## Capture provenance and complete error handling

The diagnostic redirects a copied initializer's entry into a declared payload.
The copied runtime changes only its unrelated RNG initial state to 5; conversion
instructions and mode remain original. The normal universe/maintenance body is
not executed. No original guest, existing capture or live save is modified.

Before each call, the trace writes `D16!`, RNG state, all eight input bytes and
the measured mode byte (0). After a successful call, it saves BX before output
can clobber it, then writes the eight FAC bytes, RNG, mode and footer. Successful
traces are exactly 36 bytes. FAC bytes 4–5 become the result; the lower four and
upper two input bytes remain intact. RNG and mode are preserved on success.
The API returns only the numeric result and success boolean, not FAC state.

All 104 first attempts returned naturally without timeout, retry, missing files
or discarded outcomes. The 30 overflow traces retain the full 17-byte input
prefix and original CRLF message, including the different diagnostic call
addresses for memory/FAC variants. No result or post-error state is synthesized.
As in the SINGLE controls, runtime Overflow returns to the DOS shell with
ERRORLEVEL 0. Therefore shell `PROGRAM_OK` is not proof of numeric success.
The verifier requires either complete successful framing or the exact complete
native error message; substring matching, clamping and fabricated return frames
are rejected.

A fixed manifest covers each case's raw DOS date/time, actual host argv/version,
fixed CPU, stdout/stderr, return markers, trace, copied executable hashes and
frozen source/recipe. The independent verifier reconstructs complete payloads
and copied images without importing the writer. Portable vectors must match
the full authenticated corpus, including explicit null overflow outcomes.
Native bytes and control characters are preserved with `.gitattributes` rules.

## Verification and limits

- `python3 scripts/verify_int16_double.py`: all 104 native outcomes, full source,
  REA, executable, launch, clock, return, mode/RNG/FAC and fixture provenance.
- `python3 scripts/test_verify_int16_double.py`: ten acceptance/corruption tests
  covering independent recipes/payloads, float64 demotion, tie policy, input and
  FAC residues, mode/RNG, framing, fabricated success/clamping, error call-site
  substitution, immutable inventory and portable fixture replacement.
- `go test -race ./internal/qbmbf ./internal/qbrng ./internal/qbinit` and matching
  `go vet`: new DOUBLE native vectors and precision regressions, old numeric
  primitives and the twenty unchanged initializer goldens.

CI includes the new audit and corruption controls. This is a bounded mode-0
DOUBLE-to-int16 recovery, not general MBF arithmetic or arbitrary-world/native
BBS acceptance. Mode 4 and other arithmetic paths remain
separate work. Do not repeat this or earlier numeric slices as missing work.


The earlier signed32/LONG deferral is withdrawn by the [conversion scope
audit](../yt-mbf-int16/CONVERSION_SCOPE.md): QuickBASIC 3.0 has no LONG language
type. This correction does not change any DOUBLE observation or API.


The [explicit mode-4 supplement](../yt-mbf-int16-mode4/RECOVERY.md) now qualifies
the separate floor-to-signed16 branch with declared mode setting. This default-mode
contract and its observations remain unchanged; normal mode-4 callers are not
inferred by those diagnostic controls.

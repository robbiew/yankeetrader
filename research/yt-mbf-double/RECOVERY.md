# BRUN30 raw-DOUBLE INT and FIX

The SINGLE [INT](../yt-mbf-int/RECOVERY.md) and [FIX](../yt-mbf-fix/RECOVERY.md)
operations are already complete. This separate milestone adds their eight-byte
DOUBLE counterparts: `internal/qbmbf.IntDouble` floors negative fractions, while
`FixDouble` truncates toward zero. **24 native diagnostic controls / 1,536 exact
raw input/output records over 42 distinct encodings** agree with the independent
reference and portable Go implementation.

No existing gameplay/generation arithmetic selects these primitives. Source
recipes, twenty initializer goldens, gameplay streams, save 35 and sysop
procedures remain unchanged. This is not general MBF arithmetic or arbitrary-world
maintenance compatibility.

## Existing source evidence reused

The original runtime SHA-256 is
`3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8`.
The existing stock-conversion native verifier authenticates four retained reads
across three original packets. Its dispatch window includes DOUBLE FIX opcode02
and DOUBLE INT opcode04; the existing `ac9d`/`acb2` windows include both entries:

| Operation | Runtime code entry | Exact entry bytes |
| --- | --- | --- |
| DOUBLE FIX, INT3D/02 | `aca2` | `87f3e8cd0087f351b90600e8670059cb` |
| DOUBLE INT, INT3D/04 | `ad0a` | `87f3e8650087f351b90600ebaa` |

Both load eight-byte input through `ad74`. Their mask count is six low bytes,
compared with the SINGLE count of two. FIX calls common mask `ad17`; INT joins
the existing sign/exponent-selected floor path at `acc1`. The new audit checks
these full entries against the original image and reauthenticates the unchanged
existing packets. Local `ndisasm` only rendered those already retained bytes;
no new REA observation, packet identity or static provider session is claimed.

## Native diagnostic acquisition

The frozen writer and prelaunch recipe in `native/` declare twelve argument
groups for each operation: zero aliases, positive/negative subunits, positive/
negative fractions, positive/negative byte boundaries, positive/negative precision
boundaries, positive/negative finite extremes and mixed histories. Each case has
64 operations; both operation families use the same argument groups, not the
other operation's outputs. This does not repeat earlier SINGLE acquisitions.

The copied initializer redirects entry to a declared diagnostic payload. The
copied runtime changes only the explicit initial RNG state; its math handler
instructions remain original. Each record retains eight input bytes, four RNG
state bytes and eight output FAC bytes. Operation-specific `DINT`/`DFIX` headers,
exact 1,292-byte framing and a terminating footer distinguish complete runs.
The unrelated RNG state stays unchanged for every record, including max-state
mixed controls. The normal universe/maintenance body is not executed.

All 24 first attempts completed naturally with explicit DOS success and return
markers. No native run was discarded, retried or normalized. Original guests
remain unchanged. A fixed manifest authenticates every retained command, host
launch/version/fixed CPU, raw date/time, stdout/stderr, copied-image hash and
actually executed source. The independent verifier reconstructs the complete
payload and copied images without importing the writer; the portable fixture
must equal the complete verified native corpus.

## DOUBLE precision and raw results

MBF DOUBLE has **56 significant bits**, not IEEE float64's 53. Encoding or
rounding through float64 before these operations can therefore lose data.
For example, MBF represents `2^53 - 1/2` exactly. Both positive INT and FIX must
produce `2^53 - 1`; float64 first rounds the input to `2^53`, producing a wrong
integer. For the negative value, FIX returns `-2^53 + 1` while INT carries to
`-2^53`. Native tests exercise these differences and the boundary near `2^55`.

The Go primitives operate on the raw 56-bit significand using bounded integer
masks and carries. The independent Python model uses exact rational arithmetic
and integer floor/truncation. Neither uses native outputs to choose a branch or
converts through float64.

Exponent-zero aliases retain all eight bytes. Positive subunit results, and FIX
negative subunit results, clear only the exponent and retain the seven other
bytes. Negative INT subunits become canonical -1 (`0000000000008081`). Integral
large finite values retain their original bytes. Numeric equality alone cannot
satisfy the audit: zero-residue and low-significand differences are checked raw.
The DOUBLE precision threshold for automatically integral inputs is exponent184,
compared with SINGLE's exponent152.

## Verification and remaining boundaries

- `python3 scripts/verify_double_int_fix.py`: 24 native controls, all 1,536 raw
  pairs, unchanged native source contracts, full image/launch/return provenance
  and exact portable fixture correspondence.
- `python3 scripts/test_verify_double_int_fix.py`: eleven acceptance/corruption
  tests covering independent payloads, float64 demotion, INT/FIX substitution,
  zero normalization, subunit direction, carry, input/RNG/result mutations,
  operation-specific framing and integral extremes.
- `go test -race ./internal/qbmbf ./internal/qbrng ./internal/qbinit` and matching
  `go vet`: full DOUBLE native vectors, explicit 56-bit regressions, existing
  SINGLE/RNG vectors and all twenty unchanged initializer goldens.

The existing SINGLE INT/FIX and stock-native tests and all 4,682 archive hashes
also pass. CI runs the new native audit and corruption controls. No new live BBS
acceptance is claimed. Remaining work includes machine-integer casts and other
MBF arithmetic/rounding operations; do not repeat the now-complete raw SINGLE/
DOUBLE INT/FIX or argumented RND milestones as missing work.

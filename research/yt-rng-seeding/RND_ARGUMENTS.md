# BRUN30 argumented RND: bounded native recovery

The shared primitive now supports raw-MBF-single `RND(argument)` through
`Generator.Float32MBF`. This extends the existing argumentless RND and RANDOMIZE
operations; no gameplay stream, source recipe, generation fingerprint, save
version or sysop command changes. Existing initializer goldens remain unchanged.

## Existing evidence reused

The original runtime SHA-256 is
`3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8`.
The original [port recovery packet](../yt-port-generation/runtime-rea.json)
already includes the entire relevant 110-byte handler:
`ev_e8f581f65736b7d492e44136bf3abf1ba826a4339027ca4743411df652ee2884`,
REA loaded address `0x1b2c2`, original file offset `0xb4c2`. The independent audit
pins this packet and checks every byte against the original runtime. Local
`ndisasm` rendered these existing bytes; it supplies no new REA observation.
A new REA open was unavailable because its configured Java path was stale; no
configuration or installation was changed, and no new REA evidence is claimed.

The runtime dispatch table binds argumented INT3D/33 to code `b2c7` and
argumentless INT3D/34 to `b2c2`. Both load through the common argument setup;
argumentless execution skips the argument tests at `b2ca..b2d4`. The argument
path first checks the MBF exponent, then the sign. The existing RANDOMIZE control
with a negative input is a different operation and did not establish this path.

## Recovered operations

For current 24-bit state `S` and raw MBF bytes `b0,b1,b2,e`:

| Input | State update | Result |
| --- | --- | --- |
| `e == 0`, including residual sign/mantissa | None | `S / 2^24` |
| `e != 0`, sign bit `b2 & 128 == 0` | Ordinary one-step LCG | Updated `S / 2^24` |
| `e != 0`, sign bit set | Replace state with `(b0 + 256*b1 + 65536*b2 + e) mod 2^24`, then one-step LCG | Updated `S / 2^24` |

The LCG is the already recovered `(214013*S + 1744579) mod 2^24`.
At `b316..b32b`, the exponent is added to the low mantissa byte with carry
through the next two bytes; the upper fourth byte is discarded. Negative RND
replaces the whole old state. RANDOMIZE instead XORs the argument words into the
upper 16 bits and preserves the old low byte. These are not interchangeable.
Exponent-zero arguments take the zero branch before their sign is examined.

## Controlled diagnostic runs

The frozen writer and prelaunch recipe under `argument-dos/` declare 16 cases,
each with 64 operations. These are copied-initializer diagnostic probes, not
normal universe generation or unmodified gameplay runs. Original executables
remain unchanged. The copied initializer redirects the entry into a declared
machine-code payload; the copied runtime changes only its initial raw state.
The verifier reconstructs both complete copied executable hashes independently.

Controls include current states 0/5/max, canonical/residual/signed zeros,
positive 1/.5/100.5, negative 1/.5/100.5, distinct old states, a low-word carry,
a full 24-bit wrap and mixed-call sequences. All 16 first-attempt executions
completed with exact frames, zero-error DOS return markers and natural host
exits. The dispatch preflight initially rejected an incorrect proposed slot35
before any native process or output directory was created; the actual frozen
probe uses verified slot33. No native outcomes were discarded or retried.

Every record retains raw argument bytes, resulting four-byte state and raw FAC.
All **1,024 state/numeric-value pairs** match the independent rules exactly.
Raw FAC bytes remain observations; this does not claim complete MBF/FAC residue
emulation. Captured DOS date/time, complete commands, loaded host/version/fixed
CPU, stdout/stderr, original hashes, copied hashes and actually executed source
are retained behind a fixed corpus manifest. Existing controls are unchanged.

## Implementation and verification

- `python3 scripts/verify_rng_arguments.py`: native identities, reused static
  bytes, independent payload/patch reconstruction, launch/return/clock provenance,
  every state/value pair and exact portable fixture correspondence.
- `python3 scripts/test_verify_rng_arguments.py`: eight tests, including
  complete corpus, independent payload agreement, framing, coherent state/value
  forgery, RANDOMIZE substitution, zero advancement, discarded carry and altered
  argument/FAC controls.
- `go test ./internal/qbrng ./internal/qbinit`: all native records through the
  new API, explicit zero/positive/negative properties, previous 4,096 RNG pairs
  and unchanged twenty whole-world initializer goldens.

The portable fixture includes all raw traces and provenance hashes, not rounded
printed samples. CI runs the new independent audit and corruption controls.
Remaining work includes broader MBF arithmetic, other numeric-runtime operations,
unmeasured encounter combinations and arbitrary-world compatibility. Do not
repeat argumented-single RND, the sixteen probes or the already merged bounded
tax/hiring replay as missing work.

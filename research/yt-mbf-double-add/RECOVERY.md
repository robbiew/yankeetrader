# Direct raw-DOUBLE addition

## Scope and reuse

`AddDouble` models BRUN30 INT3F/82 FAC plus memory. `AddDoubleWithFAC` models /80
memory plus memory with independent prior FAC; /84 memory plus FAC passes the
right operand as initial FAC. All operands and results retain eight raw bytes,
including the complete 56-bit significand. These isolated primitives introduce
no production caller, numeric policy, source fingerprint, save or sysop change.
Inline /86 and DOUBLE subtraction/multiplication/division remain separate.

PR #136 merged after two current-head green observations and an immediate full
review/CI recheck with expected-head protection. Its ancestry was verified on
fetched main before this branch began. The plan, README, APIs, native fixtures
and open PRs were audited first; DOUBLE INT/FIX and signed16 conversions were
already complete, while no raw DOUBLE addition primitive/corpus existed.

The retained `yt-plague-civil-war/rea/target-paths.json` observation named
`runtime-double-subtract` contains 90 bytes at analysis address 1ad81. Despite its
historical name, it includes the shared eight-byte copy exit, all direct-add
entry mappings, directional zero selection and the 56-bit exponent-gap guard.
The retained dispatch, ABI and Overflow/error packets were also reused.
Only the missing **352 bytes at 1addb..1af3a** were queried. The complete new REA
packet is retained as `rea/add-tail.json` and authenticated against the original
BRUN30 digest and loaded image. No old packet, observation hash or capture was
changed. Reusing a subtraction-named packet does not qualify DOUBLE subtraction.

The bounded static `maintenance-calls.json` inventory matches all annotated
slots to original YTMAINT bytes: four /80, ten /82 and no /84 direct sites. Four
inline /86 sites are recorded separately and excluded. These counts are static
caller evidence, not execution coverage or an exhaustive indirect-call graph.

## Native semantics and implementation

- A zero-exponent left operand copies the complete right encoding, even when
  both are zero aliases. A zero right operand instead copies the left. Thus
  bitwise zero selection is directional and must not be canonicalized.
- An exponent gap greater than **56** copies the complete dominant operand.
  At gap 57, `1 - 3*2^-58` therefore returns raw one; rounding the full exact
  mathematical sum would return the preceding DOUBLE encoding. The API preserves
  the native shortcut rather than promising unrestricted IEEE-style addition.
- Within the guard, the native alignment retains guard/sticky information and
  rounds to 56 significant bits with ties to even. Byte/word alignment, near-half
  values on both sides of the tie and low bits beyond float64 are controlled.
- Cancellation/underflow clears only the initial FAC exponent, preserving all
  seven sign/mantissa bytes. Independent /80 FAC residue is not either operand.
- Overflow retains the complete native fatal message. The Go API returns a zero
  array and false as a rejection convention; native post-error FAC is unclaimed.

The Go implementation aligns exact signed integers, bounded to **112 bits** by
the native gap guard, then rounds once. Standard-library `math/big` avoids losing
the bottom three significand bits through float64. Existing DOUBLE INT/FIX,
conversion and SINGLE primitives are unchanged. The independent Python oracle
uses exact rational arithmetic plus source-qualified zero/gap rules, not the Go
implementation or captured outputs as expected answers.

## Retained acquisition and controls

All **145 first-attempt disposable processes** completed: **136 numeric returns
and nine exact Overflows**. There are 89 FAC-plus-memory /82 controls, 36 /80
controls (including sixteen independent-FAC cases), and twenty memory-plus-FAC
/84 controls. The matrix includes raw zero aliases, sign changes, cancellation,
minimum/subunit results, maximum/carry/rounding overflow, low-significand bits,
even/odd half ties and adjacent sticky values. Same/opposite-sign exponent gaps
span bit/byte/word boundaries through 58; reversed and negative boundary cases
separately constrain the 56/57 cutoff. Two RNG initial states are retained.

The acquisition freezes its exact source and closed recipe before first launch.
Both original startup calls remain. The copied initializer body contains the
bounded diagnostic; runtime code is unchanged, with only its declared RNG data
seed set. Independent preflight compared every generated payload and rejected
loader relocations overlapping the patch before any process launched. All first
outcomes were retained, without retries or replacement. Originals remain intact.

The `DAD1` prefix records all eight prior FAC bytes, both ordered eight-byte
memory blocks, RNG and default mode. Every successful 66-byte frame preserves
both memory blocks, RNG and mode and retains the complete raw result and footer.
Every fatal frame retains its complete diagnostic at 01A3:011A for /80-/82 or
01A3:0117 for /84. The verifier derives those continuation offsets from the
independently reconstructed five-byte call slot; it never fabricates post-error
state. This is the declared original-startup diagnostic context, not arbitrary
modules, error hooks, ON ERROR/RESUME or general stack/unwind qualification.

Immutable manifests pin every observation, frozen source and recipe. The verifier
reconstructs complete copied executable hashes, verifies relocation boundaries,
artifact inventories, pinned DOSBox Staging 0.83.0/fixed 200000-cycle launch,
raw 2026-11-02/time-zero controls and native shell return provenance. DOS errorlevel
alone never classifies arithmetic success. Portable fixtures retain full traces
and source hashes; ordinary Go tests need no emulator or original executables.

Sixteen corruption/verifier tests reject lost precision/residue, changed bytes,
wrong ties/gap cutoff, reordered FAC bindings, altered continuations, counterfeit
success, changed source/fixture and unsupported SINGLE/inline entry substitutions.
Go tests compare all 145 full native frames and explicitly exercise precision
beyond float64 and independent prior-FAC behavior.

```sh
python3 scripts/verify_add_double.py
python3 scripts/test_verify_add_double.py
go test -race ./internal/qbmbf ./internal/qbrng ./internal/qbinit
go vet ./internal/qbmbf ./internal/qbrng ./internal/qbinit
```

Next: audit retained inline /86 caller/address evidence before adding missing
bounded controls. Do not repeat this direct arithmetic capture, completed
SINGLE arithmetic, DOUBLE INT/FIX/signed16 conversion or initializer acceptance.
General numeric parity, full maintenance, DOS save interoperability and native
Windows/live-BBS acceptance remain separate; gameplay and save 35 are unchanged.

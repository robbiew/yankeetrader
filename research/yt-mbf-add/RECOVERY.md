# BRUN30 raw-SINGLE addition, INT3F/81

`qbmbf.AddSingle(left, right)` now models the original FAC-plus-memory SINGLE
addition entry. Left is the initial four-byte FAC at `001a`; right is the memory
operand addressed through DI. **82 new one-operation native controls retain
78 raw results and four complete Overflow outcomes**. Nine earlier HQ reward
controls are separately reused as addition-followed-by-INT regressions.

This isolated primitive changes no existing gameplay, generation arithmetic,
source fingerprints, save 35 or sysop procedure. Other addition entry forms,
subtraction, DOUBLE arithmetic and multiplication/division remain separate.

## Existing evidence audited and reused first

The [HQ reward recovery](../yt-xannor-hq-reward/RECOVERY.md) already retained
positive credit-addition and rounding controls. Its complete REA packet remains
unchanged. Four selected original observations authenticate the runtime dispatch,
complete SINGLE addition kernel, credit helper and million-credit constant.
The new verifier checks packet identity, all returned bytes, original subjects
and MZ mappings; the existing reward verifier continues to check all 38 gameplay
controls and all twelve observations. No new provider query was needed.

Existing initializer contracts separately authenticate addition cancellation
and the shared normalizer/zero exit. Those contracts, annotated source listing
and twenty complete initializer goldens are reused, not regenerated. The prior
positive reward model and the initializer's residue handling remain correct in
their stated domains; this work fills raw signed/range/alignment gaps.

The original BRUN30 SHA-256 is
`3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8`.
Dispatch opcode 81 selects `b369`, which points SI at the existing FAC, then
joins the common addition body. Code `b3a5–b3ac` skips the smaller operand at
an exponent difference greater than 24. `b46b–b483` compares guard bits and
uses the low retained bit to select even ties. `b49a` clears only FAC exponent
`001d` on cancellation/underflow. The old observations cover the full paths.
Local ndisasm rendered those original bytes during the audit; it is not a new
REA observation or an additional execution corpus.

## Missing native controls

The frozen source and prelaunch recipe under `native/` declare 82 cases:

- Zero aliases, either operand zero, and both-zero operand order.
- Both signs, sign crossings, exact cancellation and nearby differences.
- Even/odd low-bit ties with adjacent below/above operands and signed carries.
- Exponent gaps 23–26, opposite signs, reversed operand positions and sticky bits.
- Minimum-normal differences, underflow, maximum finite values and rounding carry.
- Two maximum-RNG-state controls, alongside the other controls' explicit state 5.

The copied initializer redirects its first body instruction into a declared
single-operation diagnostic. The copied runtime changes only the explicit RNG
initial data; addition instructions and default mode remain original. No normal
world body or reward gameplay is executed. Every first attempt is retained,
without retry, timeout, missing artifact or discarded error.

Each trace starts with `ADD1`, initial RNG, both raw operands and measured mode
zero. DI points at the right operand and the diagnostic calls original INT3F/81.
A successful 34-byte frame records all four FAC result bytes, the unchanged right
operand, unchanged RNG/mode and `END!`. The four overflow traces preserve the
complete 17-byte input prefix and exact original CRLF error text, including
call address `01A3:00DA`; they do not invent a returned FAC or post-error state.
As in the cast controls, native runtime Overflow returns DOS ERRORLEVEL 0, so
shell success alone cannot qualify an arithmetic result.

A fixed manifest covers raw clock logs, actual host argv/version/fixed CPU,
stdout/stderr, return markers, trace, source, recipe and copied executable hashes.
The independent verifier reconstructs whole copied images and rejects relocation
overlap with the hook/payload. Original files and every older capture stay intact.

## Numeric and raw-byte behavior

| Case | Original INT3F/81 behavior |
| --- | --- |
| Normal retained addition | Round to 24 significant bits, ties to even |
| `1 + 2^-24` | 1 (even tie) |
| `(1 + 2^-23) + 2^-24` | `1 + 2^-22` (odd tie carries) |
| `1 - 3*2^-26` | 1, because the smaller exponent is 25 lower |
| `1.5 + (-1.5)` | Raw `00004000`, retaining the initial FAC mantissa |
| `-1.5 + 1.5` | Raw `0000c000`, retaining the opposite initial sign/residue |
| Both exponent-zero encodings | Return the right encoding, including its residue |
| Exact nonzero magnitude below minimum normal | Clear only the initial FAC exponent |
| Unrepresentable large sum or rounding carry | Original Overflow error |

The exponent-gap shortcut is **not** equivalent to correctly rounded IEEE
float32 addition. For `1 - 3*2^-26`, IEEE rounds to `1 - 2^-24`, while the native
kernel skips the smaller operand and returns 1. The shortcut is retained as
measured behavior, not corrected to a modern policy.

Likewise, mathematical commutativity does not imply identical raw zero bytes.
Cancellation and underflow preserve the initial left FAC's first three bytes,
even if they no longer describe the mathematical result's sign. If both operands
have exponent zero, the source's first zero test selects the right encoding.
Underflow is a successful raw zero result, not an overflow error or a subnormal
IEEE value. MBF SINGLE has no IEEE NaN/infinity encodings in this contract.

Go first applies those source-qualified zero/shortcut rules. The remaining gap
is bounded to 24, allowing an exact signed 64-bit sum of both 24-bit significands.
Integer normalization, guard/remainder comparison and ties-to-even rounding then
produce the MBF bytes, with explicit exponent bounds. The independent Python
reference uses exact fractions plus the separately source-derived shortcut and
raw-zero rules. Neither uses host floating-point arithmetic or native answers
to choose result branches.

## Reused positive reward controls

Nine earlier native cases retain base, zero, fractional and large balances,
including both 2^30 tie parities and balances where the effective million changes
or disappears. The fixture refers to original before/after world hashes and raw
credit fields. Original compressed worlds remain bound to their complete fixed
manifest; no earlier capture is rewritten or rehashed.

Go applies `IntSingle(AddSingle(beforeCredit, million))` and compares the resulting
raw credits with those retained native after-fields. This composes separately
qualified primitives for a regression; it does not replace the modern gameplay
reward policy, add a new native run, or broaden the old positive-only model.

## Verification and limits

- `python3 scripts/verify_single_add.py`: all 82 new native outcomes, whole copied
  image/source/host/clock/return provenance, original opcode/kernel contracts,
  right-input/RNG/mode preservation, complete error bytes and fixture equality,
  plus nine separately identified earlier reward controls.
- `python3 scripts/test_verify_single_add.py`: twelve acceptance/corruption tests
  covering independent recipe/payloads, odd/even ties, IEEE shortcut substitution,
  directional zero aliases, cancellation/underflow normalization, input/result/
  memory/RNG/mode corruption, framing, wrapped/clamped overflow, immutable source/
  inventory and forged new/reused fixture outputs.
- Race-enabled Go tests and Go vet for qbmbf/qbrng/qbinit cover every new trace,
  the nine reused rewards, explicit native/IEEE differences and old contracts.
- The existing HQ verifier, archive hash audit and twenty initializer goldens
  retain their independent validation. CI runs the new verifier and tests.

Only the INT3F/81 FAC-plus-memory state contract is qualified here. Other entries
can have a different prior FAC independent of their operands; those are not
silently admitted by this API. No exhaustive enumeration of every raw operand
pair, arbitrary-world parity, normal negative reward call or live BBS acceptance
is claimed. Existing saves and source profiles remain unchanged.

# Direct SINGLE-addition entry-state parity

The [INT3F/81 FAC-plus-memory contract](../yt-mbf-add/RECOVERY.md) is complete.
This supplement qualifies two other direct entry forms using the same original
kernel, but with separately measured operand/FAC relationships. **184 new native
controls retain 176 raw results and eight exact Overflow outcomes**.

`qbmbf.AddSingleWithFAC(left, right, initialFAC)` reuses `AddSingle` arithmetic and
adds the independent prior-FAC state required by memory-to-memory addition.
For memory-to-FAC addition, right must be the initial FAC. Existing entry81 APIs,
source profiles, gameplay, save 35 and sysop procedures remain unchanged.

## Original entry evidence reused

The unchanged HQ reward packet already covers the complete common kernel,
entry instructions and dispatch words. The new audit reauthenticates the parent
source contracts and checks these direct entries against those same original bytes:

| INT3F opcode | Original code offset | Operand mapping |
| --- | --- | --- |
| 7f | `b374` | Caller supplies SI = left memory, DI = right memory; prior FAC is independent |
| 81 (parent) | `b369` | Entry sets SI to FAC `001a`; left is initial FAC |
| 83 | `b371` | Entry sets DI to FAC `001a`; right is initial FAC |
| 85 (not qualified) | `b36e` | Calls the inline-address resolver before selecting FAC |

No new static provider query is required. Opcodes 7f/81/83 share the same
arithmetic: even ties, exponent-gap shortcut, right-operand selection when both
inputs have zero exponent, and the normalizer's exponent-only zero exit. The
last of these operates on the **prior destination FAC**, which need not equal
either memory operand. That is an entry-state contract, not another arithmetic
rounding rule or an independently rewritten numeric kernel.

The inline resolver used by 85 has its own compiled-frame/address obligations.
This supplement does not execute or admit it and does not relabel addition
wrappers as subtraction operations.

## New native controls and source provenance

The frozen recipe contains both direct entries over the parent's 82 operand/RNG
cases (164 new executions). Entry7f uses independent sentinel FAC `5aa5d592`;
entry83 installs right as the FAC, as required by its original entry instruction.
Twenty additional entry7f controls vary four prior FAC encodings over five
zero/cancellation/underflow cases: canonical zero, residual zero, a negative
minimum-normal encoding and negative maximum finite. Thus zero-result state is
measured independently of operand values rather than inferred from numeric equality.

Both user memory blocks are distinct from FAC. For entry7f, SI/DI point to those
blocks. For entry83, SI points to left memory and the original entry sets DI to
FAC; the recorded right memory block is only an unchanged trace shadow of its
initial FAC value. The verifier explicitly requires right == initialFAC for 83.
It does not pretend the shadow is a second operand consumed by that entry.

A copied initializer redirects entry to a declared one-operation diagnostic.
The copied runtime changes only its explicit RNG initial data, never addition
instructions or mode. Every first attempt is retained; all 184 terminated
naturally without timeout, retry, missing artifact or discarded error. Normal
world generation/maintenance does not run and no live data is mounted.

Complete 42-byte success frames retain `ASE1`, RNG, initial FAC, left/right raw
values, measured mode zero, raw result, both unchanged memory blocks, unchanged
RNG/mode and footer. The eight error frames instead retain the full 21-byte
input prefix and exact original CRLF Overflow message: diagnostic call address
`00F6` for 7f and `00F3` for 83, in segment `01A3`. No returned FAC or post-error
state is invented. Native Overflow again has DOS ERRORLEVEL 0; shell success is
not arithmetic success.

A fixed manifest binds the actual executed source, prelaunch recipe, copied
image hashes, raw DOS clocks, host argv/version/fixed CPU, stdout/stderr, return
markers and every trace. The independent verifier reconstructs entire payloads
and copied images and rejects loader relocation overlap. Original binaries and
all parent captures stay unchanged. Reusing raw operand cases is not reusing
execution evidence for an unobserved entry.

## Observed state distinctions

For `1.5 + (-1.5)`, entry81 retains the left FAC's `00004000` residue. Entry7f
with sentinel prior FAC returns `5aa5d500`; entry83, whose prior FAC is right,
returns `0000c000`. All three are numeric zero but different exact state.
Underflow follows the same prior-FAC exponent-only clearing rule.

If both operands have zero exponent, the shared fast path returns the **right
operand encoding**, ignoring an independent prior FAC. For example, memory left
`12345600` plus FAC right `ffffff00` through entry83 returns `ffffff00`.
Naively calling `AddSingle(right, left)` would return `12345600`. That mapping
matches many numeric examples but fails this raw state contract.

`AddSingleWithFAC` delegates numeric arithmetic to the unchanged parent API. Only
when both inputs are nonzero and a successful result has zero exponent does it
substitute the initial FAC's first three bytes and clear its exponent. Operand
zero fast paths remain operand-directed, not prior-FAC-directed. The Python
reference separately applies the qualified shared model and source-derived
entry-state rule; native results do not choose its numeric branches.

This general state API represents entry7f directly, entry83 with right as prior
FAC, and parent entry81 with left as prior FAC. It does not resolve inline
addresses, select gameplay callers or broaden old bounded replay admissions.

## Verification and boundaries

- `python3 scripts/verify_single_add_entries.py`: all 184 outcomes, complete
  frozen-source/image/host/clock provenance, direct entry mappings, actual FAC
  alias constraints, memory/RNG/mode preservation, exact errors and fixture.
- `python3 scripts/test_verify_single_add_entries.py`: twelve tests for independent
  recipe/payloads, arbitrary prior-FAC residues, naive operand-state substitutions,
  zero-alias swapping, the entry83 FAC constraint, input/state damage, exact error
  call sites, fabricated success, immutable source/fixture and complete framing.
- Race-enabled Go tests and Go vet for qbmbf/qbrng/qbinit preserve the unchanged
  parent vectors/rewards and old numeric/initializer contracts. CI includes the
  new audit and corruption controls.

All claims concern the direct 7f/83 forms with declared memory/FAC relationships.
No arbitrary inline85 frame, exhaustive operand-pair enumeration, subtraction,
normal gameplay caller integration or live BBS acceptance is newly claimed.

# Direct raw-SINGLE subtraction parity — 2026-11-09

## Source and scope

This slice qualifies direct INT3F/97, /99 and /9b subtraction. It reuses the
qualified [addition kernel](../yt-mbf-add/RECOVERY.md) and
[explicit prior-FAC state model](../yt-mbf-add-entries/RECOVERY.md). It does not
repeat arithmetic implementation, alter earlier observations, or depend on the
separate inline-addition PR #128.

The retained `yt-xannor-planets/rea/assault-paths.json` packet contains the entire
96-byte wrapper region at 1b354, the 396-byte dispatch table and 128-byte ABI
helper at 11f6b. The verifier pins the complete packet and maps every selected
byte back to the original archived runtime. The parent packet qualifies shared
normalization, gap skipping, rounding and range behavior. No new source reads
are needed for these direct subtraction entries.

| Entry | Loaded code offset | Inputs |
|---|---|---|
| 97 | b35f | SI left memory, DI right memory; independent prior FAC |
| 99 | b354 | SI set to FAC, DI right memory; prior FAC is left |
| 9b | b35c | SI left memory, DI set to FAC; prior FAC is right |

After the register-saving ABI call, the wrapper loads the right operand's high
word, XORs its sign bit in AL, then joins addition at b37a. It does not negate
operand memory or the actual initial FAC. The direction is **left minus right**.
`SubtractSingleWithFAC` copies and sign-flips right locally, then calls the
existing `AddSingleWithFAC`; `SubtractSingle` supplies left as prior FAC for 99.
No host floating-point arithmetic or duplicate rounding implementation is added.

`maintenance-calls.json` matches all 43 annotated direct call sites in the
archived maintenance listing against their original five-byte machine opcodes:
37 entry 97, one 99 and five 9b. This is a static direct-call inventory, not observed
execution or exhaustive indirect-call coverage. The inherited operand-case names
are identifiers from the old addition matrix, not descriptions of subtraction
results; each new recipe explicitly records subtraction opcode and ordered inputs.

## Native controls and observed state

The new frozen acquisition source retains every first outcome in a separate
process/mount. It keeps both original initializer startup calls intact, replaces
only the first body call with a diagnostic, and leaves runtime code unchanged.
The sole runtime data intervention is the declared initial RNG state. No world,
archive, live BBS data or old evidence is executed in place or rewritten.

All **266** first attempts completed naturally: **251 returned results** and
**15 exact native Overflow outcomes**. No observations were retried or rewritten.

Each of the three direct entries runs the existing 82 ordered operand/RNG
recipes, now through actual subtraction. Entry 97 uses independent prior FAC
`5aa5d592`; 99 installs left in FAC and 9b installs right. The unused memory block
is explicitly a trace shadow in FAC forms. Twenty extra 97 probes vary four prior
FAC encodings across both-zero, zero-alias, cancellation and both underflow
directions, at initial RNG 16777215. Both original operand memory blocks are
checked unchanged on successful return. RNG and default mode remain unchanged.

The controls cover both signs, zero aliases, aligned/sticky significands,
exponent gaps 23–26, ties, carries, minimum/maximum values, cancellation, underflow
and exact error paths. The wrapper flips the right sign **even for exponent-zero
aliases**: subtracting `ffffff00` from `12345600` yields `ffff7f00`. Numeric zero
does not imply canonical raw bytes. Cancellation and underflow instead clear
only the *original* prior FAC's exponent, preserving its unnegated residue.
Overflow preserves the exact native diagnostic, without inventing a post-error
FAC or operand state. Native shell success alone is not interpreted as arithmetic
success.

The host is DOSBox Staging 0.83.0, fixed 200000 cycles, requested DOS date
2026-11-02 and time 00:00:00, with raw clock/host/command/return logs retained.
Every 21-byte prefix contains protocol `SUB1`, initial RNG/FAC, ordered operand
shadows and mode. A success has a complete 42-byte frame including result,
unchanged shadows, final RNG/mode and footer. Errors retain the complete native
message and caller address (00F6 for 97/99, 00F3 for 9b).

## Validation and boundaries

The independent verifier reconstructs payloads and complete copied executables,
checks loader relocation exclusion, pinned host/version/clock controls, immutable
source/recipe/manifest inventories, source mappings, exact framing, state and
fixture equality. It reuses the independent exact-rational addition oracle only
after the source-derived register sign flip. Go compares both APIs with all
portable native traces. Twelve acceptance/corruption tests check independent
payloads, direction, zero alias sign, FAC state constraints, every trace byte,
error framing, fabricated success, caller coverage and source/fixture mutation.

Inline 9d address/frame handling, DOUBLE subtraction, multiplication/division,
normal complete maintenance caller integration, exhaustive raw operand space and
live BBS acceptance are not admitted. Gameplay, initializer source fingerprints,
save 35 and sysop procedures remain unchanged. PR #128 separately owns inline
addition and must not be repeated by this work.

Local validation passed: the new complete native verifier and twelve corruption/
acceptance tests; race-enabled qbmbf/qbrng/qbinit tests and Go vet; both parent
addition verifiers and their 24 tests; twenty native initializer goldens; and all
4,682 archived file hashes. These local results do not claim PR CI or live BBS
acceptance.

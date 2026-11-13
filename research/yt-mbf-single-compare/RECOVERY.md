# Direct raw SINGLE comparisons and branch flags

The retained Xannor `rea/target-paths.json` packet already contains all 192 bytes
at analysis 0x1a802, including the direct wrappers and complete comparison core.
Its original BRUN30 identity and loaded bytes are independently checked; no new
source query was needed. Existing ABI evidence is reused. The original-byte
maintenance inventory matches 203 direct sites: /9f (131), /a1 (69), /a3 (3).
The separately recorded inline /a5 inventory is excluded from this contract.

`CompareSingle` implements these three ordered operand bindings. It predicts
CF/PF/ZF/SF/OF (mask 08c5) and all sixteen short Jcc conditions (70..7f).
Exponent-zero aliases, sign exits, negative operand reversal, descending word
comparison and subtraction overflow/parity are retained. Signed CPU jumps are
not numeric MBF ordering: positive one versus negative one takes both JA and JL.
AF is undefined on logical exits and is deliberately not predicted.

## Native controls and provenance

All 216 first attempts returned normally: 72 per entry, comprising 64 input
pairs and eight repeated pairs with another RNG and initial arithmetic flags.
Cases include zero residues, both signs, exponent extremes, equality, fraction
bits, high/low word boundaries and signed subtraction overflow. The SCF1 protocol
retains complete pre/post FLAGS, all sixteen actual Jcc outcomes, readonly full
FAC and operand memory, registers, RNG and mode. The harness executes each Jcc
immediately after PUSHF saves the result; only MOV/Jcc instructions intervene.
Branches are not synthesized by reloading saved flags. ES=DS and DF clear are
explicit admissions; DF returns clear. /a1 sets SI to FAC and /a3 sets DI to FAC
before the shared register-preserving wrapper.

`native/recipe.json` and its frozen acquisition source precede execution.
`native/pins.json` fixes every raw observation and source. The independent
verifier reconstructs each copied executable and all diagnostic bytes, excludes
loader relocations, checks shell return/date/time/host controls, then checks the
portable fixture against every raw trace. Full raw FLAGS remain immutable even
where no semantic prediction is made. Corruption tests distinguish semantic
flag admission from immutable observation integrity.

Run:

```
python3 scripts/verify_single_compare.py
python3 scripts/test_verify_single_compare.py
go test ./internal/qbmbf
```

The exported primitive is isolated research support. Inline /a5, DOUBLE
comparisons, arbitrary segment/direction contexts, general error/unwind policy,
production maintenance integration and Windows/live-BBS acceptance remain
separate. No gameplay, save format (35), initializer profile or sysop procedure
changes in this milestone.

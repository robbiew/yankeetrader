# Raw sign/zero-test entries /a7–/aa

The source audit reused the complete seventy-byte observation at analysis
1ac1e in the plague/civil-war packet, plus the shared dispatch context. Only
four missing prefix bytes at 1ac1a were queried: `50 8b 44 02` (PUSH AX;
MOV AX,[SI+2]). The fixed new packet and earlier observation are independently
matched to original BRUN30 bytes. The original executable is unchanged.

| Entry | Loaded code | Input |
| --- | --- | --- |
| /a7 | ac1a | SINGLE memory through SI, high word at SI+2 |
| /a8 | ac26 | DOUBLE memory through SI, high word at SI+6 |
| /a9 | ac2c | FAC high word at 001c |
| /aa | ac2c | Same FAC high-word entry as /a9 |

The source ORs the exponent byte with itself, skips rotation for exponent zero,
and otherwise rotates the sign/fraction byte left through carry once. AX is
restored before RETF. The defined CF/PF/ZF/SF/OF equal the qualified raw
comparison-against-zero flags, so `SignZeroSingle` and `SignZeroDouble` compose
those existing primitives. These APIs return CPU flags, not integer SGN values.
CF carries sign only for nonzero operands; SF derives from the exponent's
logical flags and must not be interpreted as numeric sign. Exponent-zero
residues are zero aliases. AF is undefined and outside the semantic contract.

The original-byte maintenance inventory matches 102 direct slots: /a7 49,
/a8 19, /a9 32 and /aa 2. It is a bounded static inventory, not observed execution
or exhaustive indirect coverage. Adjacent /ab and later boolean helpers are
not admitted by this milestone.

## Native controls and provenance

All 248 first attempts returned normally: 62 per entry. Each entry covers six
exponents (00, 01, 7f, 80, 81, ff) and nine sign/fraction patterns, plus eight
repeated controls under another initial flag/RNG seed. Independent FAC/memory
sentinels distinguish the actual operand bindings. SINGLE memory has an unused
four-byte tail; DOUBLE memory has nonzero low words; FAC tests exercise the
shared top word with independent memory. Zero aliases, both signs, exponent
parity/SF and all four top sign/fraction rotate combinations are retained.

The separate 113-byte SZF1 protocol captures raw pre/post FLAGS and all sixteen
actual short-Jcc outcomes, full FAC, both memory blocks, nine registers, RNG and
mode. Only MOV/Jcc instructions intervene after immediate PUSHF result capture;
no flags are reloaded to synthesize branches. ES=DS and DF clear are explicit
admissions; DF returns clear. Inputs, FAC, captured registers, RNG and mode are
unchanged. Raw FLAGS remain immutable even where no semantic bit is predicted.

The acquisition source and recipe were frozen before launch. Fixed manifests
retain every first outcome and acquisition source. The independent verifier
reconstructs complete copied diagnostics/executables, rejects loader relocation
overlap, checks actual host/date/time/commands and shell return, then binds the
portable fixture to every raw trace. Tests reject changed flags/branches,
registers/inputs, seed state, source provenance and missing fixture rows. AF
corruption demonstrates the distinction between an unpredicted bit and an
immutable original observation.

```
python3 scripts/verify_sign_zero.py
python3 scripts/test_verify_sign_zero.py
go test ./internal/qbmbf
```

Production maintenance integration, arbitrary direction/segment/frame contexts,
general boolean/error/unwind helpers, DOS save interoperability and native
Windows/live-BBS acceptance remain separate. Gameplay, save format 35, source
fingerprints and sysop procedures are unchanged. The next integration candidate
is a bounded pure Go before-only clean-port maintenance replay using the existing
captures, rather than another broad numeric or gameplay migration.

# Direct raw DOUBLE comparisons and branch flags

The existing Xannor `rea/target-paths.json` packet contains all 192 original
bytes at analysis 0x1a802, including the DOUBLE wrappers and shared comparison
core. The SINGLE comparison verifier authenticates its original BRUN30 identity,
complete bytes, shared ABI and core; this supplement additionally checks the
DOUBLE dispatch and wrappers. No new source query was needed. The bounded
maintenance inventory matches 30 original-byte direct sites: /a0 (15), /a2 (15),
/a4 (0). Seven inline /a6 sites are recorded separately and excluded.

`CompareDouble` qualifies the three ordered bindings: memory/memory, FAC/memory
and memory/FAC. Unlike a conversion to SINGLE, it retains all 56 significand
bits. After the shared zero/sign exits, native code compares four words from
high to low, reversing operands for same-sign negatives. The flags come from
the first unequal word, or the final equal low word. This preserves subtraction
overflow and low-byte parity independently of numeric order.

The API reuses `ComparisonFlags`: CF/PF/ZF/SF/OF at mask 08c5 and all sixteen
short Jcc conditions, opcodes 70..7f. Signed CPU jumps are not numeric MBF
ordering; positive one versus negative one takes both JA and JL. Exponent-zero
residues compare as zero aliases. AF is undefined on logical exits and remains
outside the semantic contract.

## Native controls and exact provenance

The corpus retains 486 first attempts: 162 per direct entry, comprising 154
ordered pairs and eight repeated pairs under another RNG/initial flag seed.
Controls cover equality, both signs, zero aliases, exponent extremes, bit
positions through 54, subtraction/parity boundaries in every lower word and
higher-word precedence over opposing lower-word differences. The independent
verifier and portable Go fixture admit only normal complete returns.

DCF1 is a separate 113-byte protocol. It retains complete pre/post FLAGS,
sixteen actual native Jcc outcomes, both full operands, the full eight-byte FAC,
nine registers, RNG and mode. Each branch executes after the immediate PUSHF
result capture with only MOV/Jcc instructions intervening; the harness does not
synthesize flags or branches. ES=DS and DF clear are explicit entry admissions;
DF returns clear. /a2 changes SI to FAC 0016 and /a4 changes DI to FAC 0016
before the common register-preserving wrapper. Inputs, FAC, RNG and mode remain
unchanged.

`native/recipe.json` and its frozen acquisition source precede execution.
`native/pins.json` fixes every original observation and source. The independent
verifier reconstructs complete copied images and diagnostics, checks relocation
exclusion, actual commands, shell return, fixed host, date/time and every raw
trace. Complete FLAGS stay immutable even where no semantic prediction is made.
Corruption tests separately exercise supported flags/branches, source protocol,
readonly state, initial flags, provenance and portable fixture completeness.

Run:

```
python3 scripts/verify_double_compare.py
python3 scripts/test_verify_double_compare.py
go test ./internal/qbmbf
```

These are isolated research APIs. Inline /a6 and /a5 comparisons, arbitrary
segment/direction contexts, production maintenance integration, general unwind
policy and native Windows/live-BBS acceptance remain separate. Gameplay, save
format 35, initializer fingerprints and sysop procedures are unchanged.

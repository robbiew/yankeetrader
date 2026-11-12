# Direct raw-DOUBLE subtraction

## Scope and retained source

This qualifies INT3F/98 memory minus memory, /9a FAC minus memory and /9c memory
minus FAC through `SubtractDouble` and `SubtractDoubleWithFAC`. The wrapper
flips bit 7 of the right operand's seventh byte in a register, including raw
exponent-zero aliases, then enters the already-qualified addition kernel.
Inputs remain unchanged. Cancellation/underflow preserves the original initial
FAC's seven residue bytes, not a negated operand's residue. Overflow returns a
rejected API result without claiming native post-error FAC state.

The README, plan, retained source, APIs and open PRs were audited first. PR #137
is merged as `8e711469`; PR #138 merged bounded inline DOUBLE addition as
`fea64d23` and must not be repeated. This branch now integrates that merged
work while preserving its original controls. There was no existing direct DOUBLE subtraction corpus
or API in that bounded audit. No new source query was necessary.

The fixed `yt-plague-civil-war/rea/target-paths.json` packet already includes
`runtime-double-subtract`, Evidence
`ev_e12ba0779b3cef76b32a1b3126aa1f4f5c4489c30c32f52764d749175a37834c`:
90 bytes at analysis 1ad81. The dispatch targets are /98 ad8c, /9a ad81 and
/9c ad89. Original file af81..af96 retains the direct mappings, ABI call,
`MOV CX,[DI+6]; XOR CL,80; JMP` into the shared kernel. The register sign change
also reaches the zero-copy exit, which copies lower memory words unchanged and
stores the modified high word. It never negates operand memory.

The [addition source verifier](../../scripts/verify_add_double.py) authenticates
that packet, the previously recovered kernel tail and shared ABI/error packets.
The new verifier reuses that authentication and separately constrains subtraction
entry bytes and dispatch. Existing observations and manifests are unchanged.
Static byte agreement is not observed execution of normal maintenance paths.

The new [original-byte inventory](maintenance-calls.json) matches all **21 direct
sites** in the bounded annotated maintenance listing: twelve /98, four /9a and
five /9c. There are **no inline /9e sites** in that listing. This is not an
exhaustive indirect-call audit. Inline /9e frames remain separate despite the
retained packet containing their entry.

## New native controls

All **148 first-attempt disposable processes** completed, with **139 numeric
returns and nine exact Overflow diagnostics**. The matrix contains 92 FAC-minus-
memory /9a controls, 36 /98 controls (including sixteen independent initial-FAC
cases) and twenty /9c controls. Raw operands are declared in the closed recipe;
subtraction uses the original right input, not a reclassified addition trace.

The matrix covers both directions of zero aliases, operand-order counter-controls,
signs, cancellation/underflow, precision beyond float64, even/odd half ties and
adjacent sticky values, raw word/byte alignment, minimum/maximum results and
carry/rounding Overflow. Signed and reversed exponent-gap boundaries constrain
the native 56/57 shortcut. Four independent FAC encodings and two RNG seeds
separate input binding from retained residue.

Frozen acquisition source and recipe precede every first launch. Both original
initializer startup calls remain. Only the copied initializer diagnostic body,
operands/FAC and runtime RNG data seed change; runtime code is untouched.
Independent preflight reconstructed all payloads and excluded loader relocation
overlaps before launch. All first outcomes were kept without replacement/retry.

The distinct `DSD1` prefix records initial FAC, both ordered memory blocks, RNG
and mode. Each successful 66-byte frame retains the full eight-byte output,
unchanged input memory, RNG/mode and footer. Each Overflow retains the complete
native diagnostic at 01A3:011A for /98-/9a or 01A3:0117 for /9c. The verifier
derives these continuations from its independent five-byte call-slot model.
This is the original-startup diagnostic context, not general error/unwind,
ON ERROR/RESUME, hook or arbitrary module/frame qualification.

Immutable manifests pin source, recipe and every observed byte. The verifier
reconstructs complete copied executable hashes, checks exact inventories,
relocation bounds, the pinned DOSBox Staging 0.83.0/fixed 200000-cycle launch,
raw 2026-11-02/time-zero controls and complete native shell return provenance.
ERRORLEVEL alone never classifies arithmetic success. The independent Python
oracle computes an exact rational difference, then applies source-qualified
zero-alias, gap and residue rules. It does not use the Go result or captured
output as an expected answer.

Portable fixtures retain full traces and source hashes; Go tests compare all
148 outcomes without an emulator. Seventeen verifier/corruption tests reject
changed bytes, addition/opcode substitution, memory negation, operand rebinding,
lost precision/residue, wrong rounding/gaps, altered source/fixture and fabricated
post-error state. The Go adapter reuses the bounded exact addition kernel;
there is no float64 demotion or new arithmetic implementation. CI runs both new
checks and Git attributes preserve native control bytes unchanged.

```sh
python3 scripts/verify_subtract_double.py
python3 scripts/test_verify_subtract_double.py
go test -race ./internal/qbmbf ./internal/qbrng ./internal/qbinit
go vet ./internal/qbmbf ./internal/qbrng ./internal/qbinit
```

Gameplay, source fingerprints, save 35 and sysop behavior are unchanged. Next:
audit retained inline DOUBLE subtraction /9e address/source evidence before
adding missing bounded controls. Do not repeat addition, completed conversions,
SINGLE arithmetic or initializer acceptance. Other DOUBLE arithmetic, complete
maintenance, DOS save interoperability and native Windows/live-BBS acceptance
remain separate.

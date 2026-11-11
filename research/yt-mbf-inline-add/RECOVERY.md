# INT3F/85 inline SINGLE addition — 2026-11-09

## Evidence and result

This supplement reuses the qualified addition kernel and direct entry-state
model from [the parent](../yt-mbf-add-entries/RECOVERY.md). It qualifies the inline
address wrapper, not another arithmetic implementation. The original BRUN30
entry b36e calls resolver 1ec3, then selects FAC as the right operand and joins
shared addition. The resolver preserves AX, restores DS from ES and returns the
operand offset in SI. The five-byte opcode consumes one following selector byte.

The descriptor's first word comes through the segment stored at SS:[BP-2]. It is
**separate from** the opcode caller's CS header. Tag 7a62 selects caller CS:0012;
every other tested tag selects CS:0010. The address is the selected base plus
8 times (selector & 7f), wrapping at 16 bits. Synthetic tag zero establishes the
fallback comparison, not validity of arbitrary modules. `SingleAddInlineOffset`
computes this offset only. Full arithmetic uses existing `AddSingleWithFAC` with
the right operand also supplying the initial FAC.

The retained Xannor packet supplies dispatch, ABI and 49 resolver bytes. New REA
packets supply the 14-byte frame helper, four-byte indirect-jump tail (one byte
overlaps the old read), and 24 bytes surrounding an original maintenance caller.
All bytes are mapped back to immutable archived executables. The fixed
`maintenance-calls.json` inventory matches 35 annotated direct call sites against
original machine bytes, selectors 80 through 89. This is a static listing audit,
not observed normal execution or an exhaustive indirect-call graph.

## Native protocols and interventions

Two frozen acquisition sources and manifests retain every first attempt:

- `native/`: 70 resolver-only controls across 14 selectors and five descriptor/base
  contexts, plus 48 full additions across eight operand pairs, two tags and three
  selectors. Resolver contexts include high-bit aliases, fallback tag and wrapping.
- `caller-native/`: 20 resolver-only controls for all ten maintenance selectors
  with the archived header values 7e00/08c3 and both descriptor branch tags.

All **138** attempts completed naturally: **90 resolver-only** and **48 full
successful additions**. These are controlled initializer-hosted probes, not full
maintenance runs. Both original startup calls execute untouched. After startup,
the diagnostic constructs an explicit BP local frame, sets ES to data DS, stores
a descriptor word at DS:5000 and its paragraph alias in SS:[BP-2], and writes the
declared caller-CS base words in memory. The original on-disk header remains
unchanged. RNG initial data is explicitly seeded; the runtime host is fixed
DOSBox Staging 0.83.0 at 200000 cycles and DOS date 2026-11-02/time zero.

Resolver-only controls replace copied runtime b371's `BF1A00` with `CB9090` to
return after unchanged address resolution. They do not dereference potentially
unsafe/wrapped offsets or execute addition. FAC remains unchanged. Full controls
retain original runtime code, use safe four-byte operand spans, and populate the
alternate-base slot with a distinct poison operand. They preserve both memory
slots, AX=BEEF, DS/ES/BP, RNG and mode. Full cases cover zero aliases,
cancellation in both directions, underflow, ties, gap skipping, sign crossing and
alignment. No full inline85 overflow/unwind, cross-segment operand read, arbitrary
frame validity, complete normal maintenance or live BBS acceptance is claimed.

## Verification

`verify_inline_add.py` authenticates fixed complete artifact inventories, frozen
prelaunch sources/recipes, reconstructed copied executables and payloads, raw
host/clock/return logs, complete 57/65-byte frames, source packet mappings and
static maintenance inventory. It independently reconstructs the address protocol
and reuses the parent arithmetic oracle only for full additions. The portable
fixture includes every raw trace and digest. Eight acceptance/corruption tests
exercise all trace bytes, framing, source/fixture substitution, independently
reconstructed payloads, caller coverage and resolver/arithmetic separation. Go
compares the offset helper against all 138 native frames and the existing
arithmetic against the 48 full cases. CI runs both verifier layers.

Gameplay, source fingerprints, save format 35 and sysop procedures are unchanged.
Subtraction, DOUBLE arithmetic and multiplication/division remain separate work;
do not repeat completed entry81, direct7f/83 or this bounded inline85 recovery.

Local validation passed: both new verifier layers; both parent addition verifiers
and their 24 tests; race-enabled qbmbf/qbrng/qbinit tests and Go vet; twenty native
initializer goldens; and all 4,682 archived file hashes. These checks are distinct
from PR CI and live BBS acceptance.

The [bounded overflow supplement](../yt-mbf-inline-overflow/RECOVERY.md) now
qualifies complete fatal diagnostics in declared bootstrap/frame-depth contexts.
It does not observe post-error FAC/registers or admit general unwind/ON ERROR.

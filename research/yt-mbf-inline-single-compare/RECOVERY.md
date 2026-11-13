# Bounded inline SINGLE comparison /a5

All source evidence already existed. The retained comparison packet contains
/a5 at a831: it calls the shared 1ec3 inline resolver, selects right FAC 001a,
then uses the qualified direct SINGLE comparison core. The resolver/frame tail,
original caller header and descriptor helper are independently authenticated by
the inline-add verifier. This supplement checks the actual /a5 dispatch and
wrapper and reuses both source validators; no new source query was needed.

Sixteen /a5 slots in the bounded maintenance listing match original bytes. Their
selectors are 80, 81 and 82. The existing immutable direct comparison inventory
records them separately; this supplement admits them as static caller evidence,
not observed execution or an exhaustive indirect inventory.

The Go model composes `SingleAddInlineOffset` with `CompareSingle` after reading
the selected four-byte operand. It preserves operand ordering: selected memory
is left, the latter four bytes of the eight-byte FAC are right. Descriptor word
7a62 selects caller CS:0012; every other word selects CS:0010. The high selector
bit is discarded, slots have stride eight and offsets wrap at sixteen bits.
No new arithmetic algorithm or gameplay call site is introduced.

## Native controls

All 296 first attempts returned normally. There are 275 full comparison runs:
64 direct-control pairs across two descriptor tags and selectors 80/82, eight
extra selector controls, eight alternate RNG/initial-flag runs with explicit
16/32-byte frame padding, one fallback tag and two last-safe four-byte spans at
fffc. The 21 separate resolver-only runs cover selector aliases, wraparound,
fallback and the original caller header 7e00/08c3 with selectors 80/81/82 under
both tag paths. Only resolver-only runs replace the post-resolver `MOV DI,001a`
with RETF; their traces make no operand-read or comparison-flag prediction.

The I5CF protocol is 101 bytes for full runs and 93 for resolver-only runs.
It captures the actual descriptor word, caller header, DS/ES/BP/descriptor frame,
selector, requested and actual initial flags, immediate result FLAGS and sixteen
actual short-Jcc outcomes. Only MOV/Jcc instructions intervene between PUSHF
capture and the branch probes. Full runs retain both selected memory and an
alternate-base poison value, the whole eight-byte FAC, nine registers, RNG and
mode. Readonly input/FAC, restored DF and the actual resolved SI/right-FAC DI
are checked. Address-only runs instead return resolved SI/DI without reading an
operand. Full spans are safe and disjoint; wraparound remains offset-only.

As for direct comparisons, only CF/PF/ZF/SF/OF (mask 08c5) are predicted. Signed
CPU jumps are not numeric MBF ordering; AF is undefined on logical exits. All
raw FLAGS remain immutable observations even where semantic flags are excluded.
ES=DS and DF clear, declared synthetic SS:BP-2 descriptor frames, safe reads and
the recorded padding are explicit admissions, not arbitrary stack/module policy.

## Provenance and validation

The acquisition source and recipe were frozen before launching each first run.
Fixed pins cover complete original observations, copied executable hashes,
commands, host/date/time controls and frozen source. The independent verifier
reconstructs every diagnostic and both copied images, rejects relocation overlap,
checks exact shell outcomes and binds the portable fixture to all raw traces.
Tests reject flags/branches, protocol relabeling, input/FAC/poison mutations,
wrong resolver metadata, altered native observations and dropped fixture cases.

```
python3 scripts/verify_inline_single_compare.py
python3 scripts/test_verify_inline_single_compare.py
go test ./internal/qbmbf
```

Inline DOUBLE /a6, arbitrary memory/segment/frame contexts, production replay
integration, general unwind policy and native Windows/live-BBS acceptance remain
separate. Gameplay, save format 35, source fingerprints and sysop procedures are
unchanged.

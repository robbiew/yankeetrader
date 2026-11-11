# Inline SINGLE subtraction — 2026-11-09

## Scope and reused evidence

This bounded supplement qualifies successful INT3F/9d inline subtraction and its
address resolver in explicitly constructed frames. It depends on the separate
[inline-addition resolver](../yt-mbf-inline-add/RECOVERY.md) (#128) and
[direct subtraction model](../yt-mbf-sub/RECOVERY.md) (#129). Both were open when
this branch started. Their commits are integrated here; neither parent branch
is changed. Do not merge this branch into a parent feature branch. After both
parents merge, target main and review the remaining inline9d change.

No new disassembly observations are needed. The retained dispatch table maps 9d
to b359. Existing complete wrapper bytes show a call to the same resolver 1ec3,
followed by DI=FAC and the original subtraction wrapper (right sign flipped in a
register, then shared addition). The retained resolver, frame helper, indirect
jump tail, arithmetic and ABI bytes are reauthenticated against archived images.
Original packets, capture bytes, sources and fixed manifests remain unchanged.

`SingleAddInlineOffset` is the shared address computation despite its historical
addition-specific name. This slice expands its documented scope to 9d, then uses
`SubtractSingleWithFAC(left,FAC,FAC)` for complete arithmetic. No new arithmetic
implementation, address algorithm or production call site is introduced.

## New controls and interventions

All **89 first attempts** completed naturally: **23 resolver-only** frames and
**66 full successful subtractions**, with complete raw host/clock/return logs.
The primary frozen acquisition source retains 83 outcomes; a separately frozen
six-case supplement covers the other archived caller selectors without rewriting
or retrying any original observations. The 138 inline-addition and 266 direct
subtraction controls are reused, not recaptured.

The new primary address controls cover selector high-bit aliases, highest slot,
16-bit wrapping, both descriptor branches and the non-bz fallback. Eight controls
across both new corpora use the actual archived maintenance header bases 7e00/08c3
with selectors 80–83. A fixed static inventory independently matches all five
annotated direct inline9d calls against original six-byte machine sequences.
That inventory is not observed normal execution or exhaustive indirect coverage.
The descriptor tag is a separate input from the caller-CS base words.

Full controls cover eleven ordered operand pairs, both descriptor tags and
selectors 80/83/ff: zero aliases, left/right zero, positive/negative cancellation,
both underflow directions, even tie, exponent-gap cutoff, sign crossing and raw
alignment. They check original left and alternate-base poison memory unchanged,
FAC subtraction rather than addition, and register/RNG/mode preservation.

The copied initializer runs both original startup calls intact. Only its first
body call is redirected to the diagnostic. After startup the diagnostic builds
an explicit BP local frame, sets ES=DS, stores the descriptor tag at DS:5000 and
its paragraph alias at SS:[BP-2], and writes declared caller-CS base words in
memory. The original on-disk header is unchanged. Runtime RNG data is seeded
explicitly; full controls leave runtime code unchanged and use safe four-byte
operand spans.

Resolver-only controls replace copied runtime file b55c's `BF1A00` with `CB9090`
to return immediately after the unchanged 9d resolver. They never dereference
potentially unsafe/wrapped addresses or execute subtraction, and FAC is unchanged.
This is a different return location from 85; its original bytes and exact copied
image reconstruction are checked separately.

The host remains DOSBox Staging 0.83.0 at fixed 200000 cycles with requested DOS
date 2026-11-02/time zero. The new protocol marker is `IS9D`, preventing accidental
substitution of `IA85` evidence. Otherwise it retains the parent's complete
57/65-byte state protocol: descriptor/base/frame context, selector, SI/DI/AX/DS/ES/
BP, raw FAC/RNG/mode and optional selected/alternate memory. AX=BEEF is preserved;
SI is the resolved operand, DI is that offset in address-only controls and 001a
in full subtraction.

## Verification and remaining limits

The shared verifier now has a closed add/subtract operation choice, choosing
operation-specific opcode, marker, return-stub location and arithmetic oracle.
Default addition behavior and its immutable fixtures remain unchanged. The new
verifier authenticates both complete pinned corpora, frozen prelaunch sources,
independently reconstructed payloads/images, original mappings, raw clock/host
controls and exact portable fixture equality. Eleven acceptance/corruption tests
cover all trace bytes, independent source payloads, framing, source/fixture
mutation, selector inventory, forbidden operations and addition/subtraction
substitution even with a changed marker. Go compares all 89 native offsets against
the existing helper and all 66 full results against the existing subtraction API.

Native inline9d overflow/unwind, arbitrary frame validity, cross-segment reads,
complete normal maintenance, DOUBLE subtraction and live BBS acceptance remain
unqualified. Gameplay, source fingerprints, save 35 and sysop procedures are
unchanged. Do not repeat completed direct subtraction, resolver arithmetic or
successful inline85/9d controls as missing work. Fatal inline error/unwind is a
separate bounded research question if pursued next.

Local validation passed: both complete inline verifiers and their 19 tests; the
266-control subtraction verifier and twelve tests; both direct addition verifiers
and their 24 tests; race-enabled qbmbf/qbrng/qbinit tests and Go vet; twenty native
initializer goldens; and all 4,682 archived file hashes. These local results are
separate from PR CI and live BBS acceptance.

The [bounded overflow supplement](../yt-mbf-inline-overflow/RECOVERY.md) now
qualifies complete fatal diagnostics in declared bootstrap/frame-depth contexts.
It does not observe post-error FAC/registers or admit general unwind/ON ERROR.

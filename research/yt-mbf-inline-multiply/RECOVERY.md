# Bounded inline SINGLE multiplication — 2026-11-11

## Result and reuse

This supplement qualifies INT3F/95 in declared synthetic frames using the
existing shared resolver and `MultiplySingleWithFAC(left,FAC,FAC)`. It adds no
arithmetic algorithm or production caller. PR #132 was checked at its current
head, merged after green CI/clear reviews, and ancestry-verified before this
branch started from merged main.

All **81 first attempts** completed naturally, in separate protocols:

- **25 resolver-only controls**, with no multiplication or computed-operand read.
- **42 complete numeric returns** and **14 exact Overflow diagnostics** from
  **56 full executions**, including baseline and padded frames.

Previously qualified direct products, shared address semantics and error source
observations are reused unchanged. No new disassembly query is needed. The
retained dispatch/wrapper observations map 95 to b4a5: call 1ec3 resolves the operand,
then DI selects FAC at b4a8 and execution joins the original multiplication ABI.
The retained resolver, descriptor-frame helper, return tail, complete product
kernel, rounding/zero exits and error dispatch are reauthenticated against the
immutable runtime. Source-level dispatch and native output remain distinct
forms of evidence.

`SingleAddInlineOffset` retains its historical name; its documented shared
resolver scope now includes 85/9d/95. Its implementation is unchanged. The
existing multiplication API models arithmetic after address resolution. Neither
helper walks or validates arbitrary machine stacks or module descriptors.

## Source callers and addressing protocol

The fixed inventory from [direct multiplication](../yt-mbf-multiply/RECOVERY.md)
already contains all twelve annotated inline 95 call sites, matched to original
maintenance bytes. Those rows are reused directly, rather than copied into a
new competing inventory. Their selector set is 80,81,82,84,85. It is a static
listing-matched inventory, not observed maintenance execution or exhaustive
indirect-call coverage.

`address-native/` uses a separately frozen source/recipe with marker `IM95` and
complete 57-byte frames. Eight controls cover both descriptor branches and
high-bit selector aliases; six cover 16-bit wrapping; one covers the non-bz
fallback. Ten inject the archived maintenance base values 7e00/08c3 into the
initializer-hosted caller header and cover all five source selectors with both
descriptor tags. The descriptor's first word is distinct from caller-CS header
base words. No normal maintenance run is claimed.

These controls replace copied runtime file b6a8's `BF1A00` with `CB9090`, returning
after unchanged address resolution and before FAC selection/operand arithmetic.
That is the inline 95-specific return point, not the 85/9d stub location. The
computed offset, AX/DS/ES/BP, unchanged FAC, RNG and default mode are checked.
Wrapped/potentially unsafe offsets are never dereferenced. They do not count as
arithmetic successes.

## Full product and bounded error protocol

`native/` retains 56 full executions from a frozen source/recipe. Thirteen ordered
input pairs run with both descriptor tags and selectors 80/85: raw zero aliases,
left/right zero, signed products, pre-round underflow, raw alignment, an even
tie, an above-half sticky case, positive/negative range overflow and rounding
carry overflow. Four more controls use padding 16/bm and 32/bz with selector 84,
each pairing positive overflow and finite underflow. These are declared
combinations, not an exhaustive or orthogonal frame matrix.

The original initializer runs both startup calls intact before redirecting its
first body call to the diagnostic. After startup, the harness constructs a BP
local, sets ES=DS, supplies a descriptor at DS:5000 through SS:[BP-2], and writes
safe caller-CS bases 6000/6800 in memory. The original on-disk header is unchanged.
Full runtime code is untouched; only declared RNG data is seeded. Both operand
spans are safe, and alternate-base memory holds a distinct finite poison operand.
No resolver-only return stub is present in these full cases.

The existing `IOF1` protocol records 46 pre-entry bytes, including actual opcode 95,
operands, selector/base/descriptor context, synthetic BP, original BP and runtime
error route/hook/saved BP/SP/module stack. The admitted bootstrap route is 0a68,
with no ON ERROR hook and the prior saved-SP snapshot 0. Saved BP equals original
BP; module stack is original BP minus 6; synthetic BP is original BP minus 8 minus
padding. These are observed bootstrap admission constraints, not arbitrary-frame
rules. The current ABI invocation changes saved stack after this snapshot.

Finite returns have complete 79-byte frames: resolved SI, DI=FAC, AX=BEEF,
DS/ES/BP, raw product, selected/poison memory, RNG/mode and footer. Zero/underflow
retains the **right FAC's** original residue. Calling `MultiplySingle(left,FAC)`
naively would instead preserve left's residue, which fails these raw zero cases.

A fatal trace instead has the exact 85-byte native Overflow diagnostic after the
prefix (131 total), at 01A3:0194 for baseline or 0197 for padded call sites. The
address is derived from the independent copied-code layout plus the consumed
sixth selector byte. Fatal output is null in the fixture: no post-error FAC,
register, memory or RNG state is invented. A successful native shell return or
host exit status never classifies arithmetic success.

All processes use fresh disposable mounts, DOSBox Staging 0.83.0 at 200000 cycles,
and requested DOS date 2026-11-02/time zero. Exact command/host/clock/return logs,
whole copied-image hashes and every first result are retained. No observed
artifact or executed acquisition source was retried, rewritten or rehashed to
hide a mismatch.

## Verification and remaining work

Shared validators now have closed multiply/op95 cases, preserving old add/subtract
protocols and pinned corpora. The new verifier authenticates both full artifact
inventories, frozen actual sources/recipes, independent payload and copied-image
reconstruction, relocation exclusion, original source mappings, host/clock and
return logs, case profiles and exact portable equality. Address and execution
cases remain separate arrays. Arithmetic uses the existing independent product
oracle, with FAC as right operand and original destination state.

Fourteen acceptance/corruption tests cover independent payloads, every native
trace byte, right-FAC residue, addition/operator substitution, resolver-only
classification, source caller coverage and dispatch, consumed return IP, padding,
fake success, immutable source/fixture profiles and closed operation selection.
Go compares all 25 native offsets with the existing helper and all 56 full
outcomes with the existing multiplication API, without attributing arithmetic
to address-only frames or post-state to fatal diagnostics.

General unwind, ON ERROR/RESUME, arbitrary frame validity, cross-segment reads,
DOUBLE arithmetic, complete maintenance and live BBS acceptance remain
unqualified. Gameplay, recipe fingerprints, save 35 and sysop procedures are
unchanged. Next independent arithmetic work is direct SINGLE division; inspect
its retained source/normal callers before acquiring missing controls. Do not
repeat qualified multiplication, addition/subtraction, resolver or bounded fatal
controls as missing work.

Local validation passed: both complete new profiles and fourteen verifier tests;
the existing direct multiplication and inline/direct addition/subtraction/error
suites; race-enabled qbmbf/qbrng/qbinit tests and Go vet; twenty native initializer
goldens; and all 4,682 archive hashes. PR CI and live BBS acceptance remain separate.

# Mode-selector startup and replay admission

The explicit mode-4 numeric recovery is complete and merged. This separate audit
asks whether normal Yankee Trader code selects that branch and whether an
existing replay should use it. The result is bounded: **all seven original-startup
observations show selector zero; no normal mode-4 caller is admitted**. Indirect
writes or selection later in execution remain unestablished, not disproved.

No numeric implementation, gameplay, save 35, source-generation fingerprint,
existing replay or sysop procedure changes. The mode-4 APIs remain isolated.

## Original startup observations

`native/` retains one first-attempt snapshot for every shipped compiled program:

| Program | Observed DS byte `001f` after startup |
| --- | --- |
| LOCAL.EXE | 0 |
| PORTNAME.EXE | 0 |
| RMT-INIT.EXE | 0 |
| YT-INIT.EXE | 0 |
| YT.EXE | 0 |
| YTCONFIG.EXE | 0 |
| YTMAINT.EXE | 0 |

The frozen acquisition and prelaunch recipe bind all seven original binary
identities and the unchanged original BRUN30. A disposable copy redirects its
first user-body instruction, immediately after the two original startup calls,
to a snapshot-and-exit diagnostic. Both startup calls and their relocation
entries remain untouched; the verifier also rejects any relocation overlapping
the diagnostic or hook. The first 64 DS bytes are recorded with `MSEL`/`END!`
framing; DS `001f` is byte 35 in each complete 72-byte trace.

The diagnostic never writes the selector, calls a numeric conversion, forces
RNG state or executes the normal gameplay/maintenance body. No supporting live
world files are mounted. Runtime instructions and runtime data on disk are
unchanged. This observes actual original initialization followed by an explicit
snapshot intervention, not a complete normal session or later call-site trace.

All seven first attempts returned naturally, with complete framing, shell return
markers and zero host exit; no timeout, missing artifact, discard or retry occurred.
A fixed manifest authenticates raw DOS date/time, actual host argv/version/fixed
CPU, stdout/stderr, traces, return markers, source and recipe. The independent
verifier reconstructs each entire copied program and verifies the runtime hash
is original. Snapshot addresses/pointers are retained exactly, not normalized.

## Selector reference inventory and its limits

The original BRUN30 shared-kernel observations already authenticate four direct
`cmp byte [001f],4` sites. A new REA/Ghidra byte observation retains the fifth
context at linear `1d6e3` (file `d8e3`, 30 bytes). That helper validates BX 0–3,
selects a byte from table `0069`, and increments the returned integer unless
selector 4 is active. It is not another numeric conversion entry; this audit
does not assign it an unverified BASIC function name.

The five comparison file offsets are `ab07`, `ab3b`, `ab66`, `aba3` and `d8f5`.
All retained provider packets and their original runtime identity/mapping are
checked. Existing conversion/kernel/helper observations are reused unchanged.

`byte-inventory.json` is explicitly an **ordinary byte-signature inventory**, not
REA Evidence, a decoded instruction listing, or an exhaustive reference graph.
Its generator scans the entire post-header file payload for each MZ image,
including data and overlays, for the runtime and all seven compiled programs:
74 literal `1f00` address-word candidates and five complete comparison patterns.
Some literal matches are relative call displacements, immediate values or data;
they are not automatically classified as memory references or executed callers.

The inventory enumerates 319 absolute byte/word destination signatures covering
selected 8086 MOV/XCHG/arithmetic/shift/INC/DEC/NOT/NEG/POP forms. Word destinations
at `001e` are included because their high byte overlaps selector `001f`. No
matching signature occurs in the eight original image payloads. This does **not**
exclude indirect stores, string copies, computed addresses, other instruction
forms or later selection. Corruption tests demonstrate these coverage limits.

The retained REA `xrefs` query at `1fe1f` returns an empty list despite the five
positive comparison-byte contexts. That provider result is preserved, not used
as proof that no references or setter exist. The audit requires the known positive
reads independently, so an empty reference list cannot silently erase them.

## Existing replay admission decisions

The old initializer source contracts already authenticate the sector-write
INT3F/75 at code `16ab` / file `18ab`. Its current replay admits sectors 1–3000;
these integral numeric values agree in both mode-0 nearest and mode-4 floor
conversion. The existing model also retains upper FAC residue from the preceding
record-position expression. A new regression checks all 3,000 sector IDs and
the zero-warp residual records; the twenty complete initializer goldens remain
the stronger retained full-world validation. No mode-4 caller at this instruction
is established by the new startup-only snapshots.

Maintenance stock pickup is a different operation. The previously retained
native contracts bind stock decode and **INT3D/03 returning MBF** at code `4cdb`,
then its save/clear/transfer sequence. The later INT3F/77 at `4cf2` follows the
name-related descriptor `1894`; it is not the stock-floor call. These existing
original-source contracts are reauthenticated, not recaptured or rewritten.

The bounded stock replay admits a measured SINGLE value of 189529.5 and transfers
189529. Replacing it with a signed16 converter would overflow, even though both
operations floor some fractions. A regression exercises the actual existing
stock helper and the independently qualified signed16 reference to preserve that
domain distinction. There is no source/evidence basis to switch this replay to
the mode-4 API or to relax its historical admission guards.

## Validation and next evidence boundary

- `python3 scripts/verify_mode_selector_startup.py`: seven native startup outcomes,
  full frozen-source/image/launch/clock/return provenance, ordinary byte inventory,
  existing and new provider packets, and original replay-source distinctions.
- `python3 scripts/test_verify_mode_selector_startup.py`: twelve tests covering
  independent payload reconstruction, relocation-overlap rejection,
  selector/frame/source/capture mutations,
  positive direct-store controls including overlapping words, non-store and
  indirect-store scope, empty-xref limitations, all sector IDs and large stock.
- Existing numeric/native audits, twenty initializer goldens and archive hash
  checks retain their independent coverage. CI runs the new audit and tests.

Do not relist the seven-program startup observation or direct-signature inventory
as missing work. Normal mode-4 **later or indirect** selection still needs its
own evidence before caller integration; this is not a proof of global absence.
Other MBF arithmetic remains a separate source-selected milestone.

# Native plasma launch, routing and aftermath

This is static shipped-artifact evidence, interpreted with the historical
QuickBASIC-aware listings. It is not recovered BASIC source or a DOS execution
trace. Runtime controls and their exact saved outcomes are documented separately
in [RECOVERY.md](RECOVERY.md). Modern safety choices belong in
[CONTRACT.md](CONTRACT.md).

The original `archive/dos-original/YT.EXE` SHA-256 is
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
[rea/yt.json](rea/yt.json) retains 13 complete byte reads and one complete
`inspect_native_load_image` observation from REA/Ghidra 12.1.4. The profile digest
is `92fec87c3e8c374652fd603898f727129f4c0cecccf8cee1c17c98a90aced029`.
[rea/ledger.json](rea/ledger.json) binds every read to its exact original-file
range, source and relocated byte digests, provider address and Evidence ID.
The native session was closed after exporting the evidence.

An independent reconstruction used the 3584-byte MZ header, 170737-byte module,
870 relocation words and load segment `0x1000`. It matched every read byte for
byte. There is no appended overlay. Addresses below use the historical segment
aliases: sub `1f42:xxxx` maps to linear `0x1f420+xxxx`; main `1000:xxxx` maps to
`0x10000+xxxx`; sub2 `2e79:xxxx` maps to `0x2e790+xxxx`. Original-file mapping
subtracts the load base and adds the header. Relocation words must be applied
before comparing loaded calls to original bytes. The original executable was
not modified or executed by this native inspection.

## Evidence ledger

| Read | Linear address | Bytes | Evidence ID |
|---|---|---:|---|
| Main plasma admission and debit/call | `0x12079` |642| `ev_daf3c8f456f1c9292f0674c709dfc5af1b52abf9f2140414bde084c7e6335e2f` |
| Plasma decision/impact body a9bb..bcb9 | `0x29ddb` |4863| `ev_b076de5f8463d0c44628c8129d3fe9a8730e2d25a74ebf123bd1005e7d601cd6` |
| Course helper and adjacent bytes | `0x20436` |1536| `ev_80149c188225cd4e9471c28991078236f67dc645fb3a59e360206bc065dc480c` |
| Launch, loss, fighter and mine constants/text | `0x388f0` |448| `ev_3594ca84bd01a2f1ab2a349ee8b5334c2a72689c141816893116d0aef23ca27e` |
| Post-call dispatch and death flag | `0x122fe` |112| `ev_1255723b4ae5a8d7199c9a258f6fa4588dafc26991caaf221caa87b6c4f2844a` |
| Basic zero/one/two and adjacent constants | `0x365f0` |272| `ev_00bda9852a50259616b70bc87f24ae05ab224e64359cacc953e0f3bd9322194e` |
| Double one at DS a936 | `0x36be6` |8| `ev_21e087df273ebc2bc57b79e1079f9c1ff945507037590989a27196e4c3fb1460` |
| Shield and planetary constants/text | `0x38ae2` |176| `ev_695c49a2cf6b88f5edae3a5aa0005fe0bac88cf0aa6c02d7e9ede4f6a29939d9` |
| Positive-turn gate | `0x1a89b` |55| `ev_6201ae7cb011f90ebd07bea320c33fb61fa5621489a439e0de20f187605634ab` |
| Common turn/cloak debit prefix | `0x1a6e3` |353| `ev_174815fe92217d7e0187fd94398ce1ca685d03714ac35a6965db36a4a7b6dcc9` |
| Player reload | `0x1a41c` |176| `ev_dafaedafe6663d1e5290e809a79d7ed91ea446202a50d7598592610161ca8493` |
| Nonmonotonic FIELD declaration | `0x2b106` |214| `ev_b811e4f40d7fe4d3cefbf454c5aac9669daf41493088059e0220f6b46d6e6861` |
| Planet loader/cache initialization | `0x2f227` |325| `ev_10c1aaa63c4627de13d00fb2ff575f18a5c1d57a4bc6c7716d291116e2fbfd06` |

The load-image observation is
`ev_03514cdc41e9c75482e17cee3453202b476020e2c67335ece260857148a762e9`.
The full course helper is sub1016..13ca; its read intentionally retains a suffix
outside the helper rather than implying the whole read is one function.

## Admission and launch accounting

Main2079 selects plasma mode 2 and the player's plasma inventory. Main2094..20b1
reloads the player and calls GOSUBa89b. That helper admits only positive remaining
turns; otherwise it sets the refusal flag and prints `Sorry but you have no turns
left.`. No stock produces `You dont have any!` before a target prompt.

The target is read through VAL at2170, converted to single, and compared against
1 and the declared sector count. Blank input returns to the shell; an out-of-range
sector prints `Invalid Sector number!` and restarts admission. Quantity at21d1
uses VAL, the QB INT operation and single conversion. A resulting amount below1
returns to the shell; one above the selected inventory prints `You dont have that
many!` and returns. This original permissive numeric parser is not a requirement
to accept fractional or malformed input in a modern implementation.

On accepted quantity, main224e..2257 calls the common turn/cloak helper a6e3.
Its prefix reloads the player, subtracts one turn and writes turns. The routine
also performs the ordinary turn-based cloak handling. Main2278..22a6 then writes
plasma inventory minus the selected quantity to descriptor1990 and saves the
player record, before calling the weapon procedure at22dc. There is no separate
final yes/no confirmation in this observed admission path. A later route failure
does not undo these preceding DOS writes. Modern atomic saves are a distinct
policy.

The procedure's four by-reference inputs are source sector, requested destination,
bolt quantity and a Mercenary/source-label mode. Main passes source1c44, target4e12,
quantity4e32 and its ordinary-player mode. The procedure can mutate the working
source/destination variables when it creates a course or is deflected; that is
not itself a persisted player movement.

## Course and energy

Suba9e0..aa01 computes launch energy `E0=bolts*2,500,000` as single multiplication
promoted to double; it retains `E0/50` as a single-precision fixed hop loss. The
energy pool is shared by every bolt in the launch. The per-bolt animation does
not create separate independent shots.

Subab3d..aba8 prepares a course. For different endpoints it calls1016 with flag0.
The course helper clears its tables, performs a FIFO breadth-first search through
the six stored exits in column order, and reverses predecessor links into a
next-sector route. Passing flag0 bypasses the helper's avoid-list preload at108c.
Plasma therefore uses directed connectivity without the caller's avoided-sector
exclusions. A failed search zeros the source's next link and emits the helper's
route-refusal text. Equal endpoints take a special synthetic-source branch so
that the requested current sector is still visited; the shot is not discarded as
an empty path.

The traversal atabb1..ac12 subtracts the retained fixed loss before advancing each
hop except the first departure from its current course source. It loads the next
sector and exits before processing when the link is0 or energy is less than1.
Thus an ordinary adjacent sector receives full remaining launch energy; the
second receives `E0-E0/50` before absorption. With no absorption or redirection,
one bolt has at most50 entered sectors, with50,000 energy at entry50 and0 before
entry51. This is arithmetic derived from the native loop, corroborated by the
runtime range controls, not a recovered DOS random-number sequence.

## Disruption precedes local absorption

The shot prints its sector/energy entry, then at ac65..ac86 compares that sector
to both session black-hole variables1878 and187c. A match branches before the
sector record is loaded atad17. Consequently local fighters, mines, ships and
planet are bypassed on that entry.

On a match ac89..acb5 copies the current sector into the working source, computes
`INT(RND*(header_sector_end-header_sector_base))+1`, and writes the resulting
1..N destination. It prints `The plasma bolt is deflected by a black hole in
sector ... to sector ...!` and jumps toab3d to build a fresh directed course.
The random number is a new requested destination, not an immediate teleport of
the damage pool to that sector. An unavailable new route stops the shot. The new
course's first departure uses the remaining energy without another fixed hop
loss, because its current sector equals its new source.

There is no explicit redirection counter in this routine. A same-sector draw can
re-enter the same hole via the equal-endpoint branch without spending energy.
Disconnected geometry, repeated deflections and zero random energy decrements
need explicit modern work bounds. No frequency or universal termination claim
is made from this static control flow. The pair's initialization is documented
in [the earlier disruption native report](../yt-disruption/NATIVE.md).

## Shared pool and target order

For an ordinary entry, the routine reads the sector and checks whether there are
sector fighters, mines, a port, a planet or a cached ship position there. An empty
sector takes a fast path to the next course hop. The absorption stages are:

1. Sector fighters, af02..b096.
2. Sector mines, b099..b26b.
3. Player-record ships in ascending record order2..header sector-base (normally51),
   each ship's fighters before its shields, b26e..b6f3.
4. The sector's linked planet, b6f6..bc61.

No separate port-damage absorption stage appears in this procedure, although a
port prevents the empty-sector shortcut. This observation is bounded to this
procedure; it does not declare every indirect ownership effect impossible.

The sector-fighter owner is used for names and attribution, including `YOU`,
without a friendly-fire exemption. A ship's admission predicate compares its
cached position to the shot's sector and checks positive energy. The observed
ship loop has no team, governor, self or cloak-exclusion test. Separate DOS
self/friendly/cloaked controls establish how the cache behaves in those cases;
the position-cache producer is outside this native read set.

Fighter increments are `floor(E/5000)+1`; shield increments are
`floor(E/10000)+1`; mine increments are `floor(E*0.000001)+1`. Damage is capped to
the available defense, and each iteration subtracts a single-precision
`RND*25000` promoted to double from the shared energy. Energy is clamped at0 when
the subtraction goes negative. Stage transitions check the remaining energy;
there is no reset to E0 for each target. Exact DOS MBF rounding and RNG sequencing
remain separate from any bounded modern numerical model.

## Ship death, wreck mines and continuation

A ship whose resulting shields are below1 enters death handling atb4f2. The
routine clears its carried-mine/scanner fields, saves, and adds carried mines to
the shot's current sector. Other-player death calls shared helpers2993 and2ddd
for estate/salvage handling. Self death instead marks the launcher's death flag
18b4 and invalidates its cached position. Those calls are identified here; their
entire transitive effects are not independently re-recovered by these byte reads.

Atb667..b688, positive energy plus a positive wreck-mine count jumps back tob099,
so fresh wreck mines absorb energy before the procedure resumes its ship pass.
This can change which later ship or planet is reached. Following a surviving
ship, its reduced shields and fighters are saved before moving to the next
record. Post-call main232e..233b sees the self-death flag and jumps into the common
login/death path. Generation-safe modern death cleanup and concurrency guarantees
cannot be inferred from DOS's incremental record writes.

## Planetary damage and destruction

The planet path first calls the ordinary lazy planet loader, then copies the
three production rates and stocks and loads ground forces. Relevant FIELD
bindings are raw45/49/53 production,57/61/65 stocks,73 governor,77 ground,
85 planet-name length, and sector93 planet link. The declaration is not monotonic
for every later descriptor; descriptor1990 is raw113, not an arithmetic guess.

The loader prefix at sub2ac4..ae5 first loads saved ore production (raw45) into
1a48, organic production into1a4c and equipment production into1a50. It does not
load ore stock into1a48. However, that prefix is not the whole lazy updater:
its later indexed surplus adjustment can rewrite these cached rates from the
warehouses before saving the projected rates. The previous
[independently verified production recovery](../yt-missiles/PRODUCTION_DESTRUCTION.md#why-the-apparent-ore-omission-was-wrong)
covers that later write. The current read set includes the loader prefix, not
that entire later helper. Therefore **raw pre-session ore0 is not evidence of
impact-entry cache1a48=0**. For example, the fresh all-zero pre-session rate
control retains1000/2000/3000 warehouses and reports600 productivity reduced:
loading has supplied positive impact rates before the damage loop. This does not
prove a minimum200 rate or a special unconditional initial damage iteration.

After copying those projected rates, the initial path b84b..b873 falls directly
into the b876..b8bb eligibility gate. The back edge b92d also returns to that
gate. A positive-energy iteration atb8c0 requires at least one of these to be
positive: the **post-lazy-update impact-entry ore cache**1a48, the mutable organic
rate, or the mutable equipment rate. If none is positive, b8bd jumps tob930,
bypassing the damage iteration but still performing subsequent clamp/save and
all-zero retirement checks. A `hit planet` or `planet was destroyed` message
alone cannot distinguish that bypass from one or more iterations. The new
pre-session-zero controls must be interpreted through their projected rates and
receipts, not assumed to be zero-rate impact controls.

The ore branch remains asymmetric during impact: the damage loop changes its
local ore rate but does not change1a48. Positive impact-entry ore can keep it
running after all mutable rates become negative. With impact-entry ore cache0,
exhaustion of the mutable organic/equipment rates can stop it earlier. This is
not ore-only immunity. Lazy growth and surplus updates mean raw pre-session
stocks and rates must not be treated as the immediate impact baseline.

Each planetary iteration computes `E*0.000004` via double multiplication and
single conversion, subtracts that from ground and all three mutable rates, then
subtracts the usual random energy loss. Rates are clamped at0 afterward, and
stocks are capped to ten times their reduced corresponding rate. Ground undergoes
integer conversion and a below1 clamp; no surviving ground clears the governor.
The routine writes those changes before checking all three production rates for
exact zero. All zero clears the planet's name-length field and the sector's planet
link and prints `The planet was destroyed!!`. The bytes establish those two
retirement writes, not erasure of every stale planet field or a globally atomic
retirement. The remaining-energy loop can continue to later route sectors.

## Remaining boundaries

The plasma decision/impact body and complete course helper are covered, but
the plasma byte read ends at the final return opcode bcb9; the two operands
of RETF at bcba..bcbb are outside this fresh read set. This is a
manually interpreted QB/runtime program. The initialized byte observation alone
does not establish DOS timing, exact RNG draws or MBF parity, valid maximal input,
multinode behavior, every transitive shared-helper effect, protected Earth/HQ
policy, or safe finite modern execution. Runtime controls and the explicit modern
contract retain those distinctions. This research adds no playable Go plasma
command or save-schema change.

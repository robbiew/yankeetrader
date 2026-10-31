# Wanderer native evidence ledger

This track reads the shipped DOS binaries without executing or modifying them.
The interpretations below use the preserved QuickBASIC-aware listings; REA byte
observations corroborate the selected native ranges. They are static findings,
not DOS runtime observations. Parent research supplies the independent controls.
All three REA sessions were exported and closed.

## Identity and mapping

| Bundle | Original artifact SHA-256 | Header / module bytes | Relocations |
|---|---|---|---:|
| `yt-init.json` | `601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2` | 512 / 19873 | 28 |
| `ytmaint.json` | `8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6` | 512 / 42673 | 108 |
| `yt.json` | `c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037` | 3584 / 170737 | 870 |

Each bundle retains one complete verified `inspect_native_load_image` Evidence
record and every complete `read_bytes` result, including inline bytes, subject
identity, provider identity, limitations and source mappings. Ghidra 12.1.4 uses
DOS-MZ real-mode x86 with load segment `0x1000`. Its linear addresses are analyzed
coordinates, not an observed DOS runtime location. They include MZ loader fixups.

All 14 selected byte observations were independently compared with the original
file after applying every MZ relocation word with load segment `0x1000` (1006
entries across three binaries). All matched. All three load-image observations
reported `verified`, with no appended overlay. Ordinary x86 disassembly/decompiled
C is unreliable around the QuickBASIC runtime's inline operands and jump tables.

| Bundle | Analyzed address | Bytes | Purpose | Evidence ID |
|---|---|---:|---|---|
| yt-init | `0x103c9` | 415 | Record137/FIELD declarations and header reads | `ev_357062571c5c339e433d8a4f269fdbe58bd2e4610b2ae135f43a7f2fc3f70de9` |
| yt-init | `0x11efa` | 207 | Planet-slot initialization, main `1efa..1fc8` | `ev_3426fc4038407c20bbf204be39d0343302d36bd21d10acbafeb90cae6e8dccc2` |
| yt-init | `0x123c2` | 34 | Initial maintenance invocation, main `23c2..23e3` | `ev_7fc8dae983ae4c3544555e286dfb284d01825a3063ce46f5936e32632ee11b76` |
| ytmaint | `0x10096` | 426 | FIELD declarations/header loads, main `0096..023f` | `ev_9510a20ecdfcfd9ef54695510038f91bffa48098d40927fb31b16a262142709e` |
| ytmaint | `0x11cf5` | 884 | Wanderer lifecycle, main `1cf5..2068` | `ev_6a69002287c173dd1b4f16f53082301ea750c935ad3bc8c30109cb91b388783f` |
| ytmaint | `0x178f3` | 240 | Random candidate helper and adjacent nested helper | `ev_83e7420f94915b498d61fcbb597e0831fb3d83484d6aa35185ade10ee43a0060` |
| ytmaint | `0x19078` | 80 | Embedded initial DS constants `82a8..82f7` | `ev_529bd032496d9b671023c5b8c3e043eb1e7b6861f9a0ad0aff7bd38221c4c862` |
| yt | `0x132a3` | 230 | Confirmed thruster loop, main `32a3..3388` | `ev_e2cd39e92268fc6b1a7e20029d777c2e6b6f52a9b572e8b33e63115747a10655` |
| yt | `0x13515` | 395 | Landing entry/forced landing, main `3515..369f` | `ev_9308ee25bccb06d0059006c9f095191b6a7fd1c770e6342f6e099a0c4bae3d07` |
| yt | `0x15464` | 428 | Rename guard, confirmation/save and following shell | `ev_17409d9c563e9e4e0a200a8cf546e54f15022264a5deac3cd29047ae6543d966` |
| yt | `0x20ef9` | 39 | Sub `1f42:1ad9..1aff`, random integer helper | `ev_ee0aa19506682a236cfc6f1d7b9a5aba0d8bb9a677b1bef25e18f295af31bb2c` |
| yt | `0x274e2` | 1191 | Sub `1f42:80c2..8568`, complete thruster step | `ev_888dba03d262eac91b655fe85f755516972bd150cd64d82dd83a6f2ccd9621aa` |
| yt | `0x2809f` | 689 | Sub `1f42:8c7f..8f2f`, generic landing access | `ev_8165ee58132fd8bce5ddc6dbd293ef6bfc27fcd9c80ac52f7f6fbd0047db51c7` |
| yt | `0x2b0df` | 264 | Sub FIELD bindings, `1f42:bcbf..bdc6` | `ev_3bb91a3625e1c740b4a268475d8eca4cc15dfd2200562426bc12b913692af508` |

The load-image Evidence IDs are:

- `yt-init.json`: `ev_4dc14482eecd48448ac59e50211f07c280f9a9230793bc365babfc30cd7eda70`.
- `ytmaint.json`: `ev_c0b1f0d925c95b6699340df487158ca0aa9f97d90b6cdd026a9f7c8c5b3f594c`.
- `yt.json`: `ev_03514cdc41e9c75482e17cee3453202b476020e2c67335ece260857148a762e9`.

Each range-level interpretation below refers to the matching byte-range row
above; the range row and bundle identify the complete retained Evidence record.

The maintenance embedded-DS mapping is DS `7e60` -> source file `8e30` ->
analyzed `18c30`. Thus DS constant `82a8` maps to analyzed `19078`.
Code-module addresses use load base `10000` plus their module-relative offset;
YT's second code module starts at `1f420`, so its subroutine offsets are added
there. Complete mappings and relocation positions are in each bundle.

## Field mapping

All record numbers are one-based; byte offsets are zero-based within137 bytes.
Wanderer is reserved planet slot1, default absolute record4052, referenced by
sector field93=1. Its name or active indicator does not define its slot identity.
Relevant maintenance FIELD descriptors:

| Descriptor | Offset | Planet meaning |
|---|---:|---|
| `1864` | 0..40 | Space-padded name |
| `1868` | 41 | Production date |
| `186c/1870/1874` | 45/49/53 | Base cargo production rates |
| `1878/187c/1880` | 57/61/65 | Cargo stocks |
| `1884` | 69 | Missiles |
| `1888` | 73 | Owner |
| `188c` | 77 | Ground forces |
| `1890` | 81 | Legacy field; reset by regeneration |
| `1894` | 85 | Active/name-length indicator |
| `1898` | 89 | Production time |
| `189c` | 93 | Sector's planet-slot link when reading a sector |
| `18b4` | 109 | Legacy field |
| `18b0` | 113 | Plasma bolts |
| `18bc` | 117 | Bank |
| `18b8` | 121 | Ground production rate |
| `18c0` | 125 | Mines |
| `18c4` | 129 | Fighters |

The FIELD tail is not numerically ordered by descriptor; the captured sequence
is authoritative. In particular250000 at descriptor18bc is **bank117**, not
fighters129. YT-INIT's descriptorA566 is active85, not owner73.

## Initial creation and daily lifecycle

**Initialization — answered statically for the selected path.** YT-INIT main
`1eff..1fc7` allocates/reserves planet slots and writes zero to active85 in each
slot. It does not fill a complete clean Wanderer record here. Main `23c2..23df`
prints initial-maintenance text and invokes `ytmaint.exe`. Therefore named
Wanderer creation comes through initial maintenance, not a separate named
YT-INIT constructor. Reused file-buffer fields must not be assumed zero.
This describes YT-INIT.EXE specifically; RMT-INIT.EXE is a different executable
and its reset/maintenance behavior requires its own runtime evidence.

**Find/unlink — answered statically.** Maintenance `1d07..1d8b` scans sector
records in ascending order for the first planet93 equal to1. It clears and saves
that first link, then stops scanning. It neither checks slot1 active85 nor
searches for a matching name. Other duplicate references are not cleared here.
A still-linked inactive slot follows the ordinary relocation path; missing all
links enters restoration even if the slot remains active and named.

**Restoration — answered statically, with intentionally retained fields.** If no
source link was found, `1d9d..1f50` emits missing/destruction news, reads existing
planet slot1 and replaces only these fields:

- Name `The Wanderer`, active/name length85=12, date41=current day−10.
- Base cargo rates45/49/53=5000 each; cargo stocks57/61/65=0.
- Missiles69, owner73, ground77, field81 and mines125=0.
- Bank117=250000.

This branch does not explicitly replace fields89,93,97,101,105,109,113,121 or129.
Stale time, bolts, ground production or fighters can therefore survive a partial
restore unless earlier maintenance phases independently changed them. The
following relocation phase still runs after this restoration.

**Destination and record mutation — answered statically.** `1f51..1fc7` obtains
`INT(RND(1)*sector_count)+1` through helper `78f3..7933`. That helper reseeds from
the runtime timer. Only a positive destination planet93 causes rejection and
retry. This selected path does not reject Earth, fighters, mines, ports,
disconnected routes or the former source. Source unlink precedes destination
selection; there is no finite retry budget. In a full universe, a valid source
link creates one vacancy; without a source link, restoration can occur before
an endless candidate search with no vacancy.

At `1fc9..1ff5` the accepted destination link is saved as slot1. Then
`1ffa..2064` reloads planet slot1, unconditionally clears owner73 and refills
bank117 to250000 **only when the current bank equals zero**. Nonzero bank values
are not replaced by this final test. These are separate DOS writes, not one atomic
world transaction. Ordinary daily planet production/events run before this block,
so observed economic deltas cannot all be attributed to Wanderer relocation.

**Date gating — listing interpretation; corroborate with runtime.** Main
`0317..0389` prints `Maintenance not needed!` for an already-current date, then
falls through into the maintenance phases. The selected Wanderer block itself
contains no date guard. Do not infer replay safety from that printed message;
the dedicated same-date controls establish the operational behavior.

**Receipt timing — answered statically.** `1f8b..1f98` prints
`Wanderer has successfully warped!` before the destination record is read or
its occupancy is checked. Rejected occupied candidates can therefore print the
optimistic line before any accepted destination has been saved.

## Player access, names and thruster transport

**Landing — answered statically for the entry/access paths.** Main
`3515..357b` follows a nonzero sector planet93 to the corresponding slot, then
calls generic access `8c7f..8f2f`. There is no slot1-specific admission lock in
these selected paths and no name/active check in the landing entry itself.
Generic access first performs lazy production, then permits zero-ground,
self-owned or friendly-team planets. Neutral/dead-governor defended planets can
be claimed through unrest; active foreign defended planets can offer forced
landing. A normally restored zero-ground neutral Wanderer is landable without
being automatically claimed by the zero-ground bypass. This does not establish
all later planet commands or every concurrent-session permission boundary.

**Renaming — answered statically.** Main `5464..54bf` blocks reserved slot1,
the final planet slot, and its predecessor before asking for a new name. The
slot1 guard depends on the slot, not current owner or display name. For ordinary
slots, input passes normalization then exact reserved-name comparisons at
`54fa..553a` (`The Wanderer`, `Xannoron`, `Mercenary Base`). Successful rename
saves name and active/name length at `5599..55d3`. Case/normalization behavior
needs the matching typed-input controls; do not infer it from strings alone.

**Thruster special case — answered statically.** All ordinary route admission,
full-route affordability and confirmation happen first. Step `80c2..83a4` checks
reserved final slot, destination collision, source unlink and random stress
before testing the Wanderer special case. Thus a first-edge collision or stress
explosion can destroy slot1 before it gets a random escape destination.

On survival, `83a7..8431` recognizes slot1 by its position relative to planet
base. It prints `The Wanderer vanishes from your sensors!`, sets the route-stop
flag, and loops until a random candidate has no positive planet93. Random helper
`1ad9..1afa` returns `INT(RND*sector_count)+1` without the maintenance helper's
per-call reseed. The source sector is already unlinked at this point.

The planet's link is written at random destination **global4b50** (`8503..8523`),
while the ship's saved sector57 is the caller's **planned next route sector**
(`854b..8554`). These coordinates can differ. The successful step deducts ten
turns before saving the player (`8534..8562`), then the stop flag ends the quoted
route after one edge. The vanish message precedes candidate acceptance and
both saves. There is no cash debit or ownership clear in this transport helper;
daily maintenance's owner-clear rule is separate.

Normal main arrival resumes after the helper and can process hazards at the
ship's planned destination. The random planet destination's local mine/fighter
checks in `848f..8500` only affect the stop flag, which is already set for slot1.
Do not mistake those helper checks for ship arrival at the planet's new sector.

## Remaining limits

The three question groups (initializer/maintenance, player admission/naming,
and special transport) are answered statically within the listed ranges.
The root investigation now retains **57 DOS controls** covering the selected
runtime save deltas, duplicate/stale links, partial restoration, date replay,
capacity and receipt cases; see [the combined recovery report](../RECOVERY.md)
for their exact results and bounds. Those observations belong to the runtime
track, not these native reads. Exact DOS RNG/MBF compatibility, crash consistency,
concurrent actions and native-platform operational acceptance are not established
by this static track or implied by the finite control count.
No Go gameplay, README, archived source, branch or commit was changed by this track.

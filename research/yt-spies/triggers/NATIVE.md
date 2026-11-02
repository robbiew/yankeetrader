# Native spy-trigger and detection-sharing evidence

## Artifact and evidence boundary

`rea.json` retains 20 complete REA/Ghidra byte observations, one byte-pattern
search and one independently verified DOS MZ load image for the archived,
unmodified `YT.EXE`:

`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`

Ghidra 12.1.4 uses load segment `0x1000`, `x86:LE:16:Real Mode`, and linear
byte coordinates. The loaded header/module mapping and all 870 MZ relocations
were verified by `inspect_native_load_image`. This is a static load image,
not an executed DOS process, live register dump, or QuickBASIC decompilation.

The interpretation below uses the archived `qb-annotated.txt` listings under
`archive/analysis/yt-combat/{main,sub,sub2}`. Those listings decode BASIC
interrupt operations and annotate known string descriptors. Each selected code
range is independently anchored to newly observed loaded bytes. Logical
`DS:xxxx` variables are names from that reconstruction; they are not claims
about a measured runtime DOS segment register. Existing static and new runtime
findings must remain distinguishable.

## Four direct trigger sites, not one trigger per command or turn

The retained `direct-main-trigger-pattern` search (`ev_53fd6e6b97ad3a0ba5b45f20fa8ac51ed9946dc4b6791946339ca33f53c7ca0b`)
searched all 62,496 initialized bytes of `CODE_0`, linear
`0x10000..0x1f41f` inclusive, for `cd 3f 58 e3 a6`. It returned exactly four
matches, without a cursor or skipped uninitialized/unloaded regions. The
sequence is BASIC's GOSUB operation with target word `a6e3`; the following
wrapper begins at `1000:a6e4`, pushes the active spy count (`DS:50ae`) and
far-calls `2e79:1d3a`. The interpreter's target convention and the wrapper's
preceding `INT3` should not be confused with a native x86 direct CALL.

| Direct site | Context and bounds from preserved code |
| --- | --- |
| `1000:1cae` | Movement, after destination/warp validation and the optional scanner-confirmation gate; before the player sector write at `1cca..1ce1` |
| `1000:2253` | Shared cruise-missile/plasma launch path, after valid target, positive quantity and sufficient ammunition; before the weapon debit/effects |
| `1000:6693` | Docking, after a port exists and the docking input has been read; before entering the Earth/trading dispatch |
| `1000:a1da` | Computer 9 Planet Report's unavailable-information branch, after a valid sector inquiry |

The `2253` call was previously described as fighter deployment in older
research. Its actual entry labels are `205a` (cruise missile, selector zero)
and `2079` (plasma bolt, selector two), both joining at `2094`. Quantity less
than one exits at `21f4`; invalid sectors exit via `21ad`; insufficient stock
returns via `223d`. These paths do not reach the spy call. Fighter Drop/Take
begins separately at `1cfe`; the search finds no extra direct trigger there.
The shared launch site is evidence of a trigger after accepted launch input,
not a guarantee that a later projectile reaches its target.

Likewise, a `No port here!` result branches away at `666f..667d` before the
docking trigger. A planet-report cancellation or invalid sector returns before
the unavailable-information site. Its compound access predicate uses queried sector defenses, rather than only
planet ground troops. At `a061..a080`, `4cfe` receives sector fighters (offset81)
and `1a40` receives their owner (offset85); `1f42:974f..980e` supplies the
self/same-team access flag `4bc4`. The caller's team `4d0e` comes from saved
player offset89 (`a494..a49d`), not the sector owner.

The decoded `a17b..a1d5` condition enters No Information when there is no
planet, or positive sector fighters deny access: a caller with a team needs
the self/same-team flag, while a teamless caller needs to own those defenses.
Planet ground troops (offset77) participate in an earlier abbreviated
name/ground report branch (`a0df..a178`); foreign ground troops alone do not
establish this spy trigger. The raw FIELD mapping is preserved in
[planet mobility native evidence](../../yt-planet-mobility/rea/NATIVE.md#record-mapping-avoid-linear-descriptor-guesses).
Runtime controls distinguish ordinary own/foreign planet reports, no planet and
hostile sector defenses rather than assuming that a foreign planet must be
unavailable. Full self/same-team defense predicate coverage remains a static
interpretation unless separately identified as a runtime control.

This is a complete search for that **direct five-byte encoding in CODE_0**.
It does not enumerate all command aliases, loop reentries, BASIC indirect
control transfers or every transitively reachable caller. It cannot establish
that only four user commands can ever advance a spy. Movement/autopilot aliases
need runtime corroboration rather than counting byte matches as commands.

## Scan suppression, reporting and movement

The complete spy body is retained through the `RETF 2` at
`2e79:257a..257c` (`spy-routine`, `ev_65a9fae9fd71a4f473c0ba538db2adfb6cfc85538a3839994c110431a84a8048`).

- `1d6f..1d83` reads the spy's current sector from the session's `DS:4b74`
  integer array. `1d86..1db7` compares it with the remembered sector at
  index `spy+4`, suppressing scanning when that remembered sector is nonzero
  and equal. The suppression branch joins movement at `234f`.
- The first actual finding calls the report-header subroutine at `24a5`.
  `24d6..24eb` writes the current sector to the remembered `spy+4` slot.
  An empty scan does not use this report-header write.
- `238a..2478` reads six outgoing warp slots, repeatedly samples a nonzero
  slot and stores the next current hunt sector. It executes after scanning,
  including on the suppression branch. It is not a shortest-path search.
- The retained `spy-drain-input` and `spy-pause-input` helpers are input/output
  pacing routines. Their presence is not an independent spy progression site.

Consequently "last reported sector" is not "last visited sector". A spy can
move without a report. A return to the last reported location can remain
suppressed even if other unreported sectors were traversed in between. Runtime
chains must distinguish these cases and retain the exact parent world and
input rather than infer them from final location alone.

## One observer-local cache is shared with sensors and attacks

Spy cloak checks at `2e79:1f5e..1f8c` read the cached MBF single at
`DS:1a70 + 4*(target-record+0x34)`. A successful shimmering branch prints the
notice to the observer, then `1fac..1fc2` writes zero into that same slot.
`spy-constants` independently observes MBF single zero at logical `DS:c9c0`;
this is not an inference from the variable name. The branch's subsequent
`6008=1` flag allows the newly detected ship to be reported immediately.
The cached value is then checked again at `1fe6..2010`.

Other consumers use that exact array and indexing:

| Consumer | Selected instructions |
| --- | --- |
| Adjacent-sector sensors | `1f42:5e7a..5e93` compares RND against the cached cloak; `5ebd..5ed3` clears a newly detected slot; `5eff..5f27` gates ship details |
| Ship attack candidates | `1000:2978..29c4` combines cached sector/current-player checks with a positive cached-cloak rejection |
| Initial cache load | `1f42:bfa3..c080` reads each saved player record once under `DS:1a74`, filling cached sector from `DS:1958` and cached cloak from `DS:19a0` |
| Current player's refresh/decay | `1000:a554..a56a` and `a770..a786` address the current player's cache slot; the decay path also writes the current player's saved cloak |

The initialization fields correspond to saved player sector offset 57 and
cloak offset 125. The shared constants observation anchors `DS:a36e=0`,
`a372=1`, and sound selector `a36a=4` as MBF singles.

**Static conclusion:** successful spy detection changes the observer login's
shared visibility cache, so the same target can subsequently pass sensor and
attack-candidate cloak gates in that login. This is more than spy-network-only
memory. It is not a write to the target's saved cloak, not a reveal broadcast
to every player, and not proof of how a second concurrently running DOS process
would synchronize its independent cache. Runtime spy→sensor and spy→attack
controls must corroborate the selected paths. Reopening the target or observer
world tests persistence separately.

## Target notification: bounded negative evidence

The shimmering branch calls `1f42:1b78`, an ordinary observer-output wrapper,
then selects sound/presentation code **4** and calls `1f42:0e42`. The retained
sound helper chooses BASIC PLAY strings (for example `MBT128O5L48P64CP64C` for
selector 4) or local terminal presentation. This call is **not** evidence that
the detected target receives mail or a warning.

The direct `CALLF` inventory in the complete spy body reaches ordinary output,
warning/presentation, planet lookup, input draining and pause helpers. There is
no direct BASIC random-file PUT (`QB_3e_28`) in that body and no explicit
foreign-target mailbox writer in its shimmering/report path. The observed
cache clear is followed by report generation, not a target-record cloak write.

This is a bounded static negative, not an exhaustive proof that no original
DOS feature ever notifies targets. Nested helper behavior outside the retained
ranges, other detection mechanisms, sysop modes and simultaneous online
sessions remain separate. Positive spy detection followed by an exact target
relogin with retained auxiliary files can establish whether **that tested
path** queues a warning; a broad string search alone cannot.

## Retained byte-read index

Every row below has a complete `bytes_hex` payload and immutable subject/profile
identity in `rea.json`; the portable verifier reconstructs the MZ image rather
than trusting the annotated text.

| Label | Linear start | Length |
| --- | --- | --- |
| wrapper | `0x1a6e4` | 20 |
| move-gate | `0x11bf4` | 265 |
| launch-gate | `0x1205a` | 512 |
| dock-gate | `0x1660e` | 175 |
| planet-report-gate | `0x19f80` | 632 |
| spy-routine | `0x304ca` | 2,115 |
| sensors-shared-cache | `0x2525d` | 493 |
| attack-shared-cache | `0x1292b` | 373 |
| cache-initialization | `0x2b3c3` | 224 |
| self-cache-refresh | `0x1a545` | 40 |
| cloak-decay-cache | `0x1a764` | 37 |
| sound-helper | `0x20262` | 465 |
| console-helper | `0x20f98` | 139 |
| warning-helper | `0x29826` | 99 |
| spy-drain-input | `0x30d10` | 82 |
| spy-pause-input | `0x30d65` | 187 |
| shared-constants | `0x3661a` | 16 |
| spy-constants | `0x38c0c` | 108 |
| caller-field-refresh | `0x1a41d` | 296 |
| owner-team-access | `0x28b6f` | 194 |


The completed [runtime matrix](RECOVERY.md) now corroborates the selected
spy→sensor and declined attack-choice paths. The no-spy attack control also
obtains visibility after an independent ordinary detection notice; it does not
establish a deterministic counterfactual with an identical random sequence.

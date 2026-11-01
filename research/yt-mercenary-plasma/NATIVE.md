# Native Mercenary plasma sales investigation

This is static shipped-artifact evidence for the archived Yankee Trader 3.6
`YT.EXE`, interpreted with the historical QuickBASIC-aware listings. It does not
execute the original game or recover its BASIC source. Runtime controls and the
version-history finding belong in [RECOVERY.md](RECOVERY.md); the project decision
belongs in [CONTRACT.md](CONTRACT.md).

## Version identity changes the question

The archived change log records the Mercenary **Mother Ship** selling plasma for
5,000,000 credits each under version 3.3. Version 3.4 explicitly removes that ship
because planets can produce plasma bolts and program space was limited. The
current `YTINSTR.DOC` describes planetary acquisition. Those are versioned text
observations, not evidence that a live 3.6 Mercenary Base sale routine exists.
A Mercenary Base planet, a Mercenary fighter group and the removed Mother Ship
must not be treated as the same seller.

The native search therefore checks current acquisition interfaces and preserved
plasma inventory writes. It does **not** invent current eligibility, price,
quantity, hostility, tax or purchase-receipt behavior from that old price note.

## Artifact and retained Evidence

The original `archive/dos-original/YT.EXE` SHA-256 is
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
[rea/yt.json](rea/yt.json) retains **12 complete byte reads and one verified native
load-image observation** from REA/Ghidra 12.1.4. These are selected ranges, not a
claim that 12 complete functions were recovered. Four small/contextual ranges
are retained explicitly as such rather than used as a broad absence proof.
The analysis profile digest is
`92fec87c3e8c374652fd603898f727129f4c0cecccf8cee1c17c98a90aced029`.
The native session was closed after exporting the Evidence.

[rea/ledger.json](rea/ledger.json) binds every read to its original-file range,
source and relocated byte hashes, provider address and Evidence ID. An independent
reconstruction used the 3,584-byte MZ header, 170,737-byte module, all 870
relocation words and load segment `0x1000`; every retained byte matched. The
load-image Evidence ID is
`ev_03514cdc41e9c75482e17cee3453202b476020e2c67335ece260857148a762e9`.

Addresses use the historical main alias `1000:xxxx`, linear `0x10000+xxxx`.
The data segment base is linear `0x2c2b0`; original-file mappings subtract the
`0x10000` load base and add the 3,584-byte header. Relocation words must be
applied before comparing original source bytes with the provider's loaded bytes.
Static inspection did not modify or execute the archived binary.

| Retained range | Linear address | Bytes | Evidence ID |
|---|---|---:|---|
| Main shell dispatch entry | `0x11659` | 528 | `ev_fb361deb2b9d28e471cf64db96e8b744fb157013c3e4bd8120774b958d63c8d0` |
| Movement dispatch suffix | `0x11ac0` | 1152 | `ev_a8f5116f9c4b3f7f65062af6918d528030a27d0e87ca38c3590ed250a92a217e` |
| Plasma firing admission prefix only | `0x12079` | 16 | `ev_7049ed4bc8d32cc9d2d6cc8071ff9808e2976e7d27dcf899f754c927f6acd126` |
| Planet thruster confirmation context (not sales admission) | `0x13240` | 1024 | `ev_fdc76e0bc436fb94db44f15223c5a53c3b118c728b2ffa946f0556109917847e` |
| Planet take dispatch, amount parsing and initial writes | `0x13e61` | 1536 | `ev_089aa58363eb6d73ea33114b401e078b668a09ee53e6b0fa79f8692d5be9249e` |
| Planet take plasma decrement and final save | `0x144a1` | 320 | `ev_c602a24c8cc873d6c39d6e2cdf7037cd86cabac0e4259643145f0e3d8aafe54e` |
| Planet deposit menu and plasma full-stock transfer | `0x148b0` | 1536 | `ev_5c3cd9d3e4eeab1ba3497315747f6155ce15afd4752993a735e792b3752930b7` |
| Port positive-turn gate and Earth selection | `0x1660d` | 512 | `ev_496d9278968384588ee4305d9568e35dcec59eb5c35e36377bada215b237765c` |
| Ordinary port pricing projection | `0x168e0` | 640 | `ev_8da0a7335ea77d77f744a8adb412536093dc64376efe808a1119c4b5713a71da` |
| Earth menu, dispatcher and item handlers | `0x16d00` | 4096 | `ev_111011b9d4ba9e16cf8e23bd1183eda8853f57de270202a099db7e3a6a2434f5` |
| Planet take and transfer labels | `0x3415a` | 800 | `ev_add1d7a47e8f32cd4c06fb17e9af3d8e293cbc80abebb443d4836a8e19916642` |
| Earth menu labels and input prompts | `0x34ef6` | 1480 | `ev_e83d443bc5d9bf3be107b83aa0ed12a89ecf1b3edca77c6bd7326256089c3e43` |

## Current Earth shop and shell dispatch

The shell entry at main1659..1735 accepts a one-character command and uses the
literal command table `W!+ABCFLMPQTD$GN`. The plasma `+` entry leads to firing,
not a seller. This entry table by itself does not prove every indirect helper
or hidden path is absent.

Port entry at main660d..66b7 calls the positive-turn gate before loading the
sector's port. Current sector 1 selects the Earth shop at72c8. The retained shop
range main6d00..7cff includes its menu, input dispatcher and item handlers. Its
menu declares:

| Item | Current Earth action |
|---|---|
| 1 | Cloak Energy |
| 2 | Cargo Holds |
| 3 | Fighters |
| 4 | Play Lottery |
| 5 | Danger Scanner |
| 6 | Anti-Cloak Device |
| 7 | Ground Forces |
| 8 | Shield Power |
| 9 | Hire Spies |

Main7315..7330 takes the first input character, applies `VAL` and converts the
result before the numeric jump table. An input beginning with `1` is therefore
not an unsupported two-digit item test. In particular, item9 is **spies at
Earth**, whereas item9 is **plasma on a planet**. Main739e handles ship info;
main73db..73fe checks `LM0C` navigation and emits the original misspelled
`INAVLID CHOICE!` for the remaining unsupported selection. No plasma item is
present in this menu/dispatcher range. This is a bounded interface observation,
not a global theorem that no binary byte could encode another seller.

## Current planetary plasma source

The planet command table at main3e61 is `F!MPC1234569LTAB$`. Its help at3f11 names
`9 - Take Plasma Bolts`; main4073 names the selected `Plasma Bolts>` prompt.
The common amount prompt and checks precede item9's inventory branch. At4336..
4356, item9 adds the selected quantity to the cached ship plasma value `4e2e`
and writes the player field descriptor1990. The player record is saved at4364
before the planet record is loaded at4372. At44dd..4516, the same item9 branch
subtracts the selected quantity from the planet's cached stock and writes the
planet descriptor1990; the planet record is saved at4524. The subsequent cache
update and player reload return to the planet shell. This is a stock transfer,
not a five-million-credit sale. Its original sequential record writes do not
establish atomicity in the modern implementation.

The transfer-to-planet menu at4959..49c9 lists `[B] Plasma Bolts`. Main4c49..4ccd
handles B: it zeroes the ship's plasma field, saves that player record, then adds
the previous full carried amount `4e2e` to the planet's cached stock `1a38` and
saves the planet record. It prints `Plasma Bolts Transferred!`. This branch
transfers the full carried stock; it is not a merchant quantity/cost prompt.
It contains no credit-price calculation in that branch. No assertion about
all surrounding turn/landing/ownership costs is inferred from this local slice.

## Negative-search boundary and unknowns

The retained analysis combines the concrete current shell, Earth, take/deposit
paths with a text search of the archived main/sub/sub2 annotated listings for
`mercenar`, `plasma`, `bolt`, `buy`, `sell` and `purchase`. Such a search can miss
encoded, dynamically assembled or otherwise unrecognized paths. Its usefulness
here is corroboration of the **explicit versioned removal notice**, rather than
an independent universal absence proof.

No historical 3.3 executable was supplied or executed. That version's seller
location, movement, encounter/hostility thresholds, quantity or carrying caps,
input parsing, payment-before-delivery order, turn/cloak charges, tax destination,
reconnect behavior and overflow bugs remain unknown. The change log supplies
only the old unit price and named Mother Ship, followed by its removal. Current
3.6 Mercenary Base or force behavior cannot fill those historical gaps.

The research does not justify adding Mercenary sales to a 3.6 reconstruction.
Restoring the old feature would be a separate explicitly chosen extension with
new modern rules and, if historical fidelity is desired, a matching old binary
and fresh observations. Existing planet production/take/deposit paths remain the
supported plasma supply mechanism.

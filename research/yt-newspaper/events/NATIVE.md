# Planet-creation and port-acquisition native evidence

## Artifact, observations and limits

`rea.json` retains **21 complete byte observations**, **four complete bounded
byte-pattern searches** and **one verified load-image observation** from REA's
Ghidra 12.1.4 provider against the unmodified archived DOS 3.6 `YT.EXE`:

`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`

Ghidra imports x86 16-bit real-mode MZ with load segment `0x1000`; addresses in
Evidence are loaded linear byte coordinates, not unique segment:offset aliases.
`inspect_native_load_image` verified the complete initialized mapping and all
**870 relocation records**. Every retained byte span and search result was also
compared with an independently reconstructed, relocated original image. The
complete REA session was exported before closing the owned session.

The interpretation below uses the preserved QuickBASIC interrupt-op listings in
`research/yt-combat/{main,sub}/qb-annotated.txt` to name descriptors, string
operations and control flow. Primitive observations anchor those selected ranges
to the shipped bytes. They are static facts, not DOS execution, measured registers
or recovered original BASIC source. The shared DOS runs separately establish
which branches and public/private file effects actually occurred.

## Planet creation publishes a public line

The creation path at `1000:36a0..39b0` first announces that no planet exists and
sets the 25,000-credit price. The selected `planet_gate_poor` observation covers
the insufficient-funds gate and return; `planet_consent_capacity_name` covers the
Y consent gate, free-slot search, full-capacity diagnostic and name-helper call.
A non-Y purchase answer returns before planet initialization, fee or news.
These gates are interpreted branches; runtime controls establish accepted inputs.

`1000:37b1` invokes the local name helper at `1000:5464`. After it returns,
`37b6..37c4` checks for an empty candidate and exits before the new-planet writes.
The name helper's selected observations cover:

- Empty input returning at `54e9..54f7` with the candidate still empty.
- The reserved-name comparisons for `The Wanderer`, `Xannoron` and
  `Mercenary Base` at `54fa..553a`, followed by a rejection/return. This does not
  establish every case variant or the entire input filter.
- The `0x29` (**41-character**) left-substring operation at `553d..554a`, then the
  candidate snapshot at `5552..5558`.
- The `Is this OK? (Y/n) [Y] ?` prompt and comparison against **N** at
  `5577..5596`. N loops to `5464`; other accepted input proceeds. The subsequent
  name/length writes and return are retained through `55d5`.

Planet initialization occurs only after that nonempty-name gate. The fee helper
call at `391f` precedes the news construction at `3927..394d`. The actual
construction concatenates:

```
  -  <caller alias> made a planet: <accepted planet name>
```

`planet_success` (`ev_63c3256a4a53a7239ef046b846ca881cc81707811e89d9c387be25fdb62d7de1`)
and `planet_fee_news` retain the full concatenation and direct far call at
`1000:394d` to the shared newspaper writer `1f42:1a9b`. The newly read
`planet_text` bytes independently contain ` made a planet: ` at linear
`0x33f72`. The display-only sentence `Planet "..." created with Genesis Device!`
comes **after** the append call and is not the newspaper format.

The line construction uses the caller-alias descriptor and accepted planet-name
candidate. It does not append sector, team, fee, ship resources or account/bank
balances. That statement is scoped to this selected construction, not every
possible action log. DOS writes/fees/news occur in a sequence: static ordering
is not evidence of atomic crash durability. A modern implementation should place
its event and successful action in one authoritative save.

## Port acquisition has a private seller notice, not a direct public append

The purchase dispatch `1000:2341..270b` is retained as a complete 971-byte
bounded region (`port_success_complete`), with smaller overlapping gate,
settlement and final-write observations. It covers no-port/already-owned exits,
price/funds checks, consent, prior-owner settlement, optional naming, new owner,
buyer debit and final confirmation. Initial consent compares Y at `24cd..24d8`;
non-Y branches to the refusal at `26fb` before settlement. Insufficient funds and
already-owned/no-port paths return earlier.

The existing-owner branch constructs a different message at `25af..260e`:

```
<buyer alias> bought your port "<old port name>" in <sector> for <price> credits
```

It pushes the **old owner** as recipient, the system sender selector **-2**, and
the formatted body, then far-calls `1f42:2561` at `1000:2629`. That routine calls
`1f42:2059`, whose selected bytes open **`ytRMSG.DAT`** with fixed record length
**0x56 = 86**. `radio_packet` retains the recipient/sender/body field writes and
`radio_packet_return` retains the complete return instruction. The literal
`radio_file` observation independently reads `ytRMSG.DAT` at linear `0x36b1a`.
The construction is before the optional port-name dialogue, so it references the
old displayed port name rather than a later newly accepted name.

For comparison, `news_append` reads the shared writer `1f42:1a9b..1ad5`, whose
filename is `ytnews.DAT`; `newspaper_file` reads that literal at `0x36aa2`.
These are separate writer paths and scopes, not two spellings for the same file.

The complete bounded searches establish:

| Search | Bounds, inclusive | Observed direct calls |
| --- | --- | --- |
| `no_public_append_in_purchase` | `0x12341..0x1270b`, 971 bytes | Zero `9a 9b 1a 42 1f` shared-news calls |
| `private_writer_in_purchase` | Same 971-byte region | One `9a 61 25 42 1f` radio call at `0x12629` |
| `no_public_append_in_rename` | `0x1a9f0..0x1ab34`, 325 bytes | Zero direct shared-news calls |
| `public_append_in_planet_creation` | `0x136a0..0x139b0`, 785 bytes | One shared-news call at `0x1394d` |

All searches have complete coverage, no continuation cursor and no skipped
uninitialized/unloaded bytes. They establish the absence of this **direct byte
encoding in those regions**, not the absence of all conceivable indirect logging
or all original event producers. The runtime file checks are needed before
classifying the tested acquisition path as private-only.

## Naming refusal is not acquisition cancellation

The port naming helper `1000:a9f0..ab34` is a loop. Empty name input reuses the
old name (`aaa0..aaa6`) but still asks `Is this OK? [y/N]`. Y writes name/length
and returns (`aaf7..ab23`). A non-Y answer clears the candidate and repeats
(`ab26..ab2f`), rather than undoing the already accepted purchase.

This order matters: old-owner settlement and private seller notice precede the
rename helper, while the buyer/new-owner writes follow its return. A test that
stops during this dialogue cannot be described as a normally returned cancelled
purchase. Initial B/N and a name-refusal-then-corrected/kept-name flow are separate
controls. Blank or malformed prompts must not be guessed to have cancellation
semantics from the English wording alone.

## Deliberate boundary for reconstruction

The public planet-creation event is a candidate for a subsequent gameplay change,
subject to normally returned runtime controls, exact action/resource validation
and an atomic Go save. The selected port-acquisition block supports a private
seller notice and supplies no direct newspaper append. A public port-acquisition
announcement would require additional evidence or an explicit modern design
choice; the backlog should not invent it merely because the action is playable.

Exact output colors, DOS string edge cases beyond the controls, account-key
attribution, concurrent DOS writers and crash behavior remain unverified by this
native slice. No Go gameplay or persistent schema is changed by these records.

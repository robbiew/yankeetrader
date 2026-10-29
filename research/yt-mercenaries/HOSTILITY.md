# Hostility, eager random checks and offer comparison

This follow-up resolves the implementation blockers from the
[initial offer-boundary research](RECOVERY.md). It combines 24 additional completed
original-DOS sessions (48 snapshots), three new Ghidra/REA byte observations and
eight verified BRUN30 dispatch fragments. Together the two slices retain 43
sessions and 86 before/after snapshots. Original executables remain unchanged.

## Resolved decision tree

`F` is total fighters aboard; `D` is current sector defenders. Draws below are
independent calls to the game's RND routine, not statistical estimates from the
captured runs. The conditions are recovered from the binary/runtime handlers.

1. Non-Mercenary groups refuse. Xannor always force full-ship-fighter combat.
   Human groups force combat only when `D > F` and `RND < .33`. The draw occurs
   even for Xannor or a human group that is not stronger: BASIC evaluates both
   sides before combining the conditions (`1000:12eb..132f`).
2. Mercenaries in a sector with a nonzero planet reference refuse negotiation
   without drawing randomness (`1335..135e`). This reads the sector reference,
   not the planet's owner. Neutral and human-owned planet controls both refuse.
3. Otherwise draw `r1` and `r2` unconditionally. Force combat if
   `r1 < .05`, or if `D > F && r2 > .9`, or if the session hostility flag is set
   (`1361..13f3`). Even the always-hostile case consumes the two preliminary
   draws; the second draw also occurs when the ship is stronger.
4. If negotiation remains possible, DOS reads the offer. Blank cancels. An offer
   exceeding available credits or **strictly below** `D + 2*D*r3` insults the
   group and forces full-ship combat (`1456..14e4`). Equality accepts. The third
   draw occurs even for an over-budget DOS offer, due to eager evaluation.
5. Acceptance debits the exact offered amount, recruits the whole group and
   clears both defense count and owner (`14e7..1587`). Insult/refusal combat
   does not debit the offer.

The probability thresholds in the original are MBF constants; Go uses the named
modern decimal thresholds and `[0,1)` RNG. The recorded sessions establish
outcomes and conservation, not QuickBASIC RNG or bit-exact rounding parity.

## The hostility flag

DS:4D5E is set to -1 at `1000:10b0..10b6`, under the Mercenary-owner check and
only after positive defending casualties. It is read by the pre-offer OR at
`1392..139c`. It belongs to the loaded BASIC module, not a saved DAT field.

The partial-attack run destroys 17 of 1,000 Mercenary fighters, then offers
50,000 to the remaining 983. They refuse with “We just want your miserable
life” and fight. A fresh-login control against 1,000 accepts that same offer.
The cross-group run destroys 100 Mercenaries at 101, moves to 107 and offers
50,000 to a different 100-fighter group; that group also forces combat. A human
surrender at 101 followed by the same Mercenary offer at 107 accepts. The
owner-specific flag assignment is established statically; the human control is
surrender, not a claim about measured human combat casualties.

The stop-after-partial run quits with 983 defenders left. `reconnect` starts a
new original-DOS process from **exactly those final YTDATA bytes**, without
patching or resetting the world, and its 50,000 offer is accepted. Both the raw
world chain and final 983-fighter recruitment are verified. This establishes
same-login memory and reconnect reset independently of a world-field hypothesis.

A modern login therefore starts with no hostility memory. Only a successfully
committed fighter battle that destroys Mercenaries sets it. A transaction rolled
back before replacement must not publish memory; a post-replacement durability
warning retains it, matching the committed combat. Missile damage is not a
recovered producer of this main-module fighter-combat flag and does not set it.

## Supporting controls and probe limits

Eight clock controls (01:00 through 08:00) and eight corrected sensor controls
all reached negotiation and accepted in the retained captures. The sensor
controls use a two-neighbor first sector (101 and 103), with the adjacent enemy
cloaked at .5, to avoid the long sensor display's key pause. They are validation
of reachable normal branches, not empirical confirmation of a particular
percentage or exact RNG sequence. Injected Go tests cover all strict random
boundaries, eager draw counts and forced branches.

An earlier 15-probe sensor series consumed the B key at its display/encounter
pause. Those sessions exited normally but never offered a bribe, so they are
excluded from the retained evidence and from all outcome counts. The successful
stop-after-partial parent from that batch is retained and independently checked.
The eight corrected sensor runs have explicit negotiation/completion assertions.

## Static provenance

[hostility-path.json](rea/hostility-path.json) retains three REA observations:

- `ev_e267ea787e3117a33e92f7f7ab272197286d18d28b758f16e31af2f02c3b279e`:
  linear `0x110a2`, 23 bytes, owner-specific flag assignment.
- `ev_de00f3142ba4f010c575d5a2c39b9fb1343c5055591a8f50025dbcbffeeac62c`:
  `0x108a1`, 12 bytes, sector planet-reference load.
- `ev_c201cfe58a4afbab7b8423aea7d50f3bf80e063ff3f5dfe9ad8853b94d644ce9`:
  `0x112eb`, 74 bytes, human/Xannor refusal/retaliation conditions.

The offer-path reads from the initial slice cover `0x11361` and `0x11456`.
[Runtime fragments](rea/runtime-dispatch.json) come directly from unchanged
BRUN30.EXE: dispatch table file offset `0x58d`, opcode entry = little-endian
word at `table + 2*opcode`, fragment file offset = `0x200 + entry`.
The verifier checks these mappings and every captured byte. In particular,
3F/AE consumes inline exponent adjustment `01` (multiply by two), 3F/82 adds the
remaining defender operand, and 3F/A6 compares the saved offer with that result.
This resolves the earlier disassembler's instruction-boundary error and inferred
threshold. REA used Ghidra 12.1.4 and the ephemeral session was closed.

## Reproduction and validation

```sh
python3 scripts/recover_navigation.py /tmp/yt-hostility-new --hostility
python3 scripts/recover_navigation.py /tmp/yt-hostility-reconnect-new \
  --only npc-hostility-reconnect \
  --source /tmp/yt-hostility-new/npc-hostility-stop-after-partial
python3 scripts/verify_bribes.py
python3 scripts/verify_bribe_hostility.py
python3 scripts/verify_archive.py
```

Every destination must be fresh. The reconnect command is separate so it starts
only after its parent completes. The preserved results were collected in four
fresh batches; their manifests and source-chain hashes are authoritative.
Replays can differ in random outcomes. The portable verifier checks provenance,
exact fixture rebuilding, command execution, debit/fighter conservation, both
cleared groups, retained partial defenses, reconnect chain and all static bytes.
Rehashed debit and reconnect-input corruptions are rejected. CI needs neither
DOSBox nor REA. All 4,682 archival file hashes remain unchanged.

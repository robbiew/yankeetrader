# Native broadcast radio, shared delivery budget and maintenance

This is static shipped-artifact evidence from the archived **DOS 3.6** YT.EXE
and YTMAINT.EXE. It is interpreted with the historical QuickBASIC-aware listings,
not recovered BASIC source or a runtime trace. The accompanying DOS controls
establish actual packet values, delivery and public newspaper effects separately.
Maintenance conclusions in this slice are static only; no YTMAINT runtime
control is counted.
This extended research does not overwrite the earlier six-control broadcast
slice or imply that its modern private-copy adaptation matches this original
shared-record policy.

## Evidence identity and independent byte checks

The original YT.EXE SHA-256 is
c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037;
YTMAINT.EXE is
8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6.
Both sessions used REA/Ghidra 12.1.4, analysis profile
92fec87c3e8c374652fd603898f727129f4c0cecccf8cee1c17c98a90aced029.
Neither executable was modified or executed by native inspection. Both native
sessions were closed after exporting complete Evidence.

[YT evidence](rea/yt.json) contains nine complete byte reads plus one verified
MZ load-image observation. [MAINT evidence](rea/maint.json) contains two complete
byte reads plus its verified MZ image. These are selected complete ranges, not
claims that eleven complete functions or the whole binary were recovered.
Contextual suffixes and the full shared editor are labeled accordingly.

The independent [YT ledger](rea/ledger.json) and
[MAINT ledger](rea/maint-ledger.json) bind every read to original-file offsets,
raw and relocated byte hashes, provider addresses, lengths and Evidence IDs.
Reconstruction applies all 870 YT relocations to its 3,584-byte header/
170,737-byte module and all 108 MAINT relocations to its 512-byte header/
42,673-byte module. Both load at segment 0x1000 and every retained byte matched.
Original-file mapping subtracts load base 0x10000 and adds the appropriate
MZ header; loaded call operands must be compared after fixups.

| Target / selected range | Loaded address | Bytes | Evidence ID |
|---|---|---:|---|
| YT: Radio file open and FIELD declaration | 0x21479 | 75 | ev_3009eae74cffa186891b4969c04eab2250c31c8f5ac78fdd5c23ebe578a08b1f |
| YT: Broadcast newspaper append helper with contextual suffix | 0x20ebb | 225 | ev_3b7633d692a846edf606ebe1b15cfa36f6d748933a8e186ac2bdc67c3abbabfa |
| YT: Radio writer and delivery/history reader | 0x21981 | 1114 | ev_4562df73fab00b489c0fd32083b5c28aa4da3bfea1a4efc2c15de814a2223fb4 |
| YT: Startup mailbox delivery call | 0x10802 | 29 | ev_67532e34d0221e1a0ba01322975fa8843b98161b451b6204549c27ef8a4162dc |
| YT: Single-precision shared radio constants and context | 0x36590 | 1200 | ev_7fa075eb491e06482140065ae30728ba3f5e400b03ac15f5249747b46c2f983a |
| YT: Radio selector/editor/send labels | 0x35cf0 | 960 | ev_880164852c75e6f0b7b75a9f8fdfb5ff88e95de05df6e8f47ee95085e7464a37 |
| YT: Computer radio history dispatch | 0x18c77 | 45 | ev_8d52d463868d4e8e765ffe4739fbdf4cf2cd2c2d22e2dbd070509215611109e4 |
| YT: Radio file/read labels and constants | 0x36b20 | 500 | ev_92682363ea90ad33f9785c61528324cffac7805c6813ca65b17f97a538f16a9f |
| YT: Radio selector, editor and send dispatcher with bounded suffix | 0x193a1 | 3055 | ev_f69df1baa2cb8dca2247fe09feaebde9d75485535ecb72911782f7b8a301cdd3 |
| MAINT: Maintenance radio-file declaration | 0x17155 | 85 | ev_29cb79843e134545e0c974e4638aec1bad726d3268b81c095c99d4bba3e73eed |
| MAINT: Daily nonzero-message compression and newspaper rotation | 0x1672d | 499 | ev_dda450b3eec63a105b926448f55e88c1644923d85b38be8e10ab5b9a72fd6b6c |

The YT image observation is
ev_03514cdc41e9c75482e17cee3453202b476020e2c67335ece260857148a762e9;
the MAINT image is
ev_c0b1f0d925c95b6699340df487158ca0aa9f97d90b6cdd026a9f7c8c5b3f594c.
The portable verifier independently checks both images and every relocation.

## ALL is a shared destination, not roster fanout

Main 93a1 opens the radio action. The recipient prompt explicitly offers ALL
and TEAM, and normalizes the input through the shared string helper before
comparing with Team and All. TEAM loads the player's roster and changes the
recipient-loop count. ALL instead prints its broadcast warning at 9451, writes
destination -2 to 4b94 at 945f..9465 and jumps directly to the shared editor 9517.
It does not enumerate current players or generate one addressed copy per person.

The original editor says 20 lines and tracks individual line slots. Its
character handling wraps at 74 characters; send 9ac8..9b6f walks the retained
lines. The extended range intentionally includes editor/abort/contextual code,
but this milestone does not claim a full recovered multiline-editing contract.
Abort 9a2e..9a5e requires confirmation and bypasses the send branch.

At send 9a6f..9a9a, destination -2 causes a newspaper author header to be appended.
For each retained line, 9afb..9b21 appends the text with the ordinary newspaper
prefix before 9b24..9b4d calls the same radio-packet helper used by private mail.
A broadcast line therefore has both a public newspaper side effect and one
shared radio record. New radio record and newspaper writes are sequential
original-DOS file operations; they are not evidence of a cross-file transaction.
A failed later write could leave an earlier publication visible.

## Packet layout and initial delivery budget

Sub 2059 opens ytRMSG.DAT as an 86-byte random-access record and declares three
four-byte fields plus 74 bytes of text. Sub 2561 reopens that file, chooses a new
record after the existing file length and writes:

1. First field 30 when destination is -2, otherwise ordinary flag 1.
2. Destination (broadcast -2 or private player-record number).
3. Sender player-record number.
4. Padded 74-byte line text.

The runtime controls corroborate the broadcast tuple (30,-2,sender). The first
field is a shared remaining-delivery budget, not a timestamp, recipient roster,
set of independent flags or 30 days. The writer has no current account count or
per-recipient acknowledgement array in this branch.

No price calculation or ordinary turn-debit helper is present in this selected
compose/send path. Zero-turn admission and unchanged resource accounting are
corroborated by the DOS controls; this is not a blanket claim that all surrounding
computer/navigation actions are free.

## Startup delivery, history and exhaustion

The known startup call atmain 0802..081e passes current player and mode 0 to
sub 2614. Computer option 6 at8c85..8ca0 passes mode 1 to the same reader. The
reader's header distinguishes checking for new messages from the sent/received
log. The main 0cc6 literal RADIO MESSAGE COMING IN belongs to a fighter encounter,
not an online mailbox polling or broadcast-subscription loop.

The selection at sub 26be..2722 combines private recipient/sender-history
eligibility with a global first-field-greater-than-one branch. Consequently
a positive shared budget greater than 1 exposes a broadcast to a reader even
when that player did not exist or was not a team member at send time. It is
current shared-record eligibility, not a frozen recipient list.

At 28f6 the mode check skips acknowledgement writes for history mode. Startup
mode instead updates the first field at 2901..2947: values greater than 1 consume
two from that shared budget; ordinary flags clear to 0. The runtime read probes
measure30 → 28 and the boundary distinction between 2 and 1/0/-1. Repeated fresh
logins can therefore consume the same record's budget without an independent
per-account already-read flag. The private sent-mail clause must not be treated as proof of an exhausted
broadcast exception for its author. Retained budget-boundary controls use the
other account ENEMY; the exhausted author's own history is not separately
established by those controls.

These branches contain no calendar or elapsed-time comparison. Calling this
an expiration date or an independent unread receipt for every player would
misdescribe the original data and selection rules.

## Maintenance pruning and text-width mismatch

MAINT 672d..691e opens a temporary random-access output, reads the existing
message file and copies only records whose first field is nonzero. It then
replaces ytRMSG.DAT and rotates the newspaper files. There is no per-record
date test or ordinary daily decrement in this selected compression loop.
A flag 1 record is globally undeliverable yet nonzero and therefore survives
this retention predicate; exhausted 0 is removed at maintenance.

The retained MAINT declarations expose a separate historical defect:
both source and temporary record layouts declare three four-byte fields and
0x48 (72) text bytes within an 86-byte record. The YT writer/reader declares74
text bytes. Maintenance therefore does not map the final two bytes through
its text variable. Short text controls cannot establish preservation of all 74
positions; no long-line maintenance execution is retained in this slice. The final two
byte outcomes therefore remain unknown; no full 74-byte preservation claim is made. This mismatch is not a
modern archive format recommendation.

## Boundaries and modern-policy separation

Static reads establish selected current binary paths and their file/field
mechanics; runtime evidence establishes actual calls' packet values and effects.
No simultaneous original-DOS writer safety, per-account delivery history,
atomic newspaper/mail save, exhaustive malformed-record policy or exact numeric
parity is inferred. Whole-program negative absence and all indirect paths are
not proved by selected byte ranges.

A modern implementation must state whether it intentionally adapts original
shared-budget broadcasts into private recipient copies or preserves the original
public shared record. It must separately define fresh consent, immutable
publication text/author, acknowledgement authority, idempotence, batch capacity,
history visibility, public newspaper atomicity, finite work and committed-save
receipts. Neither a private TEAM fanout nor the existing newer broadcast
adaptation can be silently labeled exact DOS lifetime parity.

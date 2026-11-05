# Initial-maintenance auxiliary synthesis

Bounded research only. Original YTMAINT.EXE SHA256
8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6.
The pure model is scripts/replay_maintenance_aux.py. It accepts the three before
files, a separately synthesized world, date and explicit news/scoreboard clocks.
It does not load any after-world, target auxiliary file or completed transcript.
The only path read inside synthesis is the immutable original executable, for
native length-prefixed literals and the PRINT USING mask.

## Native observations

All records are full REA/Ghidra12.1.4 read_bytes observations in rea.json. An
independent MZ relocation reconstruction matched every byte. Addresses are linear
Ghidra load coordinates; subtract10000 to obtain the main loaded-image offset.

| Address | Bytes | Evidence ID | Question |
| --- | ---: | --- | --- |
| 0x15773 | 61 | ev_3a0b3c0746aed70b357b4a152c67924a6963412830e2b7e241727177d84c5ed3 | Calendar/config day writer |
| 0x18234 | 192 | ev_9550f17a9afcabe8faaa26a90f0e047c4ee026fad6aefb08376774ef7f5765ab | Stored score writer |
| 0x17ed0 | 129 | ev_dfadb8826f9382a04985865025f0c3b8f8ec8c36010df8848e09d82ce36c2641 | Inactive score branch |
| 0x18534 | 1202 | ev_784fb33fc1253b419634f88b11a7791bcc91eac95e3137c94953a3330442d4b0 | Board headers, denominator, PRINT USING row |
| 0x19b50 | 1240 | ev_a886776fd2990236859ee7243df62b63aba4dcb08d2727d2dc09d6d442674a19 | Complete board literal/mask area |
| 0x18c90 | 2130 | ev_a711317ae9e5911f2d9234b5aff301a3fbdf14176fd4669621a9a1426f749de8 | News and revision literals |
| 0x168b3 | 107 | ev_4a7a6301cb63291e8d13531e44e2492bef79558b39712e2d4c791034464c3f41 | Message/news file rotation tail |
| 0x194e0 | 128 | ev_27960d89479193e1dcb366aa0db58e238774b51fb4149e1003c11ad19fdf9706 | Remaining Mercenary news literal |
| 0x19b2a | 12 | ev_7780b9339a4ab4e61784c452aea32e9b6301c9daf8b4798e1539d7494e5a9f57 | Inactive eight-byte numeric constant |
| 0x18148 | 236 | ev_f93603d0889daaa9c237564a9a1e0fc5402d894983432e6c4fefedcca679e2c7 | Sector defense scores and NPC ownership |

These are static observations, not execution traces. Each CLI operation owned
an ephemeral source-immutable import and completed cleanup. No MCP target remains
open and original archives were never modified.

## Synthesis rules

- Missing/empty message archive compresses to an empty YTRMSG.DAT. General message
  records, recipients, expiry and nonempty compression are not modeled.
- The old YTNEWS.DAT becomes YTYNEWS.DAT unchanged in the selected transition.
  YTNAME.DAT is preserved exactly. The new news file consists of the sampled
  news clock/date and revision followed by missing/regenerated Wanderer,
  newly created Xannoron, Xannor report, zero dynamic regeneration, Mercenary
  report and newly built Mercenary Base messages. Literal bytes are recovered
  from their original string descriptors; CRLF and DOS EOF1a are serialized.
- All50 player slots are inactive and empty, so human/team ranking rows are
  absent. The board's original headers and PRINT USING mask are reused as
  immutable program constants, not copied from an after-file template.
- Native8148+ loads sector fighter field81, multiplies by100 and accumulates
  owner-1 in7dbc and owner-2 in7dc0. The modeled world conserves10000 Xannor
  fighters, giving1000000 points; Mercenary deployment remains0. Planet ground
  troops, bank and NPC planet ownership do not enter this selected score sum.
- Native855d..8596 chooses an NPC denominator when the leading human score is0.
  Here Xannor is the sole positive score, giving exactly100.00% and0.00%.
  General NPC normalization, fractional scores, overflow and halfway PRINT USING
  rounding are explicitly not claimed.

The supported pure model rejects active players, populated inactive assets,
nonempty message archives, pre-existing/additional active planets and non-Xannor
positive defense deployments. It permits only the observed bootstrap NPC total.
These guards bound the formatter; they do not replace the caller's independently
validated world model or input provenance.

## Important inactive-score constant correction

The archived single-precision annotator labels DS8d5a as0 because its first four
bytes are zero. The actual constant is EIGHT-byte MBF double:
0000000000008081 = -1. Runtime load3f70 at7f32 consumes that double for7d8e's
8-byte score entries. Thus the inactive branch7f24..7f49 explicitly supplies-1;
it is not a mysteriously changed zero or a value inferred solely from a target.
The later8234+ writer reads the array entry, converts it to the record's numeric
string and updates the cached score field. The independent parent writer maps
that descriptor to player offset109 using the native record layout. The day
writer5773+ calls79e3 and updates configuration field81 through the shared FIELD
buffer. Parent comparison proves baseline305 ->306 and all50 caches ->-1.

The embedded data mapping used for this constant is DSoffset + file0xfd0, so
DS8d5a maps to file9d2a / loaded linear19b2a. The field's eight bytes and code
load are both retained above; do not reapply a four-byte MBF decoder to it.

## Separate verification result

First the formatter was isolated against the retained post-world only as an
outside-the-model shape comparison. The stronger follow-up passed an independently
synthesized NPC world to the auxiliary model: before inputs + the41/19 retained
TIMER inputs + raw Xannoron TIMERcdcc4c7c -> replay_maintenance_npcs.synthesize,
then replay_maintenance_aux.synthesize. No post-world was supplied to synthesis.
After-target bytes were opened only afterwards for comparison.

All1372 auxiliary bytes matched exactly:

| File | Bytes | SHA256 |
| --- | ---: | --- |
| YTNAME.DAT | 26 | af3183fabb75a3c5ae25b71abf89bd6c7e19a7470e8363214fe9b9b88923d08f |
| YTYNEWS.DAT | 309 | 1acaf18a99ffc43c85f96b375476c46a1fd25904ffc75d8a93dce829a27e313a |
| YTRMSG.DAT | 0 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| YTNEWS.DAT | 434 | 496dd8e6f9d32228c2e3b50c714a33edfa97366e1e0609e9b2a2dfd555ad041c |
| YTSCORE.ASC | 603 | e8c51ad1607e48ad85896c41c18639abc180801b76d5d0a4dbc0bc0486c03aba |

This auxiliary result alone does not prove the caller's entire568687-byte world,
port timing, arbitrary clocks/configurations, normal gameplay, live BBS behavior
or native Windows durability. Those remain separate obligations.

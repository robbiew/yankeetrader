# Route-commerce reports, populated spies and radio

Recovered 2026-10-26 against original Yankee Trader 3.6. The
[evidence manifest](commerce-dos/results.json) retains **18 completed DOS sessions,
36 full world snapshots**, auxiliary DAT snapshots, inputs, transcripts and
emulator logs. Executable copies and the archive remain unmodified. YT.EXE SHA-256:
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
This establishes a bounded research baseline, not implemented Go features.

## Nearest ports and trade forecasts

Eight commerce probes clear all sector-to-port references except ports at 101 and
107. Their six-link graph is recorded separately from explicit field overrides.
From 100, sector 101 is one directed hop away and 107 is two hops away. The second
port is named Servoa in the preserved fixture.

- Computer 14, All: reports 101 at distance 1 and 107 at distance 2, in that order.
- Computer 14, Ore/Selling: reports only 107. The displayed **B/S describes the
  player's action**, not the port's action. At 101 the player buys ore for 10 and
  sells organics for 44; at 107 the player sells ore for 30 and buys organics for 15.
- The Team filter with no membership rejects the query without moving or charging.
- Computer 16 lists `101, 107 Org -> Ore @ Profit of 49` with or without a direct
  return warp from 107 to 101. In the one-way fixture the return requires a longer
  route through 109, 110 and 100. The pair list is not proof of reciprocal adjacency.
- Computer 17 rejects a current sector with no trading port. At sector 101 it
  reports the same 49-credit spread for the adjacent partner.
- The forecast remains 49 with both 100-hold and 10-hold ships. It matches
  `(44 - 15) + (30 - 10)`, not full-ship earnings or income after travel costs.

All eight queries preserve position, turns, ship cash and inventory. They do not
execute trades. Stock depletion, price changes, cargo availability, existing cargo
and extra return hops can change achievable earnings. Modern route advice must
use the directed graph and label price forecasts honestly rather than promise
this number as guaranteed profit per turn.

Static anchors: main `1000:8804..8956` selects nearest-port filters; sub
`1f42:00b2` searches the starmap; sub2 `2e79:2693..31b8` finds pairs; sub2
`2e79:00b2..0a94` handles adjacent-profit reporting. Populated team/owner filters,
long-distance search limits and every commodity combination remain separate
boundaries; the tested output must not be generalized to them without evidence.

## Hiring and reconnecting spies

The spy probes begin at Earth with two million credits and no active spies.
Ordinary shop option 9 is used; no spy array is injected.

| Case | Saved credits | Turns | Active list |
|---|---:|---:|---|
| `intel-hire-one` | 1,667,000 | 499 | Spy 1 at 101 |
| `intel-hire-three` | 1,001,000 | 499 | Spies 1–3 at 101, 102, 103 |
| `intel-limit-four` | 2,000,000 | 499 | Four rejected; no spies |
| `intel-reconnect` | 1,667,000 | 499 | No spies after reopening the exact one-spy save |

The observed fee is **333,000 credits per spy**, with a maximum of three. A fourth
is rejected even though this fixture can afford four. The only turn charged in
these purchase probes is the one for docking at Earth. Reconnect does not refund
the fee or restore that spent turn.

The spy list is session state in this tested path. The reconnect's before-world
hash equals the purchase's after-world hash; neither credits, position nor turns
are reset to a fresh fixture. Hiring, list display and loss on reconnect are
established. Actual search movement, findings, failure probabilities and spy
notifications are not established by a populated list alone.

Static anchors: main `1000:6dbb` sets the fee; `7b11..7b33` enforces three;
`7b45..7c19` assigns the session array; `a381..a419` displays it. Future Go spy
persistence/refund behavior needs an explicit policy, particularly for disconnects.

## Radio send, abort, delivery and history

All radio messages stay within disposable original-game fixtures. The synthetic
sender is player 2 (alias Q) and recipient is player 3 (alias Enemy).

1. Computer 5 searches Enemy, confirms the recipient and accepts one line,
   `YT RADIO PROBE`. Send prints Transmission successful.
2. The previously empty `YTRMSG.DAT` gains an 86-byte record: three MBF fields
   `[1, 3, 2]` followed by the padded message line. In this observed record these
   are unread/delivery marker, recipient ID and sender ID.
3. A separate LOCAL ENEMY session reopens the sender's exact committed world and
   auxiliary files. Login displays the message, and Computer 6 displays it again
   in received history. The first numeric marker becomes zero; sender, recipient
   and payload remain unchanged.
4. A second ENEMY session reopens that exact post-read state. Login does not
   announce the message again, but Computer 6 still shows it in history. The
   message record remains unchanged with its read marker.

The abort probe types `YT ABORT PROBE`, chooses Abort and confirms. It never
prints transmission success and leaves the message file unchanged. An empty log
and TEAM without team membership are also exercised; neither creates a message.
All six radio sessions preserve actor position, turns, money and equipment.

Message history and unread delivery are distinct. Marking a message read is not
deletion or a privacy-retention policy. These cases establish one direct recipient
and one-line delivery, not ALL/team routing, third-party isolation, multiline
editing, truncation, concurrent send/read safety or eventual cleanup.

Static anchors: main `1000:93a1..9517` selects recipients; `9518..98fd` edits
lines; `9a2e..9a5e` confirms abort; `9a61` onward commits transmission.
[REA evidence](encounter-rea/commerce-radio.json), from Ghidra 12.1.4, cross-checks
nearest/pair entry bytes, the spy cap and radio send dispatch. Coordinates are
linear DOS analysis addresses using load segment 0x1000, not file offsets. The
ephemeral analysis session was closed.

## Reproduction and verification

```sh
python3 scripts/recover_navigation.py /tmp/yt-commerce-new --commerce
python3 scripts/recover_navigation.py /tmp/yt-spy-login-new \
  --source /tmp/yt-commerce-new/intel-hire-one --only intel-reconnect
python3 scripts/recover_navigation.py /tmp/yt-radio-login-new \
  --source /tmp/yt-commerce-new/radio-send --only radio-read
python3 scripts/recover_navigation.py /tmp/yt-radio-again-new \
  --source /tmp/yt-radio-login-new/radio-read --only radio-read-again
python3 scripts/verify_commerce_evidence.py
```

Each destination must not exist. DOS date/time are fixed at 2026-10-24 00:00:00.
The verifier checks world and auxiliary hashes, exact source chains, prices and
distances, one-way versus reciprocal links, fee/cap accounting, spent-turn
preservation, recipient/sender IDs, delivery markers, and repeated-login history.
Only completed emulator sessions are packaged. No Go gameplay changed.

Validation on 2026-10-26 passed the commerce, utility, hazard, encounter,
follow-up, navigation and avoid-list verifiers, all 4,682 archive checksums and
`git diff --check`. Negative controls changed a profit forecast and restored an
unread delivery marker, recomputed their hashes, and were still rejected.

# Mercenary offers and faction refusal — bounded DOS recovery

Nineteen controlled original Yankee Trader 3.6 sessions extend the nine faction
encounters in [the earlier utility recovery](../yt-navigation/UTILITIES.md).
They preserve 38 complete before/after saves, exact keys, transcripts, emulator
logs and fixture provenance under [dos](dos/results.json). No Go gameplay or
save-format changes are included in this research milestone.

## Method

`recover_navigation.py --bribes` copies the archived `fixture-team-captain`
universe into a new disposable directory for each session. It clears and rewires
the same eleven-sector graph used by the earlier navigation probes. All runs use
DOS date 10/24/2026 and time 00:00:00, then execute the unmodified original
`YT.EXE` through `LOCAL TESTER` and the preserved key feeder. Only each copied
scenario directory is mounted. The archive is never mounted or edited.

The caller begins at 100 with 500 turns, 100,000 credits and 2,000 fighters;
sector 101 holds 100 Mercenaries. The source fixture's public alias is `Q`;
this is an existing fixture label, not evidence that the quit command changed
the alias. Every probe moves to 101 and chooses B at the hostile-defense prompt.
The human control instead has ten ship fighters and defenders owned by player 3.
Two Mercenary controls start with ten and zero ship fighters respectively.

All 19 sessions complete and return to the local logon program. Every final ship
is alive at 101 with 499 turns. Only entry spent a turn; negotiation/combat did
not add one in these probes. Shields stay unchanged. Quitting unresolved
encounters preserves the defended sector and its owner rather than undoing entry.

## Observed offer boundaries

| Offer against 100 Mercenaries | Result in this recorded run | Credits afterward | Ship fighters afterward |
|---|---|---:|---:|
| Blank | Cancel; retain 100 defenders and owner -2 | 100,000 | 2,000 |
| 0, -1, 1, 100, `abc` | Insult; immediate full-force combat | 100,000 | 1,934 |
| 200 | Accepted; whole group recruited | 99,800 | 2,100 |
| 300 | Accepted; whole group recruited | 99,700 | 2,100 |
| 1,000 | Accepted | 99,000 | 2,100 |
| 10,000 | Accepted | 90,000 | 2,100 |
| 50,000 | Accepted | 50,000 | 2,100 |
| 100,000 (all available credits) | Accepted | 0 | 2,100 |
| 100,001 (over budget) | Insult; immediate full-force combat | 100,000 | 1,934 |
| 50,000.5 | Accepted with the fractional debit intact | 49,999.5 | 2,100 |

Accepted offers clear both defense count and owner. The debit is the **offered
amount**, not a computed tariff. Rejected offers do not debit credits. In these
insult runs all 100 defenders are destroyed and 66 attacking fighters are lost.
Those identical casualties are samples from these clock-controlled fixtures;
they are not a fixed combat penalty or independent random trials.

A blank line and a literal zero have different behavior. DOS numeric parsing of
`abc` reaches the insulting-offer branch. A modern integer-money frontend should
reject malformed, negative, fractional and unaffordable input explicitly, before
any mutation or random draw, rather than inheriting these surprising input rules.
A valid small offer can still be dangerous; the confirmation must say so.

The ten-fighter and zero-fighter Mercenary controls both accept 50,000, ending
with 110 and 100 ship fighters. Having fewer fighters than the defenders does
not unconditionally prevent recruitment. These are single outcomes, not evidence
that a powerless ship is guaranteed a chance to negotiate.

## Faction and planet controls

- **Mercenaries with a planet reference:** the copied sector points at planet 2,
  whose copied owner is also -2. DOS says “This planet is OURS!”, does not offer
  negotiation and leaves credits, ship fighters and defenses unchanged. This
  establishes that specific guarded-planet fixture, not every combination of
  neutral/foreign planet ownership or an orphan planet reference.
- **Human defenders, stronger than the caller:** refuse the bribe. The observed
  run retains ten ship fighters, all credits and the 100 human defenders. It does
  not establish that human refusal can never provoke combat.
- **Xannor:** refuse, immediately fight with the caller's full ship force, lose
  all 100 defenders and inflict 64 attacker losses. No money changes hands.

## Static evidence and remaining randomness

The archived runtime-aware listing at `1000:12c1..1587` separates faction refusal,
planet refusal, pre-negotiation hostility, offer validation and recruitment.
The automatic disassembly becomes incorrect after `1000:1478`: `INT 3F/AE`
consumes an inline byte which the listing treats as x86 instructions.

Two new Ghidra 12.1.4 / REA byte observations are retained in
[rea/offer-path.json](rea/offer-path.json):

- `ev_b8d0d44334b7b4d0d9f930cbfe0df93152c72bb6faecee2fd93c27497579823b`
  reads the offer comparison at linear address `0x11456` (65 bytes).
- `ev_7edd3cde37708660c771d2e1d523e2da0676bbcd4aecd89fab880a697921f5fb`
  reads the pre-offer branch at `0x11361` (151 bytes).

These coordinates assume DOS load segment 0x1000. The verifier independently
compares every observed byte against the unchanged MZ file. REA's ephemeral
session was closed without changing the executable.

Reading the original BRUN30 dispatch table, `3F/AE` consumes a signed exponent
adjustment; the offer path contains `AE 01`, followed by double addition `82`
and a comparison against the saved offer at temporary slot `80`. Together with
the preceding random draw and multiplication by defender strength, this supports
an **inferred** threshold of `defenders * (1 + 2 * RND)`, subject to available
credits. The 100-credit refusal and 200/300-credit successes fit this reading.
They do not by themselves prove exact comparison equality, all floating-point
operation order or the random distribution. No Go pricing formula has been
selected from the small sample.

The pre-offer code also contains 0.05 and 0.9 comparisons, a relative-strength
comparison and an additional value at DS:4D5E. The human-refusal path has a 0.33
comparison. This milestone does **not** establish their complete conditions or
draw order. A follow-up must resolve that flag and independently validate these
branches before claiming full original negotiation probability parity. Exact
QuickBASIC RNG and MBF behavior remain separate from modern integer policies.

## Implementation contract and next step

Before exposing BRIBE, resolve the remaining random/flag rules or explicitly
specify and test a modern negotiation policy. Bind each prepared offer to the
current ship generation, position and exact defending group. After a fresh,
separate confirmation, revalidate credits, fighter capacity, deadline and the
entire warning under the world lock. Reject changed/replayed offers without a
debit, recruitment or RNG consumption.

Accepted debit, recruitment and clearing the group must be one transaction.
Refusal/insult combat must use the existing defense battle and mine aftermath,
with actual killer attribution and rollback on any later error. Ship capacity
must be checked before removing defenders. Current mine encounters must remain
an earlier gate, and an unresolved hostile group must continue blocking ordinary
actions. Keep `B` for port acquisition outside an encounter; use explicit BRIBE
unless an encounter-specific classic binding is added safely. No new save fields
are implied by these observed rules. NPC daily movement, hiring from taxes and
planet creation are separate milestones.

## Reproduction and validation

```sh
python3 scripts/recover_navigation.py /tmp/yt-bribes-fresh --bribes
python3 scripts/verify_bribes.py
python3 scripts/verify_utility_evidence.py
python3 scripts/verify_archive.py
```

The destination must not exist. The packaged runs were collected in two fresh
batches (15 offer/faction controls and four strength/threshold controls), then
combined without changing their saved inputs/outputs. Replays need not reproduce
identical random recruitment or casualties; investigate differences rather than
rewriting the captured outcomes as deterministic rules.

The portable verifier checks all hashes, executable identity, exact declared
fixture reconstruction, key streams, completion, entry turns, debit/recruitment
conservation, combat casualty reconciliation and the two REA observations.
CI runs it without DOSBox or REA. Rehashed negative controls modifying an accepted
debit or an undeclared fixture field must still fail semantic validation.
All 4,682 original archive checksums remain unchanged. Native/live BBS acceptance
is not established by these original-DOS experiments.

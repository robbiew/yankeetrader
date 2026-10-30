# Cloak-energy purchasing and anti-cloak activation — research

This is a research milestone, not a Go gameplay update. World version 21 remains
current. Earth options 1 and 6 are still unavailable in the modern door. The
preceding scanner/manual-warp implementation was merged in
[PR #45](https://github.com/robbiew/yankeetrader/pull/45).

## Questions and evidence boundary

The 37 retained controls contain 74 before/after world snapshots and four exact
reconnect chains. The scope is Earth recharge pricing, numeric limits and defaults; anti-cloak
payment, confirmation and repeat activation; stored versus session visibility;
reconnect, turn-decay and score effects. Controlled DOS sessions use unmodified
YT.EXE, BRUN30.EXE and LOCAL.EXE, with copied worlds mounted independently in
DOSBox Staging. The original archive is never mounted for gameplay or rewritten.

| Question | Status within this slice | Witnesses |
|---|---|---|
| Price, capacity, poor/full/default inputs | Answered for tested quantities | `energy-*` controls |
| Arbitrary numeric/MBF boundaries | Partial | Fractional input and retained raw values; wider boundaries remain open |
| Paid activation, repeat and empty results | Answered | `anti-exact`, `anti-repeat`, `anti-empty` |
| Stored energy versus session visibility | Answered for existing targets and reconnect | `anti-own-full`, `anti-far`, four parent-linked reloads |
| Own display and turn decay | Answered at the tested boundary | `control-decay`, `anti-decay`, `anti-boundary-reconnect` |
| Credit and score effects | Answered for retained balances | All post-logout worlds and score caches |
| Concurrent observers and later target incarnations | Unresolved | No corresponding DOS runtime control |

The retained baseline is the existing `fixture-team-captain` world, SHA-256
`04eaf42c54d4f35c3412737e27fa968b5abcd22eb295cb5d8b45ab8045fcd0ec`.
The declarative recipe records all graph, Earth-port and player changes. Player 2
is the caller; player 3 is Enemy, initially fully cloaked. Other named active
players provide distant positive-cache controls. Each run preserves before/after
worlds, auxiliary input/output bytes, exact keyboard stream, DOS date/time,
transcript, binary hashes and completion metadata. Reconnects use the exact
parent's final world and auxiliary files.

Preparatory runs that lacked Earth's port link, and over-capacity probes whose
keyboard stream failed to leave the shop, are excluded from the retained corpus.
Corrected runs restore the declared port link and supply a separate shop exit.
This distinction matters: normal completion alone does not prove a purchase path
was exercised; the verifier also checks prompts, outcomes and conserved bytes.

## Cloak-energy purchase

Earth item 1 costs **1,000 credits per percentage point**. Stored player field 125
is a fraction, not a percentage. Buying 10 points from zero spends 10,000 credits
and saves approximately 0.1 in MBF single precision. Buying 10 from approximately
0.37 saves approximately 0.47. These decimal fractions have the expected binary
representation error; monetary balances in the tested range remain exact.

| Control | Observed result |
|---|---|
| One point with 1,000 / 1,001 credits | Balance 0 / 1; approximately 1% stored cloak |
| One point with 999 credits | Refused; balance and cloak unchanged |
| 90% plus 10 points | Full cloak; 10,000-credit debit |
| 90% plus 11, zero plus 101, full plus 1 | Over-100% message; no charge after cancelling the renewed quantity prompt |
| Zero, negative or nonnumeric quantity | Cancels without a charge |
| Quantity `1.9` | Buys one whole point for 1,000 credits |
| Blank at 90% with ample cash | Default buys the missing 10 points |
| Blank with 1,999 credits and zero cloak | Default buys one point, leaving 999 credits |
| Blank at full cloak | Default zero; no charge |
| Consecutive purchases of 10 and 20 points | Two debits totalling 30,000; approximately 30% stored cloak |
| Reconnect after buying 10 points | Stored 10% survives, without another debit |

The displayed default is bounded by missing points and affordable whole points.
Blank input adopts that default; it is not a cancellation in the DOS interface.
An over-capacity request renews the quantity prompt, clearing the queued answer.
An explicit fresh zero cancels that prompt; leaving the Earth shop is a separate
input. Docking costs one turn. The purchases themselves cost no additional turn.

All other inventory, ownership, bank and treasury bytes remain unchanged in the
retained controls. Logout regenerates score caches. The caller's saved score
minus remaining credits is 9,890,250 throughout these fixtures, even as cloak
changes: recharge adds no cloak asset value. The score constant belongs to these
fixtures, not to every player or a proposed scoring formula.

## Anti-cloak is an activation for one login

Earth item 6 checks affordability for a fixed **500,000 credits**, then asks:

> Anti-Cloaking Device works for this logon only. Buy one? [y/N]

Affirmative input pays once and runs a galaxy-wide cached-cloak clear. The output
lists affected aliases, including a target in sector 103 outside Earth's adjacent
sensor sectors. Later sensors and local encounter targeting use the caller's
cleared cache. Neither the victim's stored cloak nor their ship location changes.
A full-cloak target still has field 125 equal to one in the final world.

No and blank confirmation decline without charge or activation. Invalid input
renews the confirmation; the controlled follow-up explicitly answers No. A poor
caller is rejected before the activation confirmation. Repeat activation is
chargeable: it is not duplicate-protected installation or permanent equipment.
Activation with no positive cloak entries still costs the fixed price. Only
positive cached entries generate uncloaking notices; a second clear does not
invent another set of affected targets.

The buyer's information display reads **FAIL** while the activation is in effect.
Their stored cloak energy remains intact. Recharge during an active anti-cloak
login still debits money and changes stored energy, while the session display
continues to report FAIL. Reconnect restores normal energy display and rebuilds
visibility: the full-cloak Enemy is hidden again in adjacent sensors. It does not
refund the purchase or clear the victim's energy.

The charge reduces the caller's published score through credits alone. There is
no saved anti-cloak inventory or additional device asset value in these controls.
The original global alias notices are an observed reconnaissance capability;
this report does not treat them as evidence of a permanent reveal or as a
recommendation to expose private balances or inventories.

## Own-cloak decay side effect

The paired boundary controls start with 477 turns and full stored cloak. Docking
leaves 476 turns. A normal move then leaves 475 and approximately 0.99 cloak.
After anti-cloak activation, that same move leaves 475 but retains stored cloak
one. The session flag suppresses the usual decay write during that login.

A linked reconnect from an active purchase saved at 476 turns restores ordinary
behavior: the next move leaves 475 and approximately 0.99 cloak. This separates
the session flag from stored energy and from the normal daily-turn mechanism.
It is a native side effect to account for explicitly, not an inferred free
permanent cloak upgrade.

## Native corroboration and limits

[The complete REA bundle](rea/yt.json) contains ten complete byte observations
from YT.EXE SHA-256
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
Ghidra 12.1.4 uses an ephemeral immutable import with load segment 0x1000.
The verifier reconstructs MZ relocations and compares every retained byte with
that load image. These are static observations, not execution traces.

| Question | Native location |
|---|---|
| Earth price assignments | `0x16d3f` and `0x16d7c` |
| Recharge missing/default arithmetic | `0x1769a` |
| Recharge parsing, capacity, payment and stored energy | `0x1774d` |
| Anti-cloak affordability, confirmation and session flag | `0x178b0` |
| Positive cached-cloak clearing and notices | `0x2874e`, `0x28836` |
| Shared purchase billing | `0x17c2e` |
| Reload of stored cloak with session-cache suppression | `0x1a539` |
| Normal turn-boundary decay and anti-cloak flag gate | `0x1a712` |

Key shipped-artifact records are recharge `ev_1727a16e892fbb694fb3cf6088f965705ebd39eeff06f18a62cc9324ac9039bd`,
activation `ev_a79c0457510b0964f6dd3afdae7021d6758aa08305f6a4b0a88b0e09a2f070ec`, and turn decay
`ev_fb5636eec16d5daf1411b9fe5e31f63b4e19aa1715ea009ab6fe8e4e82c7c26e`. All remaining IDs, exact lengths and coverage
limitations are retained in the linked bundle.

Annotated historical QuickBASIC listings support interpretation of runtime calls;
automatic C output is not treated as original source. Existing ship, cloak and
ranking research remains useful background, with its earlier limitations intact.

The tested input points do not establish every MBF rounding boundary, enormous
credit balance, scientific notation, original random state or malformed save.
Concurrent DOS sessions, another observer already logged in, targets created or
replaced after activation, target reconnect during the buyer's login, and the
complete global reveal/combat/reward chain are not established by this corpus.
Death, replacement and mine damage use earlier bounded evidence; this research
adds no claim of complete purchase-plus-death parity. Live BBS acceptance and
native Windows durability remain separate.

## Proposed bounded implementation contract — not shipped here

- Add Earth item 1 and a compact recharge command with whole-point input, finite
  stored energy bounded to zero through one, exact integer debit, current docking
  authorization and a post-lock session deadline check. Preserve the recovered
  blank default in the classic shop; make cancellation behavior explicit.
- Add Earth item 6 and a compact activation with fresh cost/risk confirmation.
  Debit and stage only this login's visibility changes together. On ordinary save
  failure publish neither; on a committed durability warning retain both the
  debit and committed session state, as with existing staged spies. Success
  receipts identify the actual saved debit and scope without claiming permanent
  equipment or changing every victim's energy.
- Bind reveals to the buyer and each target's current ship incarnation. Do not
  allow stale warnings, replacement generations or concurrent retries to create
  unpaid effects. Bound traversal to validated player slots and retain current
  team, sector, life and combat eligibility checks.
- Treat repeats explicitly as another paid, confirmed activation if retained.
  State the number actually newly revealed and handle empty results truthfully.
  Reconnect ends the activation; it neither refunds money nor extends authority.
- Keep the ordinary saved cloak consumption rule in the modern implementation;
  document the intentional difference from DOS's anti-cloak decay suppression.
  Show actual stored energy alongside a clear activation status rather than
  overwriting stored energy or presenting a misleading permanent FAIL state.
- Keep the existing score-cache publication boundaries. Cloak recharge and
  anti-cloak contribute no new asset bonus. Reuse the current persisted cloak
  field; any later schema change must be justified independently, with no free
  hardware, energy, credit or reveal grants during migration.
- Validate exact/poor/full/default/cancel/repeat purchases, reconnect and observer
  isolation, target replacement, post-lock expiry, concurrent confirmations,
  rollback and committed durability failure, both interfaces and real terminals.

## Reproduction and verification

Run `python3 scripts/recover_cloak_equipment.py /absolute/new/disposable-directory`
to capture a fresh set; original binaries must remain unchanged. Run
`python3 scripts/verify_cloak_equipment.py` for the retained evidence and
`python3 scripts/test_cloak_equipment_verifier.py` for rehashed corruption controls.
The verifier freezes the declarations, reconstructs all setup and linked inputs,
checks completion and exact keyboard streams, rejects undeclared world effects,
and checks purchase, visibility, score and decay claims independently of capture
metadata. Twenty-three corruption controls, including rehashed world/transcript
attacks, challenge semantic evidence rather than
merely demonstrating a broken checksum.

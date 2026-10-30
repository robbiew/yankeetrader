# Xannor HQ victory credit reward

This research retains **38 normally completed original-DOS sessions**, exact
before/after worlds, parent auxiliary-file chains, **12 REA byte observations**,
a narrow executable model and **16 rehashed semantic corruption controls**.
It covers the three reward callers, recipient, arithmetic, reporting, repeat
eligibility and pause behavior. No Go gameplay or save-format changes are made.
This is the historical research slice. The supported modern fighter/missile
reward is now implemented; see [bounded policies and validation](IMPLEMENTATION.md).

## Finding ledger

| Question | Finding | Evidence and limits |
|---|---|---|
| Amount and recipient? | Fixed 1,000,000 passed to the current player's ship-credit helper. No team split. | Fighter/missile/plasma controls, two team actors, `sub:a886–a893` and `4b67–4baa`. |
| Eligibility for fighters/missiles? | Destroy the initially positive HQ-sector force whose prior owner was Xannor. | HQ/off-HQ, other-owner, partial, cancellation, empty and insufficient-stock controls; caller traces. |
| Does plasma enforce the same owner rule? | No. It also rewards destruction of Mercenary, human and the shooter's own fighters at HQ. | Three ordinary `+` controls, with initially positive force; `sub:b05f–b083`. This is an original gate defect, not modern policy. |
| Must the shooter or requested target be HQ? | No for missiles/plasma: the traversed encounter sector is tested. | HQ 101 is intercepted while shooter remains 100 and requested destination is 102. |
| Is an HQ planet required? | No. These reward controls have no planet at the HQ sector. | Sector links in the retained inputs; the tested reward is for sector fighters. |
| Is it once per player or pending revenge? | Neither. A prior revenge pointer does not suppress payment; a fresh restored HQ force can pay again. | Existing-queue and parent-linked restored-force controls. Reconnect with no new victory does not pay. |
| Does the full million always reach the account? | No at large balances: single rounding can increase/decrease the effective gain or erase it. Existing fractional credits are floored. | Exact native precision controls, complete runtime addition/rounding bytes and floor trace. |
| When is it saved? | After the HQ text/pause and announcement, before public/broadcast congratulations and the revenge-pointer write. | Helper/callee order; normal sessions. Interrupted-write outcomes remain untested. |
| Must a key answer the HQ pause? | No. The helper permits timer expiry; the no-extra-key control completes and pays. | Timed pause called with 99, plus the recorded delayed keyboard stream. No precise timer calibration is claimed. |
| Are other financial stores changed by the reward? | No direct bank, treasury, teammate or bystander payment. | Every planetary bank/port treasury and every nonactor account is checked. Ordinary logout recalculates scores separately. |

## Original identities and fixture method

The immutable inputs are copied into disposable DOSBox Staging mounts. Executables
are unpatched and are never executed from the archive or a live BBS directory.
All retained sessions use ordinary LOCAL logon and player attack commands, then
return normally. The initial six exploratory runs are outside this retained set.
An initial no-key pause probe paid but timed out during final logout; it is also
excluded. The retained pause control adds a later logout key and exits normally.

| Artifact | SHA-256 |
|---|---|
| YT.EXE | `c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037` |
| BRUN30.EXE | `3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8` |
| LOCAL.EXE | `bb970c43eb29fb80e7252f3968884f1c43543a5e39c6714b209ffca7dbf2d93a` |
| XANNORHQ.TXT | `72719e94dc04c655d7239e76f824b79ae6846e0f48c62148d48b9b07b9e694df` |
| Research KEYFEED.COM | `06dd2b9fcb91502185f6f4a2123ad7fdac144f47f5170df203760b86db127596` |
| Canonical before world | `cd1f9d5e99ef1d251fbbe9196ebeb21a8e401d6765419a2c7157ff729ed1cfb6` |
| Frozen recipe | `a70aa0f2ea6d4e2db0b8638df12fdeff7738c0d650486b32268e166622e4518e` |

The [frozen recipe](dos/recipe.json) and [result manifest](dos/results.json) index
every retained session. The world derives from the archived surrender-Xannor
before snapshot. Actor 2
starts at sector 100; ranged targets are sector 101, with 102 used for through-HQ
routes. The ordinary fighter control attacks 10001 with two million carried
fighters against one defender. Missile/plasma controls launch 20 missiles or one
bolt against one defender. Negative controls vary only declared fields/commands.
Team probes use the original overlaid metadata and membership layout. Actor 3's
logon mapping and account are explicit, so alias changes cannot fake the recipient.
No reward control destroys an HQ planet.

DOS DATE/TIME are recorded for October 24, 2026 at midnight. Parent follow-ups
advance to 00:02 and inherit **every retained DAT/ASC auxiliary file** and the exact
world, with only their declared patches. `restored-hq-repeat` explicitly restores
one HQ defender to the parent's defeated world; this is a synthetic restoration
control, not a claim about an untested original daily regeneration sequence.

Every ordinary session has a 60-second bound. The pause-expiry probe has 180 seconds
and a long declared keyboard delay, then exits normally. Timeouts are never counted
as completed sessions. Each case retains compressed worlds, exact keys, transcript,
clocks, losslessly compressed auxiliary before/final payloads, and executable/file hashes. The verifier
rebuilds all setup bytes independently from the canonical world and frozen recipe.

These are diagnostic edited worlds, including unusually large balances and
non-Xannor HQ occupants; they do not prove ordinary play can generate every input.

## Callers and location/owner checks

Only three direct calls to helper `1f42:a7de` were found in the three annotated YT
modules under `archive/analysis/yt-combat`:

- Fighter victory, `main:1248–1272`: the preceding path has removed all defenders;
  current sector equals HQ, and the saved defending owner equals −1.
- Missile victory, `sub:72e3–731b`: remaining fighters are zero, traversed sector
  equals HQ, and saved prior owner equals −1. The owner is saved before sector
  ownership is cleared. Own fighters are skipped by the missile route.
- Plasma victory, `sub:b05f–b083`: remaining fighters are zero and traversed sector
  equals HQ. Entry to that combat branch requires initially positive force, but
  there is no equivalent owner guard.

The native controls distinguish every owner path from an empty-force shortcut.
Empty, partial, aborted, over-stock missile and off-HQ cases do not pay. The ranged
through-HQ controls both pay with requested destination 102 while the encountered
HQ is 101. The original plasma defect is confirmed through ordinary `+;101;1`,
not an internal helper call or patched executable. No additional reward producer
was found in this bounded direct-call search; indirect/bulk writes remain outside
that negative claim.

## Financial path and precision

`a886–a893` copies the exact single constant 1,000,000 from DS:abf8 and passes its
address to `4b67`. That helper reloads the current actor record through DS:1c3c,
reads descriptor 1970 (player credit field 81), adds the argument using single
operation 3F81, floors it via 3D03, writes the result through the same argument and
back to the player, then PUTs the record immediately. There is no cap, team split
or reward latch in that helper.

The runtime's addition rounds to 24 significant bits, with ties to even
(`BRUN:b46b–b483`). The [narrow model](recovered_rules.py) uses exact rational input
and models positive normal-single addition followed by floor. It is not a general
MBF interpreter, and it does not emulate unrelated combat or all runtime operations.

| Actual stored before | Saved after | Effective gain |
|---:|---:|---:|
| 0 | 1,000,000 | 1,000,000 |
| 1,005 | 1,001,005 | 1,000,000 |
| 1,005.75 | 1,001,005 | 999,999.25 |
| 16,777,215 | 17,777,216 | 1,000,001 |
| 1,073,741,824 | 1,074,741,760 | 999,936 |
| 1,073,741,952 | 1,074,742,016 | 1,000,064 |
| 8,796,093,022,208 | 8,796,094,070,784 | 1,048,576 |
| 17,592,186,044,416 | unchanged | 0 |
| 8,999,999,815,811,072 | unchanged | 0 |

The last case requests the modern 9-quadrillion limit, which the DOS field itself
cannot represent exactly. The table uses its actual persisted before value. A
fixed bonus announcement is therefore not evidence of a full credited million.
Every nonactor's ship credits, all 100 planetary banks and all 1,000 port treasuries
are compared independently. Logout-generated scores can change after combat and
payment; they are not a separate reward balance or an unchanged-field assertion.

## Pause, reporting, revenge and repeat timing

The helper displays XANNORHQ.TXT, renders `[PAUSE]`, then calls the timed wait
`94fd` with 99. The wait polls the keyboard/remote input and the timer; it can
return without a key. `fighter-pause-auto` deliberately sends no extra key during
the pause interval, retains the bonus receipt, saves the reward and exits normally.
This corrects the earlier revenge recovery wording that a key must be supplied.

The fixed bonus notice precedes the credit helper's immediate record PUT. Three
sound calls follow. Public separator/congratulations/separator lines and three
broadcast records are then written; each broadcast uses −2/−2 addresses. Finally,
sector 21 overlay field 105 is saved with the current actor's player-record ID,
queuing revenge. These are separate original file writes, **not an atomic DOS
transaction**. Mid-write interruption/recovery behavior has not been exercised.

An existing revenge pointer 3 neither suppresses actor 2's payout nor changes its
recipient: the pointer becomes 2 afterward. The parent-linked reconnect has no new
victory and receives no new award. After a declared one-fighter HQ restoration,
the same player receives another million and a fresh public/broadcast block.
Thus the recovered scope is payment per qualifying victory, with force/caller
conditions preventing an empty or replayed victory from qualifying. No lifetime
per-player bounty flag was found in the helper/call sites.

The verifier compares **new** public and broadcast effects against each case's
input history. An inherited congratulations cannot satisfy a second victory.
It requires the exact new three-message broadcast block, rejects invented
broadcasts on negatives and checks its recipients. Public text identifies the
victor; it does not print the ship's account balance. Reconnect does not consume
or duplicate a monetary award just because the revenge pointer remains pending.

## Historical bounded implementation contract — proposed by this research

- Reuse supported fighter/missile HQ-victory hooks and require actual prior Xannor
  ownership plus removal of a positive defending force. Do not infer eligibility
  from HQ coordinates, a news receipt or an existing revenge pointer alone. Do
  not enable unimplemented plasma equipment as a side effect of this milestone.
- Pay only the acting current ship/account, using exact integer credits. A proposed
  safe policy is `credited = min(1,000,000, MaxMoney - balance)`. A full account
  receives zero, a near-full account receives only available capacity, and any
  receipt must report the actual credited amount. This cap is a modern design
  choice; DOS neither capped nor accounted exactly at these values.
- Commit force removal, bounded reward, revenge, scores, public notice and any
  subsequent attack/death aftermath in the existing locked transaction. A failed
  callback/validation changes nothing; a committed durability failure is recovered
  from saved state instead of replaying payment.
- Give each new qualifying restored-HQ victory its reward, while repeated
  confirmations, stale ship generations, empty targets, partial losses and normal
  reconnects do not pay. Preserve public/private boundaries and live account
  identity; do not introduce a separate redeemable bonus token.
- Validate full/near-full accounts, actor/teammate distinction, remote encounters,
  simultaneous contenders, rollback/replay, generation invalidation, committed
  durability and any required save migration. Update README's playable status.

These policy probes in the executable model are analyst proposals, not
observations of DOS behavior. The later [implementation](IMPLEMENTATION.md) adopts
the bounded payment and atomic-save policies while preserving existing score-cache
publication instead of publishing scores during each combat payment.

## Verification and reproduction

```sh
python3 scripts/verify_xannor_hq_reward.py
python3 scripts/test_xannor_hq_reward_verifier.py
python3 scripts/verify_xannor_revenge.py
python3 scripts/verify_archive.py
# Requires the already-installed DOSBox Staging; destination must not exist:
python3 scripts/recover_xannor_hq_reward.py /private/tmp/yt-hq-reward-new
```

Validation covers canonical setup, all parent worlds/auxiliaries, original binary
hashes, real clocks, normal completion, exact key streams, caller gates, current
recipient, single-precision arithmetic, financial noninterference, fresh reporting
and MZ load mapping/relocations for every retained byte. The 16 corruption controls
rehash altered evidence so failures must reach semantic checks. All 4,682 original
archive hashes remain intact. No Go gameplay, live BBS or native Windows acceptance
is claimed by this research-only slice.

## Evidence index and remaining limits

The [complete REA records](rea/target-paths.json) retain subject/profile hashes,
provider identity, bytes, completeness and limitations. They are **static byte
observations**, not execution traces; the 38 DOS sessions provide runtime evidence.
Ghidra linear addresses use load segment 0x1000. YT.EXE has a 0xe00-byte MZ header,
while BRUN30 uses 0x200. The verifier applies relocations independently.

The scope establishes the three observed callers and tested boundaries. All
possible routed/faction/planet combinations, negative or malformed balances,
precise pause timing across midnight, binary interrupt atomicity, complete DOS
numeric overflow, statistical RNG parity and native/live operational acceptance
remain outside this milestone. There is no new claim of complete game parity.

| Range | Linear address / bytes | Evidence ID |
|---|---|---|
| reward | `0x29bfe` / 472 | `ev_a9b9d9b87587df1f2356bccde40fdd319e5b16f798e22d379ac0b149e8e7c6f0` |
| fighter-gate | `0x111ee` / 156 | `ev_8daa63653ff99f24801d7783b1c0a2cf57df628e8a21c9c3d485beba3e52a536` |
| missile-gate | `0x266b0` / 176 | `ev_f19e81a0675c8809efa37ac5580ea07cfa6e7c9332e7ce09cf5e6106c53bdd6b` |
| plasma-gate | `0x2a430` / 133 | `ev_4bcd1bf001667b51b29be1ed0fabe82ee86b6275647c91ed6ad7bfc9db9dfa7f` |
| credit-helper | `0x23f87` / 70 | `ev_c0b8fbba6521d37583120e77bd6568bf3a96aba5b724b3f96b6aa0546136302c` |
| pause-helper | `0x2891d` / 97 | `ev_8c9a2c3ae490493d42ee7474b1a319055fb48cba95d8e51fb23386db00246061` |
| million-constant | `0x36ea8` / 4 | `ev_afc86c6a18a9d5920837407838ed302b77ec896f99250effcb2a0c463a6a3f96` |
| fighter-before-gate | `0x11170` / 126 | `ev_b9ad7af93a61380ff7b5d79a5e87b2ea7844203c8f9c852dbe4da510fda6d980` |
| plasma-positive-entry | `0x2a217` / 57 | `ev_75279c8369642e124cc41bbc25d542bb8988fe0966d9f6ee239035e04f16e89c` |
| runtime-dispatch | `0x1038d` / 396 | `ev_3d057849ccb0d9cfe69764c83ea0276f2830fd959126a3b0f9efac0da45549b1` |
| runtime-floor | `0x1acb2` / 180 | `ev_567123d41857df939d326c9daf676249df6b745ddf6c8bd7b563373a125605f5` |
| runtime-single-add | `0x1b369` / 316 | `ev_a9b4d6f12e5517aed0b59c419f808f9d13b0c13c7adb8794afa662d9dfb14620` |

# Xannor direct-combat turn bonus

The newspaper inventory found an original bonus announcement with no corresponding
Go mechanic. This follow-up recovers the award before enabling that report.

Target is original DOS 3.6 YT.EXE, SHA-256
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
Only disposable copied DOS worlds were executed; no archive executable or live
BBS save was modified.

## Confirmed rule

Direct sector-fighter combat against the Xannor grants one turn per complete 200
Xannor casualties, limited to the room below the daily turn allowance:

```
credited = min(floor(actual Xannor fighter casualties / 200), daily cap - current turns)
```

No award is made when this is below one. The original announcement records the
**actual credited turns**, including a capped award, and the actual direct-fighter
casualty count. It is not based on the initial enemy group size or a cached total.
The original CHANGES.TXT describes this rule at lines 511–513; the cap setting is
mentioned at lines 210–212. The modern game currently has a fixed 500-turn daily
allowance, so its cap is 500 rather than introducing a new configuration option.

## Native observations and limitations

`rea.json` preserves REA Ghidra loaded-byte observations. The selected
`0x11028..0x111ad` region corresponds to main `1000:1028..11ad`:

- `1028..104f` skips the bonus path when the attacker has neither fighters nor
  shields, entering ship-destruction handling instead.
- `1052..1062` requires positive accumulated defender casualties; no test of
  complete sector victory intervenes before the award.
- `10b9..10c4` selects owner -1, The Xannor.
- `10cc..1104` divides casualties by the double constant 200, converts to an
  integer and limits the result to the remaining daily allowance.
- `1107..112c` requires at least one and saves the incremented turns.
- `113d..11a1` constructs the receipt and public collected-bonus announcement.

The MBF64 constant at loaded `0x32ba8` is `0000000000004888` (200).
`archive/analysis/yt-combat/runtime_evidence.py` independently identifies the
`3F/88` runtime operation as double SI/DI division. The floor interpretation is
corroborated by the 199/200/399/400 runtime controls, not merely an opcode guess.
An unrelated retained read at `0x168f8` is not used to infer the rule. All retained
reads are checked against an independently relocated MZ image.

The cap loading/sanitization paths in the annotated sub listing (`bdea..bdf3`,
`bf6b..bf95`) support the interpretation of the original configurable allowance.
These were not new runtime configuration controls. Exact MBF behavior outside the
small integer boundaries remains unclaimed; the Go rule uses exact integer math.

## Eleven normally returned DOS controls

`dos/` contains complete before/after worlds, before/after auxiliary snapshots,
raw logs, input keys, clock files, return markers and hashes. The runner reuses
the copied-world capture engine with a separate recipe and explicit patches.
No timed-out session is admitted as a successful control.

| Control | Result |
| --- | --- |
| kills-199 | 100 turns stays 100; no announcement |
| kills-200 / kills-399 | 100 becomes 101; one credited turn |
| kills-400 | 100 becomes 102; two credited turns |
| cap-one | 1,000 kills at 499 turns credits one; ends at 500 |
| at-cap | 1,000 kills at 500 credits nothing; no announcement |
| mercenary / player-defense | 400 casualties of another owner give no bonus |
| partial-escape | Starting 100,000 Xannor, 1,000 attacking fighters: 1,504 direct fighter casualties credit seven, leaving 107 turns; attacker fighters reach zero while shields remain 11,069 |
| missiles / plasma | Destroying 400 Xannor with either weapon spends one launch turn (100 to 99), without a bonus |

The `partial-escape` recipe name describes the intended losing fighter exchange,
not a claim that DOS changed sector: the retained DOS ship remains in sector100.
The original subsequently clears that defense during its shield response. This
case establishes that reward is based on direct-fighter casualties even without a
winning fighter exchange. It does not establish parity between that DOS shield
response and the modern emergency-escape policy, which remains unchanged.

The human-owner control explicitly declines surrender and proves all 400 defenders
were destroyed; accepting a surrender is not treated as a casualty control. The
verifier independently requires the exact shell-return marker, raw normal-return
message and matching decoded transcript in addition to metadata flags.

The independent verifier compares the saved turn balance and exact bonus lines,
ownership/casualty controls, valid return markers and artifact hashes. Eleven
corruption variants reject changed saved turns, a spurious capped announcement,
changed casualty reports, a false human surrender control, missing return markers,
missing normal-return output, native-byte corruption, and zero/one-byte native
code/constant observations, including self-consistent length metadata. Native
read addresses, requested/returned lengths and parameter contracts are fixed.

```sh
python3 scripts/verify_xannor_turn_bonus.py
python3 scripts/test_xannor_turn_bonus_verifier.py
```

## Go implementation and save compatibility

Confirmed direct `BREACH`/classic sector fighting, including forced fighter combat
following a rejected bribe, credits `floor(DefenderLosses/200)` for owner Xannor,
within the fixed 500-turn allowance. Entry spends its movement turn before the
bonus cap is measured. Partial modern battles still qualify; the existing escape
policy is preserved. Successful paid recruitment, human/Mercenary casualties,
missiles and plasma do not receive the reward. Xannor HQ credit rewards are a
separate existing mechanic and can occur in the same victory.

The credited amount is part of `DefenseOutcome` and printed after the authoritative
save succeeds. A typed combat journal record stores alias, sector, actual credited
turns and direct defender casualties. It is saved with casualties, ship turns,
HQ settlement and mine aftermath. Stale/replayed confirmations cannot pay again.
Later mine death keeps the actual credited turn balance; replacement does not
refill it. Conservative journal-sequence preflight remains before battle mutation.

Schema **32** adds this operation to the journal's validation contract without a
new player/world balance field. Supported schemas 1–31 upgrade without replaying
old battles or backfilling rewards. Pre-32 saves claiming the bonus event are
rejected; older binaries cannot load schema32. Stop the door, back up data and
upgrade all nodes together. See the sysop guide for rollback requirements.

Model/store tests cover rounding boundaries, cap/entry ordering, partial escape,
fatal mine aftermath, excluded owners/weapons, exact public snapshots, migration,
replay and transaction rollback. The terminal smoke covers compact/classic normal
and capped awards, cancellation, forced-bribe combat, newspaper display and
reconnect without repayment. Native Windows runtime/crash durability and live-BBS
acceptance remain separate from cross-build and local simulated-terminal tests.

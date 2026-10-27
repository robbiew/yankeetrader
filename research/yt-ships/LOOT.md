# Loot and ownership transfers — DOS recovery, 2026-10-27

Recovered from unmodified Yankee Trader 3.6 using **37 normally completed DOS
sessions, 74 compressed before/after saves and eight REA static byte observations**.
There are 32 successful ship-attack sessions (one also kills the attacker in
mine aftermath) and five negative controls. Four initial duplicate pilot runs
are not included in this packaged count. No Go gameplay rules changed here.

Original `YT.EXE` SHA-256:
`c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
DOSBox Staging 0.83.0 runs copied fixtures only; neither the archive nor a live
BBS is mounted. DOS date is 10/24/2026; time is midnight except the four named
clock variants. Source and template hashes, all numeric patches, keys,
transcripts and emulator-log hashes are in `loot-dos/results.json`.

## Salvage sampling

The runtime-aware listing at `1f42:2e9c..2f47` samples these six values in order,
even when a stock is zero:

```
new holds = INT(RND * victim holds)
credits   = INT(RND * victim credits)
missiles  = INT(RND * victim missiles)
plasma    = INT(RND * victim plasma)
ground    = INT(RND * victim ground forces)
mines     = INT(RND * victim carried mines)
```

Each value gets a separate draw. `INT` on these nonnegative products truncates
downward; there is no guaranteed minimum or fixed half-share. Actual DOS uses
single-precision MBF arithmetic, including intermediate rounding. This formula
is the recovered algorithm, not a claim that the modern random generator must
reproduce the DOS sequence or that these sessions establish a statistical
uniformity test.

Controlled midnight attacks use a defenseless, visible target so fighter/shield
rounds do not consume additional random draws. With all other inputs held fixed,
victim cash 0, 1, 2, 3, 10, 100 and 10,000 yields salvage 0, 0, 1, 2, 7, 76 and
7,675 credits. All inventories are sampled before capacity handling and receipts.
Victim weapons 41 missiles / 43 plasma / 47 ground / 5 mines yield 4 / 31 / 30 / 2.
Changing those four stocks to 100 each yields 10 / 73 / 64 / 45, consistent with
independent scaled/truncated draws. Different starting DOS clocks produce
several different credit/weapon outcomes, including zero salvaged mines.

The large-balance control starts both ships with 100,000,000 credits. The winner
saves 176,753,744, while the receipt uses scientific notation. This is evidence
of MBF quantization, not an exact-integer fixture or proof of a new minting exploit.

## Holds expand the ship; cargo rides in those new holds

The sampled new holds are capped by `maximum holds - winner's current holds`
(`1f42:318b..31bc`). They are added to the ship's installed hold capacity, rather
than being constrained by currently empty cargo space. At the configured maximum
of 1,000 holds, no holds or cargo are recovered, but cash and weapons still are.

Cargo is then sampled from the victim's original holds, without replacement,
for the number of recovered holds (`1f42:31ec..33b9`). The random integer helper
at `1f42:1ad9` chooses `INT(RND * remaining holds) + 1`. The caller makes it a
zero-based index and selects ore, organics, equipment or an empty hold from
remaining category counts, decrementing the selected population and total.
Salvaged cargo therefore fits inside the newly recovered holds. It is not three
independent cargo-percentage draws.

With a 100-hold victim carrying 11 ore / 23 organics / 37 equipment:

| Winner before | Winner after | Cargo gained |
|---|---|---|
| 10 empty holds | 88 holds | 9 ore / 17 organics / 30 equipment |
| 10 holds full of ore | 88 holds | the same cargo, in addition to the existing 10 ore |
| 990 holds | 1,000 holds | 1 ore / 3 organics / 4 equipment |
| 999 holds | 1,000 holds | 1 equipment |
| 1,000 holds | 1,000 holds | none |

Monocargo controls fill every victim hold with ore, organics or equipment. Each
yields exactly 78 of that commodity alongside 78 new holds. An empty victim ship
still yields the same 78 new holds with no cargo. These controls distinguish
hold recovery from filling existing free capacity.

`loot_rules.py` is an injected-RNG research model of this shape. The verifier
checks controlled model boundaries; it does not replay a captured DOS RNG stream.
The modern engine's eventual implementation should retain exact integer money
and must deliberately handle its configured equipment limits.

## Ordinary port titles and treasury

The death routine transfers personally owned ordinary ports to a valid human
killer, sets both the owner field (97) and its paired field (101) to that killer,
and updates cached counts. The treasury stays on the captured port; it is not
paid to the dead owner as in a voluntary buyout.

Two victim ports with treasuries 777 and 333 transfer to the attacker with both
balances intact. A third account's 555-credit port stays untouched. If the killer
already owns a third port, their count grows from one to three. In the follow-up
collection session, the killer receives the combined 1,110 credits; saved cash
becomes 9,790 = initial 1,005 + salvage 7,675 + captured accounts 1,110. Turns stay
500 throughout the direct attack and collection.

**Cached-count defect:** if the victim's cached ownership count is zero, DOS
skips its entire port scan, leaving those same two ports owned by a dead account.
The normal and zero-count cases differ only in that count. This is a controlled
consistency gap, not proof of an ordinary player-accessible counter-forging
exploit. Modern settlement must derive ownership from the authoritative ports.

## Planets, sector fighters and team membership

Active-planet controls use real planet records, nonzero name lengths, production,
banks, ground defenses and linked sectors. The victim's planet remains owned by
the dead account with its 1,000-credit bank and defenses intact. The killer's
2,000-credit planet and a third account's 3,000-credit planet also remain intact.
All three complete planet records remain byte-identical through the death.
The first inactive-planet probes are retained as weaker controls and are not the
basis of this conclusion.

Deployed sector fighters change differently. The victim's remote 123 fighters
retain their quantity but switch owner from player 3 to **-2 (Mercenaries)**.
Another account's 234 fighters and the killer's 345 fighters are untouched.

The dead victim's team ID becomes zero and their roster slot is cleared. When
the victim was captain, DOS leaves the old captain field until the established
visiting-member succession path repairs it. If the victim was the last member,
the roster becomes empty while the old name/captain metadata remains. An empty
roster makes the DOS team inactive. Neither stale captain metadata nor lingering
team names should become a second membership authority in Go.

## Attacker death in mine aftermath

`loot-live-chain-death` uses the earlier Earth-mine scenario's ship values and
adds distinguishable personal assets. The attacker kills a one-fighter,
one-shield ship carrying 100 mines, salvages 7,904 credits and 58 mines, then dies
in the victim's dropped minefield. The controlled victim has zero holds, matching
the earlier archived scenario; this probes cleanup rather than proving a naturally
reached cooperative farming cycle. The attacker record saves self killer ID 2,
sector zero and zero holds. This is the original self-attributed cleanup branch;
it is not a newly tested explicit suicide command or enemy-retaliation attribution.

The attacker's two ordinary ports become unowned, their 777/333 treasuries clear,
and their cached count becomes zero. Their active planet and bank still remain
owned by account 2. Their deployed fighters become Mercenaries. A third owner's
port/treasury is untouched. Earth retains 60 mines, independently reproducing the
already documented protected-spawn defect. Go must suppress hazardous drops at
Earth, and preserve correct cause/killer identity through chained effects.

Five negative controls remain explicit: targeting one's own sector makes the
**missiles** self-destruct, without killing the ship; mine-at-login probes with
100 and 10,000 mines instead engage emergency warp and escape. Their scenario
names include attempted self/fatal paths, but the saved outcomes do not establish
those deaths or asset cleanup. Only the actual chained death supports the
self-attributed cleanup conclusion above.

## Evidence and reproduction

- `loot-dos/`: compressed saves, keys, transcripts, emulator logs, common baseline
  and manifest for all 37 completed scenarios.
- `loot-rea.json`: eight static observations from the original loaded image:
  initial sampling, cash receipt, hold cap, cargo loop/random helper, death
  ownership scan and delay helper. Evidence IDs and provider limitations travel
  in the bundle. These static bytes do not themselves prove execution.
- `scripts/verify_loot_evidence.py`: reconstructs every input from the archived
  fixture/template and numeric patches; verifies all hashes, completed returns,
  concrete stock/ownership outcomes and model boundaries. It independently
  reconstructs DOS loader relocations to verify all eight REA byte observations.
- `scripts/recover_loot.py`: replay only in a new disposable directory. It refuses
  an existing destination. `--only` selects named scenarios. Some case names
  preserve unsuccessful hypotheses; consult the outcomes and negative controls.

```
python3 scripts/recover_loot.py /tmp/yt-loot-replay
python3 scripts/verify_loot_evidence.py
python3 scripts/verify_archive.py
```

The replay performs the same 37 scenarios in batches of four independent processes. It
uses no modified game executable, patched RNG, privileged game helper or live
BBS. Original binaries/data remain in the archive; only copies run under DOSBox.

## Modern implementation implications and remaining limits

The internal Go duel and precomputed credit-transfer helpers remain unchanged.
They do not yet implement sampled holds/cargo/weapons or these estate rules.
The temporary lifecycle policy currently retaining team membership/port titles
must be replaced by the complete settlement transaction before attacks are
exposed. Keep the existing generation checks, integer money, recipient capacity
checks and all-or-nothing rollback; consume each awarded resource once.

Before combat is enabled, implement derived ordinary-port capture versus
self-attributed release, team removal/access revocation, planet retention,
Mercenary defense conversion, protected-Earth drop rules and inventory settlement
in the same transaction as damage/death. Validate post-death replacement and
reconnect against those effects.

Remaining unknowns include NPC/deleted-killer branches, configured nondefault
limits, fractional or corrupt inventory, equipment-limit overflow, exact RNG/MBF
replay, statistical distributions, explicit suicide, enemy retaliation combined
with estate cleanup, live-BBS acceptance and the complete cooperative farming
chain. No production attack or hazard command is enabled by this research.

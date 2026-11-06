# Complete before-only active-planet and foreign-route replay

The ten [active-planet/foreign-route fixtures](OCCUPIED_ROUTE_CONTROLS.md) now
have complete before-only synthesis: **30 observations × six paired targets =
180 complete comparisons / 1080 individual files, zero byte mismatches**. Each
run calculates all 4151 world records and five auxiliary files before opening
expected outputs. Raw timestamps, numeric-zero residues, original receipt labels
and every side-file byte are compared without masks or corrections.

This closes the preceding selected-fixture integration task. It adds no Go
feature, dependency, DOS save importer or save-format change. Bounded production
gameplay and save **35** are unchanged. The historical initial/collision replay
APIs retain their existing admission boundaries and results.

## Explicit input and read boundaries

`synthesize(before_files, inputs)` accepts exactly three raw before files and
frozen typed inputs. Ten before-world SHA-256 values admit the measured contexts;
their labels are not used to select outcomes. Unknown worlds and altered name or
old-news files fail closed. No output fingerprint, observed group position or
captured RNG state is used to construct modeled bytes.

Inputs include independently source-qualified startup, phase, per-port and text
clocks, a chronological helper TIMER schedule, and separate date/raw TIMER-minute
pairs for each active planet in ascending physical-record order. Planet clocks
are sampled before their own economy update; they are not copied from an after
record. Removing or reordering a clock, fabricating a caller, using mutable rows
or leaving a helper sample unconsumed fails.

Every `rng_raw` field is discarded before creating these inputs. The full stream
calculates old states, retained low bytes, reseeds and draws. A separate audit
checks **1872 helper-entry/final scoreboard RNG witnesses** across all thirty
observations. Poisoning raw witnesses leaves inputs and output unchanged, while
the audit rejects them. Core read guards permit only the immutable original
YTMAINT executable; target files, trace/news captures, manifests and recipes are
not read during synthesis. The separate comparison-side fixture loader and
reporter open retained recipe/expected files outside that boundary.

## Ordinary economy and source rounding

The new `replay_maintenance_active_planets.py` models only the measured clean
ordinary slots 2/3: prior timestamp 305, three rates 1000, ground 500000, empty
stocks/bank/other fields and owner -1 or 0. Each has a real name and one sector
link. Arbitrary rates, bank bonuses, surplus replacement, unknown owners and
selected plague/civil-war damage are rejected.

Offset 41 is the planet's last production timestamp, not a creation date. The
source date advances it to 306. The raw TIMER/60 sample can contain a tiny
fraction; the single elapsed result is about 1.000000596, not exactly one day.
Modeled cargo stocks become 1000.0006103515625 and fighters 3000.001708984375;
missiles retain the corresponding fractional elapsed amount. Whole ground becomes
505000 and rates become 1010. Fractional stocks and the actual raw TIMER bytes
matter to full equality even when those rounded integer summaries look ordinary.

Every active planet evaluates the original three event predicates and consumes
three draws, despite selecting no event in these low-production contexts. No
observed seed replaces those draws. One active planet derives first-helper state
`d61ece`; two derive `48839b` from startup `00c805`. This naturally shifts actual
placement candidates and reproduces the occupied Wanderer/Base rejection loops.
The earlier forward-dated pilots are not admitted inputs to this profile.

## Combat, shared pursuit and the Mercenary tail

The neutral Route Haven branch uses positive strong ground and the original
one-ground/1–1000-Xannor exchange, continuing until the attacking group dies.
All nineteen attacks and twenty-five spent ground units are calculated from the
stream: ground ends 504975; actual Xannor losses total 5978. Ground never reaches
zero, so production damage, capture/deletion and loot are not guessed.

Foreign defense at sector 854 follows the already recovered whole-force source
batches: 5000 only when both remaining sides exceed 5000, otherwise 500, switching
to 1 when either falls below 500. `RND <= .5` damages defenders; the other branch
damages Xannor. Direct synthetic boundary tests exercise the exact tie and strict
500/5000 thresholds without claiming new DOS executions at those exact ties.
Owner-zero force is skipped and remains physically present.

**A defense victory clears shared pursuit.** In the 37-Mercenary fixture, group 2
dies after destroying ten defenders. Group 3 destroys the remaining twenty-seven
and survives with 1390. Source `7813–7818` clears the shared preferred output to
zero when defenders die; group 4 therefore performs its candidate scan and uses
its new fallback. Retaining sector 854 would preserve news and total force but
produce wrong later positions and helper-entry states. A regression checks this
clear directly, alongside the full-file and independent RNG comparisons.

The larger defense fixture derives 4852 Xannor and 2475 Mercenary losses. The
surviving 97525 Mercenaries later move from 854 to 2689 using their own eager
movement gate and helper TIMER. Their source departure zero remains `00002800`.
No new Mercenary combat, mines, stock pickup or occupied-origin departure is
admitted by this narrow tail. Forces are conserved by actual physical owner,
rather than counted again through repeated references.

Public events are produced from modeled rounds/counters in source order. The
original `Mercenaries: lost N, dstrd M` counters and misleading `Plyr`/`Xannor`
suffixes are preserved, not corrected or interpreted as invented human deaths.
The suffix follows calculated battle aftermath. Scores derive actual saved
faction forces; the nonzero Mercenary percentage is formatted from those scores.
Private mail stays empty, names/old news retain the original rotation/copy rules,
and console-only movement does not become public or private news.

| Fixture | Helper 1 / helper 2 | Calculated draws | Final RNG |
|---|---:|---:|---|
| Wanderer old occupied site | 41 / 19 | 22794 | `26cccf` |
| Two old occupied sites | 41 / 19 | 24697 | `2973ec` |
| Base old occupied site | 41 / 19 | 22794 | `26cccf` |
| Friendly route planet | 41 / 19 | 22794 | `26cccf` |
| Neutral route planet | 42 / 19 | 201 | `1a52bc` |
| 37 Mercenary defenders | 41 / 19 | 20664 | `44f2dd` |
| 100000 Mercenary defenders | 42 / 19 | 5007 | `67487a` |
| 37 neutral fighters | 41 / 19 | 25892 | `36bef9` |
| Actual Wanderer rejection | 42 / 19 | 25495 | `5bc082` |
| Actual Base rejection | 42 / 19 | 22795 | `53d356` |

These are derived outcomes, not branch selectors or configured draw budgets.
The neutral planet's very short stream reflects fatal-edge scan suppression and
shared pursuit, not omission of required player scans by observation.

## Additional source evidence

Two complete REA/Ghidra 12.1.4 reads fill gaps between retained source windows:

| Address / length | Covered source gap | Evidence |
|---|---|---|
| `0x11111` / 699 | Elapsed time and resource/bank-rate preparation through `0x113cc` exclusive | `ev_2e06f9f25d91b7f196eee6e8a7ab3e55dc4d4d2530bf61e5617e851faf829ec4` |
| `0x17691` / 229 | Defense receipt construction through `0x17776` exclusive | `ev_8d5de6403ec15a5956a82566f983bfa6c58fb99b42ec46c5797dc3e7041c2e99` |

[The immutable packet](occupied-replay-native/rea.json) contains all 928 bytes.
Its SHA-256 is `107dd59cca0e57ade5f590df37b178621abc999f086574de97ad6d83332d0fd7`.
The independent verifier reconstructs every relocated byte from original YTMAINT
SHA-256 `8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6`.
Existing [event/economy source windows](../yt-plague-civil-war/RECOVERY.md),
[mobile defense/source order](../yt-xannor-mobile/RECOVERY.md) and
[occupied-control native evidence](OCCUPIED_ROUTE_CONTROLS.md) remain unchanged.
These static reads are not new execution traces. CLI analysis used the existing
JDK via per-process environment and closed its private sessions on completion;
no installation or configuration was changed.

## Reproduction and limits

```sh
python3 scripts/verify_maintenance_occupied.py
python3 scripts/verify_maintenance_occupied_replay.py
python3 scripts/test_verify_maintenance_occupied_replay.py
python3 scripts/test_replay_maintenance_active_planets.py
python3 scripts/test_replay_maintenance_occupied_combat.py
python3 scripts/test_replay_maintenance_occupied_aux.py
python3 scripts/test_replay_maintenance_occupied_records.py
python3 scripts/replay_maintenance_occupied_records.py \
  --output /tmp/occupied-record-replay.json
```

All **116 new tests** pass. Coverage includes exact repeated controls, raw-state
independence, source-only reads, clock/type/order admission, fractional economy,
source rounding and zeros, synthetic combat boundaries, per-owner conservation,
private/public separation and explicit unsupported branches. Portable validation
launches no emulator, Frida, Go application or network operation. The original
60-run corpus and earlier corpus pins remain unchanged; no capture was rewritten
to fit the model. README, plan and portable CI checks accompany the research.

[Final-pointer convergence and an exact evolved-world chain](CONVERGENCE_CHAIN.md)
are now captured and [replayed before-only](EVOLVED_CHAIN_REPLAY.md) separately;
they are not implied by these ten initial before-inputs. Arbitrary populated
worlds, active players, general MBF, event damage, new mines/stock pickup, DOS save
conversion, live BBS acceptance and native Windows durability remain separate.
Research work guards are not claims that DOS implemented finite combat/retry
budgets. Production gameplay retains its documented deliberate policies.

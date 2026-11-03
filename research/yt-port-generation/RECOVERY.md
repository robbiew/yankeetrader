# DOS port generation and startup pricing

Checked 2026-11-02 against the archived Yankee Trader 3.6 binaries. This milestone
implements a bounded, opt-in port-rule adaptation; it does not reproduce the full
DOS universe, its random draw sequence or DOS save files.

## Implemented and available to test

```sh
./bin/yt -data dos-economy -init -dos-ports -seed 36
./bin/yt -data dos-economy -local Player
```

New worlds save `PortGeneration: "dos"` in schema 33. Genesis and administrative
reset retain this choice. Omission retains the established uniform-port generator
and fixed 20/30/40 reference prices. Existing supported saves upgrade without
rerolling ports, supplies or prices. The flag is rejected outside initialization,
including an explicitly supplied `-dos-ports=false`. Initialization refuses to
overwrite an existing world. Full JSON exports/restores preserve the profile;
DOS `.DAT` import/export remains unsupported.

This port milestone uses the existing reachable modern warp graph unless the
subsequently implemented `-dos-warps` profile is also selected. It places up
to 1000 ports, starting in sectors 1,3,5,7 and then sampling remaining distinct
sectors with a finite shuffle. Production is an integer 1000..32766 per commodity;
coefficient magnitudes are 1..100, exactly one positive seller and two negative
buyers. Earth is named explicitly but receives the same randomized economy.
Initial stocks materialize ten production days at the current world clock.
Names use the original weighted 908-entry pool and recovered composition rules.
Docking and remote reports share the recovered startup references for this profile.

## Original evidence and recovered rules

The original binaries remain unchanged in `archive/dos-original/`:

| Binary | SHA256 |
| --- | --- |
| YT-INIT.EXE | `601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2` |
| BRUN30.EXE | `3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8` |
| YT.EXE | `c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037` |
| YTMAINT.EXE | `8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6` |

REA/Ghidra retained initialized-memory bytes in `initializer-rea.json`,
`initializer-names-rea.json`, `runtime-rea.json` and `pricing-rea.json`. The verifier
reconstructs the MZ load image with relocations and checks every required address,
exact requested/returned length and byte. Ghidra's coordinate base is 0x10000;
initializer main offsets are relative to that base. Runtime file offsets below
map to loaded addresses by adding 0xfe00 (512-byte MZ header).

| Rule | Original location and evidence |
| --- | --- |
| First ports 1,3,5,7 | Initializer main196e..1998 |
| Later candidate 2..sectorCount, retry occupied | Main19b4..1a3c and integer helper004f..006c |
| Production `INT(RND*31767)+1000` | Main1b34..1b6a; fresh pre-maintenance records and INIT.LOG corroborate |
| Coefficients `-(INT(RND*100)+1)`; one slot negated | Main1baa..1c80; class3 sells ore,2 organics,1 equipment |
| Ten-day production backdate | Main1c9f..1cb5; fresh pre/post-maintenance stock transition |
| Weighted names | Main23e4..2605; DATA file0x33b0..0x4716 |

Names have `INT(3*RND*RND)+2` chunks sampled with replacement. Tokens longer than
four characters gain a leading space and initial capital; trim a leading space
from the whole name, then capitalize its first character. Preserve 29 duplicate
pool entries as weights; names need not be unique. The comma-joined 908-token pool
has SHA256 `8a59a909d232084d89a82db77339f680475c3187aef96ef0ce6444bd0b4002b7`.
All 999 ordinary names in the earlier preserved DOS universe can be decomposed
using these rules; this supports composition, not an independently measured
chunk-count probability distribution.

The original occupancy initialization marks sectors 1,2,3,4 instead of 1,3,5,7.
Later allocation can overwrite ports at 5 or 7. The earlier default DOS capture
has port 223 overwrite port 4 at sector 7. The three new controls happened to retain
all 1000 distinct ports; this does not disprove the static defect. Modern generation
marks the actual occupied sectors and never creates an orphaned port.

## Fresh initializer controls

Run `python3 scripts/recover_port_generation.py /tmp/new-port-captures` to reproduce
in a new disposable directory. It copies the original initializer/runtime, mounts
only that directory in DOSBox Staging and supplies fixed date 11/02/2026 and clocks
00:00:00, a repeat 00:00:00, and 12:34:00. The initializer's final child
`YTMAINT.EXE` is explicitly replaced **only in the disposable copy** by the declared
five-byte exit stub `b8004ccd21`. This preserves the pre-maintenance world; it is
not represented as an entirely untouched execution chain. Then the original
maintenance executable is copied back and run independently against that world.

Each retained case in `dos/` includes before/after compressed worlds, initializer
and maintenance output, independent shell-return markers, emulator logs, answers
and binary/file hash manifest. Both program output and return markers are required.
All worlds are 4151 records of 137 bytes (568687 bytes):

- All 3000 initial commodity stocks are zero.
- All 3000 post-maintenance stocks equal exactly ten times initial production;
  rates remain unchanged. Midnight production spans 1023..32764; later 1020..32743.
- Both stages have coefficient magnitudes1..100 and one selling commodity.
  Initial maintenance can change class/signs; magnitude and production survive.
- Port production date changes from day 296 to 306. Full before/after saves are
  retained rather than mistaking the old post-maintenance capture for raw output.
- Repeated midnight initialization is byte-identical; the later clock changes the
  generated world. This establishes clock dependence in these controls, not an
  exact general QB seeding algorithm.

## Startup price references

`YT.EXE` main003a..00ac calculates the reference values **before RANDOMIZE**:

```text
20 - 5*RND + 5*RND
30 - 7*RND + 7*RND
40 - 10*RND + 10*RND
```

BRUN30 file0xb4d6..0xb509 reads/writes the linked seed and performs the 24-bit LCG.
File0x1022c holds 214013, 0x10230 holds 1744579, 0x10234 holds initial seed 5:

```text
state = (214013*state + 1744579) mod 2^24
RND = state / 2^24
```

Explicit single-precision evaluation gives modeled references
20.051570892333984,29.302257537841797,41.20359420776367.
The existing stock-sensitive formula remains:

```text
price = max(1, floor(B * (1 - C*S/(P*1000)) + 0.5))
```

Seven retained controls in `pricing-dos/` corroborate the startup behavior:

| Declared coefficient for each commodity | Ore | Organics | Equipment |
| --- | --- | --- | --- |
| 0 |20|29|41|
| -50 |30|44|62|
| -10000, synthetic amplification |2025|2960|4162|

Amplified results repeat at midnight, noon, 23:45, for another actor and after an
exact saved-world/auxiliary reload. These distinguish the references from fixed
20/30/40; they do not establish each final float bit. The extreme coefficient is
a declared synthetic probe outside natural initializer limits, not a natural
port-generation outcome. The amplification brackets references to roughly ±0.005.
No cargo/cash trade occurs; reports and one docking turn are checked with normal
return evidence. Reproduction: `scripts/recover_port_pricing.py --help`.

## Deliberate differences and outstanding work

- The seeded Go random stream is reproducible within the modern generator, not
  the QB sequence; the port stream starts separately from graph generation.
- Finite placement fixes the original occupancy defect; reduced 8..3000-sector
  worlds remain a supported modern extension.
- Ten-day startup stock is materialized directly. This does not replay the entire
  original initial maintenance pass, class rotation, NPC setup or random draws.
- Price reference construction models singles; subsequent arithmetic uses float64.
  Exact MBF intermediate rounding, especially boundary values, is still open.
- Existing worlds retain their original fixed reference prices. The new profile
  changes new-world balance, port acquisition costs and trade routes; production
  BBS economy acceptance remains separate from local verification.
- Graph/long-warp rules, isolation repair and Earth shortcuts were subsequently
  implemented in the [warp slice](../yt-warp-generation/RECOVERY.md). Exact
  seed-to-universe replay and DOS save conversion remain separate unsupported work.

## Verification

```sh
python3 scripts/verify_port_generation.py
python3 scripts/test_verify_port_generation.py
python3 scripts/verify_port_pricing.py
python3 scripts/test_verify_port_pricing.py
python3 scripts/smoke_port_generation.py
go test -race -count=1 ./...
go vet ./...
```

Generation verification independently decodes all port records and checks the
maintenance transition, names, signs, ranges, placement, clocks and provenance.
Every sector link in both snapshots must match the last-writer-wins inverse of
the port locations. Missing, incorrect, fractional and entirely cleared links
are rejected, while the original duplicate-location behavior remains accepted.
Semantic corruption controls mutate the later-clock world to avoid rejection
solely through the independent midnight/repeat equality assertion.
Rehashed wrong stock/production/coefficient/location and missing-return controls
must fail; missing, empty and truncated native reads must also fail. Pricing
verification checks declared fixtures, observed prices and exact reload lineage.
Go tests cover weighted names, placement/economy bounds, reproducibility, quoting,
remote reports, no-reroll migration, profile persistence, season resets and stale
Genesis quote rejection. CLI tests exercise new-world admission, saved settings,
private archive contents and reset preservation. CI runs these without DOSBox;
original runtime execution is retained evidence, not a CI emulator dependency.

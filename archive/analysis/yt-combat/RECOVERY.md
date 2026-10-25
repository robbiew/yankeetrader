# YT.EXE combat recovery — Yankee Trader 3.6

## Findings

The calculator is a useful combat guide, but its plasma and surrender formulas are **estimates, not the original combat algorithm**. The supplied executable resolves both through repeated steps with random outcomes. Plasma energy is shared between defenses and attenuated by travel. Cloaking affects fighter combat odds.

Ghidra import and decoding cover all three BASIC modules. This is a partial, manually interpreted recovery, not recovered original BASIC source. Raw automatic C output is not reliable for the QuickBASIC runtime calls. Combat behavior below combines decoded control flow, original BRUN30 arithmetic handlers, and actual local play through unmodified YT.EXE.

## DOS evidence

All tests ran in separate directories under `experiments/`, using copied game binaries and deliberately constructed data fixtures. The player was first created through LOCAL.EXE's normal new-player flow. Later fixtures supplied equipment and defenses directly in copied YTDATA.DAT. The game then executed ordinary attack/fire commands. Neither the original nor copied YT.EXE was patched.

YT.EXE SHA256: `c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.

`verify_evidence.py` passes **91 checks over 12 captured combat sessions**, including 5 separate model checks. These are accounting, hash, transcript, and boundary checks, not 79 independent DOS runs. `evidence.json` records captured results and hashes. Random seeds were not frozen or recovered; repeat runs need not return these exact casualties.

| Scenario | Spreadsheet | DOS observation | Evidence directory |
|---|---:|---:|---|
| One bolt, 1,000,000 sector fighters | 50,000 | 54,736 destroyed | plasma-one |
| Same setup, another run | 50,000 | 54,197 destroyed | plasma-fast |
| Two bolts, same target | 200,000 | 201,159 destroyed | plasma-two |
| One bolt, 10,000 sector mines | 250 | **351 destroyed** | plasma-mines |
| One bolt, ship with no fighters and 1,000,000 shields | 25,000 | 25,832 shields lost | plasma-shields |
| One bolt, fighters two hops away | No distance input | 50,033 destroyed; energy fell from 2,500,000 to 2,450,000 | plasma-distance |
| One bolt, planet with three productive categories and ground forces | 1,000 ground; 1,000–3,000 production | 1,074 ground; 3,221.522 total production reduction reported | plasma-planet |
| 656,000 committed vs 500,000 defenders, full cloak | 84,040 surrender | 47,242 surrender; 176,233 attackers lost | surrender-first |
| Same setup, another run | 84,040 surrender | 32,993 surrender; 312,738 attackers lost | surrender-confirm |
| 10,001 committed vs 1,000 human defenders | 1,000 surrender | All 1,000 join, zero casualties | surrender-immediate |
| 10,000 committed vs 1,000 human defenders | 950 surrender | 950 join after 50 defender and 150 attacker casualties | surrender-ten |
| 10,001 committed vs 1,000 Xannor | No faction input | Refused; 1,000 destroyed, 504 attackers lost | surrender-xannor |

The planet result also exceeds the helper's nominal 3,000 maximum, confirming that it is not a hard bound. The 950 surrender result agrees with the helper for this particular sample; the number of rounds and attacker casualties remain random. Planet loading performs lazy growth/stock updates before impact. The fixture's raw pre-launch planet values therefore cannot be subtracted directly from its final values to isolate damage; the reported impact reduction and saved final totals were checked instead.

`surrender-first` completed and persisted combat but the session was stopped at the subsequent command prompt. Other cases reached the normal return-to-LOCAL message. Earlier login probes, an unanswered surrender prompt (`surrender-fast`), and the superseded future-timestamp planet fixture (`plasma-planet-future`, which triggered the already known clock-rollback bug) are excluded from validation. The retained planet case starts with a valid midnight timestamp.

## Plasma bolts

Recovered routine: module `bmYT-SUB`, Ghidra `1f42:a9bb..bcb9`; file mapping `file offset = 0x10220 + module offset`. Main fire command calls it at `1000:22dc`. Listings use Ghidra's normalized segment aliases for branch targets: compare physical addresses when following those branches.

### Energy and travel

- Launch energy: `E0 = bolts * 2,500,000`, multiplied as MBF single and then promoted to double (`a9e0..a9ef`). The launch is a combined energy pool, even though the display separately prints each bolt being fired.
- Fixed travel loss: `E0 / 50`, retained as a single (`a9f2..aa01`). This is 2% of **launch** energy per additional hop, rather than 2% of the diminishing remainder.
- The first adjacent sector receives full energy. DOS observed 2,500,000 at sector 101 and 2,450,000 at sector 102. Black holes can redirect the path. Range and interception matter.
- Defenses consume this shared energy in order: sector fighters, sector mines, ships, planet. Ship fighters are processed before shields. A standalone calculator cell does not account for earlier absorption or other ships/objects in the path.

### Discrete absorption

For sector/ship fighters and ship shields, repeat while energy and target defenses remain:

```
fighters destroyed += floor(E / 5,000) + 1
# or:
shields destroyed  += floor(E / 10,000) + 1
E -= RND * 25,000
```

Cap destruction at available defenses; preserve leftover energy for later targets. Fighter loop: `af02..af8a`; ship fighters: `b308..b365`; shields: `b372..b409`. RND products are calculated as single precision and promoted before subtracting from double energy.

Mines use a different discrete increment (`b11e..b1bc`):

```
mines destroyed += floor(E * 0.000001) + 1
E -= RND * 25,000
```

The repeated `+1` matters. For illustration, substituting a constant random draw of 0.5 gives 362 mines for one bolt and 1,205 for two. These illustrative model outputs are **not DOS measurements**. The observed one-bolt result was 351, 40.4% above the helper's 250.

### Why the quadratic estimates are recognizable

Replacing the random energy loss by its mean, 12,500, and integrating fighter damage gives approximately:

`E0² / (2 * 5,000 * 12,500) = 50,000 * bolts²`.

The same argument yields 25,000 for shields. This explains the spreadsheet coefficients without treating them as literal game constants. Discrete rounding, per-step increments, random draws, travel, caps, and earlier defenses change actual results. The helper's “minimum” label does not establish a guaranteed lower bound in the original algorithm.

Planet loop `b8c0..b92d` subtracts `E * 0.000004` from each production category and ground defenses before subtracting the same random energy loss. Its continuous estimate is about 1,000 per bolt squared per surviving production category, hence up to 3,000 total. Ground forces undergo integer conversion and clamping afterward. Stocks are also constrained relative to reduced production. Planet destruction and unusual zero-production combinations still need dedicated boundary tests.

## Fighter combat and surrender

Main module `1000:0b21..0f18` handles attacking a sector fighter group. The relevant temporary values are:

| DS address | Meaning |
|---|---|
| 4d12 | Total fighters aboard before the attack |
| 4d1a | Fighters committed to this attack |
| 4cfe | Initial defending fighters |
| 4d1e | Cumulative attacking casualties |
| 4d26 | Cumulative defending casualties |
| 4d32 | Current combat batch size |
| 4d4e | Cloak energy fraction |
| 4cf2 | Surrender already offered/refused flag |

For every round (`0c07..0cbc`, `0e8f..0efc`):

```
A = committed attackers - attacking casualties
D = original defenders - defending casualties
batch = max(1, floor(min(A, D) / 20))

if A / D > 10 and no previous surrender offer:
    human-owned defenders may surrender
    Xannor and mercenaries refuse
    mark offer handled
    if accepted: remaining defenders join the attacker's ship; stop

if RND + cloak_fraction / 10 < 0.45:
    attacking casualties += batch
else:
    defending casualties += batch

repeat while both committed forces survive
```

The strict `> 10` comparison is at `0c83..0ca6`. Owner checks and refusal messages are at `0d03..0da8`. The human response defaults to yes. Refusing an offer does not trigger repeated offers during that attack.

At ordinary cloak fractions 0..1, the attacker-loss probability per round is approximately 45% without cloak and 35% at full cloak. This is a probability of losing a **batch**, not a fixed percentage of initial fighters. Batch size changes as the smaller force shrinks. The exact stochastic distribution has not been measured in a large DOS sample.

This explains why a formula depending only on initial A/D cannot reproduce surrender. Some attackers can fail entirely; successful attacks reach the threshold after variable casualties. Uncommitted fighters remain aboard and surviving defenders are added to the ship on acceptance. Saved data accounting was checked against the printed casualties.

## Data mapping clarified

The FIELD statement at `1f42:bce6..bdbb` declares **23 numeric fields** after the 41-byte text region. Descriptor order is not simply increasing: `1994` is declared before `1990`, and `198c` is absent. Thus descriptors after `1988` must not be mapped by arithmetic alone. Bytes 133..136 remain outside these declared fields.

Combat-related player offsets confirmed by ordinary DOS displays, equipment use, or casualty persistence:

| Record byte offset | Player meaning |
|---:|---|
| 49 | Turns |
| 53 | Shields |
| 57 | Sector |
| 61 | Fighters |
| 85 | Alias length, including its trailing space |
| 97 | Cruise missiles |
| 113 | Plasma bolts |
| 125 | Cloak energy fraction |

Sector offset 81 holds fighters, 85 their owner, 93 a planet reference, and **129 sector mines**. Those final four declared bytes are meaningful, unlike the undeclared record tail at 133.

## Tools and reproduction

- `headless.log`, `program.txt`: Ghidra import evidence. Project: `../ghidra-projects/YankeeTrader.gpr`.
- `main/`, `sub/`, `sub2/`: linear QB-aware listings; `decompiled.c` is retained only as raw output.
- `../ghidra-scripts/DecodeQBBinary.java`: supports the 3-byte runtime calls used by YT.EXE, versus the 5-byte form seen in the initializer/maintenance binaries. Some noncombat dispatch tables are still not decoded.
- `runtime-math.txt`, `runtime_evidence.py`: original BRUN30 math dispatch entries. These establish the division and multiplication operations used above. A useful independent description of the dispatcher is [Marnetto's QB3 investigation](https://marnetto.net/2026/03/01/brun-hello-world); calculation conclusions here come from the supplied runtime and game, not that article.
- `keyfeed.asm`, `KEYFEED.COM`: small research-only keyboard feeder; NASM builds it. Hooks BIOS timer and inserts keys into the BIOS keyboard buffer. `~` pauses for roughly two seconds; command-line `|` becomes Enter in `run_session.py`. Installed only in isolated emulator sessions.
- `make_fixtures.py`, `more_fixtures.py`, `planet_fixture.py`: fixture construction. These expect their output directories to be new. `run_session.py` copies a fixture into a new directory and runs DOSBox Staging with a bounded timeout. The original interactive game does not reliably accept redirected input, so normal BIOS keyboard input is used instead.
- `recovered_rules.py`: readable selected algorithms with injectable RNG. **Not** a bit-exact MBF/BRUN emulator or complete combat engine.
- Run `python3 analysis/yt-combat/verify_evidence.py` from the distribution directory to verify captured results.

## Remaining work and intentional fixes

Missiles and planetary ground assaults are now covered in [the next recovery report](../yt-missiles/RECOVERY.md). Remaining work includes direct ship combat, overflow/negative inputs, exact MBF conversions, original RNG and seeding, and multiplayer/death timing. The planet loop appears to test ground forces, organics production, and equipment production while omitting ore-only production from its entry condition; this is a **static lead requiring a DOS reproduction**, not yet a confirmed exploit.

Keep the original stochastic rules as documented research. For the modern game, fix validated defects and exploits deliberately; retain an injected RNG and transaction boundaries so combat can be tested without depending on wall-clock timing.

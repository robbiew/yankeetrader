# Initial-maintenance RNG: entry seeding and first-hit phase evidence

Captured 2026-11-04. This is a bounded research follow-up to the
[untouched initial-maintenance handoff controls](INITIAL_MAINTENANCE.md).
It adds no Go gameplay, `qb36-v1` policy, source fingerprint or save-35 change.

## Recovered scope

The initializer's raw RNG and complete pre-maintenance replay are already
implemented. This slice measures maintenance's own seed entry, two reseeding
helpers and selected first-hit RND boundaries. It does **not** recover every
maintenance draw, loop iteration, rejected candidate or arbitrary MBF operation.
The probes terminate at their named boundary; their partial worlds are not
normal post-maintenance replay targets.

There are **151 terminating controls** across six clock/date/launch cases,
plus **six untouched completed oracles** using the same pre-launch recipe.
The baseline includes a bounded inventory of all 43 literal argumentless/argument
RND instruction sites in the original maintenance image: nine are hit and
34 are not reached. The other cases sample 18 named boundaries each. Overall,
117 probes record a hit and 34 reach the declared no-hit guard.

## Native identity and dispatch evidence

Original distribution files are unchanged:

| Binary | SHA-256 |
| --- | --- |
| YTMAINT.EXE | `8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6` |
| BRUN30.EXE | `3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8` |
| YT-INIT.EXE | `601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2` |

Two fresh REA/Ghidra 12.1.4 `read_bytes` observations in
[rng-native/rea.json](rng-native/rea.json) pin entry `0x10073` (29 bytes) and
helpers `0x178f3` (237 bytes). Evidence IDs are
`ev_7d70fc4e1cc6f694b0f110e503f1d6af5bfc6b7c28118e25ffefa0c4ec4b0f85`
and `ev_b02acf33b1143f9802b565346a30067aec0157c71e917f784414a562d059d3ed`.
The verifier independently checks exact lengths, identities and relocated MZ
bytes. These are static observations; the probes below establish runtime states.
The existing [BRUN30 seed/LCG evidence](../yt-rng-seeding/RECOVERY.md) is reused.

In main code coordinates (subtract `0x10000` from REA addresses):

- Entry `0078` obtains TIMER, `007d` negates it and `0085` invokes RANDOMIZE
  through `3E/09`, with BX pointing to the raw FAC at DS:`001a`.
- Helper `78f3` obtains TIMER at `78f8` and RANDOMIZEs at `7900` **without
  negation**. Its next RND is the argument-taking `3D/33` at `7908`.
- Helper `7939` likewise samples TIMER at `793e` and RANDOMIZEs at `7946`.
  Its argument-taking RND loop is at `7989`.
- Both tested helper RND arguments at DS:`7ea4` are exactly MBF single one,
  raw `00000081`. This does not recover other RND argument variants.

## Controlled terminating probes

Only disposable maintenance copies are patched. The original 43,185-byte file
length, complete MZ header, runtime and initializer are preserved.
A 45-byte diagnostic replaces main `0044..0070`, the return/cleanup path after
main `0073`. A five-byte jump at one selected site goes to `0049`. That code
writes exactly `MSP1 | state(4 bytes) | FAC/source(4 bytes)` and exits through
DOS `4C00`. The separately measured argument variants select DS:`7ea4` instead
of FAC. [Exact assembly](rng-native/probe.asm) and the capture writer retain
this complete patch contract; no world input bytes are edited.

If the site is never reached, normal main-body return reaches `0044`, which
exits with code 99. Independent `HIT.LOG` and `MISS.LOG` witnesses distinguish
these cases. DOSBox redirection can create/truncate a file even for a false IF,
so the two branches deliberately have separate files. A missing hit is never
silently accepted as the requested phase observation. All 18 required phases
are hit in every case; the 34 no-hit cases belong only to the baseline inventory.

Each split run starts from all three exact original pre-maintenance files retained
by the earlier handoff milestone. Each integrated run executes original YT-INIT
with the patched maintenance child, preserving initializer answers and shell
return. Raw clocks, commands, emulator launch/options, stdout, return/exit
witnesses and compressed partial worlds are retained. Probes emit no trace I/O
before their stop, so their observations do not include logging between samples.
Different probes are independent first hits, not one simultaneous execution log.

## Measured seed states

TIMER values below come from raw FAC bytes at the seed sites. Requested seconds
are not substituted for measured values. The shared 24-bit state transform is:

```text
seed = (oldState & 255)
     | ((FAC[0] XOR FAC[2]) << 8)
     | ((FAC[1] XOR FAC[3]) << 16)
next = (214013 * state + 1744579) mod 2^24
RND value = next / 2^24
```

All six cases observe state 5 before the main seed, including the integrated
initializer/child launch. At midnight, raw TIMER is `00004800`; negation yields
`0000c800`, and RANDOMIZE yields `0x00c805`. The raw residual bytes of numeric
zero are consequential, just as in the initializer recovery.

| Case | Main seed | First helper TIMER (approximately seconds) | First helper seed | Second helper TIMER (approximately seconds) | Second helper seed |
| --- | --- | ---: | --- | ---: | --- |
| Midnight split | `00c805` | 0.05 | `b08105` | 0.10 | `b181b8` |
| Independent repeat | `00c805` | 0.05 | `b08105` | 0.10 | `b181b8` |
| Requested second one | `61b205` | 1.04 | `9fbd05` | 1.09 | `0414b8` |
| Requested second two | `a90a05` | 2.03 | `698405` | 2.08 | `9cbdb8` |
| New Year midnight | `00c805` | 0.05 | `b08105` | 0.05 | `b081b8` |
| Integrated initializer | `685c05` | 6.92 | `f3f905` | 6.92 | `f3f9b8` |

The requested one/two-second clocks display 0.98/1.97 seconds; the integrated
main seed samples approximately 6.81 seconds. The helper calls preserve the
previous state's low byte: 05 at the first helper and b8 at the second observed
helper entry. Full raw bytes and exact binary fractions are checked, not rounded
printed seconds. Before/after seed FAC bytes agree in each paired boundary.

## Selected first-hit draw chain

In the baseline, the first helper's RND(1) advances `b08105 -> 5d6fb4`.
The following first-hit argumentless draws are:

| Main instruction | State before | State after |
| --- | --- | --- |
| `2237` | `5d6fb4` | `ca1fa7` |
| `226c` | `ca1fa7` | `199bce` |
| `2363` | `199bce` | `9a8359` |

Every before/after pair is one exact LCG step and every resulting FAC equals
`state / 2^24`. The same relationships hold across all six cases. The first
helper output's `floor(3000 * RND) + 1` matches the untouched oracle's Wanderer
sector: **1095, 1095, 1497, 2982, 1095 and 1349**, respectively. This is a bounded
correlation plus a measured adjacent-state chain, not a proof of arbitrary
candidate-rejection behavior or a complete phase chronology.
The second helper's first-hit RND pair also advances exactly once; its reseed
retains the independently observed low byte. Repeated helper invocations and
all subsequent loop draws are not reconstructed.

The baseline RND inventory hits `2237`, `226c`, `2363`, `3348`, `3c0e`, `46af`,
`537e`, `7908` and `7989`. The other 34 literal RND sites are not reached in this
specific inactive-player initial-world fixture. This is not a claim that those
branches are dead in ordinary gameplay or that indirect runtime paths are absent.

## Paired-oracle check and limits

All 34 no-hit probes produce the **same entire final world** as the fresh untouched
baseline oracle, SHA-256
`183706df608cad5c8d497764d363b972b857c1bd2093dcb1befd6de620c1b99b`.
The fresh untouched repeat is byte-identical. Thus the no-hit guard/patch is
world-neutral for this measured recipe. Hit probes intentionally stop earlier.

That fresh baseline differs by **97 bytes** from the earlier handoff baseline
`ada65f...`. Sector/port random/time fields differ; the three NPC planet sectors
remain unchanged. Both historical and new evidence are preserved with their own
pins. The comparison does not isolate an individual clock/command/filename
cause. It demonstrates why a clock string alone is insufficient to claim exact
maintenance replay across launch recipes. The integrated fresh oracle remains
byte-identical to the earlier integrated oracle. No old expected hashes were
changed to hide the difference.

Next: recover repeated helper reseeds, candidate rejection and complete dynamic
phase draw counts, then exact post-maintenance record/auxiliary replay against
untouched controls. General MBF arithmetic, arbitrary clocks/input worlds and
production native-BBS/Windows acceptance remain outside this slice. Existing
modern rerun/rollback and exploit safeguards remain in place.

## Reproduce and verify

Portable checks need only Python standard library and retained files:

```sh
python3 scripts/verify_maintenance_rng.py
python3 scripts/test_verify_maintenance_rng.py
```

New captures require DOSBox Staging in PATH and an absent output directory:

```sh
python3 scripts/recover_maintenance_rng.py /tmp/yt-maint-rng-new
python3 scripts/recover_maintenance_rng.py /tmp/yt-maint-rng-oracles-new --oracles
```

The default verifier checks the committed controls, paired oracles and native
reads. A changed environment/recipe needs separately reviewed observations;
expected raw hashes are not automatically refreshed. No release packages,
Go source, schema 35 or original archives change in this milestone.

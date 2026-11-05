# Maintenance runtime RNG trace — bounded instrumented controls

Captured 2026-11-04. This research extends the [untouched initial-maintenance
controls](INITIAL_MAINTENANCE.md). It changes no gameplay, `qb36-v1` source
fingerprints, schema 35, or published release.

## Established boundary

The original maintenance does **not** consume just one continuous startup-seeded
stream. It reseeds during NPC processing. Five copied-runtime traces retain every
observed shared RND conversion and RANDOMIZE store event, interleaved with the
maintenance transcript. Every draw and every reseed independently satisfies the
previously recovered [BRUN30 primitive](../yt-rng-seeding/RECOVERY.md).
There are 127,618 retained events: 127,309 draws and 309 seed events.

| Control | Total events | Seed events | Draws | Initial state | Final state |
| --- | ---: | ---: | ---: | --- | --- |
| Midnight | 24,404 | 62 | 24,342 | `c805` | `26bfeb` |
| Independent midnight repeat | 24,404 | 62 | 24,342 | `c805` | `26bfeb` |
| Requested second one | 28,052 | 61 | 27,991 | `61b205` | `282a42` |
| Requested second two | 26,354 | 62 | 26,292 | `a90a05` | `c6e649` |
| January 1, 2027 | 24,404 | 62 | 24,342 | `c805` | `26bfeb` |

Actual starting DOS time witnesses are 0.00, 0.98 and 1.97 seconds, respectively.
Startup negated TIMER FAC bytes are `0000c800`, `48e1fa80` and `f628fc81`.
The runtime's original state starts at 5; the low byte survives RANDOMIZE.
The midnight repeat's complete trace is identical, including transcript bytes;
the New Year event sequence is identical, with only date-dependent output/state
fields differing. These are bounded observations, not arbitrary-clock coverage.

The visible transcript provides broad phase boundaries. Each trace measures no
RND conversions during the port phase, four draws after planet maintenance
begins, 58 reseeds during Xannor processing, and 21 Mercenary draws. The lottery
path differs between controls. These are transcript-delimited counts, not recovered
call-site attribution or a general per-faction formula.

## Native call paths and declared instrumentation

Original YTMAINT remains byte-identical to the archive. Three original byte
contracts in the verifier locate startup `TIMER; negate; RANDOMIZE` at file
`0278`, and helper `TIMER; RANDOMIZE` sequences at `7af8` and `7b3e`. The helpers
use **positive** TIMER, distinct from startup's negated TIMER. The annotated
listing shows the first helper then calls positive-argument RND. The shared
runtime trace therefore must not be described as only argumentless RND calls.

Only a disposable BRUN30 copy is patched. The original whole-file SHA is
`3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8`.
Its MZ header and length remain unchanged. The verifier independently reconstructs:

- File `b506`: replace `MOV AX,8800` with near CALL to runtime code `fdb7`.
- File `b54f`: replace `MOV [0235],AX` with near CALL to runtime code `fdb2`.
- File `ffb2..ffed`: replace exactly 60 originally zero bytes with two displaced
  instruction stubs and the common logger. No appended image or other patch.

The shared RND hook runs after the state has been stored and before conversion to
FAC. Its FAC snapshot is therefore **pre-conversion scratch state**, not the
returned random value. The seed hook runs after the original seed store. On the
captured seed paths, the FAC snapshot supplies bytes whose word XOR matches the
stored seed. The logger preserves flags, general registers and DS, constructs
its packet on the stack and writes it in one DOS call:

```
00 52 47 21 | runtime return IP (2) | state (4) | raw FAC snapshot (4)
```

Packets are 14 bytes. Return IP `b309` identifies RND conversion; `b352`
identifies RANDOMIZE. They are runtime hook return offsets, **not** application
call sites. Each event is checked in order from state 5:

```
RANDOMIZE: (oldState & 255) | ((FAC_low_word XOR FAC_high_word) << 8)
RND:      (214013 * oldState + 1744579) & 0xffffff
```

No recurrence break is ignored or repaired. Unknown event kinds, partial frames,
missing successful completion, altered seeds/draws and inconsistent phase counts
fail validation. Complete raw traces, before/after worlds, every DAT/ASC auxiliary
output, executable identities, patch bytes, commands, emulator settings, clock
witnesses and normal shell returns are retained under [rng-controls](runtime-stream-controls).

## Instrumentation changes timing: preserve this distinction

Logging consumes emulated time. Because maintenance samples TIMER repeatedly,
a passive-looking logger can change later seeds and NPC decisions. Comparing
these traces with the corresponding untouched controls establishes:

| Control | Changed sector records | Changed raw world bytes |
| --- | ---: | ---: |
| Midnight / repeat / New Year | 19 each | 51 each |
| Requested second one | 7 | 16 |
| Requested second two | 0 | 0 |

All differences are confined to sector fields 81/85/93/105. Configuration,
player, port and planet records are byte-identical to their untouched paired
outputs in these retained runs. The two-second result matches the **complete**
untouched world. The verifier enforces the exact observed difference counts and
field boundaries; it does not mask differences to assert whole-world equality.
The traces with differences are instrumented observations, not native-output
goldens for exact maintenance replay.

Discarded development probes failed before completion or used larger logging
packets; they are not retained as accepted evidence. No new Ghidra decompilation
is claimed. The supported DOS runtime and existing byte listings supply this
slice's evidence; REA remains an optional research tool, not an app dependency.

## Verification and next precision slice

```sh
python3 scripts/verify_maintenance_runtime_streams.py
python3 scripts/test_verify_maintenance_runtime_streams.py
python3 scripts/verify_initial_maintenance.py
python3 scripts/test_verify_initial_maintenance.py
python3 scripts/verify_archive.py
```

The verifier independently reconstructs patched runtime bytes from the original,
checks original call contracts, pins every decompressed observation, verifies
launch provenance and complete clock/return witnesses, replays all seed/draw
events and enforces measured native/instrumented boundaries. Four test methods
exercise 17 rejection controls, including direct recurrence/seed/FAC/kind/phase/
completion corruption and rehashed evidence/provenance changes. CI uses only
Python standard library; no emulator is required.

To collect a fresh instrumented run, use a new disposable destination:

```sh
python3 scripts/recover_maintenance_runtime_streams.py /tmp/yt-maintenance-rng-new
python3 scripts/verify_maintenance_runtime_streams.py /tmp/yt-maintenance-rng-new
```

Existing observation pins must not be refreshed automatically for a divergent
capture. Investigate emulator/clock/probe differences first.

Next: recover application call-site order and reseeding helper behavior, using
lower-perturbation or timer-controlled probes paired with untouched controls.
General TIMER/MBF arithmetic, arbitrary RND argument variants and complete exact
post-maintenance replay remain separate. Do not repeat the startup seed or this
complete instrumented-stream capture as missing research. Modern same-day and
clock-rollback safeguards remain intentional.

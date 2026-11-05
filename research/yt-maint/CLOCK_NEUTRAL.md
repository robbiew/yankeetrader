# Clock-neutral TIMER observation: bounded untouched replay is exact

On 2026-11-05, host-side DOS time observation closed the remaining four-byte
port timestamp gap for the retained all-inactive initial-maintenance recipe.
All six output files, **570,059 bytes**, agree exactly with fresh unobserved
controls and the four historical untouched controls. No timestamp is masked,
corrected from an after-file, or special-cased by port number.

This is research, with no Go gameplay, dependency, archive, `qb36-v1` source
fingerprint or save-35 change. It does not predict arbitrary worlds or clocks.
The [historical guest-instrumented model](RECORD_REPLAY.md) and its report/pins
remain unchanged: that profile still exposes its original four-byte mismatch.
The new [explicit host-clock profile](../../scripts/replay_maintenance_clock_neutral.py)
uses the same pure record writers with independently derived clock inputs.

## Controlled result

The copied original `YTMAINT.EXE` and `BRUN30.EXE` are byte-for-byte unchanged
before and after every run. The three starting files are the same retained
`initial-controls/baseline-split` inputs, with no occupied sectors or active
humans. Guest date is **11/02/2026**, time **00:00:00**, fixed CPU setting
**200000**. Headless video/audio are the only environment overrides.

| Control | Runs | DOS time hook | Complete output comparison |
| --- | ---: | --- | --- |
| Unobserved | 2 | No Frida process attachment | All six files exact |
| Attach-only | 1 | Frida loaded; no DOS21 hook | All six files exact |
| Host observed | 3 | Paired DOS21 AH=2c entry/return | All six files exact |

All six DOSBox processes exited naturally with status zero; no forced stop,
error marker, dropped observation or hook error is accepted. Frida sessions
reported `process-terminated`, and the controller confirmed each PID had exited.
The attach-only case has no time events. Each observed case has **1,066** paired
DOS time events: **1,062** qualify as original BRUN TIMER calls and four other
DOS time calls are retained and excluded from TIMER attribution.

| Original application return IP | Attribution | Calls |
| --- | --- | ---: |
| `007d` | Startup seed TIMER | 1 |
| `0927` | Port TIMER/60 | 1000 |
| `78fd` | Helper 1 reseed | 41 |
| `7943` | Helper 2 reseed | 19 |
| `218b` | Xannoron creation TIMER | 1 |

Each trace independently derives the complete replay inputs and reproduces all
ten targets (six fresh, four historical). The generated
[comparison report](clock-neutral-replay-report.json) retains all **30** complete
comparisons. RNG consumption remains 25,891 draws, final state `4307ee`.

## Why the original discrepancy disappears

The old guest instruction counter and read-only guest comparison both moved
the clock transition to **port 606**. The host observation adds no guest opcodes
and records the original transition at **port 607**: ports 1–606 return zero
centiseconds, while port 607 returns five centiseconds. The zero raw MBF residue
is `00004800`; five-centisecond TIMER/60 is `0e745a76`. The new input array comes
from all 1,000 individually attributed return events, not a hand-written
boundary or an expected output timestamp table.

The verifier converts DOS `CH:CL:DH:DL` to seconds using exact rational arithmetic
and an independent 24-bit, nearest-even rounding implementation, then rounds the
division by 60 separately. A three-centisecond negative control distinguishes
that two-stage process from a single direct division. Only an actual zero DOS
input selects BRUN's measured zero residue. Startup raw TIMER also supplies the
original negated-seed mix, yielding `00c805`; helper and Xannoron inputs come
from the same trace. No previous terminating guest probe supplies these inputs.

The selected recipe keeps text HH:MM:SS at midnight across every DOS time event;
the profile rejects another date or a changed text second. This does not
establish how arbitrary wall-clock schedules should be predicted.

## Attribution and observer limits

The [observer](../../scripts/observe_maintenance_clock.js) filters the installed
host C++ `DOS_21Handler()` for AH=2c, snapshots before and after the native
handler, and buffers events until process exit. It only reads guest registers
and RAM. There is no guest memory/register write, guest disk tracing or per-event
IPC. Frida does patch host instructions and consumes host time: **this is not
passive observation**. Complete output equality across the controls is the
bounded evidence of neutrality; unchanged guest code alone would not suffice.

The exact installed host is DOSBox Staging **0.83.0**, macOS ARM64, SHA256
`781d61c874271a315d672c597697cf0fb3aa0f6a727934bce4d2a9ad34057de5`,
Mach-O UUID `31CDF62F-E9EE-39ED-A05A-10E4072BD15E`. The capture recipe rejects
another binary before applying offsets, and the injected observer separately
checks architecture, UUID and original handler prologue. Module-relative native
offsets resolve against the actual ASLR base. The Node controller records
Frida **17.23.2** package/module hashes and its Node version; neither tool is a
project runtime or CI dependency.

[Retained host/native notes](clock-neutral-host/FINDINGS.md), symbols,
disassembly and source hashes bridge the observer to the installed binary.
Official [v0.83.0 source](https://github.com/dosbox-staging/dosbox-staging/tree/7b40053b7ac580843d0461eba8c36a47a990e66c)
is retained at its resolved commit. `registers.h`, `callback.cpp`, and `dos.cpp`
explain the register layout, original DOS interrupt frame, returned CX/DX and
DOS overhead. Native instruction bytes corroborate the selected installed
handler; upstream source alone does not prove an unpatched bottle build.

Paired observations retain the raw 40-byte stack, DS/SS physical bases, PIC,
CPU-cycle counter, IP and original runtime/application call bytes. The verifier
checks original `50 53 51 52 b4 2c cd 21` at runtime TIMER entry, the stack return
`c137`, the runtime loader's far-call fixup at each qualified application site,
and dynamic code/data segment identities. It requires the original handler's
IP +2/cycles −5 overhead and unchanged paired guest context. It does not read
restored CX/DX at application return, where BRUN has already restored caller
registers. The raw port loop value must cover 1–1000 exactly once in order.

The pilot REA bundle is retained as method-discovery provenance, separate from
the final six-case direct-Frida corpus. REA did not report authenticated target
artifact identity or OS/architecture for that pilot; installed-host hashes,
loaded-module fields and source/native checks provide the independent bridge.
No pilot output is substituted for a final control. Retained recipes and pins
cover the final capture scripts and artifacts.

## Verification and reproduction

Portable checks use Python standard library only; they never launch DOSBox or
Frida and do not refresh expected hashes:

```sh
python3 scripts/verify_maintenance_clock_neutral.py
python3 scripts/test_verify_maintenance_clock_neutral.py
python3 scripts/test_replay_maintenance_clock_neutral.py
python3 scripts/replay_maintenance_clock_neutral.py --output /tmp/clock-neutral-replay.json
```

For fresh acquisition on the declared host, supply an existing Frida17.23.2 ESM
entrypoint and new destination/scratch directories:

```sh
python3 scripts/recover_maintenance_clock_neutral.py /tmp/clock-neutral-new \
  --scratch /tmp/clock-neutral-disposable \
  --frida-module /absolute/path/to/frida/build/src/frida.js
```

The acquisition command captures without reading expected after files. It leaves
disposable scratch files for inspection, verifies unchanged originals and natural
exit, and records controller/log/command metadata. It does not overwrite the
retained corpus or approve new pins. PID/ASLR/path fields legitimately change in
a fresh capture; a new corpus requires semantic review and independent pinning.

Scope remains one date/clock, one default initial world and one pinned emulator
host. General MBF arithmetic, arbitrary maintenance phases/worlds, other emulator
versions/CPU schedules, native Windows crash durability and live BBS acceptance
remain separate. The current production maintenance policy is unchanged.

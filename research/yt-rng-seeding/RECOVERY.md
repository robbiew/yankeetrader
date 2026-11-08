# QuickBASIC RNG seeding and bounded graph replay

Checked 2026-11-03. This milestone recovers the original initializer's seed path,
verifies the BRUN30 RNG against raw runtime records and reproduces selected DOS
warp tables exactly in a research model. It does not select a new gameplay RNG,
replay port generation or promise general DOS seed-to-world compatibility.

## What was already established

The [port milestone](../yt-port-generation/RECOVERY.md) recovered the 24-bit LCG,
initial state 5 and startup reference-price expressions, supported by integer-price
controls. The [warp milestone](../yt-warp-generation/RECOVERY.md) recovered local
and long links, repair and shortcuts, with explicit modern Go random streams.
Neither established the initializer's exact RANDOMIZE input or raw zero handling.

The new implementation isolates the verified subset in `internal/qbrng`:
argumentless RND and RANDOMIZE from four raw MBF-single bytes. Existing startup
price reference construction now uses this shared primitive with identical
results. No world schema change, existing-save rewrite, map regeneration or
change to the selected modern gameplay/generation streams is introduced.

## Recovered native path

Originals remain unchanged under `archive/dos-original/`:

| Binary | SHA256 |
| --- | --- |
| YT-INIT.EXE | `601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2` |
| BRUN30.EXE | `3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8` |

Initializer main003a..004b executes **`RANDOMIZE -TIMER`**: INT3D/43 obtains TIMER,
INT3F/B1 negates the raw single FAC, and INT3E/09 randomizes using BX001a, the FAC
address. B1 is negation, not RANDOMIZE itself. Helper004f is skipped by the
startup jump; the first main-path draw before graph generation is the HQ draw
at0921. The following ordinary-warp draw is at0eca.

| Operation | Runtime dispatch entry, file | Handler, file |
| --- | --- | --- |
| TIMER3D/43 |0x3f7→c12f|0xc32f..0xc3b3|
| Negate3F/B1 |0x6ef→abe3|0xade3..0xade8|
| RANDOMIZE3E/09 |0x455→b349|0xb549..0xb553|
| Argumentless RND3D/34 |0x3d9→b2c2|0xb4c2 onward|

TIMER calls DOS INT21h/AH2Ch once, then computes the single-precision value:

```text
(((hours*60 + minutes)*60 + seconds)*100 + hundredths) / 100
```

The pre-division integer is below 2^24 and exactly representable. Date is not a
seed input on this path. The runtime's zero normalization clears the exponent
without necessarily clearing mantissa bytes; a numeric zero is not sufficient
to reconstruct the seed argument's bytes.

For raw MBF bytes `b0,b1,b2,exponent`, RANDOMIZE stores:

```text
newState = (oldState & 255)
         | ((b0 XOR b2) << 8)
         | ((b1 XOR exponent) << 16)
```

The low state byte survives. RANDOMIZE does not normalize the argument or advance
the sequence. Argumentless RND advances:

```text
state = (214013*state + 1744579) mod 2^24
value = state / 2^24
```

Values are exact binary fractions in [0,1), including both observed endpoints 0
and 1−2^-24. The separate negative-argument path was outside this original milestone. It is
now recovered and implemented alongside zero/positive arguments in the
[argumented-single RND supplement](RND_ARGUMENTS.md); it must not be conflated
with RANDOMIZE.

Native observations in `runtime-rea.json`, `dispatch-rea.json` and
`initializer-rea.json`, together with the reused LCG observations from the port
milestone, are verified as 13 exact read contracts against relocated MZ images.
Required lengths, addresses, original hashes and bytes must all match; missing,
empty, truncated or substituted reads fail. Key native Evidence IDs include
`ev_0a84e43190ff1b8702275de4028fc74f045c6e8aa44b53d90728ad7e122f8067`
(RANDOMIZE), `ev_57bcde57ba704792310ee10df602be185e16a5358d60bbd3bb400ab7ca6695fc`
(TIMER), and `ev_9c3aece5bd62838da478d240ff6d07812565137cfeead9ec85a65c6fbcc85343`
(HQ draw). These are static observations; the raw probes below establish runtime
values rather than treating static analysis as execution evidence.

## Controlled-clock original initializer runs

Six normally returned captures in `clock-dos/` execute the original initializer
and runtime in disposable DOSBox Staging directories. Only the declared
maintenance child is replaced by the exit-only stub `b8004ccd21`; pre-maintenance
worlds are retained. Raw start/end DOS date/time, weekday, shell commands,
initializer normal-termination output, return markers and hashes are checked.

| Requested clock/date | Actual initial DOS display | Observation |
| --- | --- | --- |
| Nov 2 midnight |00:00:00.00|Baseline|
| Repeat |00:00:00.00|Entire world byte-identical|
| +1 second |00:00:00.98|Different graph/port fingerprints|
| +2 seconds |00:00:01.97|Another graph/port result|
| 12:34:00 |12:33:59.91|Different graph/port result|
| Nov 3 midnight |00:00:00.00|Same generated graph, names and economy; routine dates differ|

This environment's clock setter rounds to DOS tick resolution. Requested time
strings are not asserted to be exact seed-point TIMER values. Moving the date
changes exactly 1,101 records/1,202 bytes in these controls: configuration record 1
offset 81, 100 planet records offset 81 and 1,000 port records offset 45. Masking only
those date fields makes the complete worlds identical. This supports the native
time-only path in the tested environment, not a general emulator clock model.

## Raw seed and RND probes

`recover_rng_trace.py` copies both executables. It redirects initializer main003a
to replacement diagnostic code at main006d, before normal initialization, while
preserving the original MZ header and file length. The payload explicitly writes
raw state/FAC bytes to redirected stdout using DOS AH40h; it terminates through
DOS4C00h. It never runs the normal universe body or initial maintenance. Original
executables are not modified. The independent verifier reconstructs every byte
of both copied executables from the original plus the declared payload/seed patch.

Each trace is exactly 2072 bytes:

```text
RNG1 | initialState(4) | TIMER/input FAC(4) | negated FAC(4)
     | randomizedState(4) | 256 * (state(4) | RND FAC(4)) | END!
```

Header/footer, exact length, copied executable identities, raw DOS clock/date,
input command recipe, shell return and all retained hashes are required. The
format distinguishes real TIMER probes from synthetic raw-input and unseeded
state controls. Footer completion is diagnostic-program evidence, not the
original initializer's normal-termination message.

Sixteen retained controls verify all 4,096 state/FAC pairs. They include actual
midnight/repeat/next-date/one-second/12:34 TIMER inputs, canonical and residual
zero, positive/negative 100.5, a nondefault preserved low byte, several unseeded
states, and constructed next-output0/max boundaries.

The midnight probe is decisive:

| Field | Raw bytes/value |
| --- | --- |
| TIMER FAC | `00004800`, numerically 0 |
| Negated FAC | `0000c800`, numerically 0 |
| Initial state |5|
| Randomized state |`0x00c805` (51205)|

Canonical zero `00000000` negates to `00008000` and seeds `0x008005` instead.
Converting the measured TIMER to an ordinary float zero and re-encoding it would
therefore produce the wrong sequence. RANDOMIZE must use the original raw bytes.
At the one-second requested clock the measured TIMER FAC is `48e17a80`
(0.9800000190734863); at 12:34 it is `e9b73090` (45239.91015625), producing seed
`0x275905`. The preserved-low-byte control yields `0x87c9ab` from initial `0x1234ab`
and the same negative 100.5 argument. No intermediate decimal print conversion
is used to validate these values.

`internal/qbrng/testdata/native_rng.json` packages every full trace and its
provenance. `export_rng_fixture.py` validates first; the independent verifier
compares the complete fixture against retained raw files. Go tests check every
state and numeric RND result exactly, including zero and the largest value below 1.
They deliberately do not claim to reproduce all raw FAC residuals or implement
full MBF arithmetic.

## Exact selected graph replay

`scripts/replay_qb_graph.py --all-controls --check` obtains the initial state from
independently verified raw traces, replays the recovered original graph rules
with explicit single rounding, and compares every six-column cell with the DOS
world. It does not create, modify or select a production world/profile.

| Native control | Initial state | Cells matched | Draws including HQ | Final state |
| --- | --- | --- | --- | --- |
| Midnight before repair |0xc805|18000 / 18000|27734|0xf5b72b|
| Midnight after repair |0xc805|18000 / 18000|27754|0xdaa8af|
| Midnight full graph |0xc805|18000 / 18000|27770|0xc3cfff|
| 12:34 full graph |0x275905|18000 / 18000|27927|0xd1df02|

The full graphs reproduce the ordered 19 repair pairs and 15/13 Earth shortcuts.
Results retain source world/log/trace hashes and measured TIMER bytes in
`replay-results.json`; ordinary checking never rewrites that report unless an
explicit output path is supplied.

An important negative-control limit: zero versus one pre-graph draw can produce
the same final graph and final RNG state in these examples. An otherwise unused
offset draw for Earth's already occupied first slot resynchronizes the streams.
Thus graph equality alone cannot prove the HQ draw count. Its native instruction
provides independent evidence. Prefix 2 and wrong-seed controls diverge; changed
worlds or rehashed traces are rejected. These checks are not replaced by a broad
claim that any perturbed input must always change the graph.

## Boundaries and next work

- Implemented and verified: the BRUN30 24-bit recurrence, exact numeric
  argumentless RND, raw-byte RANDOMIZE transformation, low-byte preservation,
  initializer `-TIMER` path and the observed midnight residue.
- Selected fixed-clock graph phases replay exactly in a research model. Modern
  `-dos-warps` and `-dos-ports` continue using their existing Go streams and
  deliberate bounds/duplicate/self-link policies. Save format remains 34.
- Follow-up [port replay](../yt-port-replay/RECOVERY.md) verifies full placement,
  naming and economy consumption across six retained clock worlds and twelve
  native phase endpoints. Other clock points, other RND argument variants and
  complete MBF boundary arithmetic remain open.
- General DOS seed-to-universe production mode, exact DOS saves and original bugs
  are not introduced by this research. Any later integration needs a separately
  named compatibility policy while preserving existing saves and safeguards.

## Verification

```sh
python3 scripts/verify_rng_clock.py
python3 scripts/test_verify_rng_clock.py
python3 scripts/verify_rng_trace.py
python3 scripts/test_verify_rng_trace.py
python3 scripts/verify_rng_native.py
python3 scripts/test_verify_rng_native.py
python3 scripts/replay_qb_graph.py --all-controls --check
python3 scripts/test_replay_qb_graph.py
go test -race -count=1 ./...
go vet ./...
```

There are 24 Python test methods across clock, trace, native and replay checks,
including rehashed semantic corruption and non-identifiability controls. Go tests
run from the portable fixture without DOSBox or original binaries. Hosted CI uses
the retained evidence; native BBS acceptance and general clock/platform replay
remain separate.

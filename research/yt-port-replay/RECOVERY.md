# Exact initializer port stream replay

This is a research model, built on the [raw RNG recovery](../yt-rng-seeding/RECOVERY.md)
and retained [port native observations](../yt-port-generation/RECOVERY.md).
It introduces no production generation mode, save schema change or DOS import/export.

## Verified scope

Six original 3,000-sector/1,000-port worlds (midnight, repeat, +1 second,
+2 seconds, 12:34 and next date) reproduce all 18,000 graph cells, all
137,000 bytes of the port records and all 3,000 sector port links per world.
[Results](replay-results.json) retain source hashes, measured seeds, rejection
counts, draw counts and independently observed phase-end states.

The additional +2-second raw seed probe measures TIMER as 1.97 seconds, raw
`f6287c81`, whose negated FAC produces seed `a90a05`. The requested clock alone
is not used to infer the seed. Its independent verifier reuses the raw probe
contract with explicit one-case coverage; the parent sixteen-case corpus stays fixed.

Twelve copied-initializer controls in `state-dos` independently observe state
following graph generation, all placements and all port writes at four clocks.
The 65-byte hook occupies unused NOP space at main `2606`, replacing only a
print-begin token at `18ee`, `1a4d` or `1ecf`. It preserves registers, flags and
scratch words, writes marker plus state, then returns. The omitted print token
is an explicit diagnostic change. Every complete output world must match its
unhooked baseline byte for byte. Original archives are unchanged. The checker
reconstructs the entire patched executable and pins observed states independently
of editable metadata. Repeat/next-date have no additional state-hook runs.

| Clock | Graph end | Placement end | Port end | Placement draws / rejected |
| --- | --- | --- | --- | --- |
| Midnight | c3cfff | 54bf86 | 1ca785 | 1217 / 221 |
| +1 second | 6af4df | 451a25 | bcd835 | 1222 / 226 |
| +2 seconds | 38cb82 | 1ae0f8 | 79697c | 1198 / 202 |
| 12:34 | d1df02 | 6c4e19 | 34b8fc | 1197 / 201 |

## Random consumption and raw records

All 996 random placements precede economy/name construction. Each port consumes
three production draws (`INT(RND*31767)+1000`), three negative coefficient draws
(`-(INT(RND*100)+1)`), a generated name except Earth, then one class draw. Class
selects which coefficient becomes positive. All arithmetic follows the bounded
single-precision operations demonstrated by these controls.

The weighted DATA pool contains 908 entries, including duplicates. Name chunk
count is `INT((RND1*RND2)*3)+2`, with single-precision rounding after each
multiplication. Each chunk consumes another draw. Long chunks acquire a leading
space and initial capital; the first leading space is removed and the first
character capitalized. The model reads the pinned original DATA independently
of the production Go pool.

Full-record comparison includes name padding and length, dates, all MBF fields,
unmapped bytes and Earth’s inherited configuration tail. Nine numeric-zero
fields retain raw `0000a000`; replacing them with canonical zero is numerically
equal but fails byte comparison. Earth retains its earlier random HQ sector,
port count and configuration value; ordinary port tails remain zero.

The original occupancy initialization protects sectors 1/2/3/4 while the first
ports occupy 1/3/5/7. At +2 seconds, port 274 overwrites sector 7’s link to port 4;
both records remain. This defect is deliberately retained only by the research
model. Modern generation continues enforcing its established safeguards.

## Validation and remaining work

Run the portable checks without DOSBox, Java or REA:

```sh
python3 scripts/verify_port_replay_seed.py
python3 scripts/test_verify_port_replay_seed.py
python3 scripts/verify_port_rng_states.py
python3 scripts/test_verify_port_rng_states.py
python3 scripts/verify_port_replay_targets.py
python3 scripts/test_verify_port_replay_targets.py
python3 scripts/replay_qb_ports.py --check
python3 scripts/test_replay_qb_ports.py
```

The report is generated explicitly with `--output`; ordinary verification never
rewrites it. Tests reject rehashed state, clock, patch and world corruptions,
including raw zero changes invisible to selected numeric-field comparisons.
Native interpretation reuses retained initializer observations from port,
warp and RNG recovery; no new successful REA export is claimed for this slice.

These six clocks establish the selected graph/port stream, not all initializer
records or general MBF emulation. Remaining records, arbitrary clocks/platforms,
other RND arguments and any production compatibility profile require separate
work. Save format remains 34; existing worlds, startup prices, exports/restores
and production `-seed`, `-dos-ports`, `-dos-warps` behavior are unchanged.


## Complete-record follow-up

The [complete initializer replay](../yt-initializer-replay/RECOVERY.md) now adds
configuration, inactive players, complete sector/HQ records and inherited planet
slots across ten bounded controls. This supersedes the remaining-record deferral
above for those targets; general MBF, arbitrary inputs, production integration
and initial maintenance remain separate.

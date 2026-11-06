# Final-pointer convergence and an exact evolved-world chain

This milestone retains **18 complete original-DOS maintenance runs** and
**12 separately labelled early-cache probes**. Six independent modes carry one
world through November 2, 3 and 4, 2026. All six complete output files agree
across modes on each day: **108 full-run output files**. Every child and probe
inherits its corresponding parent mode's six output files byte-for-byte:
**144 input-file links**, with no reset, reconstruction or intervening patch.

This answers the acquisition task left by the
[complete active-world replay](OCCUPIED_RECORD_REPLAY.md). It is not before-only
record synthesis for the evolved children. No Go gameplay, dependency,
`qb36-v1` fingerprint or save **35** changes. Older exact next-day research
chains remain valid; this chain specifically adds actual final-pointer
convergence, early-cache observation and complete six-file inheritance.

## Declared input and independent modes

The first day uses the retained original 4151-record baseline plus one ordinary
slot-2 planet, **Convergence Haven**, linked at sector 2802. It has owner -1,
ground 500000, cargo rates 1000, prior production timestamp 305, a padded name
and active name length; all other numeric planet fields are zero. Reserved home
slots remain initially missing, as in the earlier initial-world controls.

The selected sector is the first preferred candidate in the already recovered
one-active-planet stream. Its real positive link supplies the original preferred
target predicate. The directed route does not cross the newly restored neutral
Wanderer. This was a declared controlled fixture, not an after-world edited to
make duplicate pointers appear.

For each date, the full modes are two unobserved runs, one attach-only and three
source-clock-observed runs. Original YTMAINT and BRUN30 bytes remain unchanged in
full runs. Each child copies **YTDATA, YTNAME, YTNEWS, YTYNEWS, YTRMSG and
YTSCORE** directly from its own parent mode. The output corpus retains all actual
before bytes as well as complete after files, hashes, launch/controller logs,
loaded observer source, actual clock frames and original transcripts.

## Actual final convergence and next-day normalization

The first run's stored mobile pointers 2–19 all end at sector **2802**. Their
announced individual forces sum to the **6552 physical fighters** stored there.
HQ sector 849 retains 3095, and group 20's sector 1169 retains 353. Total physical
Xannor force is 10000. These are observed final pointers and physical records,
not synthetic duplicate input pointers.

Each of the six next-day early-cache probes shows:

- group 1: location 849, force 3095;
- group 2: location 2802, force 6552;
- groups 3–19: normalized zero locations and forces;
- group 20: location 1169, force 353.

Only three physical sectors are consumed. Eighteen references to sector 2802
load its force once. Stored group pointers clear to canonical `00000000`; the
consumed physical force/title fields use source-specific zero **`00008000`**.
The second day's full maintenance then allocates seventeen missing groups from
HQ and disperses to twenty distinct positive pointers while preserving total
physical force. The third-day cache starts with twenty distinct groups and
requires **no shrinking-bound allocation calls**.

Across twelve probes, **all 480 source-owned raw cache cells** agree with the
independently reconstructed before-world normalization. Each probe writes 168
bytes containing forty source-owned cells plus two unused cells; the latter are
retained raw but receive no invented semantic value. The probes are explicit
patched early exits, not full maintenance runs or untouched output goldens.

| Date / stage | Single / shrinking helper calls | Positive final pointers | Unique final physical locations | Physical Xannor |
|---|---:|---:|---:|---:|
| November 2 / day 1 | 42 / 19 | 20 | 3 | 10000 |
| November 3 / day 2 | 41 / 17 | 20 | 20 | 10000 |
| November 4 / day 3 | 42 / 0 | 20 | 20 | 10000 |

The counts come from authenticated source frames. The third day's twenty
fallback helper calls include one same-origin retry. An optional unnamed lottery
selection occurs on each day. Fixed initial 41/19 counts would fail to describe
these evolved runs. All observed date/time callbacks authenticate with existing
source context definitions; no new caller was guessed or silently accepted.

## Other state carried through the chain

Wanderer sectors evolve **2787 → 2255 → 2290**. Mercenary Base stays at sector
2177. The ordinary friendly planet's ground evolves **505000 → 510050 → 515150**.
Four active planets' heterogeneous cargo, banks, ground, production times and
inventories continue through later days; they are not restored to initial
values. Persisted mines accumulate at sectors **1169, 439 and 474** without
physical fighter casualties in these runs.

The second and third public journals contain maintenance/Xannor/Mercenary
headings and zero-regeneration reports, without repeating missing-home or
regeneration notices. Private files remain empty. Each saved YTYNEWS is exactly
its input YTNEWS; score and all other prior side files are inherited before the
original writers act. Cached pointers are not interpreted as eighteen separate
copies of the shared physical force when verifying score/accounting.

## Provenance and source evidence

[The immutable corpus](convergence-chain-controls/) contains **794 files** and
six frozen acquisition sources. Pins SHA-256:
`164cc9d62bef6b213226ca8e125e39d282e6b851a9b6ffaf048e933a290d1f8c`.
The independent verifier reconstructs the first before-world, checks every
same-mode parent edge, exact launch/CPU/date/controller provenance, unmodified
full-run guests, the precisely reconstructed early-exit patch and all raw cache
fields. No failed or forced run is counted; all thirty captures returned
naturally without a capture retry.

The early probe is the previously verified 29b7 boundary, widened to exactly 168
output bytes. It changes only the declared 46-byte code area and five-byte site
jump in a disposable YTMAINT copy. BRUN30 and archive originals are unchanged.
A probe inherits its parent's old YTSCORE file and exits before scoring; that
inherited file must not be presented as a newly published scoreboard.

Existing complete REA observations already cover normalization and writeback:

| Existing range | Source scope | Evidence |
|---|---|---|
| `0x126c9` / 744 | Physical load/consume and duplicate normalization, CS26c9–29af | `ev_c735edcbe656b109fab6c962d9a7b6f1dc190542d52f91a538751c205e4e0082` |
| `0x13e30` / 323 | Final physical addition, including CS3ee8–3f4c | `ev_3255ab9a457214c46a48d189275b4ac24a898f0068bb2e245e777cb758a6b98d` |

Those [retained native reads](PLACEMENT_COLLISIONS.md) are reused, rather than
queried again. Static code and separately observed full/probe effects remain
distinct evidence types. No new provider installation, configuration change or
native byte packet was needed.

## Reproduction and next integration

```sh
python3 scripts/verify_maintenance_convergence.py
python3 scripts/test_verify_maintenance_convergence.py
# Actual acquisition requires the pinned installed DOSBox and Frida17.23.2:
python3 scripts/recover_maintenance_convergence.py /tmp/new-convergence-chain \
  --scratch /private/tmp/new-convergence-mounts \
  --frida-module /absolute/path/to/frida.js
```

All 39 independent provenance/semantic tests pass, including forged parent files,
duplicate force, cache zeros, missing source events, raw clock/header disagreement
and early-probe scoreboard substitution.

Acquisition requires fresh destinations and stops on a failed controller;
portable verification launches no emulator, Frida, Go program or network access.
All earlier corpus pins, strict replay APIs and source admission boundaries stay
unchanged. README, current plan and portable CI checks accompany this milestone.

**Next integrate this measured three-day chain into a separate before-only
profile.** The new pieces are one-day nonempty port updates; four heterogeneous
active planets; existing Wanderer/home paths with optional creation clocks;
seventeen then zero new group allocations; inherited inactive ranks and exact
old side files; and persistent mines. Reuse the already recovered cache,
economy/combat formulas and source ordering. Before-only evolved-world synthesis,
general MBF, arbitrary worlds, live BBS and native Windows durability are not
established by these controls alone.

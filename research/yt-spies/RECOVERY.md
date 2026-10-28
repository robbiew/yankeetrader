# Spies and intelligence reports — research

This slice studies the original DOS 3.6 executable. It does not implement Go
spy gameplay. README updates were verified in every merged PR #22–28; those
feature descriptions remain implementation claims, distinct from this research.

## Evidence and reproduction

`rea.json` retains Ghidra 12.1.4 byte Evidence for the unchanged executable
SHA256 `c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037`.
Addresses are loaded linear coordinates with MZ relocation segment 0x1000.
The verifier independently reconstructs relocated bytes from the archived EXE.
These are byte observations; the control-flow interpretation below also uses
preserved QuickBASIC annotations, not a claim that Ghidra decompiled BASIC.

Run `python3 scripts/recover_spies.py /private/tmp/yt-spies-new` with DOSBox
Staging installed, then `python3 scripts/verify_spies.py /private/tmp/yt-spies-new`.
The runner copies the archived fixture into disposable directories, hires through
Earth's ordinary shop, and preserves input, transcript, compressed full before/
after saves and hashes. It never mounts the archive. Date is 10/24/2026;
clock starts 00:00:00. Small controlled outgoing-warp graphs remove movement
randomness without injecting the session's spy array. `expected.json` fixes
semantic outcomes independently of emulator timing.

Earlier [hire/reconnect probes](../yt-navigation/COMMERCE_RADIO.md#hiring-and-reconnecting-spies)
establish 333,000 credits each, a three-spy cap, one docking turn, and no spies
when reopening the exact one-spy save. They remain the reconnect evidence;
the new sessions do not independently test reconnect or message-file retention.

## Static search and movement model

- Main `1000:7a7b..7cb7` validates quantity and starting sectors, charges the
  fee and stores locations in session array DS:4b74; DS:50ae is active count.
  Computer option 15 (`1000:a382..a419`) lists those current hunt locations.
- Main `1000:a6e4..a6f2` calls sub2 `2e79:1d3a..257a` with active count.
  Callers of the enclosing routine include manual movement (`1cae`), fighter
  deployment (`2253`), docking (`6693`) and an unavailable-information branch
  (`a1da`). This is not evidence that every command or every spent turn runs it.
- Each spy examines its current sector before choosing its next warp. A
  remembered last-reported sector (array index plus four) suppresses scanning
  when the current location equals that nonzero sector (`1d86..1db7`).
  The report header updates that remembered sector (`24a5..2574`).
- Findings include disruption locations, mine count, planet name/forces,
  other ships' names/team/fighters/shields, and foreign sector defenders with
  player/team or Xannor/Mercenary ownership (`1dda..234e`). Caller-owned sector
  defenses are excluded; the caller's own ship is excluded.
- Cloak inspection (`1f55..2013`) compares a random draw with the cached
  cloak fraction. A successful shimmering report clears the session's cached
  cloak entry before ship reporting. Do not interpret that write as proven
  persistent cloak-energy damage. Exact RNG parity remains unestablished.
- Movement (`238a..2478`) samples one of six warp slots repeatedly until it
  selects a nonzero destination, then writes that sector to the session array.
  It does not use shortest paths. An all-zero-warp sector needs an explicit
  safe Go policy; this code alone does not establish its runtime behavior.

## Implementation boundary

The next implementation should keep spy count, current position and last-report
position bound to the live account/session, validate hires atomically, and define
whether reports enter durable radio history as a deliberate adaptation. Do not
silently persist spies across reconnects: that contradicts the existing observed
DOS slice. Mutation/read privacy, stale sessions, disconnect delivery and safe
zero-warp handling need explicit tests. Broader random-branch sampling, repeated
multi-spy interactions, disruption reports and target notification/persistent
cloak effects remain separate research boundaries.

## Runtime results

| Probe | Listed locations, including hire | Intelligence headers | Final turns |
| --- | --- | --- | --- |
| List twice | 101, 101, 101 | 0 | 499 |
| Sensors and list twice | 101, 101, 101 | 0 | 499 |
| Move out/back, empty route | 101, 102, 101 | 0 | 497 |
| Mines and planet | 101, 102, 101 | 1 | 497 |
| Foreign defenders | 101, 102, 101 | 1 | 497 |
| Self-loop with mines | 101, 101, 101 | 1 | 497 |
| Cloaked target fixture | 101, 102, 101 | 0 | 497 |

All hire exactly one spy and finish with 1,667,000 credits. The populated report
contains seven mines and `Planet: Test Planet * Forces: 12`. Foreign defenders
report 42 fighters belonging to Enemy, team 1 / Orion. The self-loop reports
its mines once across two player moves; it retains its hunt location without
another header. The final list in the ordinary loop returns to 101, but does
not itself scan 101 again; this does not prove a report on a later revisit.

The populated fixture also places an uncloaked target at 101, while the cloak
fixture places the same target there with cloak fraction one. Neither produces
a ship line. Consequently these probes do **not** establish ship eligibility,
cloak detection odds, or a cloak-based visibility difference. Those paths above
are static interpretation only and need a successful positive runtime control
before implementation. The sensor probe's `S` command is a sensor scan, not ship
status. Extra input retries may produce an invalid-command line; the verifier
requires the intended lists, moves, reports, resource totals and clean return,
not merely process exit.

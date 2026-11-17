# Bounded Go occupied casualty news and faction scores

`ReplayOccupiedAux` takes exactly three original before files, a modeled finalized
world, explicit separate news/score dates/clocks and source-ordered typed combat
events. It returns five owned auxiliary files plus calculated faction statistics,
or nil files/zero statistics on error. It does not run maintenance, finalize a
world, read targets/files/host time, compress private mail or mutate caller data.

Admission retains default geometry and scoreboard path, inactive human assets
and published -1 ranks, missing NPC homes before/expected names after, the clean
ordinary slots 2/3 and unchanged surviving ordinary names/owners. Before taxes
are zero. Physical forces are whole, bounded and owned by Xannor, Mercenaries or
neutral; totals are limited to the measured 10000-Xannor and optional 37/100000
Mercenary or 37-neutral contexts. Each sector contributes once, independently
of group pointers. Capped event losses must conserve every physical faction.

Events have one typed primitive payload, ordered groups 2–20 at the retained
sector854 encounter. Dead groups cannot emit another event. Neutral Route Haven
events require its actual neutral before-context and group death. Defense events
require actual Mercenary before-context, one surviving side and bounded raw
damage counters covering capped losses. These validate declared modeled receipts;
they do not attest arbitrary caller-authored events as native execution.

## Formatting and source behavior

The writer reuses the existing DOS bootstrap report formatter without widening
its old public APIs. Ordered casualty lines are inserted before the Mercenary
report. Ground attacks use the actual initial moving force and Route Haven name.
Foreign-defense text preserves raw counters and the original misleading `Plyr
ftrs dstrd` / `Xannor ftrs dstrd` suffixes; it does not invent human deaths or
repair labels. No console-only movement becomes public or private mail.

NPC scores are 100 times final unique physical force; neutral force is conserved
but unscored. The larger NPC score supplies the denominator. Percentage display
uses exact integer quotient/remainder arithmetic with 64-bit intermediates and
the original two-decimal widths. Exact halfway cases and a zero denominator are
explicitly refused, preserving the Python profile's unqualified formatting
boundary. This is not a general PRINT USING or active-human ranking formatter.

Names copy unchanged, current news rotates byte-for-byte to yesterday's news,
and private messages remain empty. DOS CRLF/final EOF, comma grouping and spacing
are preserved. Separate report calendars/clocks include exact `24:00:00` without
carrying the date; no host timestamp is introduced.

## Existing evidence and tests

The exporter instruments the existing complete occupied Python runs. It captures
modeled finalized worlds, original before files, 120 calculated combat events
and five expected report hashes in 30 cases. Every completed run precedes native
target comparison. Independent qualification remains **180 six-file comparisons
/1080 native files and 1872 RNG witnesses**, plus the existing original-source
packet. No native case before-world, output or captured RNG endpoint corrects
synthesis. Original bytes/hashes and acquisition attribution are unchanged.

Go tests match all 30 complete five-file sets and faction/loss/percentage receipts.
They also compute actual Go capped ports, ordinary economy and home/mobile
routing, then feed those calculated events into this writer. The finalized world
in this test still comes from the independently modeled Python fixture: this
qualifies event-to-report composition, not complete Go six-file maintenance.

Tests cover positive Mercenary leadership (5.28% Xannor), unscored neutral force,
source suffixes/order, raw binary journal rotation, separate calendars/clocks,
DOS framing, owned output and immutable inputs/events. Unsupported assets, event
ordering/payloads, forged casualty totals, raw counters, source contexts, clocks,
halfway percentages and zero denominators fail without partial publication.
Exporter controls reject changed inputs/outputs/statistics/source identities,
native-file corruption and poisoned witnesses, enforce synthesis-before-target
ordering and permit equivalent gzip recompression by complete raw bytes.

```sh
python3 scripts/export_occupied_report_fixture.py --check
python3 scripts/test_export_occupied_report_fixture.py
go test ./internal/qbmaint -run TestOccupiedReports
```

Next compose the Go routing/reports with the downstream Mercenary/lottery tail
and final watermark/ranks, then qualify all six occupied-world files. Existing
research CLI profiles, historical admission, modern gameplay/save 35, releases
and native Windows/live BBS acceptance remain unchanged.

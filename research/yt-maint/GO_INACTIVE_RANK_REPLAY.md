# Bounded Go inactive rank-cache and watermark writer

`qbmaint.ReplayInactiveRanks` now ports the separately recovered all-inactive
writer from `configuration_and_inactive_ranks` and the clock-matrix counterpart.
It takes an independently modeled default-layout world and an explicit final
source day. It accepts no after-world, correction table or report template.

The writer sets the configuration day watermark at record 1 offset 81 and
resets the rank-cache field at offset 109 in all fifty player records to raw
MBF -1. Every other world byte is preserved. All player activity fields at offset
85 must be numeric zero, including raw aliases; active-player ranks remain
excluded. Default 4151-record geometry and final day 1..732 are guarded. Errors
return no world and leave input storage unchanged; successful output is copied.
The caller authenticates the day and supplies a modeled world. This function
does not derive a host date or migrate modern saves.

## Reused captures and separate oracle validation

No new DOS captures were acquired. The same four fresh-calendar and eight
saved-base-year matrix profiles supply 32 observed runs. All 51 written fields
per run / 1,632 complete four-byte fields match the existing Python writer and
Go output. Fresh calendars use their observed day of year; matrix schedules use
the independently observed final date and the qualified saved-base-year day
helper. Native targets are loaded only after before-only synthesis.

The new fixture references the clean-port fixture's deduplicated before-worlds
instead of copying them. Its exporter authenticates the parent capture chain,
retains complete native writer fields and binds schedules/before identities and
Python/exporter fingerprints. Three exporter regressions reject altered fields,
source inventories, days, before identities and dropped/duplicated controls.
Go tests compare every field, check every unrelated byte, input/output isolation,
late active-player rejection, geometry/day bounds and inactive zero residues.

```
python3 scripts/export_inactive_rank_fixture.py --check
python3 scripts/test_export_inactive_rank_fixture.py
go test -race ./internal/qbmaint ./internal/qbmbf ./internal/qbinit
```

This is field-writer equality, not a complete Go world/maintenance replay.
NPC movement, active rankings, auxiliary text, calendar generation, other phases,
production integration and native Windows/live-BBS acceptance remain separate.
The clean-port replay and independent Python references remain unchanged.
Gameplay, save format 35, initializer fingerprints and sysop procedures are
unchanged. Next, audit bounded NPC bootstrap/placement against existing capture
coverage before choosing its first Go migration.

# Public planet-creation news validation

Branch: `feat/planet-creation-news`, based on newspaper-event research `8fcc8fe`.
World format: **28**, upgrading supported formats 1–27 without historical backfill.

## Passed locally

- `go test -race ./...` and `go vet ./...`.
- Focused creation tests, including journal capacity/pruning, immutable snapshots,
  strict event validation, no-backfill migration, negative input/resource/archive
  cases, aborted transaction rollback, concurrent duplicate requests, committed
  directory-sync warnings, wrong bound identity, location/generation/season
  changes, pre/late/lock-wait expiry and disconnected receipt output.
- `scripts/smoke_planet_creation_news.py`: real compact/classic GoDoors; initial
  decline, rejected-name retry, one debit/event, no turn charge, reconnect public
  newspaper reading and rename-proof accepted-name snapshots. The fresh transcript
  is [planet-creation-news-smoke.txt](planet-creation-news-smoke.txt).
- Existing newspaper PTY and all ten compact/classic planet-mobility scenarios.
- Broadcast, multiline editor and spy-trigger PTY regressions.
- Newspaper date/rollover runner's three unit tests.
- Native `verify_newspaper_events.py` (34 returned controls/four reload chains),
  all six verifier tests and 54 negative variants; all 4,682 archive files.
- Linux/amd64 and Windows/amd64 builds.

Existing fixture-generated newspaper/radio transcripts are restored rather than
mixed into this milestone. Historical migration fixtures explicitly omit creation
news; mobility fixtures isolate their later event assertions from setup creation.
Current-save smoke assertions now require version28; intentional old migration
inputs remain old versions. CI includes the new creation PTY command.

These checks do not establish hosted CI, live BBS acceptance or native Windows
crash durability. Private former-owner port-sale notices remain unimplemented.
[Rules and migration](../research/yt-newspaper/events/IMPLEMENTATION.md).

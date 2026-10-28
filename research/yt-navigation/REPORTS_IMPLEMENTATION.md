# Remote computer reports

Computer options 2 (port report), 9 (planet report), and 13 (personal planet
finder) are implemented, with compact aliases `PORTREPORT [sector]`,
`PLANETREPORT [sector]`, and `MYPLANETS`. Missing sector arguments prompt for
input; a blank answer cancels. No save-format change is needed.

## Evidence and behavior

This milestone uses the existing [23-session utility research](UTILITIES.md)
and its preserved original-DOS worlds/transcripts. It adds no DOS sessions and
does not claim full screen/color parity.

- `utility-port-known`, `utility-port-empty`, and `utility-port-guarded` establish
  the ordinary-port report and free unavailable/defended cases. The output shows
  the port's buying/selling direction, projected supply and prices, and the
  caller's cargo. No port treasury or private account data is returned.
- `utility-planet-report`, `utility-planet-owned`, and
  `utility-planet-unguarded` establish full accessible reports.
  `utility-planet-private` establishes the name/ground-force-only boundary.
- `utility-planet-guarded` establishes complete denial and its one-turn cost.
  The charge and disclosure decision run together under the store lock. A query
  blocked by sector fighters is refused with no turns left; invalid sectors and
  cancelled prompts spend nothing. Turn charges use the existing cloak-decay
  rule. Denial occurs before looking for a planet, avoiding a presence disclosure.
- `utility-planets` and `utility-planets-foreign` establish a personal finder.
  It sorts by sector and excludes foreign and shared team assets.

Reports preserve position, ship assets, docking/landing state and stored
economic state, except the documented blocked-query turn charge. Port and full
planet growth is projected on value copies using existing economic rules.
Projected prices are information; docking still supplies the binding quote.
Private reports do not return hidden inventory/bank fields.

## Explicit policies and boundaries

Current team access reuses the modern planet landing policy, including immediate
revocation when membership changes. The DOS utility suite did not establish team
report behavior. Personal finders remain personal regardless of team membership.
Ground-force growth is projected before checking access, so regenerated foreign
defenses protect inventory and bank details even when the stored ground count is
zero. The projected public ground count is shown without changing stored assets.
Each input prompt is followed by a fresh authoritative read/update, so ownership,
sector defenses and ship generation are rechecked before disclosure or charging.

Earth is an equipment service rather than an ordinary cargo market. Its remote
report remains unavailable; the existing Earth shop provides actual equipment
prices. Nearest-port, port-pair, adjacent-profit, ranking, spy and newspaper
functions remain outside this milestone. Native BBS acceptance remains separate
from the local terminal evidence.

## Validation

`internal/game/reports_test.go` covers accessible/private/missing/blocked reports,
team policy, price and growth projections, no live-state aliases, invalid input,
zero-turn rejection, and personal finder filtering. Store tests cover competing
last-turn queries and transaction rollback. A regenerated-ground regression
checks private, personal, team and unowned reports without saved-state changes.
Door tests exercise classic numeric
and compact dispatch, cancellation, private output and an ownership change while
the sector prompt waits.

`python3 scripts/smoke_reports.py` exercises real GoDoors terminals: classic
computer options 2/9/13, private and full planet detail, sector-defense denial,
the saved one-turn charge, and reconnect. It writes
`evidence/reports-smoke.txt`. CI runs this smoke and the existing utility-evidence
verifier in addition to the normal race-enabled tests and vet checks.

# Nearest-port and trade-route reports

Computer 14 (nearest ports), 16 (port pairs), and 17 (adjacent-port forecasts)
are implemented. Compact aliases are `NEAREST [filter]`, `PAIRS`, and `PROFITS`.
All are free reports, including at zero turns, and do not move, dock, trade,
issue tokens, or alter saved stock, money, or route preferences. Save version
10 is unchanged by this milestone.

## Recovered baseline

The eight commerce cases in [the existing DOS report](COMMERCE_RADIO.md)
establish nearest-port distances/order, player-side buying/selling filters,
team rejection without membership, a pair with a longer directed return,
current-port requirements, and the spread's independence from cargo holds.
This implementation adds no DOS sessions and makes no new full-parity claim.

The captured quote example is ore 10 -> 30 and organics 15 -> 44, yielding
`(30 - 10) + (44 - 15) = 49` credits per unit of each commodity. Tests recreate
those quotes using controlled Go market coefficients and the captured graph
shape. These are quote regressions, not imported DOS saves or a change to the
existing Go price formula. Production, stock and prices come from current Go
rules, projected on detached copies as in the ordinary port report.

## Modern report policies

- `NEAREST` defaults to all accessible ordinary ports. It supports personal,
  current-team (including self), enemy (excluding team/self/unowned), and unowned
  filters, or a commodity with the player's buy/sell action. A team filter with
  no current membership is rejected. Distance includes a current port at zero
  warps; ties use ascending sector order.
- Directed breadth-first searches apply every nonzero AVOID slot. As with PATH,
  an avoided current sector must be cleared before plotting. Earth is a service
  port and is omitted. Hostile sector defenses hide a market just as they do in
  the ordinary port report. Transit hazards can still interrupt travel; a graph
  route is not a promise of safe passage.
- `PAIRS` considers directed edges between reachable ordinary markets. `PROFITS`
  restricts the starting market to the caller's current sector. Both require
  an available directed return path, complementary trade directions, a positive
  summed spread, and stock/demand for at least one whole unit of both goods.
  Unreachable round trips are omitted rather than described as two-way trades.
- Each pair shows the highest spread among its commodity combinations. Reciprocal
  edges are deduplicated, preferring the starting port closest to the caller,
  then the lower sector. Results sort by approach distance, start and destination.
  Approach, outward and return figures are warp counts; docking turns are excluded.
- A spread is per unit of each commodity. Displayed stock/demand limits are port
  constraints; cargo capacity, cash, existing cargo and future prices/stock are
  not forecast. No ship-income or profit-per-turn guarantee is made.
- Each page shows at most four entries. Enter requests another page; Q or another
  nonempty answer stops (Y also continues). Paging uses separate terminal input
  and preserves queued game commands. Every page performs a fresh bound read and
  recomputes permissions, membership, position, avoid preferences and quotes.
  Changing state may shift or remove entries; old hidden quotes are not cached
  across a prompt. Disconnect or generation invalidation stops the report.

Owner/team filters with populated rosters, avoid interaction, return-route
eligibility, stock filtering, tie ordering and pagination are explicit modern
policies beyond the bounded DOS probes. Original assets remain unchanged.

## Validation

Game regressions cover captured distances and quote spread, 10/100-hold ships,
direct versus longer returns, missing returns, avoid lists, defended markets,
exhausted/fractional stock, zero spreads, membership changes, private-account
exclusion, bad requests and byte-identical world state after reporting.
A 3,000-sector universe regression also checks pair deduplication and samples
return distances against the existing player path finder.

Door regressions cover computer 14/16/17 and compact dispatch, zero-turn use,
invalid requests, fresh reads after filter input, and a new defense appearing
while paging without consuming queued commands. The real terminal script
`scripts/smoke_trade_reports.py` exercises these commands, both return distances,
avoid and guard behavior, forecast labels and persisted asset conservation.
Its transcript is `evidence/trade-reports-smoke.txt`.

CI runs the existing `verify_commerce_evidence.py`, normal race-enabled Go tests
and vet, and the new terminal smoke. Native BBS acceptance remains separate.

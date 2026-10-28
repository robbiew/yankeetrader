package game

import (
	"errors"
	"sort"
	"time"
)

type PortFilter struct {
	Ownership string // all, own, team, enemy, unowned
	Good      string
	Action    string // The player's buy/sell action, not the port's action.
}

type NearestPort struct {
	PortReport
	Sector, Distance int
	OwnerID          int
	OwnerAlias       string
}

func (w *World) reportRouting(id int, now time.Time) (*Player, map[int]bool, error) {
	p, err := w.player(id)
	if err != nil {
		return nil, nil, err
	}
	if now.IsZero() || now.Before(w.Created) {
		return nil, nil, errors.New("invalid report time")
	}
	avoid := make(map[int]bool)
	for _, sector := range p.AvoidSectors {
		if sector != 0 {
			avoid[sector] = true
		}
	}
	if avoid[p.Sector] {
		return nil, nil, errors.New("current sector is in your avoid list; clear it before plotting reports")
	}
	return p, avoid, nil
}

func (w *World) reportDistances(from int, avoid map[int]bool, reverse map[int][]int) map[int]int {
	distances := map[int]int{from: 0}
	queue := []int{from}
	for head := 0; head < len(queue); head++ {
		sector := queue[head]
		links := w.Sectors[sector].Warps
		if reverse != nil {
			links = reverse[sector]
		}
		for _, next := range links {
			if _, seen := distances[next]; seen || avoid[next] {
				continue
			}
			distances[next] = distances[sector] + 1
			queue = append(queue, next)
		}
	}
	return distances
}

// NearestPorts returns detached commerce projections for reachable, accessible
// ordinary ports. Distance ties use sector order; no account state is changed.
func (w *World) NearestPorts(id int, filter PortFilter, now time.Time) ([]NearestPort, error) {
	p, avoid, err := w.reportRouting(id, now)
	if err != nil {
		return nil, err
	}
	if filter.Ownership == "" {
		filter.Ownership = "all"
	}
	switch filter.Ownership {
	case "all", "own", "enemy", "unowned":
	case "team":
		if p.Team == 0 || w.Teams[p.Team] == nil {
			return nil, errors.New("you don't belong to a team")
		}
	default:
		return nil, errors.New("choose all, own, team, enemy, or unowned ports")
	}
	good := -1
	for i, name := range Goods {
		if filter.Good == name {
			good = i
		}
	}
	if filter.Good != "" && (good < 0 || filter.Action != "buy" && filter.Action != "sell") || filter.Good == "" && filter.Action != "" {
		return nil, errors.New("commodity search requires ore, organics, or equipment and your buy/sell action")
	}
	var result []NearestPort
	for sector, distance := range w.reportDistances(p.Sector, avoid, nil) {
		report, err := w.RemotePortReport(id, sector, now)
		if err != nil {
			return nil, err
		}
		if !report.Available {
			continue
		}
		port := w.Ports[w.Sectors[sector].Port]
		owner := w.Players[port.Owner]
		teammate := owner != nil && p.Team != 0 && owner.Team == p.Team && w.Teams[p.Team] != nil
		if filter.Ownership == "own" && port.Owner != id ||
			filter.Ownership == "team" && !teammate ||
			filter.Ownership == "enemy" && (port.Owner == 0 || port.Owner == id || teammate) ||
			filter.Ownership == "unowned" && port.Owner != 0 {
			continue
		}
		if good >= 0 && report.Selling[good] != (filter.Action == "buy") {
			continue
		}
		name := "Unowned"
		if owner != nil {
			name = owner.Alias
		}
		result = append(result, NearestPort{PortReport: report, Sector: sector, Distance: distance, OwnerID: port.Owner, OwnerAlias: name})
	}
	sort.Slice(result, func(i, j int) bool {
		if result[i].Distance != result[j].Distance {
			return result[i].Distance < result[j].Distance
		}
		return result[i].Sector < result[j].Sector
	})
	return result, nil
}

type TradeRoute struct {
	From, To, ApproachHops, ReturnHops               int
	OutboundGood, ReturnGood                         int
	OutboundBuy, OutboundSell, ReturnBuy, ReturnSell int64
	Spread, OutboundUnits, ReturnUnits               int64
}

// TradeRoutes compares adjacent ordinary markets and a directed route back.
// Spread is per unit of each commodity, independent of holds or travel cost.
// Only positive spreads with stock/demand for a whole unit on both legs appear.
func (w *World) TradeRoutes(id int, adjacentOnly bool, now time.Time) ([]TradeRoute, error) {
	p, avoid, err := w.reportRouting(id, now)
	if err != nil {
		return nil, err
	}
	ports, err := w.NearestPorts(id, PortFilter{}, now)
	if err != nil {
		return nil, err
	}
	bySector := make(map[int]NearestPort, len(ports))
	for _, port := range ports {
		bySector[port.Sector] = port
	}
	if adjacentOnly && !bySector[p.Sector].Available {
		return nil, errors.New("no accessible cargo trading port in your sector")
	}
	reverse := make(map[int][]int)
	for sector, s := range w.Sectors {
		if !avoid[sector] {
			for _, to := range s.Warps {
				if !avoid[to] {
					reverse[to] = append(reverse[to], sector)
				}
			}
		}
	}
	seen := make(map[[2]int]bool)
	var result []TradeRoute
	for _, a := range ports {
		if adjacentOnly && a.Sector != p.Sector {
			continue
		}
		back := w.reportDistances(a.Sector, avoid, reverse)
		for _, sector := range w.Sectors[a.Sector].Warps {
			b, exists := bySector[sector]
			returnHops, returns := back[sector]
			key := [2]int{min(a.Sector, sector), max(a.Sector, sector)}
			if !exists || !returns || seen[key] {
				continue
			}
			best := TradeRoute{From: a.Sector, To: sector, ApproachHops: a.Distance, ReturnHops: returnHops}
			for out := range Goods {
				if !a.Selling[out] || b.Selling[out] {
					continue
				}
				for in := range Goods {
					if !b.Selling[in] || a.Selling[in] {
						continue
					}
					spread := b.Prices[out] - a.Prices[out] + a.Prices[in] - b.Prices[in]
					outUnits, inUnits := int64(min(a.Supply[out], b.Supply[out])), int64(min(a.Supply[in], b.Supply[in]))
					if spread <= best.Spread || outUnits < 1 || inUnits < 1 {
						continue
					}
					best.OutboundGood, best.ReturnGood, best.Spread = out, in, spread
					best.OutboundBuy, best.OutboundSell = a.Prices[out], b.Prices[out]
					best.ReturnBuy, best.ReturnSell = b.Prices[in], a.Prices[in]
					best.OutboundUnits, best.ReturnUnits = outUnits, inUnits
				}
			}
			if best.Spread > 0 {
				seen[key] = true
				result = append(result, best)
			}
		}
	}
	sort.Slice(result, func(i, j int) bool {
		if result[i].ApproachHops != result[j].ApproachHops {
			return result[i].ApproachHops < result[j].ApproachHops
		}
		if result[i].From != result[j].From {
			return result[i].From < result[j].From
		}
		return result[i].To < result[j].To
	})
	return result, nil
}

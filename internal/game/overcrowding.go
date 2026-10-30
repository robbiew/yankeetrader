package game

import (
	"math"
	"math/big"
	"sort"
	"time"
)

// One pass per successful daily transaction, in stable ID order. Economic
// catch-up remains capped at ten days; outbreaks never catch up or reroll.
func (w *World) overcrowding(now time.Time, rng func() float64) {
	ports := make([]int, 0, len(w.Ports))
	for id := range w.Ports {
		ports = append(ports, id)
	}
	sort.Ints(ports)
	count := 0
	canReportPorts := w.prepareNews(now) == nil
	for _, id := range ports {
		p := w.Ports[id]
		update(p, now)
		if p.Production[0]+p.Production[1]+p.Production[2] > 1_000_000 && canReportPorts {
			count++
			for i, rate := range p.Production {
				if rate > 500 {
					p.Production[i] = math.Min(1e12, rng()*rate+500)
				}
				p.Supply[i] = math.Min(p.Supply[i], 10*p.Production[i])
			}
		}
		// First positive maximum wins a tie. An all-zero port deterministically
		// sells ore; never inherit a prior port's selected commodity.
		selected := 0
		for i := 1; i < 3; i++ {
			if p.Supply[i] > p.Supply[selected] {
				selected = i
			}
		}
		for i := range p.Coefficient {
			p.Coefficient[i] = -math.Abs(p.Coefficient[i])
		}
		p.Coefficient[selected] = math.Abs(p.Coefficient[selected])
	}
	if count > 0 {
		w.appendNews(NewsEvent{At: now.UTC(), Kind: NewsPortPlague, PortCount: count})
	}

	planets := make([]int, 0, len(w.Planets))
	for id := range w.Planets {
		planets = append(planets, id)
	}
	sort.Ints(planets)
	for _, id := range planets {
		p := w.Planets[id]
		p.update(now, false)
		// Three eager, independent gates, including quiet/zero-rate planets.
		r1, r2, r3 := rng(), rng(), rng()
		kind := NewsKind("")
		if r1*(p.Production[0]+p.Production[1]+p.Production[2]) > r2*1_000_000+100_000 {
			kind = NewsPlanetPlague
		}
		if r3*float64(p.Ground) > 1_000_000 {
			kind = NewsCivilWar
		}
		// Do not silently destroy assets when journal metadata cannot record
		// their event. Full retained history rolls over normally; exhausted
		// IDs or a future journal clock defer damage, without additional draws.
		if kind == "" || w.prepareNews(now) != nil {
			continue
		}
		for i := range p.Production {
			p.Production[i] *= rng()
			p.Cargo[i] = math.Min(p.Cargo[i], 10*p.Production[i])
		}
		if p.Ground > 0 {
			a, b := rng(), rng()
			p.Ground = int64(math.Floor(float64(p.Ground) * (1 - a*b)))
		}
		if kind == NewsCivilWar {
			p.Bank -= eventDebit(p.Bank, rng())
		}
		w.appendNews(NewsEvent{At: now.UTC(), Kind: kind, PlanetName: p.Name})
	}
}

// Floor the exact product of whole credits and the injected binary fraction.
// Float multiplication near MaxMoney can round up and spend one extra credit.
func eventDebit(bank int64, draw float64) int64 {
	r := new(big.Rat).SetFloat64(draw)
	n := new(big.Int).Mul(big.NewInt(bank), r.Num())
	n.Quo(n, r.Denom())
	return n.Int64()
}

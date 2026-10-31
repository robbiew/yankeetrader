package game

import (
	"errors"
	"math"
	"sort"
	"time"
)

// Disruption belongs to a single login, never to a saved sector or public map.
// The two independent draws may select the same interior sector.
type Disruption struct {
	Player             int
	Generation, Season uint64
	Locations          [2]int
}

const MaxDisruptionWarps = 32

var ErrDisruptionLimit = errors.New("disruption chain limit reached; action aborted without spending resources")

type ForcedWarp struct {
	From, Destination, Heat int
	RechargeTurns           int64
	Meltdown                bool
}
type ArrivalOutcome struct {
	Warps                      []ForcedWarp
	Mines                      []MineOutcome
	FinalSector                int
	TurnsSpent, TurnsRemaining int64
	HostileDefense             bool
}
type arrivalContext struct {
	state        Disruption
	rng          func() float64
	now          func() time.Time
	initialTurns int64
	outcome      ArrivalOutcome
}

func warpDraw(rng func() float64) (float64, error) {
	if rng == nil {
		return 0, errors.New("missing emergency warp RNG")
	}
	r := rng()
	if math.IsNaN(r) || math.IsInf(r, 0) || r < 0 || r >= 1 {
		return 0, errors.New("invalid emergency warp RNG")
	}
	return r, nil
}

// warpHeat is shared accounting only. Trigger, destination and cloak policies
// remain separate for manual, mine escape and disruption warps.
func warpHeat(rng func() float64) (int, error) {
	a, err := warpDraw(rng)
	if err != nil {
		return 0, err
	}
	b, err := warpDraw(rng)
	if err != nil {
		return 0, err
	}
	budget := min(139, int(math.Floor(70*(a+b))))
	heat := 0
	for i := 0; i < budget; i++ {
		r, e := warpDraw(rng)
		if e != nil {
			return 0, e
		}
		if r > .75 {
			heat++
		}
		if heat == 31 {
			break
		}
	}
	return heat, nil
}
func (w *World) NewDisruption(id int, rng func() float64) (Disruption, error) {
	p, err := w.player(id)
	if err != nil {
		return Disruption{}, err
	}
	var sectors []int
	upper := 0
	for n, sector := range w.Sectors {
		if n < 1 || sector == nil || sector.ID != n {
			return Disruption{}, errors.New("invalid disruption sectors")
		}
		upper = max(upper, n)
	}
	for n := range w.Sectors {
		if n > 1 && n < upper {
			sectors = append(sectors, n)
		}
	}
	sort.Ints(sectors)
	if len(sectors) == 0 || len(w.Sectors) > 3000 {
		return Disruption{}, errors.New("no interior disruption locations")
	}
	d := Disruption{Player: id, Generation: p.ShipGeneration, Season: w.Season}
	for i := range d.Locations {
		r, e := warpDraw(rng)
		if e != nil {
			return Disruption{}, e
		}
		d.Locations[i] = sectors[int(r*float64(len(sectors)))]
	}
	return d, nil
}
func (w *World) BindDisruption(d Disruption, rng func() float64, now func() time.Time) error {
	if err := w.CheckSession(d.Player, d.Generation, d.Season); err != nil {
		return err
	}
	upper := 0
	for id := range w.Sectors {
		upper = max(upper, id)
	}
	for _, id := range d.Locations {
		if id <= 1 || id >= upper || w.Sectors[id] == nil {
			return errors.New("invalid disruption location")
		}
	}
	w.arrival = &arrivalContext{state: d, rng: rng, now: now, initialTurns: w.Players[d.Player].Turns}
	return nil
}
func (w *World) Disrupted(id, sector int) bool {
	return w.arrival != nil && w.arrival.state.Player == id && w.CheckSession(id, w.arrival.state.Generation, w.arrival.state.Season) == nil && (sector == w.arrival.state.Locations[0] || sector == w.arrival.state.Locations[1])
}
func (w *World) ArrivalOutcome() ArrivalOutcome {
	if w.arrival == nil {
		return ArrivalOutcome{}
	}
	out := w.arrival.outcome
	p := w.Players[w.arrival.state.Player]
	if p == nil {
		return ArrivalOutcome{}
	}
	out.FinalSector = p.Sector
	out.TurnsSpent = w.arrival.initialTurns - p.Turns
	out.TurnsRemaining = p.Turns
	out.HostileDefense = p.Death == nil && w.HostileDefense(p.ID, p.Sector)
	out.Warps = append([]ForcedWarp(nil), out.Warps...)
	out.Mines = append([]MineOutcome(nil), out.Mines...)
	return out
}
func mergeMines(a, b MineOutcome) MineOutcome {
	a.Bursts += b.Bursts
	a.Spent += b.Spent
	a.Dropped += b.Dropped
	a.ScannerLost = a.ScannerLost || b.ScannerLost
	a.Escaped = a.Escaped || b.Escaped
	a.Destroyed = a.Destroyed || b.Destroyed
	a.Sector = b.Sector
	if b.Destroyed {
		a.Killer = b.Killer
	}
	return a
}

// ResolveMinefield composes the login's hole-first arrival with ordinary mines.
// Other players and administrative/NPC work retain ordinary mine semantics.
func (w *World) ResolveMinefield(id int, rng func() float64, now time.Time) (MineOutcome, error) {
	if w.arrival == nil || w.arrival.state.Player != id {
		return w.resolveMinefield(id, rng, now)
	}
	return w.ResolveArrival(id, rng, now)
}
func (w *World) ResolveArrival(id int, rng func() float64, now time.Time) (MineOutcome, error) {
	p, err := w.player(id)
	if err != nil {
		return MineOutcome{}, err
	}
	if w.arrival == nil || w.arrival.state.Player != id {
		return w.resolveMinefield(id, rng, now)
	}
	if err = w.CheckSession(id, w.arrival.state.Generation, w.arrival.state.Season); err != nil {
		return MineOutcome{}, err
	}
	if now.IsZero() || now.Before(w.Created) {
		return MineOutcome{}, errors.New("invalid arrival clock")
	}
	if w.Sectors[p.Sector] == nil {
		return MineOutcome{}, errors.New("invalid arrival sector")
	}
	if p.Turns < 0 || p.Turns > 500 {
		return MineOutcome{}, errors.New("invalid arrival turn balance")
	}
	out := MineOutcome{Sector: p.Sector}
	for {
		if w.Disrupted(id, p.Sector) {
			if len(w.arrival.outcome.Warps) >= MaxDisruptionWarps {
				return MineOutcome{}, ErrDisruptionLimit
			}
			if p.WarpSequence == math.MaxUint64 {
				return MineOutcome{}, errors.New("emergency warp sequence exhausted")
			}
			heat, e := warpHeat(rng)
			if e != nil {
				return MineOutcome{}, e
			}
			if len(w.Sectors) == 0 || len(w.Sectors) > 3000 {
				return MineOutcome{}, errors.New("invalid arrival destinations")
			}
			sectors := make([]int, 0, len(w.Sectors))
			for n, sector := range w.Sectors {
				if n < 1 || sector == nil || sector.ID != n {
					return MineOutcome{}, errors.New("invalid arrival destinations")
				}
				sectors = append(sectors, n)
			}
			sort.Ints(sectors)
			r, e := warpDraw(rng)
			if e != nil {
				return MineOutcome{}, e
			}
			to := sectors[int(r*float64(len(sectors)))]
			if _, e = warpDraw(rng); e != nil {
				return MineOutcome{}, e
			}
			r, e = warpDraw(rng)
			if e != nil {
				return MineOutcome{}, e
			}
			cost := min(p.Turns, int64(4*heat)+int64(4*r))
			if heat == 31 {
				cost = p.Turns
			}
			step := ForcedWarp{From: p.Sector, Destination: to, Heat: heat, RechargeTurns: cost, Meltdown: heat == 31}
			p.Turns -= cost // Forced recharge has no ordinary movement cloak debit.
			p.Sector = to
			p.MineGraceSector = 0
			p.DockToken = ""
			p.PlanetToken = ""
			p.LandedPlanet = 0
			p.WarpSequence++
			w.arrival.outcome.Warps = append(w.arrival.outcome.Warps, step)
			continue
		}
		mines, e := w.resolveMinefield(id, rng, now)
		if e != nil {
			return MineOutcome{}, e
		}
		if mines.Bursts > 0 {
			w.arrival.outcome.Mines = append(w.arrival.outcome.Mines, mines)
		}
		out = mergeMines(out, mines)
		if p.Death != nil || !mines.Escaped {
			out.Sector = p.Sector
			return out, nil
		}
		// A supported safe mine escape may still land in this login's disruption.
	}
}

// FinishArrival is used by the store after an origin callback moved this ship.
func (w *World) FinishArrival() error {
	if w.arrival == nil {
		return nil
	}
	p := w.Players[w.arrival.state.Player]
	if p == nil {
		return ErrShipChanged
	}
	if p.Death != nil {
		return nil
	}
	if w.arrival.now == nil {
		return errors.New("arrival resolution requires a clock")
	}
	_, err := w.ResolveArrival(p.ID, w.arrival.rng, w.arrival.now())
	return err
}

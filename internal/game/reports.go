package game

import (
	"errors"
	"sort"
	"time"
)

// PortReport is a public commerce projection, not a docking quote or account.
type PortReport struct {
	Available bool
	Name      string
	Supply    [3]float64
	Cargo     [3]int64
	Prices    [3]int64
	Selling   [3]bool // The port's action, as in the commerce report.
}

func (w *World) RemotePortReport(id, sector int, now time.Time) (PortReport, error) {
	p, err := w.player(id)
	if err != nil {
		return PortReport{}, err
	}
	s := w.Sectors[sector]
	if s == nil || now.IsZero() || now.Before(w.Created) {
		return PortReport{}, errors.New("choose an existing sector and valid report time")
	}
	port := w.Ports[s.Port]
	// Earth is an equipment service, not a cargo market. Its remote service
	// report is outside the recovered ordinary-port report slice.
	if port == nil || port.ID == 1 || w.HostileDefense(id, sector) {
		return PortReport{}, nil
	}
	projected := *port
	update(&projected, now)
	report := PortReport{Available: true, Name: projected.Name, Supply: projected.Supply, Cargo: p.Cargo}
	for i := range Goods {
		report.Prices[i] = Price(&projected, i)
		report.Selling[i] = projected.Coefficient[i] > 0
	}
	return report, nil
}

// PlanetReport contains no private fields unless Details is present. A report
// blocked by sector fighters reveals nothing and spends one turn.
type PlanetReport struct {
	Available bool
	Name      string
	Ground    int64
	Details   *Planet
	TurnSpent bool
}

// RemotePlanetReport must execute in one store Update so a blocked query's
// turn charge and the permission decision use the same authoritative world.
func (w *World) RemotePlanetReport(id, sector int, now time.Time) (PlanetReport, error) {
	p, err := w.player(id)
	if err != nil {
		return PlanetReport{}, err
	}
	s := w.Sectors[sector]
	if s == nil || now.IsZero() || now.Before(w.Created) {
		return PlanetReport{}, errors.New("choose an existing sector and valid report time")
	}
	if w.HostileDefense(id, sector) {
		if p.Turns < 1 {
			return PlanetReport{}, errors.New("no turns left for a report blocked by sector fighters")
		}
		p.spendTurn()
		return PlanetReport{TurnSpent: true}, nil
	}
	planet := w.Planets[s.Planet]
	if planet == nil {
		return PlanetReport{}, nil
	}
	report := PlanetReport{Available: true, Name: planet.Name, Ground: planet.Ground}
	if planet.Owner == 0 || w.allowed(p, planet) {
		projected := *planet
		projected.update(now, true)
		report.Details = &projected
		report.Ground = projected.Ground
	}
	return report, nil
}

type PlanetLocation struct {
	Name       string
	ID, Sector int
}

func (w *World) OwnPlanets(id int) ([]PlanetLocation, error) {
	if _, err := w.player(id); err != nil {
		return nil, err
	}
	var planets []PlanetLocation
	for _, planet := range w.Planets {
		if planet.Owner == id {
			planets = append(planets, PlanetLocation{Name: planet.Name, ID: planet.ID, Sector: planet.Sector})
		}
	}
	sort.Slice(planets, func(i, j int) bool { return planets[i].Sector < planets[j].Sector })
	return planets, nil
}

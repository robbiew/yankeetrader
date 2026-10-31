package game

import (
	"errors"
	"math"
	"slices"
	"time"
)

// PlanetBattleReport is an immutable owner snapshot. It does not refer to the
// current object: destruction and later slot reuse must not rewrite history.
type PlanetBattleReport struct {
	ID                                int
	Name                              string
	GroundBefore, GroundAfter         int64
	ProductionBefore, ProductionAfter [3]float64
	CargoBefore, CargoAfter           [3]float64
	Neutralized, Interrupted          bool
}

func validatePlanetBattle(r BattleReport) error {
	p := r.Planet
	if p == nil {
		return nil
	}
	if p.ID < 1 || p.ID > 100 || !clean(p.Name) || r.FightersLost != 0 || r.ShieldsLost != 0 || p.GroundBefore < 0 || p.GroundBefore > MaxQuantity || p.GroundAfter < 0 || p.GroundAfter > p.GroundBefore || (p.Neutralized || r.Destroyed) && p.GroundAfter != 0 || r.Destroyed && p.Interrupted {
		return errors.New("invalid planetary battle report")
	}
	for i := range p.ProductionBefore {
		for _, n := range []float64{p.ProductionBefore[i], p.ProductionAfter[i], p.CargoBefore[i], p.CargoAfter[i]} {
			if math.IsNaN(n) || math.IsInf(n, 0) || n < 0 || n > float64(MaxQuantity) {
				return errors.New("invalid planetary battle quantities")
			}
		}
		if p.ProductionAfter[i] > p.ProductionBefore[i] || p.CargoAfter[i] > p.CargoBefore[i] || r.Destroyed && (p.ProductionAfter[i] != 0 || p.CargoAfter[i] != 0) {
			return errors.New("invalid planetary battle damage")
		}
	}
	return nil
}

// Corrects DOS's location-as-array-subscript bug explicitly: the 450 batch
// requires at least 450 attackers AND a rate above 500. Otherwise use one.
func xannorProductionBatch(force int64, rates [3]float64) int64 {
	if force >= 450 && (rates[0] > 500 || rates[1] > 500 || rates[2] > 500) {
		return 450
	}
	return 1
}

// xannorPlanet returns false if work/publication constraints require holding at
// the previous safe sector. All changes compose in the daily Store transaction.
func (w *World) xannorPlanet(sector int, force *int64, work *int, preferred *int, now time.Time, rng func() float64) bool {
	if sector <= 7 || *force == 0 {
		return true
	}
	planet := w.Planets[w.Sectors[sector].Planet]
	if planet == nil || planet.Owner == XannorOwner {
		return true
	}
	if *work == 0 || w.prepareNews(now) != nil {
		return false
	}
	owner := w.Players[planet.Owner]
	if owner != nil && (w.NextBattleReport == 0 || w.NextBattleReport == math.MaxUint64 || len(owner.BattleReports) > 0 && now.Before(owner.BattleReports[len(owner.BattleReports)-1].At)) {
		return false
	}
	initial := *force
	oldOwner := planet.Owner
	snapshot := &PlanetBattleReport{ID: planet.ID, Name: planet.Name, GroundBefore: planet.Ground, ProductionBefore: planet.Production, CargoBefore: planet.Cargo}
	*work-- // Dispatch also bounds encounters with already empty planets.
	for planet.Ground > 0 && *force > 0 && *work > 0 {
		planet.Ground--
		*force -= min(*force, int64(rng()*1000)+1)
		*work--
	}
	// Even mutual exhaustion neutralizes an undefended title. No NPC capture or
	// bank/weapon transfer is invented, and all existing landing grants expire.
	if planet.Ground == 0 && oldOwner != 0 {
		planet.Owner = 0
		snapshot.Neutralized = true
		w.invalidatePlanetLandings(planet.ID)
	}
	destroyed := false
	// Go permits zero-rate planets. A victorious ground defense must never trigger
	// warehouse capping or deletion merely because its rates were already zero.
	if planet.Ground == 0 && *force > 0 && *work > 0 {
		rates := planet.Production
		for *force > 0 && *work > 0 && (rates[0] > 0 || rates[1] > 0 || rates[2] > 0) {
			batch := xannorProductionBatch(*force, rates)
			if rng() < .5 {
				for i := range rates {
					rates[i] -= rng() * float64(batch) / 3
				}
			} else {
				*force -= batch
			}
			*work--
		}
		for i := range rates {
			planet.Production[i] = max(0, rates[i])
			planet.Cargo[i] = min(planet.Cargo[i], 10*planet.Production[i])
		}
		destroyed = planet.Production == [3]float64{}
		if destroyed {
			w.destroyPlanet(planet)
			*preferred = 0
		}
	}
	snapshot.GroundAfter, snapshot.ProductionAfter, snapshot.CargoAfter = planet.Ground, planet.Production, planet.Cargo
	snapshot.Interrupted = *work == 0 && *force > 0 && !destroyed
	outcome := "damaged"
	if snapshot.Interrupted {
		outcome = "unfinished"
	} else if *force == 0 {
		outcome = "defended"
	}
	if snapshot.Neutralized {
		outcome = "neutralized"
	}
	if destroyed {
		outcome = "destroyed"
	}
	w.appendNews(NewsEvent{At: now.UTC(), Kind: NewsXannorPlanet, PlanetName: planet.Name, Outcome: outcome})
	if owner != nil {
		owner.BattleReports = append(owner.BattleReports, BattleReport{ID: w.NextBattleReport, At: now.UTC(), Sector: sector, XannorLost: initial - *force, Destroyed: destroyed, Unread: true, Planet: snapshot})
		w.NextBattleReport++
		if len(owner.BattleReports) > MaxBattleReports {
			owner.BattleReports = slices.Clone(owner.BattleReports[len(owner.BattleReports)-MaxBattleReports:])
		}
	}
	if *force == 0 {
		*preferred = sector
		return true
	}
	return !snapshot.Interrupted
}

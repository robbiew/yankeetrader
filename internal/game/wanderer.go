package game

import (
	"errors"
	"math"
	"sort"
	"time"
)

// WandererResult is internal maintenance accounting. Public receipts deliberately
// omit the random destination and all account/resource details.
type WandererResult struct {
	Status, Reason string
	Generation     uint64
	From, To       int
	Destroyed      bool
}
type MaintenanceReceipt struct {
	Ran      bool
	Wanderer WandererResult
}

func planetaryDraw(rng func() float64) (float64, error) {
	if rng == nil {
		return 0, errors.New("missing planetary RNG")
	}
	r := rng()
	if math.IsNaN(r) || math.IsInf(r, 0) || r < 0 || r >= 1 {
		return 0, errors.New("invalid planetary RNG")
	}
	return r, nil
}
func (w *World) wanderer() *Planet {
	for _, p := range w.Planets {
		if p != nil && p.Wanderer {
			return p
		}
	}
	return nil
}

// Source is virtually vacated before selection; it is a legitimate candidate.
// Candidates depend only on planet occupancy, not defenses, mines or ports.
func (w *World) wandererCandidates(source int) []int {
	ids := make([]int, 0, len(w.Sectors))
	for id, s := range w.Sectors {
		if s != nil && (s.Planet == 0 || id == source) {
			ids = append(ids, id)
		}
	}
	sort.Ints(ids)
	return ids
}
func chooseWanderer(ids []int, rng func() float64) (int, error) {
	if len(ids) == 0 {
		return 0, errors.New("no empty sector for The Wanderer")
	}
	r, err := planetaryDraw(rng)
	if err != nil {
		return 0, err
	}
	return ids[min(len(ids)-1, int(r*float64(len(ids))))], nil
}

// BootstrapWanderer creates only a missing Wanderer. The initializer and Genesis call it
// explicitly; it never reruns the economy or relocates an already existing one.
func (w *World) BootstrapWanderer(now time.Time, rng func() float64) (WandererResult, error) {
	if p := w.wanderer(); p != nil {
		return WandererResult{Status: "unchanged", Generation: p.Generation, From: p.Sector, To: p.Sector}, nil
	}
	out := WandererResult{Status: "deferred"}
	if now.IsZero() || now.Before(w.Created) {
		return out, errors.New("invalid Wanderer clock")
	}
	if w.Planets[1] != nil || len(w.Planets) >= 100 {
		out.Reason = "reserved slot unavailable"
		return out, nil
	}
	ids := w.wandererCandidates(0)
	if len(ids) == 0 {
		out.Reason = "no empty sector"
		return out, nil
	}
	if w.NextPlanetGeneration < 101 || w.NextPlanetGeneration == math.MaxUint64 {
		out.Reason = "planet identity exhausted"
		return out, nil
	}
	to, err := chooseWanderer(ids, rng)
	if err != nil {
		return out, err
	}
	generation, err := w.allocatePlanetGeneration()
	if err != nil {
		return out, err
	}
	p := &Planet{Wanderer: true, Generation: generation, ID: 1, Sector: to, Name: "The Wanderer", Updated: now.UTC(), Production: [3]float64{5000, 5000, 5000}, Bank: 250000}
	w.Planets[1] = p
	w.Sectors[to].Planet = 1
	return WandererResult{Status: "restored", Generation: generation, To: to}, nil
}
func (w *World) relocateWanderer(now time.Time, rng func() float64) (WandererResult, error) {
	p := w.wanderer()
	if p == nil {
		return w.BootstrapWanderer(now, rng)
	}
	out := WandererResult{Status: "deferred", Generation: p.Generation, From: p.Sector, To: p.Sector}
	if now.IsZero() || now.Before(p.Updated) {
		return out, errors.New("invalid Wanderer clock")
	}
	to, err := chooseWanderer(w.wandererCandidates(p.Sector), rng)
	if err != nil {
		return out, err
	}
	w.invalidatePlanetLandings(p.ID)
	w.Sectors[p.Sector].Planet = 0
	p.Sector = to
	w.Sectors[to].Planet = p.ID
	p.Owner = 0
	if p.Bank == 0 {
		p.Bank = 250000
	}
	out.Status = "relocated"
	out.To = to
	if to == out.From {
		out.Status = "held"
	}
	return out, nil
}

// RunMaintenance is the error-aware production entry point. Call inside one
// Store.Update and propagate errors so any invalid draw rolls back every phase.
func (w *World) RunMaintenance(now time.Time, rng func() float64) (out MaintenanceReceipt, err error) {
	if day(now) <= w.LastMaintenance {
		return out, nil
	}
	if rng == nil {
		return out, errors.New("missing maintenance RNG")
	}
	var drawErr error
	checked := func() float64 {
		if drawErr != nil {
			return 0
		}
		r, e := planetaryDraw(rng)
		if e != nil {
			drawErr = e
			return 0
		}
		return r
	}
	out, err = w.maintenancePhases(now, checked)
	if drawErr != nil {
		return out, drawErr
	}
	return
}

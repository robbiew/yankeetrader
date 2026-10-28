package game

import (
	"errors"
	"math"
	"slices"
	"time"
)

const SpyPrice int64 = 333000
const MaxSpies = 3
const SpyHistoryLimit = 30

// SpyNetwork is private to one login. It is never serialized with World.
// Store stages a clone and publishes it only after the associated world saves.
type SpyNetwork struct {
	owner        int
	generation   uint64
	locations    []int
	lastReported []int
	reports      []SpyReport
	next         uint64
}
type SpyReport struct {
	ID              uint64
	Spy, Sector     int
	Mines           int64
	Planet          string
	Ground          int64
	DefenseFighters int64
	DefenseOwner    string
	Unread          bool
}

func NewSpyNetwork(id int, generation uint64) *SpyNetwork {
	return &SpyNetwork{owner: id, generation: generation, next: 1}
}
func (n *SpyNetwork) Clone() *SpyNetwork {
	c := *n
	c.locations = slices.Clone(n.locations)
	c.lastReported = slices.Clone(n.lastReported)
	c.reports = slices.Clone(n.reports)
	return &c
}
func (n *SpyNetwork) check(w *World) error {
	if n == nil {
		return errors.New("spies require a live login")
	}
	return w.CheckShip(n.owner, n.generation)
}
func (n *SpyNetwork) Locations(w *World) ([]int, error) {
	if err := n.check(w); err != nil {
		return nil, err
	}
	return slices.Clone(n.locations), nil
}
func (n *SpyNetwork) Reports(w *World, unread bool) ([]SpyReport, error) {
	if err := n.check(w); err != nil {
		return nil, err
	}
	var reports []SpyReport
	for _, r := range n.reports {
		if !unread || r.Unread {
			reports = append(reports, r)
		}
	}
	return reports, nil
}
func (n *SpyNetwork) Acknowledge(w *World, reportID uint64) error {
	if err := n.check(w); err != nil {
		return err
	}
	for i := range n.reports {
		if n.reports[i].ID == reportID {
			n.reports[i].Unread = false
			return nil
		}
	}
	return errors.New("intelligence report is no longer retained")
}
func (n *SpyNetwork) Hire(w *World, token string, sectors []int, now time.Time) error {
	if err := n.check(w); err != nil {
		return err
	}
	p := w.Players[n.owner]
	s := w.Sectors[p.Sector]
	if now.IsZero() || now.Before(w.Created) || token == "" || p.DockToken != token || !now.Before(p.DockUntil) || s == nil || s.Port != 1 {
		return errors.New("dock at Earth again before hiring spies")
	}
	if len(sectors) < 1 || len(sectors) > MaxSpies-len(n.locations) {
		return errors.New("max spies allowed is 3; choose at least one")
	}
	for _, sector := range sectors {
		if w.Sectors[sector] == nil {
			return errors.New("choose an existing starting sector for every spy")
		}
	}
	cost := int64(len(sectors)) * SpyPrice
	if p.Credits < cost {
		return errors.New("not enough credits to hire these spies")
	}
	p.Credits -= cost
	n.locations = append(n.locations, sectors...)
	n.lastReported = append(n.lastReported, make([]int, len(sectors))...)
	return nil
}

// Advance searches before moving. Only the runtime-confirmed findings are
// emitted: mines, planet ground forces and nonpersonal sector defenses.
// A zero-warp sector safely holds position. Selection among nonzero warps is
// uniform, equivalent to rejecting empty slots in the original six-slot table.
func (n *SpyNetwork) Advance(w *World, now time.Time, rng func() float64) error {
	if err := n.check(w); err != nil {
		return err
	}
	if now.IsZero() || now.Before(w.Created) {
		return errors.New("invalid intelligence report time")
	}
	staged := n.Clone()
	for i, location := range staged.locations {
		sector := w.Sectors[location]
		if sector == nil {
			return errors.New("spy sector no longer exists")
		}
		if staged.lastReported[i] != location {
			report := SpyReport{ID: staged.next, Spy: i + 1, Sector: location, Unread: true}
			for _, layer := range sector.Minefield {
				report.Mines += layer.Count
			}
			if planet := w.Planets[sector.Planet]; planet != nil {
				projected := *planet
				projected.update(now, true)
				report.Planet, report.Ground = projected.Name, projected.Ground
			}
			if d := sector.Defense; d != nil && d.Owner != n.owner {
				report.DefenseFighters = d.Fighters
				switch d.Owner {
				case XannorOwner:
					report.DefenseOwner = "The Xannor"
				case MercenaryOwner:
					report.DefenseOwner = "Mercenaries"
				default:
					if owner := w.Players[d.Owner]; owner != nil {
						report.DefenseOwner = owner.Alias
						if team := w.Teams[owner.Team]; team != nil {
							report.DefenseOwner += " * Team: " + team.Name
						}
					}
				}
			}
			if report.Mines > 0 || report.Planet != "" || report.DefenseFighters > 0 {
				staged.reports = append(staged.reports, report)
				staged.next++
				if len(staged.reports) > SpyHistoryLimit {
					staged.reports = slices.Clone(staged.reports[len(staged.reports)-SpyHistoryLimit:])
				}
				staged.lastReported[i] = location
			}
		}
		if len(sector.Warps) > 0 {
			if rng == nil {
				return errors.New("spy movement requires RNG")
			}
			r := rng()
			if math.IsNaN(r) || math.IsInf(r, 0) || r < 0 || r >= 1 {
				return errors.New("spy RNG must return a finite value in [0,1)")
			}
			staged.locations[i] = sector.Warps[int(r*float64(len(sector.Warps)))]
		}
	}
	*n = *staged
	return nil
}

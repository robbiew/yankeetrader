package game

import (
	"errors"
	"math"
	"slices"
	"sort"
	"time"
)

const MaxBattleReports = 32

// BattleReport is a recipient-only snapshot, retained across ship replacement.
// Public news uses a separate whitelist and never copies these casualty counts.
type BattleReport struct {
	Planet                                *PlanetBattleReport `json:",omitempty"`
	ID                                    uint64
	At                                    time.Time
	Sector                                int
	XannorLost, FightersLost, ShieldsLost int64
	Destroyed, Unread                     bool
}

func (w *World) validateBattleReports() error {
	if w.NextBattleReport == 0 {
		return errors.New("invalid battle report sequence")
	}
	seen := map[uint64]bool{}
	for _, p := range w.Players {
		if len(p.BattleReports) > MaxBattleReports {
			return errors.New("too many private battle reports")
		}
		var last uint64
		var at time.Time
		for _, r := range p.BattleReports {
			_, offset := r.At.Zone()
			if r.ID <= last || r.ID >= w.NextBattleReport || seen[r.ID] || r.At.IsZero() || offset != 0 || r.At.Before(w.Created) || r.At.Before(at) || r.Sector <= 7 || w.Sectors[r.Sector] == nil || r.XannorLost < 0 || r.XannorLost > MaxQuantity || r.FightersLost < 0 || r.FightersLost > MaxQuantity || r.ShieldsLost < 0 || r.ShieldsLost > MaxQuantity {
				return errors.New("invalid private battle report")
			}
			if err := validatePlanetBattle(r); err != nil {
				return err
			}
			seen[r.ID] = true
			last, at = r.ID, r.At
		}
	}
	return nil
}

func (w *World) BattleHistory(id int, unreadOnly bool) ([]BattleReport, error) {
	p, err := w.player(id)
	if err != nil {
		return nil, err
	}
	reports := []BattleReport{}
	for _, r := range p.BattleReports {
		if !unreadOnly || r.Unread {
			if r.Planet != nil {
				snapshot := *r.Planet
				r.Planet = &snapshot
			}
			reports = append(reports, r)
		}
	}
	return reports, nil
}

func (w *World) AcknowledgeBattleReport(id int, reportID uint64) error {
	p, err := w.player(id)
	if err != nil {
		return err
	}
	for i := range p.BattleReports {
		if p.BattleReports[i].ID == reportID {
			p.BattleReports[i].Unread = false
			return nil
		}
	}
	return errors.New("private battle report not found")
}

func xannorShipBatch(a, b int64) int64 {
	if a < 500 || b < 500 {
		return 1
	}
	if a > 5000 && b > 5000 {
		return 5000
	}
	return 500
}

// xannorShips returns false when the activation must hold at its previous safe
// sector. Damage, reports and death cleanup are composed inside Store.Update.
func (w *World) xannorShips(sector int, force *int64, work *int, preferred *int, now time.Time, rng func() float64) bool {
	ids := []int{}
	for id, p := range w.Players {
		if p.Death == nil && p.Sector == sector {
			ids = append(ids, id)
		}
	}
	sort.Ints(ids)
	for _, id := range ids {
		if *force == 0 {
			return true
		}
		if *work == 0 {
			return false
		}
		p := w.Players[id]
		context := DeathContext{Victim: id, Generation: p.ShipGeneration, Sector: sector, Killer: XannorOwner, Cause: "xannor"}
		// All fallible lifecycle/report publication checks precede the detection draw
		// and damage. There is no partially published death on an exhausted sequence.
		if _, err := w.deathTarget(context, now); err != nil {
			return false
		}
		if err := w.prepareNews(now); err != nil {
			return false
		}
		if w.NextBattleReport == 0 || w.NextBattleReport == math.MaxUint64 || len(p.BattleReports) > 0 && now.Before(p.BattleReports[len(p.BattleReports)-1].At) {
			return false
		}
		*work-- // One detection/dispatch step, even for an unarmed or hidden target.
		if rng() < p.Cloak-.33 {
			continue
		}
		initial, fighters, shields := *force, p.Fighters, p.Shields
		for *force > 0 && p.Fighters > 0 && *work > 0 {
			batch := xannorShipBatch(*force, p.Fighters)
			if rng() > .5 {
				*force -= batch
			} else {
				p.Fighters -= batch
			}
			*work--
		}
		for *force > 0 && p.Fighters == 0 && p.Shields > 0 && *work > 0 {
			batch := xannorShipBatch(*force, p.Shields)
			if rng() >= .5 {
				p.Shields -= batch
			} else {
				*force -= batch
			}
			*work--
		}
		killed := p.Fighters == 0 && p.Shields == 0
		r := BattleReport{ID: w.NextBattleReport, At: now.UTC(), Sector: sector, XannorLost: initial - *force, FightersLost: fighters - p.Fighters, ShieldsLost: shields - p.Shields, Destroyed: killed, Unread: true}
		if killed {
			// NPCs receive no salvage. Consume the destroyed ship's inventory once,
			// without creating wreck mines; planets and remaining daily turns survive.
			w.recordDeath(p, context, now)
			w.appendNews(NewsEvent{At: now.UTC(), Kind: NewsXannorDeath, Alias: p.Alias})
			*preferred = 0
		}
		w.NextBattleReport++
		p.BattleReports = append(p.BattleReports, r)
		if len(p.BattleReports) > MaxBattleReports {
			p.BattleReports = slices.Clone(p.BattleReports[len(p.BattleReports)-MaxBattleReports:])
		}
		if *force == 0 {
			*preferred = sector
			return true
		}
		if *work == 0 {
			return false
		}
	}
	return true
}

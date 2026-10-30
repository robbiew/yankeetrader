package game

import (
	"errors"
	"sort"
	"time"
)

const XannorHome = "xannor"
const xannorWorkLimit = 10000

// Sector defenses are the sole source of deployed force: each sector is counted
// once, without DOS pointer aliases. Reserve holds only undeployed HQ fighters
// during an unfinished reclaim; it is never also present in a sector defense.
type XannorState struct {
	Revenge *XannorRevengeTarget `json:",omitempty"`
	HQ      int
	Reserve int64
}

func (w *World) validateXannor() error {
	if x := w.Xannor; x != nil {
		if target := x.Revenge; target != nil {
			player := w.Players[target.Player]
			if player == nil || player.Death != nil || player.ShipGeneration != target.Generation {
				return errors.New("invalid Xannor revenge target")
			}
		}
		if x.HQ <= 7 || w.Sectors[x.HQ] == nil || x.Reserve < 0 || x.Reserve > MaxQuantity {
			return errors.New("invalid Xannor HQ state")
		}
		if d := w.Sectors[x.HQ].Defense; d != nil && d.Owner == XannorOwner && x.Reserve > MaxQuantity-d.Fighters {
			return errors.New("Xannor HQ force exceeds capacity")
		}
	}
	for _, p := range w.Planets {
		if p != nil && p.FactionHome == XannorHome && w.Xannor == nil {
			return errors.New("Xannor home has no HQ state")
		}
	}
	return nil
}

func (w *World) xannorHome() *Planet {
	for _, p := range w.Planets {
		if p.FactionHome == XannorHome {
			return p
		}
	}
	return nil
}

// Selection is finite, stable and conservative. Neither a foreign one-fighter
// group nor an unrelated planet may be overwritten. Mines remain attributed and
// are avoided rather than bypassed by HQ relocation.
func (w *World) xannorDestinations(exclude int) []int {
	ids := []int{}
	for id, s := range w.Sectors {
		if id > 7 && id != exclude && s.Planet == 0 && len(s.Minefield) == 0 && (s.Defense == nil || s.Defense.Owner == XannorOwner) {
			ids = append(ids, id)
		}
	}
	sort.Ints(ids)
	return ids
}

func (w *World) restoreXannoron(now time.Time, rng func() float64) {
	if p := w.xannorHome(); p != nil {
		// A captured or neutralized home remains an ordinary human/neutral title.
		if p.Owner == XannorOwner {
			p.Ground += min(int64(rng()*25), MaxQuantity-p.Ground)
			if p.Bank == 0 {
				p.Bank = 1000000
			}
		}
		return
	}
	slot := 100
	if w.Planets[slot] != nil {
		for slot = 2; slot <= 100 && w.Planets[slot] != nil; slot++ {
		}
	}
	if slot > 100 {
		return
	}
	sector := 0
	if w.Xannor != nil {
		s := w.Sectors[w.Xannor.HQ]
		if s.Planet == 0 && len(s.Minefield) == 0 && (s.Defense == nil || s.Defense.Owner == XannorOwner) {
			sector = s.ID
		}
	}
	if sector == 0 {
		// Existing HQs are not silently moved just to rebuild a destroyed home.
		if w.Xannor != nil {
			return
		}
		ids := w.xannorDestinations(0)
		if len(ids) == 0 {
			return
		}
		sector = ids[int(rng()*float64(len(ids)))]
	}
	if w.Xannor == nil {
		w.Xannor = &XannorState{HQ: sector}
	}
	p := &Planet{ID: slot, Sector: sector, Owner: XannorOwner, FactionHome: XannorHome, Name: "Xannoron", Updated: now.UTC(), Production: [3]float64{100000, 100000, 100000}, Ground: int64(rng() * 250), Bank: 100000 + int64(rng()*10000000)}
	p.Ground += int64(rng() * 25)
	w.Planets[slot], w.Sectors[sector].Planet = p, slot
}

func (w *World) maintainXannor(now time.Time, rng func() float64) {
	// Mercenary restoration has first claim on scarce placement capacity. New HQs
	// start empty, gaining only the recovered score-based regeneration below.
	w.restoreXannoron(now, rng)
	if w.Xannor == nil {
		return
	}
	if w.xannorHome() == nil {
		// A reclaim/relocation may make room to rebuild later in this phase.
		defer w.restoreXannoron(now, rng)
	}
	x := w.Xannor
	s := w.Sectors[x.HQ]
	top, total := int64(0), x.Reserve
	for _, p := range w.Players {
		if p.Death == nil && p.StoredScore > top {
			top = p.StoredScore
		}
	}
	for _, sector := range w.Sectors {
		if d := sector.Defense; d != nil && d.Owner == XannorOwner {
			total += d.Fighters
		}
	}
	force := x.Reserve
	if d := s.Defense; d != nil && d.Owner == XannorOwner {
		force += d.Fighters
		s.Defense = nil
	}
	empty := force == 0
	regen := int64(0)
	if total <= top/100 {
		regen = min(top/500, MaxQuantity-force)
	}
	force += regen
	attempted := s.Defense != nil
	if attempted {
		d := s.Defense
		for work := 0; work < xannorWorkLimit && force > 0 && d.Fighters > 0; work++ {
			batch := int64(1)
			if force > 250 && d.Fighters > 250 {
				batch = 250
			}
			if rng() <= .5 {
				d.Fighters -= batch
			} else {
				force -= batch
			}
		}
		if d.Fighters > 0 {
			// Work exhaustion preserves both sides for the next daily transaction.
			x.Reserve = force
			return
		}
		s.Defense = nil
	}
	x.Reserve = 0
	if empty && !attempted || attempted && force > 0 {
		ids := w.xannorDestinations(x.HQ)
		// Do not discard overflow at a friendly destination; choose only sectors
		// that can hold all survivors in addition to their existing Xannor force.
		candidates := ids[:0]
		for _, id := range ids {
			d := w.Sectors[id].Defense
			if d == nil || force <= MaxQuantity-d.Fighters {
				candidates = append(candidates, id)
			}
		}
		if len(candidates) > 0 {
			to := candidates[int(rng()*float64(len(candidates)))]
			home := w.xannorHome()
			if home != nil && home.Owner == XannorOwner && home.Sector == x.HQ {
				s.Planet = 0
				home.Sector = to
				w.Sectors[to].Planet = home.ID
			}
			x.HQ = to
			s = w.Sectors[to]
		}
	}
	if force > 0 {
		if s.Defense == nil {
			s.Defense = &SectorDefense{Owner: XannorOwner}
		}
		s.Defense.Fighters += force
	}
}

package game

import (
	"sort"
	"time"
)

const xannorMobileGroups = 19

// Mobile identities are a daily snapshot of authoritative sector defenses.
// No persisted pointer cache can duplicate force or survive a group's capture.
func (w *World) xannorActions(now time.Time, rng func() float64) {
	if w.Xannor == nil {
		return
	}
	ids := make([]int, 0, len(w.Sectors))
	for id := range w.Sectors {
		if id > 7 {
			ids = append(ids, id)
		}
	}
	sort.Ints(ids)
	if len(ids) < 2 {
		return
	}
	type participant struct {
		sector int
		group  *SectorDefense
	}
	groups := []participant{}
	for _, id := range ids {
		if d := w.Sectors[id].Defense; id != w.Xannor.HQ && d != nil && d.Owner == XannorOwner && len(groups) < xannorMobileGroups {
			groups = append(groups, participant{id, d})
		}
	}
	// Only the original, deployed HQ garrison can fund this day's splits. Force
	// returning later is not available for another activation in the same phase.
	budget := int64(0)
	if d := w.Sectors[w.Xannor.HQ].Defense; d != nil && d.Owner == XannorOwner && w.Xannor.Reserve == 0 {
		budget = d.Fighters
	}
	if budget == 0 && len(groups) == 0 {
		return
	}
	top := w.xannorTopPlayer()
	score := int64(0)
	if top != nil {
		score = max(int64(0), top.StoredScore)
	}
	topSector := w.xannorHuntSector(ids, top, rng)
	acted := map[*SectorDefense]bool{}
	preferred := 0
	for slot := 2; slot <= 20; slot++ {
		from := w.Xannor.HQ
		var group *SectorDefense
		spawned := slot-2 >= len(groups)
		if !spawned {
			p := groups[slot-2]
			if acted[p.group] || w.Sectors[p.sector].Defense != p.group {
				continue
			}
			from, group = p.sector, p.group
			acted[group] = true
		} else {
			// Integer comparison preserves fractional score/2000 thresholds. Zero
			// budget never enters the legacy helper's stale-result spawning path.
			if budget < 1 || budget*2000 < score {
				continue
			}
			amount := budget
			for i := 0; i < 4; i++ {
				amount = int64(rng()*float64(amount)) + 1
			}
			d := w.Sectors[from].Defense
			d.Fighters -= amount
			if d.Fighters == 0 {
				w.Sectors[from].Defense = nil
			}
			budget -= amount
			group = &SectorDefense{Owner: XannorOwner, Fighters: amount}
		}
		target := w.xannorTarget(slot, from, ids, topSector, score, budget, &preferred, rng)
		path, err := w.path(from, target, []int{1, 2, 3, 4, 5, 6, 7})
		if err != nil {
			if spawned {
				w.joinXannor(from, group.Fighters, acted)
			}
			continue
		}
		w.walkXannor(group, path, acted, &preferred, now, rng)
	}
}

func (w *World) xannorTopPlayer() *Player {
	var top *Player
	for _, p := range w.Players {
		if p.Death == nil && (top == nil || p.StoredScore > top.StoredScore || p.StoredScore == top.StoredScore && p.ID < top.ID) {
			top = p
		}
	}
	return top
}

func (w *World) xannorHuntSector(ids []int, top *Player, rng func() float64) int {
	if top != nil && top.StoredScore >= 2500000 && rng() >= top.Cloak-.33 && top.Sector > 7 {
		return top.Sector
	}
	return ids[int(rng()*float64(len(ids)))]
}

func (w *World) xannorTarget(slot, from int, ids []int, topSector int, score, budget int64, preferred *int, rng func() float64) int {
	others := make([]int, 0, len(ids)-1)
	for _, id := range ids {
		if id != from {
			others = append(others, id)
		}
	}
	target := others[int(rng()*float64(len(others)))]
	candidate := ids[int(rng()*float64(len(ids)))]
	s := w.Sectors[candidate]
	qualifies := s.Planet != 0 || s.Defense != nil && s.Defense.Owner != XannorOwner && s.Defense.Fighters > 1
	if !qualifies {
		players := []int{}
		for id, p := range w.Players {
			if p.Death == nil && p.Sector == candidate {
				players = append(players, id)
			}
		}
		sort.Ints(players)
		for _, id := range players {
			if rng() > w.Players[id].Cloak {
				qualifies = true
				break
			}
		}
	}
	if qualifies {
		*preferred = candidate
	}
	if *preferred > 7 {
		target = *preferred
	}
	// Revenge is not enabled in this slice. World locking supplies one coherent
	// current player position, so DOS's stale-vs-cached position draw is omitted.
	if slot == 20 {
		target = topSector
	}
	if budget*2000 < score {
		target = w.Xannor.HQ
	}
	return target
}

func (w *World) xannorCapacity(sector int) int64 {
	capacity := MaxQuantity
	if d := w.Sectors[sector].Defense; d != nil {
		if d.Owner != XannorOwner {
			return 0
		}
		capacity -= d.Fighters
	}
	if w.Xannor != nil && sector == w.Xannor.HQ {
		capacity -= w.Xannor.Reserve
	}
	return capacity
}

// joinXannor returns any overflow rather than deleting it. Receiving force
// consumes a pending snapshot activation; merely passing through does not.
func (w *World) joinXannor(sector int, force int64, acted map[*SectorDefense]bool) int64 {
	take := min(force, w.xannorCapacity(sector))
	if take > 0 {
		s := w.Sectors[sector]
		if s.Defense == nil {
			s.Defense = &SectorDefense{Owner: XannorOwner}
		} else {
			acted[s.Defense] = true
		}
		s.Defense.Fighters += take
	}
	return force - take
}

func (w *World) xannorUnsupported(sector int) bool {
	if p := w.Planets[w.Sectors[sector].Planet]; p != nil && p.Owner != XannorOwner {
		return true
	}
	return false
}

func (w *World) walkXannor(group *SectorDefense, path []int, acted map[*SectorDefense]bool, preferred *int, now time.Time, rng func() float64) {
	origin, current := path[0], path[0]
	force := group.Fighters
	if w.Sectors[origin].Defense == group {
		w.Sectors[origin].Defense = nil
	}
	hold := func() {
		// Every entered sector has space for the whole moving force; origin also
		// retains the capacity vacated by this participant (or by its HQ split).
		left := w.joinXannor(current, force, acted)
		if left > 0 {
			w.joinXannor(origin, left, acted)
		}
	}
	work := xannorWorkLimit
	for hop, next := range path[1:] {
		if next <= 7 || work == 0 || w.xannorUnsupported(next) {
			hold()
			return
		}
		s := w.Sectors[next]
		// Keep a representable holding point when passing a friendly group. A
		// partially full final destination can receive force without dropping excess.
		if s.Defense != nil && s.Defense.Owner == XannorOwner && w.xannorCapacity(next) < force && hop != len(path)-2 {
			hold()
			return
		}
		work-- // Hops, mine bursts and battle rounds share this activation's budget.
		for len(s.Minefield) > 0 && force > 0 && work > 0 {
			force -= min(force, int64(rng()*1000)+1)
			s.Minefield[0].Count--
			if s.Minefield[0].Count == 0 {
				s.Minefield = s.Minefield[1:]
			}
			work--
		}
		if force == 0 {
			return
		}
		if len(s.Minefield) > 0 {
			hold()
			return
		}
		if d := s.Defense; d != nil && d.Owner != XannorOwner {
			for force > 0 && d.Fighters > 0 && work > 0 {
				batch := int64(500)
				if force > 5000 && d.Fighters > 5000 {
					batch = 5000
				}
				if force < 500 || d.Fighters < 500 {
					batch = 1
				}
				if rng() <= .5 {
					d.Fighters -= batch
				} else {
					force -= batch
				}
				work--
			}
			if d.Fighters == 0 {
				s.Defense = nil
				*preferred = 0
			}
			if force == 0 {
				*preferred = next
				return
			}
			if s.Defense != nil {
				hold()
				return
			}
		}
		// Foreign planets still hold before any encounter mutation. Ship battles
		// follow mines/sector fighters; friendly planetary stocks are untouched.
		if !w.xannorShips(next, &force, &work, preferred, now, rng) {
			hold()
			return
		}
		if force == 0 {
			return
		}
		if w.xannorCapacity(next) < force {
			force = w.joinXannor(next, force, acted)
			hold()
			return
		}
		current = next
	}
	hold()
}

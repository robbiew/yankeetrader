package game

import (
	"math"
	"sort"
)

// Each group gets a bounded work allowance shared by all mine bursts and combat
// rounds on its route. Unfinished encounters leave survivors at the previous
// sector; the remaining field/defense persists for a later maintenance run.
const mercenaryWorkLimit = 10000

func (w *World) mercenaryActions(rng func() float64) {
	ids := make([]int, 0, len(w.Sectors))
	for id := range w.Sectors {
		if id > 7 {
			ids = append(ids, id)
		}
	}
	sort.Sort(sort.Reverse(sort.IntSlice(ids)))
	type participant struct {
		sector int
		group  *SectorDefense
	}
	groups := []participant{}
	for _, id := range ids {
		if d := w.Sectors[id].Defense; d != nil && d.Owner == MercenaryOwner {
			groups = append(groups, participant{id, d})
		}
	}
	acted := map[*SectorDefense]bool{}
	for _, p := range groups {
		if acted[p.group] || w.Sectors[p.sector].Defense != p.group {
			continue
		}
		acted[p.group] = true
		if len(ids) < 2 || (w.Sectors[p.sector].Planet != 0 && rng() < .66) {
			continue
		}
		// Sample once from distinct permitted destinations. A failed path holds
		// the group in place; it cannot become a relocation or an unbounded retry.
		targets := make([]int, 0, len(ids)-1)
		for _, id := range ids {
			if id != p.sector {
				targets = append(targets, id)
			}
		}
		to := targets[int(rng()*float64(len(targets)))]
		path, err := w.path(p.sector, to, []int{1, 2, 3, 4, 5, 6, 7})
		if err != nil {
			continue
		}
		w.walkMercenaries(p.group, path, acted, rng)
	}
}

func (w *World) walkMercenaries(group *SectorDefense, path []int, acted map[*SectorDefense]bool, rng func() float64) {
	current := path[0]
	w.Sectors[current].Defense = nil
	work := mercenaryWorkLimit
	for _, next := range path[1:] {
		s := w.Sectors[next]
		// NPC mines consume the existing attributed layers FIFO. They do not
		// create player deaths or change source identities on unspent mines.
		for len(s.Minefield) > 0 && group.Fighters > 0 && work > 0 {
			bound := int64(10000)
			for i := 0; i < 2; i++ {
				bound = int64(rng()*float64(bound)) + 1
			}
			group.Fighters -= min(group.Fighters, bound)
			s.Minefield[0].Count--
			if s.Minefield[0].Count == 0 {
				s.Minefield = s.Minefield[1:]
			}
			work--
		}
		if group.Fighters == 0 {
			return
		}
		if len(s.Minefield) > 0 {
			w.Sectors[current].Defense = group
			return
		}
		if d := s.Defense; d != nil {
			if d.Owner == MercenaryOwner {
				// Receiving a moving group consumes a pending activation too.
				transfer := min(group.Fighters, MaxQuantity-d.Fighters)
				if transfer > 0 {
					acted[d] = true
				}
				d.Fighters += transfer
				group.Fighters -= transfer
			} else {
				roll := rng() // DOS consumes this even for negative faction owners.
				if d.Owner > 0 && roll <= .95 {
					transfer := min(group.Fighters, MaxQuantity-d.Fighters)
					d.Fighters += transfer
					group.Fighters -= transfer
				} else {
					for group.Fighters > 0 && d.Fighters > 0 && work > 0 {
						batch := int64(1)
						if group.Fighters > 200 && d.Fighters > 200 {
							batch = 150
						}
						if rng() < .5 {
							d.Fighters -= batch
						} else {
							group.Fighters -= batch
						}
						work--
					}
					if d.Fighters == 0 {
						s.Defense = nil
						if group.Fighters == 0 {
							return
						}
						// A won defense battle continues the route without revisiting
						// this planet for pickup, matching the recovered ordering.
						current = next
						continue
					}
				}
			}
			if group.Fighters > 0 {
				w.Sectors[current].Defense = group
			}
			return
		}
		if planet := w.Planets[s.Planet]; planet != nil {
			take := min(int64(math.Floor(planet.Fighters)), MaxQuantity-group.Fighters)
			group.Fighters += take
			planet.Fighters -= float64(take)
			// Stock pickup ends this activation; title and ground are untouched.
			current = next
			break
		}
		current = next
	}
	w.Sectors[current].Defense = group
}

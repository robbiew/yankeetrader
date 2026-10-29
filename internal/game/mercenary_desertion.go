package game

import "sort"

// desertHumanDefenses applies the recovered strict RND*100 > fighters rule.
// Modern player IDs start at 1; DOS's literal owner>1 cutoff is not portable.
// Protected Union sectors retain their existing owner and consume no draw.
func (w *World) desertHumanDefenses(rng func() float64) {
	ids := make([]int, 0, len(w.Sectors))
	for id, sector := range w.Sectors {
		if id <= 7 || sector.Defense == nil || sector.Defense.Owner <= 0 {
			continue
		}
		owner := w.Players[sector.Defense.Owner]
		if owner != nil && owner.Death == nil {
			ids = append(ids, id)
		}
	}
	sort.Sort(sort.Reverse(sort.IntSlice(ids)))
	for _, id := range ids {
		d := w.Sectors[id].Defense
		if rng()*100 > float64(d.Fighters) {
			d.Owner = MercenaryOwner
		}
	}
}

package game

import (
	"math/rand"
	"sort"
)

// hireMercenaries spends this maintenance's ordinary-port taxes. DOS discards
// both division remainders; unplaced groups and force above the modern quantity
// limit are also discarded, without carry or refund. No existing group moves.
func (w *World) hireMercenaries(taxes int64) {
	budget := taxes / 10
	if budget < 1 {
		return
	}
	count, size := 1, budget
	if budget >= 10 {
		count, size = 10, budget/10
	}
	if size > MaxQuantity {
		size = MaxQuantity
	}
	// Preserve the modern Union protection, unlike DOS's sector 2..N range.
	// Planets, ports and mines do not exclude an otherwise empty sector.
	available := make([]int, 0, len(w.Sectors))
	for id, sector := range w.Sectors {
		if id > 7 && sector.Defense == nil {
			available = append(available, id)
		}
	}
	sort.Ints(available)
	if count > len(available) {
		count = len(available)
	}
	// Partial Fisher-Yates selection: exactly count bounded draws, no retries.
	for i := 0; i < count; i++ {
		j := i + rand.Intn(len(available)-i)
		available[i], available[j] = available[j], available[i]
		w.Sectors[available[i]].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: size}
	}
}

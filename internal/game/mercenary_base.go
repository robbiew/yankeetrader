package game

import (
	"sort"
	"time"
)

// Faction identity survives capture and renaming. Never infer it from a player
// planet's slot or name, and never restore ownership over a captured base.
const MercenaryHome = "mercenaries"

func (w *World) restoreMercenaryBase(now time.Time, rng func() float64) {
	for _, planet := range w.Planets {
		if planet.FactionHome != MercenaryHome {
			continue
		}
		if planet.Owner == MercenaryOwner {
			if planet.Ground < 1 {
				planet.Ground = 150000
			}
			if planet.Bank == 0 {
				planet.Bank = 25000000
			}
		}
		return
	}
	// Prefer the recovered reserved slot, but preserve all existing planets,
	// including legacy player planets at 99. Every search is finite.
	slot := 99
	if w.Planets[slot] != nil {
		slot = 2
		for slot <= 100 && w.Planets[slot] != nil {
			slot++
		}
	}
	if slot > 100 {
		return
	}
	sectors := make([]int, 0, len(w.Sectors))
	for id, sector := range w.Sectors {
		if id > 7 && (w.Xannor == nil || id != w.Xannor.HQ) && sector.Planet == 0 && (sector.Defense == nil || sector.Defense.Owner == MercenaryOwner) {
			sectors = append(sectors, id)
		}
	}
	if len(sectors) == 0 {
		return
	}
	sort.Ints(sectors)
	sector := sectors[int(rng()*float64(len(sectors)))]
	generation, err := w.allocatePlanetGeneration()
	if err != nil {
		return
	}
	w.Planets[slot] = &Planet{Generation: generation, ID: slot, Sector: sector, Owner: MercenaryOwner, FactionHome: MercenaryHome,
		Name: "Mercenary Base", Updated: now.UTC(), Production: [3]float64{100000, 100000, 100000},
		Ground: 150000, Bank: 25000000}
	w.Sectors[sector].Planet = slot
}

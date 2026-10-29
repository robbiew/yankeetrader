package game

import (
	"encoding/json"
	"testing"
	"time"
)

func mercenaryGroups(w *World) (int, int64) {
	count := 0
	var total int64
	for _, sector := range w.Sectors {
		if sector.Defense != nil && sector.Defense.Owner == MercenaryOwner {
			count++
			total += sector.Defense.Fighters
		}
	}
	return count, total
}

func TestMercenaryHiringTaxRounding(t *testing.T) {
	for _, tc := range []struct {
		tax, size int64
		groups    int
	}{
		{0, 0, 0}, {9, 0, 0}, {10, 1, 1}, {19, 1, 1},
		{90, 9, 1}, {99, 9, 1}, {100, 1, 10}, {109, 1, 10},
		{110, 1, 10}, {199, 1, 10}, {200, 2, 10}, {100112, 1001, 10},
	} {
		w, err := New(clock, 36, 32)
		if err != nil {
			t.Fatal(err)
		}
		w.Ports[1].Treasury = MaxMoney
		w.Ports[2].Treasury = tc.tax * 10
		if !w.Maintain(clock.Add(24 * time.Hour)) {
			t.Fatal("maintenance skipped")
		}
		count, total := mercenaryGroups(w)
		if count != tc.groups || total != int64(tc.groups)*tc.size {
			t.Fatalf("tax %d: groups/force %d/%d, want %d/%d", tc.tax, count, total, tc.groups, int64(tc.groups)*tc.size)
		}
		for id, sector := range w.Sectors {
			if sector.Defense != nil && (id < 8 || sector.Defense.Fighters != tc.size) {
				t.Fatalf("tax %d: invalid placement at %d: %+v", tc.tax, id, sector.Defense)
			}
		}
		if w.Ports[1].Treasury != MaxMoney || w.Ports[2].Treasury != tc.tax*9 {
			t.Fatal("wrong debit or Earth taxed", tc.tax)
		}
		if err := w.Validate(); err != nil {
			t.Fatal(err)
		}
	}
}

func TestMercenaryHiringIndividualPortTaxesAndNoCarry(t *testing.T) {
	for _, treasury := range []int64{5, 15} {
		w, _ := New(clock, 36, 32)
		w.Ports[2].Treasury, w.Ports[3].Treasury = 95, treasury
		w.Maintain(clock.Add(24 * time.Hour))
		_, force := mercenaryGroups(w)
		if (treasury == 5 && force != 0) || (treasury == 15 && force != 1) {
			t.Fatal("taxes combined before rounding", treasury, force)
		}
	}
	w, _ := New(clock, 36, 32)
	w.Ports[2].Treasury = 1990
	w.Maintain(clock.Add(24 * time.Hour))
	if _, force := mercenaryGroups(w); force != 10 {
		t.Fatal("wrong first hire", force)
	}
	// Isolate tax-funded hires from both faction homes. Mercenary routes can
	// collect Xannoron stocks too; production/pickup has separate coverage.
	for _, planet := range w.Planets {
		if planet.FactionHome != "" {
			planet.Updated = clock.Add(48 * time.Hour)
		}
	}
	before, _ := json.Marshal(w)
	if w.Maintain(clock.Add(24*time.Hour)) || w.Maintain(clock) {
		t.Fatal("maintenance repeated")
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("replay changed tax, placement or force")
	}
	w.Maintain(clock.Add(48 * time.Hour))
	if _, force := mercenaryGroups(w); force != 20 || w.Ports[2].Treasury != 1612 {
		t.Fatal("division remainder carried into next day", force, w.Ports[2].Treasury)
	}
}

func TestMercenaryHiringFiniteCapacityAndExistingAssets(t *testing.T) {
	for _, free := range []int{0, 1, 3} {
		w, _ := New(clock, 36, 20)
		player, _ := w.Join("hiring", "Captain")
		for id, sector := range w.Sectors {
			if id > 7+free {
				sector.Defense = &SectorDefense{Owner: player.ID, Fighters: 123}
			}
		}
		// A planet, mines and a port do not exclude a free sector. Hiring itself
		// must not plunder, retitle, detonate, move, or change an existing group.
		if free > 0 {
			w.Sectors[8].Minefield = []MineLayer{{Owner: player.ID, Count: 3}}
			w.Sectors[8].Planet = 2
			w.Planets[2] = &Planet{ID: 2, Sector: 8, Name: "Guarded", Owner: player.ID, Ground: 500, Fighters: 37, Updated: clock.Add(24 * time.Hour)}
		}
		w.Ports[2].Treasury = 1000
		w.Maintain(clock.Add(24 * time.Hour))
		count, total := mercenaryGroups(w)
		if count != free || total != int64(free) || w.Ports[2].Treasury != 900 {
			t.Fatal("capacity policy", free, count, total)
		}
		for id, sector := range w.Sectors {
			if id <= 7 && sector.Defense != nil {
				t.Fatal("protected sector used", id)
			}
			if id > 7+free && *sector.Defense != (SectorDefense{Owner: player.ID, Fighters: 123}) {
				t.Fatal("existing group overwritten", id)
			}
		}
		if free > 0 && w.Sectors[8].Minefield[0].Count != 3 {
			t.Fatal("hiring spent mines")
		}
		if free > 0 && (w.Planets[2].Owner != player.ID || w.Planets[2].Ground != 500 || w.Planets[2].Fighters != 37) {
			t.Fatal("hiring plundered or retitled a planet")
		}
		if err := w.Validate(); err != nil {
			t.Fatal(err)
		}
	}
}

func TestMercenaryHiringMaximumEconomyRemainsValid(t *testing.T) {
	w, _ := New(clock, 36, 3000)
	for _, port := range w.Ports {
		port.Treasury = MaxMoney
	}
	w.Maintain(clock.Add(24 * time.Hour))
	count, total := mercenaryGroups(w)
	if count != 10 || total != 10*MaxQuantity {
		t.Fatal("force cap or accumulated tax overflow", count, total)
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}

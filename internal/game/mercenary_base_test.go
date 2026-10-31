package game

import (
	"encoding/json"
	"reflect"
	"testing"
	"time"
)

func TestMercenaryBaseCreationAndReserveRestoration(t *testing.T) {
	w, _ := New(clock, 36, 8)
	w.restoreMercenaryBase(clock, func() float64 { return 0 })
	p := w.Planets[99]
	if p == nil || p.Sector != 8 || w.Sectors[8].Planet != 99 || p.Owner != MercenaryOwner || p.FactionHome != MercenaryHome || p.Name != "Mercenary Base" || p.Production != [3]float64{100000, 100000, 100000} || p.Ground != 150000 || p.Bank != 25000000 || !p.Updated.Equal(clock) {
		t.Fatal("wrong recovered creation defaults or links", p)
	}
	if p.Fighters != 0 || p.Mines != 0 || p.Missiles != 0 || p.Plasma != 0 || p.Cargo != [3]float64{} || w.Sectors[8].Defense != nil {
		t.Fatal("creation invented force, stock or sector defense")
	}
	p.Production, p.Fighters = [3]float64{0, 12, 34}, 37.75
	p.Ground, p.Bank = 0, 0
	w.restoreMercenaryBase(clock, nil) // Existing bases do not need placement RNG.
	if p.Ground != 150000 || p.Bank != 25000000 || p.Production != [3]float64{0, 12, 34} || p.Fighters != 37.75 {
		t.Fatal("repair reset production/stocks or failed to restore empty reserves")
	}
	p.Ground, p.Bank = 1, 1
	w.restoreMercenaryBase(clock, nil)
	if p.Ground != 1 || p.Bank != 1 || len(w.Planets) != 1 {
		t.Fatal("repair topped up positive reserves or duplicated base")
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestMercenaryBasePreservesLegacySlotAndCapturedOwnership(t *testing.T) {
	w := routeWorld(t)
	_, _ = w.Join("captain", "Captain")
	legacy := &Planet{Generation: uint64(99), ID: 99, Sector: 8, Owner: 1, Name: "Mercenary Base", Updated: clock, Ground: 123, Bank: 1234}
	w.Planets[99], w.Sectors[8].Planet = legacy, 99
	before := *legacy
	w.restoreMercenaryBase(clock, func() float64 { return 0 })
	if !reflect.DeepEqual(*legacy, before) || w.Planets[2] == nil || w.Planets[2].FactionHome != MercenaryHome || w.Planets[2].Sector != 9 {
		t.Fatal("legacy slot/name was commandeered or fallback failed")
	}
	for _, owner := range []int{0, 1} {
		base := w.Planets[2]
		base.Owner, base.Ground, base.Bank, base.Name = owner, 0, 0, "Captured Home"
		before, _ := json.Marshal(w)
		w.restoreMercenaryBase(clock.Add(24*time.Hour), nil)
		after, _ := json.Marshal(w)
		if string(before) != string(after) {
			t.Fatal("captured or neutralized home was retitled, replenished or duplicated", owner)
		}
		if err := w.Validate(); err != nil {
			t.Fatal(err)
		}
	}
}

func TestMercenaryBaseFinitePlacementAndCapacity(t *testing.T) {
	for _, mode := range []string{"planet-full", "human-defense", "xannor-defense", "slots-full"} {
		t.Run(mode, func(t *testing.T) {
			count := 8
			if mode == "slots-full" {
				count = 108
			}
			w, _ := New(clock, 36, count)
			_, _ = w.Join("owner", "Captain")
			switch mode {
			case "planet-full":
				w.Planets[2] = &Planet{Generation: uint64(2), ID: 2, Sector: 8, Name: "Occupied", Updated: clock}
				w.Sectors[8].Planet = 2
			case "human-defense":
				w.Sectors[8].Defense = &SectorDefense{Owner: 1, Fighters: 1000}
			case "xannor-defense":
				w.Sectors[8].Defense = &SectorDefense{Owner: XannorOwner, Fighters: 1000}
			case "slots-full":
				for id := 2; id <= 100; id++ {
					sector := id + 6
					w.Planets[id] = &Planet{Generation: uint64(id), ID: id, Sector: sector, Name: "Occupied", Updated: clock}
					w.Sectors[sector].Planet = id
				}
			}
			before, _ := json.Marshal(w)
			w.restoreMercenaryBase(clock, func() float64 { t.Fatal("placement drew without capacity"); return 0 })
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("capacity exhaustion changed existing assets")
			}
			if err := w.Validate(); err != nil {
				t.Fatal(err)
			}
		})
	}
}

func TestMercenaryBaseDestroyedThenRebuiltAndDailyReplay(t *testing.T) {
	w, _ := New(clock, 36, 8)
	now := clock.Add(24 * time.Hour)
	w.maintain(now, func() float64 { return 0 })
	if w.Planets[99] == nil {
		t.Fatal("daily maintenance omitted base restoration")
	}
	// A destroyed planet loses both record and reference, as missile aftermath
	// does. The daily guard prevents immediate same-day resurrection.
	delete(w.Planets, 99)
	w.Sectors[8].Planet = 0
	if w.maintain(now, nil) || w.maintain(clock, nil) || len(w.Planets) != 0 {
		t.Fatal("base rebuilt on replay/clock rollback")
	}
	w.maintain(now.Add(24*time.Hour), func() float64 { return 0 })
	if w.Planets[99] == nil || w.Planets[99].Ground != 150000 || w.Planets[99].Owner != MercenaryOwner {
		t.Fatal("missing base not rebuilt next day")
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestFactionHomeValidation(t *testing.T) {
	for _, mode := range []string{"unknown", "unmarked-npc", "xannor", "protected", "duplicate", "broken-link"} {
		t.Run(mode, func(t *testing.T) {
			w := routeWorld(t)
			w.restoreMercenaryBase(clock, func() float64 { return 0 })
			p := w.Planets[99]
			switch mode {
			case "unknown":
				p.FactionHome = "unknown"
			case "unmarked-npc":
				p.FactionHome = ""
			case "xannor":
				p.Owner = XannorOwner
			case "protected":
				w.Sectors[p.Sector].Planet = 0
				p.Sector = 7
				w.Sectors[7].Planet = 99
			case "duplicate":
				other := *p
				other.ID, other.Sector = 2, 9
				w.Planets[2], w.Sectors[9].Planet = &other, 2
			case "broken-link":
				w.Sectors[p.Sector].Planet = 0
			}
			if w.Validate() == nil {
				t.Fatal("invalid faction identity/owner/reference accepted")
			}
		})
	}
}

func TestMercenaryBaseLandingAndCapturePolicy(t *testing.T) {
	w, p := setup(t)
	w.restoreMercenaryBase(clock, func() float64 { return 0 })
	p.Sector = 8
	base := w.Planets[99]
	if w.Land(p.ID, clock) == nil {
		t.Fatal("guarded NPC home permitted human landing")
	}
	report, err := w.RemotePlanetReport(p.ID, 8, clock)
	if err != nil || !report.Available || report.Details != nil || report.Ground != 150000 {
		t.Fatal("NPC home report leaked private resources or hid public defenses", report, err)
	}
	base.Ground = 0
	p.Ground = 100
	if err := w.Land(p.ID, clock); err != nil {
		t.Fatal(err)
	}
	if err := w.Garrison(p.ID, p.PlanetToken, 100, clock); err != nil {
		t.Fatal(err)
	}
	w.restoreMercenaryBase(clock, nil)
	if base.Owner != p.ID || base.Ground != 100 || base.FactionHome != MercenaryHome {
		t.Fatal("capture lost title, ground or stable home identity")
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestMercenaryBaseMissileDestructionRemovesFactionIdentity(t *testing.T) {
	w, p := setup(t)
	w.restoreMercenaryBase(clock, func() float64 { return 0 })
	p.Sector, p.Missiles = 7, 10
	w.Sectors[7].Warps = []int{8}
	base := w.Planets[99]
	base.Ground, base.Bank, base.Production = 1, 1, [3]float64{1, 1, 1}
	v, _ := w.NewVisibility(p.ID)
	intent, err := w.PrepareMissile(p.ID, 8, 10, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return .999 }, clock)
	if err != nil || !out.Primary.PlanetDestroyed || w.Planets[99] != nil || w.Sectors[8].Planet != 0 {
		t.Fatal("NPC base destruction retained record, link or home identity", out, err)
	}
	w.maintain(clock.Add(24*time.Hour), func() float64 { return 0 })
	if w.Planets[99] == nil || w.Planets[99].Owner != MercenaryOwner || w.Planets[99].Ground != 150000 {
		t.Fatal("destroyed base did not rebuild in the next daily transaction")
	}
}

func TestMercenaryBaseProductionFeedsExistingRoutePickup(t *testing.T) {
	w := routeWorld(t)
	w.restoreMercenaryBase(clock, func() float64 { return .2 }) // Sector 9.
	w.Sectors[8].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 100}
	w.maintain(clock.Add(24*time.Hour), func() float64 { return 0 })
	base := w.Planets[99]
	// Initial production 300,000 + initial bank/500 = 350,000 fighters.
	if base.Sector != 9 || w.Sectors[9].Defense == nil || w.Sectors[9].Defense.Fighters != 350100 || base.Fighters != 0 || base.Owner != MercenaryOwner || base.Bank != 25250000 {
		t.Fatal("base growth/pickup was lost, duplicated or reset", base, w.Sectors[9].Defense)
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}

package game

import (
	"encoding/json"
	"fmt"
	"testing"
	"time"
)

func TestHumanDefenseDesertionStrictThresholdAndFirstPlayer(t *testing.T) {
	for _, tc := range []struct {
		fighters int64
		roll     float64
		deserts  bool
	}{
		{1, 0, false}, {1, .01, false}, {1, .010001, true},
		{50, .5, false}, {50, .500001, true},
		{99, .99, false}, {99, .999, true},
		{100, .999999, false}, {1000, .999999, false}, {MaxQuantity, .999999, false},
	} {
		for _, owner := range []int{1, 2} {
			t.Run(fmt.Sprintf("%d-%g-owner%d", tc.fighters, tc.roll, owner), func(t *testing.T) {
				w := routeWorld(t)
				_, _ = w.Join("first", "First")
				_, _ = w.Join("second", "Second")
				w.Sectors[8].Defense = &SectorDefense{Owner: owner, Fighters: tc.fighters}
				draws := 0
				w.desertHumanDefenses(func() float64 { draws++; return tc.roll })
				want := owner
				if tc.deserts {
					want = MercenaryOwner
				}
				if d := w.Sectors[8].Defense; d.Owner != want || d.Fighters != tc.fighters || draws != 1 {
					t.Fatal("strict threshold, first-player identity or force changed", d, draws)
				}
				if err := w.Validate(); err != nil {
					t.Fatal(err)
				}
			})
		}
	}
}

func TestHumanDefenseDesertionScopeAndConservation(t *testing.T) {
	w := routeWorld(t)
	p, _ := w.Join("owner", "Captain")
	p.Sector, p.Fighters, p.Ground, p.Credits = 8, 1000, 500, 12345
	w.Ports[8].Owner, w.Ports[8].Treasury = p.ID, 123
	w.Sectors[8].Planet = 2
	w.Planets[2] = &Planet{Generation: uint64(2), ID: 2, Sector: 8, Owner: p.ID, Name: "Probe", Fighters: 37.75, Ground: 500000, Bank: 1234, Updated: clock}
	w.Sectors[7].Defense = &SectorDefense{Owner: p.ID, Fighters: 1}
	w.Sectors[8].Defense = &SectorDefense{Owner: p.ID, Fighters: 1}
	w.Sectors[9].Defense = &SectorDefense{Owner: XannorOwner, Fighters: 1}
	w.Sectors[10].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 1}
	before, _ := json.Marshal(w)
	draws := 0
	w.desertHumanDefenses(func() float64 { draws++; return .99 })
	if draws != 1 || w.Sectors[7].Defense.Owner != p.ID || w.Sectors[9].Defense.Owner != XannorOwner || w.Sectors[10].Defense.Owner != MercenaryOwner {
		t.Fatal("protected or NPC group participated", draws)
	}
	if w.Sectors[8].Defense.Owner != MercenaryOwner {
		t.Fatal("eligible group did not desert")
	}
	// Undo only the expected owner change; every other saved field must match.
	w.Sectors[8].Defense.Owner = p.ID
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("desertion changed ships, taxes, titles, ground, stocks or unrelated factions")
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestHumanDefenseDesertionStableOrder(t *testing.T) {
	w := routeWorld(t)
	_, _ = w.Join("owner", "Captain")
	for _, id := range []int{8, 10, 12} {
		w.Sectors[id].Defense = &SectorDefense{Owner: 1, Fighters: 50}
	}
	rolls := []float64{.9, .5, .1}
	i := 0
	w.desertHumanDefenses(func() float64 { r := rolls[i]; i++; return r })
	if w.Sectors[12].Defense.Owner != MercenaryOwner || w.Sectors[10].Defense.Owner != 1 || w.Sectors[8].Defense.Owner != 1 || i != 3 {
		t.Fatal("human groups did not use stable descending sector order")
	}
}

func TestHumanDefenseDesertionPrecedesRoutesAndScorePublication(t *testing.T) {
	w := routeWorld(t)
	p, _ := w.Join("owner", "Captain")
	w.Sectors[8].Defense = &SectorDefense{Owner: p.ID, Fighters: 50}
	w.Sectors[9].Defense = &SectorDefense{Owner: p.ID, Fighters: 50}
	w.Ports[2].Treasury = 90 // Nine tax credits do not fund a fresh group.
	now := clock.Add(24 * time.Hour)
	if !w.maintain(now, func() float64 { return .99 }) {
		t.Fatal("maintenance skipped")
	}
	// Both groups deserted before movement. The group at 9 cannot reach its
	// sampled target 8. The group at 8 then merges into it, preserving all 100.
	if w.Sectors[8].Defense != nil || w.Sectors[9].Defense.Owner != MercenaryOwner || w.Sectors[9].Defense.Fighters != 100 {
		t.Fatal("desertion occurred after routing or converted group acted twice")
	}
	owned, err := w.OwnSectorFighters(p.ID)
	if err != nil || len(owned) != 0 {
		t.Fatal("deserted fighters still reported as personally owned", owned, err)
	}
	report, _ := w.PlayerRankings(p.ID, false)
	if len(report.Players) != 1 || p.StoredScore != report.Players[0].Score || w.Ports[2].Treasury != 81 {
		t.Fatal("scores or taxes not committed after ownership changes")
	}
	before, _ := json.Marshal(w)
	noDraw := func() float64 { t.Fatal("daily replay consumed randomness"); return 0 }
	if w.maintain(now, noDraw) || w.maintain(clock, noDraw) {
		t.Fatal("daily replay or clock rollback ran phases")
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("replay changed desertion, force, score or economy")
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}

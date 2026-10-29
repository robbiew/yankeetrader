package game

import (
	"encoding/json"
	"testing"
	"time"
)

func routeWorld(t *testing.T) *World {
	t.Helper()
	w, err := New(clock, 36, 12)
	if err != nil {
		t.Fatal(err)
	}
	for id := 8; id <= 12; id++ {
		w.Sectors[id].Warps = nil
		if id < 12 {
			w.Sectors[id].Warps = []int{id + 1}
		}
	}
	return w
}

func TestMercenaryRoutesWalkOnceAndRejectInvalidPaths(t *testing.T) {
	for _, mode := range []string{"multi-hop", "unreachable", "protected-transit", "protected-destination"} {
		t.Run(mode, func(t *testing.T) {
			w := routeWorld(t)
			w.Sectors[8].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 100}
			want := 12
			if mode == "unreachable" {
				w.Sectors[8].Warps = nil
				want = 8
			}
			if mode == "protected-transit" {
				w.Sectors[8].Warps = []int{1}
				w.Sectors[1].Warps = []int{12}
				want = 8
			}
			if mode == "protected-destination" {
				w.Sectors[8].Defense = nil
				w.Sectors[2].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 100}
				want = 2
			}
			draws := 0
			w.mercenaryActions(func() float64 { draws++; return 0 })
			count, force := mercenaryGroups(w)
			if count != 1 || force != 100 || w.Sectors[want].Defense == nil || draws > 1 {
				t.Fatal("route repeated, lost force, or relocated through failed/protected path", count, force, draws)
			}
			if err := w.Validate(); err != nil {
				t.Fatal(err)
			}
		})
	}
}

func TestMercenaryRoutesMergedReceiverCannotActAgain(t *testing.T) {
	w := routeWorld(t)
	w.Sectors[12].Warps = []int{8}
	w.Sectors[8].Warps = []int{9}
	w.Sectors[12].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 100}
	w.Sectors[8].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 200}
	// Descending target list: last index selects sector 8 from source 12.
	draws := 0
	w.mercenaryActions(func() float64 { draws++; return .99 })
	if draws != 1 || w.Sectors[8].Defense == nil || w.Sectors[8].Defense.Fighters != 300 || w.Sectors[12].Defense != nil {
		t.Fatal("merged recipient received another activation", draws)
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestMercenaryRoutesRelocationCannotCreateAnotherActivation(t *testing.T) {
	w := routeWorld(t)
	w.Sectors[12].Warps = []int{8}
	w.Sectors[12].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 100}
	draws := 0
	w.mercenaryActions(func() float64 { draws++; return .99 })
	if draws != 1 || w.Sectors[8].Defense == nil || w.Sectors[8].Defense.Fighters != 100 {
		t.Fatal("relocated group was scanned again", draws)
	}
}

func TestMercenaryRoutesPlanetPickupPreservesTitleGroundAndFractions(t *testing.T) {
	for _, owner := range []int{0, 1} {
		w := routeWorld(t)
		_, _ = w.Join("planet", "Captain")
		w.Sectors[8].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 100}
		w.Sectors[9].Planet = 2
		w.Planets[2] = &Planet{ID: 2, Sector: 9, Name: "Probe", Owner: owner, Ground: 500000, Fighters: 37.75, Updated: clock}
		w.mercenaryActions(func() float64 { return 0 })
		p := w.Planets[2]
		if w.Sectors[9].Defense == nil || w.Sectors[9].Defense.Fighters != 137 || p.Owner != owner || p.Ground != 500000 || p.Fighters != .75 {
			t.Fatal("pickup/title/ground/stock accounting", p)
		}
		before, _ := json.Marshal(w)
		// A planet at the origin holds a group for draws below .66.
		w.mercenaryActions(func() float64 { return 0 })
		after, _ := json.Marshal(w)
		if string(before) != string(after) {
			t.Fatal("held group moved or plundered its origin")
		}
		if err := w.Validate(); err != nil {
			t.Fatal(err)
		}
	}
}

func TestMercenaryRoutesMineLayersAndBoundedWork(t *testing.T) {
	for _, tc := range []struct {
		force, first, second, left, spent int64
	}{
		{100, 3, 0, 0, 1},
		{100000, 2, 1, 92497, 3},
		{MaxQuantity, MaxQuantity, 0, MaxQuantity - mercenaryWorkLimit*2501, mercenaryWorkLimit},
	} {
		w := routeWorld(t)
		_, _ = w.Join("mines", "Captain")
		w.Sectors[8].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: tc.force}
		w.Sectors[9].Minefield = []MineLayer{{Owner: 1, Count: tc.first}}
		if tc.second > 0 {
			w.Sectors[9].Minefield = append(w.Sectors[9].Minefield, MineLayer{Owner: 0, Count: tc.second})
		}
		// Direct route separates target selection from exact damage controls.
		w.walkMercenaries(w.Sectors[8].Defense, []int{8, 9, 10, 11, 12}, map[*SectorDefense]bool{}, func() float64 { return .5 })
		_, force := mercenaryGroups(w)
		if force != tc.left {
			t.Fatal("nested mine rolls or loss cap", tc, force)
		}
		var remaining int64
		for _, layer := range w.Sectors[9].Minefield {
			remaining += layer.Count
		}
		if remaining != tc.first+tc.second-tc.spent {
			t.Fatal("wrong mine debit", tc, remaining)
		}
		if remaining > 0 && (w.Sectors[9].Minefield[0].Owner != 1 || (force > 0 && w.Sectors[8].Defense == nil)) {
			t.Fatal("source attribution lost or exhausted work entered field")
		}
		if err := w.Validate(); err != nil {
			t.Fatal(err)
		}
	}
}

func TestMercenaryRoutesMinesPrecedeDefensesAndShareWork(t *testing.T) {
	w := routeWorld(t)
	_, _ = w.Join("owner", "Captain")
	w.Sectors[8].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 1}
	w.Sectors[9].Defense = &SectorDefense{Owner: 1, Fighters: 1000}
	w.Sectors[9].Minefield = []MineLayer{{Owner: 1, Count: 1}}
	w.walkMercenaries(w.Sectors[8].Defense, []int{8, 9}, map[*SectorDefense]bool{}, func() float64 { return 0 })
	if len(w.Sectors[9].Minefield) != 0 || w.Sectors[9].Defense.Fighters != 1000 {
		t.Fatal("defense interaction preceded fatal mine")
	}
	w = routeWorld(t)
	w.Sectors[8].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: MaxQuantity}
	w.Sectors[9].Minefield = []MineLayer{{Owner: 0, Count: 6000}}
	w.Sectors[10].Minefield = []MineLayer{{Owner: 0, Count: 6000}}
	w.walkMercenaries(w.Sectors[8].Defense, []int{8, 9, 10, 11, 12}, map[*SectorDefense]bool{}, func() float64 { return 0 })
	if w.Sectors[9].Defense == nil || w.Sectors[9].Defense.Fighters != MaxQuantity-mercenaryWorkLimit || len(w.Sectors[9].Minefield) != 0 || w.Sectors[10].Minefield[0].Count != 2000 {
		t.Fatal("work allowance restarted at each field or fallback lost survivors")
	}
}

func TestMercenaryRoutesPlanetHoldStrictBoundary(t *testing.T) {
	for _, roll := range []float64{.65, .66} {
		w := routeWorld(t)
		w.Sectors[8].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 100}
		w.Sectors[8].Planet = 2
		w.Planets[2] = &Planet{ID: 2, Sector: 8, Name: "Origin", Fighters: 37, Updated: clock}
		w.mercenaryActions(func() float64 { return roll })
		if (w.Sectors[8].Defense != nil) != (roll < .66) || w.Planets[2].Fighters != 37 {
			t.Fatal("planet hold threshold or origin pickup", roll)
		}
	}
}

func TestMercenaryRoutesDefenseOrderingAndCombatThreshold(t *testing.T) {
	for _, tc := range []struct {
		name                       string
		owner                      int
		force, defenders, attacker int64
		roll                       float64
	}{
		{"human reinforcement", 1, 100, 1000, 0, 0},
		{"human threshold reinforcement", 1, 100, 1000, 0, .95},
		{"Xannor fight", XannorOwner, 201, 201, 201, 0},
		{"threshold below", XannorOwner, 200, 201, 200, 0},
		{"tie favors defender", XannorOwner, 201, 201, 0, .5},
		{"human attack", 1, 201, 201, 0, .99},
		{"bounded combat", XannorOwner, MaxQuantity, MaxQuantity, MaxQuantity, 0},
	} {
		t.Run(tc.name, func(t *testing.T) {
			w := routeWorld(t)
			_, _ = w.Join("owner", "Captain")
			w.Sectors[8].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: tc.force}
			w.Sectors[9].Defense = &SectorDefense{Owner: tc.owner, Fighters: tc.defenders}
			w.Sectors[9].Planet = 2
			w.Planets[2] = &Planet{ID: 2, Sector: 9, Name: "Probe", Fighters: 37, Updated: clock}
			draws := 0
			w.walkMercenaries(w.Sectors[8].Defense, []int{8, 9, 10, 11, 12}, map[*SectorDefense]bool{}, func() float64 { draws++; return tc.roll })
			_, force := mercenaryGroups(w)
			if force != tc.attacker || w.Planets[2].Fighters != 37 {
				t.Fatal("battle/reinforcement or post-battle pickup", force)
			}
			if tc.name == "human reinforcement" && (w.Sectors[9].Defense.Owner != 1 || w.Sectors[9].Defense.Fighters != 1100) {
				t.Fatal("reinforcement changed owner or lost force")
			}
			if tc.name == "Xannor fight" && draws != 53 {
				t.Fatal("wrong 200 threshold, 150 batch or eager faction draw", draws)
			}
			if tc.name == "threshold below" && draws != 202 {
				t.Fatal("batch used at exactly 200", draws)
			}
			if tc.name == "bounded combat" && (draws != mercenaryWorkLimit+1 || w.Sectors[8].Defense == nil || w.Sectors[9].Defense.Fighters != MaxQuantity-150*mercenaryWorkLimit) {
				t.Fatal("unbounded combat or invalid fallback", draws)
			}
			if err := w.Validate(); err != nil {
				t.Fatal(err)
			}
		})
	}
}

func TestMercenaryRoutesCapacityConservesForce(t *testing.T) {
	for _, owner := range []int{MercenaryOwner, 1} {
		w := routeWorld(t)
		_, _ = w.Join("owner", "Captain")
		w.Sectors[8].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 100}
		w.Sectors[9].Defense = &SectorDefense{Owner: owner, Fighters: MaxQuantity - 20}
		w.walkMercenaries(w.Sectors[8].Defense, []int{8, 9}, map[*SectorDefense]bool{}, func() float64 { return 0 })
		if w.Sectors[8].Defense.Fighters != 80 || w.Sectors[9].Defense.Fighters != MaxQuantity || w.Sectors[9].Defense.Owner != owner {
			t.Fatal("capacity merge lost force or changed ownership")
		}
		if err := w.Validate(); err != nil {
			t.Fatal(err)
		}
	}
	w := routeWorld(t)
	w.Sectors[8].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: MaxQuantity - 20}
	w.Sectors[9].Planet = 2
	w.Planets[2] = &Planet{ID: 2, Sector: 9, Name: "Probe", Fighters: 37.75, Updated: clock}
	w.walkMercenaries(w.Sectors[8].Defense, []int{8, 9}, map[*SectorDefense]bool{}, func() float64 { return 0 })
	if w.Planets[2].Fighters != 17.75 || w.Sectors[9].Defense.Fighters != MaxQuantity {
		t.Fatal("planet pickup discarded overflow")
	}
}

func TestMercenaryRoutesMaintenanceIntegrationAndReplay(t *testing.T) {
	w := routeWorld(t)
	w.Sectors[8].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 100}
	w.Maintain(clock.Add(24 * time.Hour))
	if w.Sectors[8].Defense != nil {
		t.Fatal("daily maintenance omitted route actions")
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
	before, _ := json.Marshal(w)
	if w.Maintain(clock.Add(24*time.Hour)) || w.Maintain(clock) {
		t.Fatal("route maintenance repeated")
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("daily replay moved a group")
	}
}

package game

import (
	"encoding/json"
	"testing"
	"time"
)

func xannorWorld(t *testing.T) *World {
	t.Helper()
	w := routeWorld(t)
	w.Xannor = &XannorState{HQ: 8}
	w.restoreXannoron(clock, func() float64 { return .5 })
	return w
}

func xannorForce(w *World) int64 {
	total := int64(0)
	if w.Xannor != nil {
		total = w.Xannor.Reserve
	}
	for _, s := range w.Sectors {
		if d := s.Defense; d != nil && d.Owner == XannorOwner {
			total += d.Fighters
		}
	}
	return total
}

func TestXannoronRestorationCaptureAndCapacity(t *testing.T) {
	w := xannorWorld(t)
	p := w.Planets[100]
	if p.Name != "Xannoron" || p.FactionHome != XannorHome || p.Owner != XannorOwner || p.Ground != 137 || p.Bank != 5100000 || p.Production != [3]float64{100000, 100000, 100000} || w.Sectors[8].Planet != 100 {
		t.Fatal("wrong creation defaults", p)
	}
	p.Fighters, p.Plasma, p.Mines, p.Missiles = 37.5, 5, 3, 4
	p.Cargo = [3]float64{11, 12, 13}
	p.Bank, p.Ground = 0, MaxQuantity-1
	w.restoreXannoron(clock, func() float64 { return .99 })
	if p.Bank != 1000000 || p.Ground != MaxQuantity || p.Fighters != 37.5 || p.Plasma != 5 || p.Mines != 3 || p.Missiles != 4 || p.Cargo != [3]float64{11, 12, 13} {
		t.Fatal("reserve repair reset existing inventory or exceeded capacity", p)
	}
	_, _ = w.Join("captain", "Captain")
	for _, owner := range []int{0, 1} {
		p.Owner, p.Ground, p.Bank, p.Name = owner, 0, 0, "Captured"
		before, _ := json.Marshal(w)
		w.restoreXannoron(clock, nil)
		after, _ := json.Marshal(w)
		if string(before) != string(after) {
			t.Fatal("captured home changed", owner)
		}
		if err := w.Validate(); err != nil {
			t.Fatal(err)
		}
	}
}

func TestXannoronFinitePlacementAndLegacyPreservation(t *testing.T) {
	for _, mode := range []string{"human-one", "mercenary-one", "unrelated-planet", "mines", "slots-full"} {
		t.Run(mode, func(t *testing.T) {
			count := 8
			if mode == "slots-full" {
				count = 108
			}
			w, _ := New(clock, 36, count)
			_, _ = w.Join("captain", "Captain")
			switch mode {
			case "human-one":
				w.Sectors[8].Defense = &SectorDefense{Owner: 1, Fighters: 1}
			case "mercenary-one":
				w.Sectors[8].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 1}
			case "unrelated-planet":
				w.Planets[100] = &Planet{Generation: uint64(100), ID: 100, Sector: 8, Owner: 1, Name: "Xannoron", Updated: clock}
				w.Sectors[8].Planet = 100
			case "mines":
				w.Sectors[8].Minefield = []MineLayer{{Owner: 1, Count: 1}}
			case "slots-full":
				for id := 2; id <= 100; id++ {
					w.Planets[id] = &Planet{Generation: uint64(id), ID: id, Sector: id + 6, Name: "Occupied", Updated: clock}
					w.Sectors[id+6].Planet = id
				}
			}
			before, _ := json.Marshal(w)
			w.maintainXannor(clock, func() float64 { t.Fatal("no capacity must not draw RNG"); return 0 })
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("capacity exhaustion changed assets")
			}
			if err := w.Validate(); err != nil {
				t.Fatal(err)
			}
		})
	}
	w := routeWorld(t)
	_, _ = w.Join("captain", "Captain")
	legacy := &Planet{Generation: uint64(100), ID: 100, Sector: 9, Owner: 1, Name: "Xannoron", Updated: clock, Ground: 100, Bank: 123}
	w.Planets[100], w.Sectors[9].Planet = legacy, 100
	before := *legacy
	w.restoreMercenaryBase(clock, func() float64 { return 0 })
	w.restoreXannoron(clock, func() float64 { return 0 })
	if *legacy != before || w.Planets[2] == nil || w.Planets[2].FactionHome != XannorHome || w.Xannor.HQ != 10 {
		t.Fatal("commandeered legacy planet or lost independent faction homes")
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestXannorRegenerationCountsUniqueForcesAndLivingStoredScores(t *testing.T) {
	for _, tc := range []struct {
		name                             string
		score, hq, mobile, reserve, want int64
	}{
		{"strict above cutoff", 999999, 10000, 0, 0, 10000},
		{"cutoff equality", 1000000, 10000, 0, 0, 12000},
		{"integer division", 1000500, 10000, 0, 0, 12001},
		{"mobile counts", 1000000, 10000, 1, 0, 10001},
		{"reserve counts", 1000000, 9999, 0, 2, 10001},
		{"capacity", MaxMoney, MaxQuantity - 2, 0, 0, MaxQuantity},
		{"negative score", -1, 100, 0, 0, 100},
	} {
		t.Run(tc.name, func(t *testing.T) {
			w := xannorWorld(t)
			p, _ := w.Join("captain", "Captain")
			p.StoredScore = tc.score
			w.Sectors[8].Defense = &SectorDefense{Owner: XannorOwner, Fighters: tc.hq}
			if tc.mobile > 0 {
				w.Sectors[9].Defense = &SectorDefense{Owner: XannorOwner, Fighters: tc.mobile}
			}
			w.Xannor.Reserve = tc.reserve
			w.maintainXannor(clock, func() float64 { return 0 })
			if got := xannorForce(w); got != tc.want {
				t.Fatal("regeneration wrong", got, tc.want)
			}
			if err := w.Validate(); err != nil {
				t.Fatal(err)
			}
		})
	}
	w := xannorWorld(t)
	p, _ := w.Join("dead", "Dead")
	p.StoredScore = MaxMoney
	p.Death = &Death{}
	w.maintainXannor(clock, func() float64 { return 0 })
	if xannorForce(w) != 0 {
		t.Fatal("dead account funded regeneration")
	}
}

func TestXannorHQReclaimThresholdTieAndFirstPlayer(t *testing.T) {
	for _, owner := range []int{1, MercenaryOwner} {
		for _, tc := range []struct {
			name                 string
			force, defense       int64
			roll                 float64
			draws                int
			survivors, remaining int64
		}{
			{"large tie", 251, 251, .5, 2, 251, 0},
			{"strict threshold", 250, 251, .5, 251, 250, 0},
			{"defender threshold", 251, 250, .5, 250, 251, 0},
			{"loss", 251, 251, .50001, 2, 0, 251},
			{"bounded", MaxQuantity, MaxQuantity, .75, xannorWorkLimit, MaxQuantity - 250*xannorWorkLimit, MaxQuantity},
		} {
			t.Run(tc.name+string(rune('A'+owner)), func(t *testing.T) {
				w := xannorWorld(t)
				_, _ = w.Join("captain", "Captain")
				w.Xannor.Reserve = tc.force
				w.Sectors[8].Defense = &SectorDefense{Owner: owner, Fighters: tc.defense}
				draws := 0
				w.maintainXannor(clock, func() float64 { draws++; return tc.roll })
				// Existing-home growth consumes one draw; success consumes a relocation draw.
				wantDraws := tc.draws + 1
				if tc.remaining == 0 {
					wantDraws++
				}
				if draws != wantDraws || xannorForce(w) != tc.survivors {
					t.Fatal("wrong battle work/tie/force", draws, wantDraws, xannorForce(w))
				}
				if tc.remaining > 0 {
					if w.Xannor.HQ != 8 || w.Sectors[8].Defense.Owner != owner || w.Sectors[8].Defense.Fighters != tc.remaining || w.Xannor.Reserve != tc.survivors {
						t.Fatal("failed/unfinished reclaim lost participants")
					}
				} else if w.Xannor.HQ == 8 || w.Sectors[8].Defense != nil || w.Planets[100].Sector != w.Xannor.HQ {
					t.Fatal("successful reclaim did not relocate home and survivors")
				}
				if err := w.Validate(); err != nil {
					t.Fatal(err)
				}
			})
		}
	}
}

func TestXannorRelocationConservesForceAndPreservesCapturedHome(t *testing.T) {
	w := xannorWorld(t)
	_, _ = w.Join("captain", "Captain")
	p := w.Planets[100]
	p.Owner, p.Name, p.Ground, p.Bank = 1, "Captured", 7, 123
	w.Xannor.Reserve = 10
	w.Sectors[8].Defense = &SectorDefense{Owner: 1, Fighters: 1}
	w.Sectors[9].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 1}
	w.Sectors[10].Defense = &SectorDefense{Owner: XannorOwner, Fighters: 20}
	w.Planets[2] = &Planet{Generation: uint64(2), ID: 2, Sector: 11, Name: "Unrelated", Updated: clock}
	w.Sectors[11].Planet = 2
	w.Sectors[12].Defense = &SectorDefense{Owner: XannorOwner, Fighters: MaxQuantity}
	w.maintainXannor(clock, func() float64 { return 0 })
	if w.Xannor.HQ != 10 || w.Sectors[10].Defense.Fighters != 30 || w.Sectors[9].Defense.Owner != MercenaryOwner || w.Sectors[12].Defense.Fighters != MaxQuantity || p.Sector != 8 || w.Sectors[8].Planet != 100 || p.Owner != 1 || p.Name != "Captured" || p.Ground != 7 || p.Bank != 123 {
		t.Fatal("relocation overwrote a participant, overflowed or moved captured home")
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
	// With no free destination, successful reclaim holds the old HQ.
	for _, id := range []int{8, 9, 11, 12} {
		w.Sectors[id].Defense = &SectorDefense{Owner: 1, Fighters: 1}
	}
	w.Xannor.Reserve = 100
	w.Sectors[10].Defense = &SectorDefense{Owner: 1, Fighters: 1}
	w.maintainXannor(clock, func() float64 { return 0 })
	if w.Xannor.HQ != 10 || w.Sectors[10].Defense.Owner != XannorOwner || w.Sectors[10].Defense.Fighters != 100 {
		t.Fatal("no-capacity reclaim lost surviving HQ")
	}
}

func TestXannorNoPhantomForceAndDailyGuard(t *testing.T) {
	w := xannorWorld(t)
	w.Sectors[9].Defense = &SectorDefense{Owner: XannorOwner, Fighters: 2}
	w.maintainXannor(clock, func() float64 { return 0 })
	if w.Xannor.HQ != 9 || xannorForce(w) != 2 || w.Sectors[9].Defense.Fighters != 2 || w.Sectors[8].Defense != nil {
		t.Fatal("zero-force relocation invented fighters")
	}
	now := clock.Add(24 * time.Hour)
	w.maintain(now, func() float64 { return 0 })
	before, _ := json.Marshal(w)
	if w.maintain(now, nil) || w.maintain(clock, nil) {
		t.Fatal("daily guard repeated lifecycle")
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("replay changed world")
	}
	delete(w.Planets, 100)
	w.Sectors[w.Xannor.HQ].Planet = 0
	w.maintain(now.Add(24*time.Hour), func() float64 { return 0 })
	if w.xannorHome() == nil {
		t.Fatal("destroyed home did not rebuild")
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestXannorValidation(t *testing.T) {
	for _, mode := range []string{"protected", "missing-sector", "negative", "overflow", "combined-overflow", "missing-state", "duplicate", "wrong-faction-owner"} {
		t.Run(mode, func(t *testing.T) {
			w := xannorWorld(t)
			switch mode {
			case "protected":
				w.Xannor.HQ = 7
			case "missing-sector":
				w.Xannor.HQ = 99
			case "negative":
				w.Xannor.Reserve = -1
			case "overflow":
				w.Xannor.Reserve = MaxQuantity + 1
			case "combined-overflow":
				w.Xannor.Reserve = MaxQuantity
				w.Sectors[8].Defense = &SectorDefense{Owner: XannorOwner, Fighters: 1}
			case "missing-state":
				w.Xannor = nil
			case "duplicate":
				p := *w.Planets[100]
				p.ID, p.Sector = 2, 9
				w.Planets[2], w.Sectors[9].Planet = &p, 2
			case "wrong-faction-owner":
				w.Planets[100].Owner = MercenaryOwner
			}
			if w.Validate() == nil {
				t.Fatal("invalid HQ/home accepted")
			}
		})
	}
}

func TestXannoronLandingCaptureAndMissileRebuild(t *testing.T) {
	w := xannorWorld(t)
	p, _ := w.Join("captain", "Captain")
	p.Sector = 8
	home := w.Planets[100]
	home.Ground = 100
	if w.Land(p.ID, clock) == nil {
		t.Fatal("guarded Xannor home allowed landing")
	}
	report, err := w.RemotePlanetReport(p.ID, 8, clock)
	if err != nil || !report.Available || report.Details != nil || report.Ground != 100 {
		t.Fatal("report leaked private home inventory", report, err)
	}
	home.Ground = 0
	p.Ground = 100
	if err := w.Land(p.ID, clock); err != nil {
		t.Fatal(err)
	}
	if err := w.Garrison(p.ID, p.PlanetToken, 100, clock); err != nil {
		t.Fatal(err)
	}
	w.restoreXannoron(clock, nil)
	if home.Owner != 1 || home.Ground != 100 || home.FactionHome != XannorHome {
		t.Fatal("capture did not retain title and identity")
	}
	p.Sector = 6
	p.PlanetToken = ""
	p.LandedPlanet = 0
	p, _ = w.Join("attacker", "Attacker")
	p.Sector, p.Missiles = 7, 10
	w.Sectors[7].Warps = []int{8}
	home.Ground, home.Bank, home.Production = 1, 1, [3]float64{1, 1, 1}
	v, _ := w.NewVisibility(p.ID)
	intent, err := w.PrepareMissile(p.ID, 8, 10, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return .999 }, clock)
	if err != nil || !out.Primary.PlanetDestroyed || w.Planets[100] != nil || w.Sectors[8].Planet != 0 || w.Xannor.HQ != 8 {
		t.Fatal("destruction retained home or discarded HQ", out, err)
	}
	w.maintain(clock.Add(24*time.Hour), func() float64 { return 0 })
	if w.Planets[100] == nil || w.Planets[100].Owner != XannorOwner || w.Planets[100].FactionHome != XannorHome {
		t.Fatal("destroyed home did not rebuild next day")
	}
	if w.Planets[99] == nil || w.Planets[99].Sector == 8 {
		t.Fatal("Mercenary creation commandeered existing Xannor HQ")
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}

package game

import (
	"encoding/json"
	"math"
	"math/rand"
	"reflect"
	"testing"
	"time"
)

func shipWorld(t *testing.T, fighters, shields int64) (*World, *Player) {
	t.Helper()
	w := mobileWorld(t, 12)
	p, _ := w.Join("captain", "Captain")
	p.Sector, p.Cloak, p.Fighters, p.Shields = 10, 0, fighters, shields
	return w, p
}

func TestXannorShipThresholdsTiesAndStageOrder(t *testing.T) {
	for _, n := range []int64{499, 500, 5000, 5001} {
		want := int64(500)
		if n == 499 {
			want = 1
		}
		if n == 5001 {
			want = 5000
		}
		if xannorShipBatch(n, n) != want {
			t.Fatal("batch boundary", n)
		}
	}
	for _, tc := range []struct {
		name                string
		f, s, g             int64
		roll                float64
		dead                bool
		leftF, leftS, leftG int64
	}{
		{"fighter-tie", 500, 0, 500, .5, true, 0, 0, 500},
		{"fighter-above", 500, 17, 500, .500001, false, 500, 17, 0},
		{"shield-tie", 0, 500, 500, .5, true, 0, 0, 500},
		{"shield-below", 0, 500, 500, .499999, false, 0, 500, 0},
		{"large-then-unit", 5001, 0, 5001, .5, true, 0, 0, 5001},
		{"both-stages", 500, 500, 1000, .5, true, 0, 0, 1000},
		{"unarmed", 0, 0, 100, 0, true, 0, 0, 100},
	} {
		t.Run(tc.name, func(t *testing.T) {
			w, p := shipWorld(t, tc.f, tc.s)
			force, work, preferred := tc.g, 20000, 12
			if !w.xannorShips(10, &force, &work, &preferred, clock, func() float64 { return tc.roll }) {
				t.Fatal("unexpected work exhaustion")
			}
			if (p.Death != nil) != tc.dead || p.Fighters != tc.leftF || p.Shields != tc.leftS || force != tc.leftG {
				t.Fatal("damage", p, force)
			}
			if len(p.BattleReports) != 1 {
				t.Fatal("missing report")
			}
			r := p.BattleReports[0]
			if r.FightersLost != tc.f-tc.leftF || r.ShieldsLost != tc.s-tc.leftS || r.XannorLost != tc.g-tc.leftG || r.Destroyed != tc.dead {
				t.Fatal("wrong private casualties", r)
			}
			if tc.dead && (p.Death.Cause != "xannor" || p.Death.Killer != XannorOwner || p.Death.Sector != 10 || len(w.News) != 1 || w.News[0].Kind != NewsXannorDeath) {
				t.Fatal("missing atomic attribution/news")
			}
			validMobile(t, w)
		})
	}
}

func TestXannorShipDetectionAndUnattackableShips(t *testing.T) {
	for _, delta := range []float64{-.000001, 0, .000001} {
		w, p := shipWorld(t, 500, 0)
		p.Cloak = 1
		roll := p.Cloak - .33 + delta
		force, work, preferred := int64(500), 100, 0
		draws := 0
		w.xannorShips(10, &force, &work, &preferred, clock, func() float64 { draws++; return roll })
		if delta < 0 {
			if draws != 1 || force != 500 || len(p.BattleReports) != 0 {
				t.Fatal("below cloak threshold must evade")
			}
		} else if force != 0 || len(p.BattleReports) != 1 {
			t.Fatal("full cloak grants immunity")
		}
	}
	for _, mode := range []string{"dead", "elsewhere", "protected", "generation", "report-sequence", "news-sequence", "clock"} {
		w, p := shipWorld(t, 100, 100)
		now := clock
		if mode == "dead" {
			if err := w.RecordDeath(DeathContext{Victim: p.ID, Sector: 10, Cause: "hazard"}, clock); err != nil {
				t.Fatal(err)
			}
		}
		if mode == "elsewhere" {
			p.Sector = 11
		}
		sector := 10
		if mode == "protected" {
			p.Sector = 7
			sector = 7
		}
		if mode == "generation" {
			p.ShipGeneration = math.MaxUint64 - 1
		}
		if mode == "report-sequence" {
			w.NextBattleReport = math.MaxUint64
		}
		if mode == "news-sequence" {
			w.NextNews = math.MaxUint64
		}
		if mode == "clock" {
			now = clock.Add(-time.Hour)
		}
		before, _ := json.Marshal(w)
		force, work, preferred := int64(100), 100, 0
		w.xannorShips(sector, &force, &work, &preferred, now, func() float64 { t.Fatal("ineligible target drew randomness", mode); return 0 })
		after, _ := json.Marshal(w)
		if string(before) != string(after) || force != 100 {
			t.Fatal("ineligible ship changed", mode)
		}
	}
}

func TestXannorShipMultipleVictimsEstateAndNoWreck(t *testing.T) {
	w, p := shipWorld(t, 0, 1)
	other, _ := w.Join("other", "Other")
	other.Sector, other.Cloak, other.Fighters, other.Shields = 10, 0, 0, 0
	p.Turns, p.Credits, p.Mines, p.Missiles, p.Plasma, p.Ground = 37, 12345, 5, 7, 9, 20
	p.Cargo = [3]int64{2, 3, 4}
	w.Ports[2].Owner, w.Ports[2].Treasury = p.ID, 777
	if err := w.CreateTeam(p.ID, "Orion", "ABCD"); err != nil {
		t.Fatal(err)
	}
	if err := w.JoinTeam(other.ID, 1, "ABCD"); err != nil {
		t.Fatal(err)
	}
	w.Sectors[12].Defense = &SectorDefense{Owner: p.ID, Fighters: 37}
	planet := &Planet{Generation: uint64(2), ID: 2, Sector: 11, Owner: p.ID, Name: "Estate", Updated: clock, Ground: 500, Bank: 1234}
	w.Planets[2], w.Sectors[11].Planet = planet, 2
	force, work, preferred := int64(100), 100, 12
	w.xannorShips(10, &force, &work, &preferred, clock, func() float64 { return .5 })
	if p.Death == nil || other.Death == nil || len(p.BattleReports) != 1 || len(other.BattleReports) != 1 || p.BattleReports[0].ID >= other.BattleReports[0].ID {
		t.Fatal("record order or multiple victims")
	}
	if force != 100 || p.Shields != 0 || p.Credits != 0 || p.Mines != 0 || p.Missiles != 0 || p.Plasma != 0 || p.Ground != 0 || p.Cargo != [3]int64{} || p.Turns != 37 {
		t.Fatal("NPC retained/duplicated disposable inventory", p)
	}
	if len(w.Sectors[10].Minefield) != 0 || w.Ports[2].Owner != 0 || w.Ports[2].Treasury != 0 || w.Sectors[12].Defense.Owner != MercenaryOwner || w.Sectors[12].Defense.Fighters != 37 || planet.Owner != p.ID || planet.Bank != 1234 {
		t.Fatal("wrong estate/no-wreck rules")
	}
	if len(w.Teams) != 0 || p.Team != 0 || other.Team != 0 {
		t.Fatal("empty team retained")
	}
	if err := w.CheckShip(p.ID, 0); err == nil {
		t.Fatal("dead session accepted")
	}
	if err := w.ReplaceShip(p.ID, clock); err != nil {
		t.Fatal(err)
	}
	if p.ShipGeneration != 2 || p.Turns != 37 || len(p.BattleReports) != 1 || !p.BattleReports[0].Unread {
		t.Fatal("replacement lost private aftermath or refilled turns")
	}
	if err := w.CheckShip(p.ID, 0); err == nil {
		t.Fatal("stale session accepted")
	}
	validMobile(t, w)
}

func TestXannorShipDeathRevokesTeamAccessAndCaptain(t *testing.T) {
	w, p := shipWorld(t, 0, 0)
	mate, _ := w.Join("mate", "Mate")
	if err := w.CreateTeam(p.ID, "Orion", "ABCD"); err != nil {
		t.Fatal(err)
	}
	if err := w.JoinTeam(mate.ID, 1, "ABCD"); err != nil {
		t.Fatal(err)
	}
	force, work, preferred := int64(100), 100, 0
	w.xannorShips(10, &force, &work, &preferred, clock, func() float64 { return 0 })
	if w.Teams[1].Captain != 0 || mate.Team != 1 || p.Team != 0 {
		t.Fatal("stale captain or surviving team removed")
	}
	if _, err := w.VisitTeam(mate.ID); err != nil {
		t.Fatal(err)
	}
	if w.Teams[1].Captain != mate.ID {
		t.Fatal("captain succession failed")
	}
	validMobile(t, w)
}

func TestXannorShipsBudgetAndRouteContinuation(t *testing.T) {
	for _, win := range []bool{false, true} {
		w, p := shipWorld(t, 0, 0)
		if !win {
			p.Fighters = 500
		}
		g := mobileGroup(w, 9, 100)
		w.Sectors[11].Minefield = []MineLayer{{Owner: p.ID, Count: 1}}
		preferred := 0
		w.walkXannor(g, []int{9, 10, 11, 12}, map[*SectorDefense]bool{}, &preferred, clock, func() float64 {
			if win {
				return 0
			}
			return .99
		})
		if win {
			if p.Death == nil || len(w.Sectors[11].Minefield) != 0 {
				t.Fatal("victory failed to continue route")
			}
		} else if len(w.Sectors[11].Minefield) != 1 || p.Death != nil || preferred != 10 {
			t.Fatal("loss continued route or lost pursuit")
		}
		validMobile(t, w)
	}
	w, p := shipWorld(t, MaxQuantity, MaxQuantity)
	g := mobileGroup(w, 9, MaxQuantity)
	preferred := 0
	draws := 0
	w.walkXannor(g, []int{9, 10, 11}, map[*SectorDefense]bool{}, &preferred, clock, func() float64 { draws++; return .75 })
	if draws != xannorWorkLimit-1 || p.Death != nil || w.Sectors[9].Defense == nil || w.Sectors[10].Defense != nil || len(p.BattleReports) != 1 || w.Sectors[9].Defense.Fighters+p.BattleReports[0].XannorLost != MaxQuantity {
		t.Fatal("unfinished ship battle exceeded budget or lost force", draws)
	}
	validMobile(t, w)
	// A final partial merge must not bypass a ship sitting on friendly force.
	w, p = shipWorld(t, 0, 0)
	g = mobileGroup(w, 9, 100)
	mobileGroup(w, 10, MaxQuantity-50)
	w.walkXannor(g, []int{9, 10}, map[*SectorDefense]bool{}, &preferred, clock, func() float64 { return 0 })
	if p.Death == nil || w.Sectors[10].Defense.Fighters != MaxQuantity || w.Sectors[9].Defense.Fighters != 50 {
		t.Fatal("partial merge bypassed ship or discarded overflow")
	}
	validMobile(t, w)
}

func TestXannorBattleHistoryRetentionValidationAndPrivacy(t *testing.T) {
	w, p := shipWorld(t, 500, 0)
	other, _ := w.Join("other", "Other")
	for i := 0; i < 40; i++ {
		force, work, preferred := int64(1), 10, 0
		w.xannorShips(10, &force, &work, &preferred, clock, func() float64 { return .99 })
	}
	entries, err := w.BattleHistory(p.ID, true)
	if err != nil || len(entries) != MaxBattleReports || entries[0].ID != 9 || w.NextBattleReport != 41 {
		t.Fatal("bounded history", err)
	}
	if out, err := w.BattleHistory(other.ID, false); err != nil || len(out) != 0 {
		t.Fatal("history exposed another player")
	}
	entries[0].Unread = false
	if !p.BattleReports[0].Unread {
		t.Fatal("history aliases persistent storage")
	}
	if err := w.AcknowledgeBattleReport(other.ID, 9); err == nil {
		t.Fatal("wrong recipient acknowledged report")
	}
	if err := w.AcknowledgeBattleReport(p.ID, 9); err != nil {
		t.Fatal(err)
	}
	if !p.BattleReports[1].Unread || p.BattleReports[0].Unread {
		t.Fatal("acknowledged wrong report")
	}
	validMobile(t, w)
	for _, mode := range []string{"duplicate", "date", "sector", "count"} {
		raw, _ := json.Marshal(w)
		var corrupt World
		_ = json.Unmarshal(raw, &corrupt)
		r := &corrupt.Players[p.ID].BattleReports[1]
		switch mode {
		case "duplicate":
			r.ID = 9
		case "date":
			r.At = clock.Add(-time.Hour)
		case "sector":
			r.Sector = 7
		case "count":
			r.ShieldsLost = MaxQuantity + 1
		}
		if corrupt.Validate() == nil {
			t.Fatal("invalid private report accepted", mode)
		}
	}
	// Migration starts empty and rejects future fields instead of backfilling events.
	old := mobileWorld(t, 12)
	old.Version = 14
	old.NextPlanetGeneration = 0
	for _, planet := range old.Planets {
		planet.Generation = 0
	}
	old.Season = 0
	old.GenerationSeed = nil
	old.NextBattleReport = 0
	if err := old.Upgrade(); err != nil || old.Version != WorldVersion || old.NextBattleReport != 1 {
		t.Fatal("v14 migration", err)
	}
	if !reflect.DeepEqual(old.News, []NewsEvent(nil)) {
		t.Fatal("migration invented news")
	}
}

func TestXannorSeededShipCasualtyConservation(t *testing.T) {
	for seed := int64(0); seed < 32; seed++ {
		rng := rand.New(rand.NewSource(seed))
		fighters, shields, initial := rng.Int63n(12000), rng.Int63n(12000), rng.Int63n(20000)+1
		w, p := shipWorld(t, fighters, shields)
		force, work, preferred := initial, xannorWorkLimit, 0
		w.xannorShips(10, &force, &work, &preferred, clock, rng.Float64)
		if len(p.BattleReports) != 1 {
			t.Fatal("missing seeded encounter", seed)
		}
		r := p.BattleReports[0]
		if force < 0 || p.Fighters < 0 || p.Shields < 0 || force+r.XannorLost != initial || p.Fighters+r.FightersLost != fighters || p.Shields+r.ShieldsLost != shields || work < 0 {
			t.Fatal("seeded casualty accounting", seed, r)
		}
		if force > 0 && p.Death == nil && work > 0 {
			t.Fatal("seeded battle stopped without outcome or budget", seed)
		}
		validMobile(t, w)
	}
}

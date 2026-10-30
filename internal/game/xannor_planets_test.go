package game

import (
	"encoding/json"
	"math"
	"math/rand"
	"reflect"
	"testing"
)

func assaultWorld(t *testing.T, ground int64, rates, cargo [3]float64) (*World, *Player, *Planet) {
	t.Helper()
	w, p := shipWorld(t, 123, 456)
	p.Sector = 1
	planet := &Planet{ID: 2, Sector: 10, Owner: p.ID, Name: "New Eden", Updated: clock, Ground: ground, Production: rates, Cargo: cargo, Bank: 1234, Fighters: 37.5, Missiles: 100, Mines: 200, Plasma: 300}
	w.Planets[2], w.Sectors[10].Planet = planet, 2
	return w, p, planet
}
func TestXannorPlanetGroundVictoryNeverDamagesProductionOrShips(t *testing.T) {
	for _, roll := range []float64{0, .999999} {
		w, p, planet := assaultWorld(t, 2, [3]float64{}, [3]float64{11, 22, 33})
		force, work, preferred := int64(1), 100, 0
		if !w.xannorPlanet(10, &force, &work, &preferred, clock, func() float64 { return roll }) {
			t.Fatal("unexpected hold")
		}
		if force != 0 || planet.Ground != 1 || planet.Owner != p.ID || planet.Cargo != [3]float64{11, 22, 33} || w.Planets[2] != planet || preferred != 10 || p.Death != nil || p.Fighters != 123 || planet.Bank != 1234 || planet.Fighters != 37.5 {
			t.Fatal("defended zero-rate world lost assets", planet, p)
		}
		if p.BattleReports[0].Planet.GroundBefore != 2 || p.BattleReports[0].Planet.GroundAfter != 1 || p.BattleReports[0].XannorLost != 1 || w.News[0].Outcome != "defended" {
			t.Fatal("bad ground report")
		}
		validMobile(t, w)
	}
	// Ground exchange extremes: one troop loses 1 or 1000 attackers, never negative.
	for _, tc := range []struct {
		roll float64
		lost int64
	}{{0, 1}, {.999999, 1000}} {
		w, _, planet := assaultWorld(t, 1, [3]float64{1000, 0, 0}, [3]float64{1, 0, 0})
		force, work, preferred := int64(2000), 2, 0
		w.xannorPlanet(10, &force, &work, &preferred, clock, func() float64 { return tc.roll })
		if force != 2000-tc.lost || planet.Ground != 0 || planet.Owner != 0 || planet.Production[0] != 1000 || planet.Cargo[0] != 1 {
			t.Fatal("ground exchange or work boundary", force, planet)
		}
		validMobile(t, w)
	}
}
func TestXannorPlanetProductionDrawsThresholdsCapsAndTies(t *testing.T) {
	for _, tc := range []struct {
		force int64
		rate  float64
		batch int64
	}{{1, 501, 1}, {449, 501, 1}, {450, 500, 1}, {450, 500.001, 450}, {451, 501, 450}} {
		if xannorProductionBatch(tc.force, [3]float64{tc.rate}) != tc.batch {
			t.Fatal("force-aware batch", tc)
		}
	}
	w, p, planet := assaultWorld(t, 0, [3]float64{501, 100, 0}, [3]float64{10000, 3, 17})
	force, work, preferred := int64(450), 2, 0
	w.xannorPlanet(10, &force, &work, &preferred, clock, mobileRNG(t, 0, .9, .6, .3))
	// Independent draws for all three rates, then clamp. Stocks only fall to cap.
	if planet.Production != [3]float64{366, 10, 0} || planet.Cargo != [3]float64{3660, 3, 0} || force != 450 || planet.Owner != 0 || !p.BattleReports[0].Planet.Interrupted {
		t.Fatal("production/cargo", planet)
	}
	validMobile(t, w)
	w, p, planet = assaultWorld(t, 0, [3]float64{501}, [3]float64{10000})
	force, work = 1, 100
	w.xannorPlanet(10, &force, &work, &preferred, clock, mobileRNG(t, .5))
	if force != 0 || planet.Production[0] != 501 || planet.Cargo[0] != 5010 || p.BattleReports[0].XannorLost != 1 {
		t.Fatal("tie or small-force correction", planet)
	}
	validMobile(t, w)
}
func TestXannorPlanetDestructionInvalidatesEveryLandingAndRetainsSnapshot(t *testing.T) {
	w, p, planet := assaultWorld(t, 0, [3]float64{.1, .1, .1}, [3]float64{1, 1, 1})
	other, _ := w.Join("other", "Other")
	for _, player := range []*Player{p, other} {
		player.Sector = 10
		player.LandedPlanet = 2
		player.PlanetToken = "0123456789abcdef0123456789abcdef"
	}
	force, work, preferred := int64(9), 100, 10
	w.xannorPlanet(10, &force, &work, &preferred, clock, mobileRNG(t, 0, .9, .9, .9))
	if w.Planets[2] != nil || w.Sectors[10].Planet != 0 || force != 9 || preferred != 0 || len(w.News) != 1 || w.News[0].Outcome != "destroyed" {
		t.Fatal("logical deletion or force accounting")
	}
	for _, player := range []*Player{p, other} {
		if player.Death != nil || player.PlanetToken != "" || player.LandedPlanet != 0 {
			t.Fatal("collateral ship death or stale access")
		}
	}
	if planet.Bank != 1234 || planet.Fighters != 37.5 || p.Credits != 1005 || p.Missiles != 0 {
		t.Fatal("destroyed stocks became loot", p)
	}
	entries, _ := w.BattleHistory(p.ID, false)
	entries[0].Planet.Name = "changed"
	if p.BattleReports[0].Planet.Name != "New Eden" {
		t.Fatal("history escaped by pointer")
	}
	// Slot reuse does not make the old token or report point at a new planet.
	w.Planets[2] = &Planet{ID: 2, Sector: 10, Name: "Replacement", Updated: clock}
	w.Sectors[10].Planet = 2
	if _, _, err := w.landed(p.ID, "0123456789abcdef0123456789abcdef", clock); err == nil {
		t.Fatal("old confirmation revived")
	}
	if !p.BattleReports[0].Destroyed || p.BattleReports[0].Planet.Name != "New Eden" {
		t.Fatal("history rewritten")
	}
	validMobile(t, w)
}
func TestXannorPlanetEligibilityCurrentTitlesCapturedHomesAndUnion(t *testing.T) {
	for _, mode := range []string{"human", "neutral", "mercenary", "captured-xannoron", "neutral-xannoron", "captured-mercenary", "xannor", "union"} {
		w, p, planet := assaultWorld(t, 1, [3]float64{}, [3]float64{5, 6, 7})
		sector := 10
		switch mode {
		case "neutral":
			planet.Owner = 0
		case "mercenary":
			planet.Owner = MercenaryOwner
			planet.FactionHome = MercenaryHome
		case "captured-xannoron":
			planet.FactionHome = XannorHome
		case "neutral-xannoron":
			planet.Owner = 0
			planet.FactionHome = XannorHome
		case "captured-mercenary":
			planet.FactionHome = MercenaryHome
		case "xannor":
			planet.Owner = XannorOwner
			planet.FactionHome = XannorHome
		case "union":
			w.Sectors[10].Planet = 0
			sector = 7
			planet.Sector = 7
			w.Sectors[7].Planet = 2
		}
		force, work, preferred := int64(1), 100, 0
		draws := 0
		w.xannorPlanet(sector, &force, &work, &preferred, clock, func() float64 { draws++; return .9 })
		if mode == "xannor" || mode == "union" {
			if draws != 0 || planet.Ground != 1 || len(w.News) != 0 {
				t.Fatal("friendly/protected attack", mode)
			}
		} else if draws != 1 || force != 0 || planet.Ground != 0 || planet.Owner != 0 || planet.Cargo != [3]float64{5, 6, 7} || w.Planets[2] == nil {
			t.Fatal("current title or mutual exhaustion", mode, planet)
		}
		if mode == "human" && !p.BattleReports[0].Planet.Neutralized {
			t.Fatal("title loss unreported")
		}
		validMobile(t, w)
	}
}
func TestXannorPlanetRouteOrderFriendlyGarrisonAndSharedBudget(t *testing.T) {
	w, p, _ := assaultWorld(t, 1, [3]float64{}, [3]float64{})
	p.Sector = 10
	p.Fighters = 0
	p.Shields = 0
	group := mobileGroup(w, 9, 100)
	w.Sectors[10].Minefield = []MineLayer{{Owner: p.ID, Count: 1}}
	w.Sectors[10].Defense = &SectorDefense{Owner: p.ID, Fighters: 1}
	preferred := 0
	// mine loses 1, sector defender loses 1, ground loses 1 attacker, then unarmed ship.
	w.walkXannor(group, []int{9, 10, 11}, map[*SectorDefense]bool{}, &preferred, clock, mobileRNG(t, 0, 0, 0, 0))
	if p.Death == nil || len(p.BattleReports) != 2 || p.BattleReports[0].Planet == nil || p.BattleReports[1].Planet != nil || w.Planets[2] != nil || len(w.Sectors[10].Minefield) != 0 || w.Sectors[11].Defense.Fighters != 98 {
		t.Fatal("route order/force")
	}
	validMobile(t, w)
	// A separate friendly garrison grants no immunity to a foreign planet.
	w, _, _ = assaultWorld(t, 0, [3]float64{}, [3]float64{})
	group = mobileGroup(w, 9, 10)
	mobileGroup(w, 10, 20)
	w.walkXannor(group, []int{9, 10, 11}, map[*SectorDefense]bool{}, &preferred, clock, func() float64 { t.Fatal("empty planet needs no draws"); return 0 })
	if w.Planets[2] != nil || w.Sectors[10].Defense.Fighters != 20 || w.Sectors[11].Defense.Fighters != 10 {
		t.Fatal("friendly garrison immunity")
	}
	validMobile(t, w)
	// An indefinitely lucky production loop still stops within the route budget.
	w, p, _ = assaultWorld(t, 0, [3]float64{float64(MaxQuantity), 0, 0}, [3]float64{})
	group = mobileGroup(w, 9, MaxQuantity)
	draws := 0
	w.walkXannor(group, []int{9, 10, 11}, map[*SectorDefense]bool{}, &preferred, clock, func() float64 { draws++; return 0 })
	if draws != (xannorWorkLimit-2)*4 || w.Sectors[9].Defense.Fighters != MaxQuantity || !p.BattleReports[0].Planet.Interrupted {
		t.Fatal("unbounded production loop", draws)
	}
	validMobile(t, w)
}
func TestXannorPlanetPublicationPreflightAndFutureState(t *testing.T) {
	for _, mode := range []string{"news-sequence", "report-sequence", "news-clock", "report-clock", "work"} {
		w, p, _ := assaultWorld(t, 1, [3]float64{10}, [3]float64{100})
		force, work, preferred := int64(100), 100, 0
		switch mode {
		case "news-sequence":
			w.NextNews = math.MaxUint64
		case "report-sequence":
			w.NextBattleReport = math.MaxUint64
		case "news-clock":
			w.News = []NewsEvent{{At: clock.AddDate(0, 0, 1)}}
		case "report-clock":
			p.BattleReports = []BattleReport{{At: clock.AddDate(0, 0, 1)}}
		case "work":
			work = 0
		}
		before, _ := json.Marshal(w)
		if w.xannorPlanet(10, &force, &work, &preferred, clock, func() float64 { t.Fatal("preflight drew"); return 0 }) {
			t.Fatal("unpublishable assault continued")
		}
		after, _ := json.Marshal(w)
		if string(before) != string(after) || force != 100 {
			t.Fatal("preflight partially mutated")
		}
	}
}
func TestXannorSeededPlanetConservation(t *testing.T) {
	for seed := int64(0); seed < 32; seed++ {
		rng := rand.New(rand.NewSource(seed))
		ground := rng.Int63n(30)
		rates := [3]float64{rng.Float64() * 1000, rng.Float64() * 1000, rng.Float64() * 1000}
		cargo := [3]float64{12345, 3, 7000}
		w, p, planet := assaultWorld(t, ground, rates, cargo)
		initial := rng.Int63n(20000) + 1
		force, work, preferred := initial, xannorWorkLimit, 0
		w.xannorPlanet(10, &force, &work, &preferred, clock, rng.Float64)
		report := p.BattleReports[0]
		if force < 0 || force+report.XannorLost != initial || work < 0 || planet.Ground < 0 || planet.Ground > ground || planet.Owner == XannorOwner || planet.Bank != 1234 || planet.Fighters != 37.5 {
			t.Fatal("conservation", seed)
		}
		for i := range rates {
			if planet.Production[i] > rates[i] || planet.Cargo[i] > cargo[i] {
				t.Fatal("resources increased", seed)
			}
		}
		validMobile(t, w)
	}
}
func TestVersionFifteenPlanetBattleMigrationAndValidation(t *testing.T) {
	w, p, _ := assaultWorld(t, 0, [3]float64{}, [3]float64{})
	w.Version = 15
	w.Season = 0
	w.GenerationSeed = nil
	old, _ := json.Marshal(w)
	if err := w.Upgrade(); err != nil || w.Version != WorldVersion {
		t.Fatal("migration", err)
	}
	if len(w.News) != 0 || len(p.BattleReports) != 0 {
		t.Fatal("invented history")
	}
	force, work, preferred := int64(10), 100, 0
	w.xannorPlanet(10, &force, &work, &preferred, clock, func() float64 { return 0 })
	raw, _ := json.Marshal(w)
	for _, mode := range []string{"future-report", "future-news", "negative", "increasing", "nonfinite", "mixed", "destroyed-ground", "public-leak"} {
		var candidate World
		_ = json.Unmarshal(raw, &candidate)
		r := &candidate.Players[p.ID].BattleReports[0]
		switch mode {
		case "future-report":
			candidate.Version = 15
			candidate.Season = 0
			candidate.GenerationSeed = nil
			candidate.News = nil
		case "future-news":
			candidate.Version = 15
			candidate.Season = 0
			candidate.GenerationSeed = nil
			candidate.Players[p.ID].BattleReports = nil
		case "negative":
			r.Planet.CargoAfter[0] = -1
		case "increasing":
			r.Planet.ProductionAfter[0] = 1
		case "nonfinite":
			r.Planet.CargoAfter[0] = math.NaN()
		case "mixed":
			r.FightersLost = 1
		case "destroyed-ground":
			r.Planet.GroundAfter = 1
		case "public-leak":
			candidate.News[0].Alias = "Private owner"
		}
		if mode == "future-report" || mode == "future-news" {
			if candidate.Upgrade() == nil {
				t.Fatal("legacy future state", mode)
			}
		} else if candidate.Validate() == nil {
			t.Fatal("invalid snapshot", mode)
		}
	}
	var again World
	_ = json.Unmarshal(old, &again)
	_ = again.Upgrade()
	if !reflect.DeepEqual(again.Players[p.ID].BattleReports, []BattleReport(nil)) {
		t.Fatal("old migration reports")
	}
}

func TestXannorPlanetNeutralizationExpiresGrantWithoutDestruction(t *testing.T) {
	w, p, planet := assaultWorld(t, 1, [3]float64{0, 0, 0}, [3]float64{11, 22, 33})
	p.Sector = 10
	if err := w.Land(p.ID, clock); err != nil {
		t.Fatal(err)
	}
	token := p.PlanetToken
	force, work, preferred := int64(1), 100, 0
	w.xannorPlanet(10, &force, &work, &preferred, clock, func() float64 { return .9 })
	if planet.Owner != 0 || w.Planets[2] != planet || p.PlanetToken != "" || p.LandedPlanet != 0 || planet.Bank != 1234 || planet.Cargo != [3]float64{11, 22, 33} || p.Death != nil {
		t.Fatal("neutralization lost object/stocks or retained grant")
	}
	if err := w.Bank(p.ID, token, 0, clock); err == nil {
		t.Fatal("pending bank confirmation survived title loss")
	}
	validMobile(t, w)
}

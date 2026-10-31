package game

import (
	"encoding/json"
	"math"
	"reflect"
	"testing"
	"time"
)

func wandererWorld(t *testing.T) (*World, *Player, *Planet) {
	t.Helper()
	w, p, ordinary := mobilityWorld(t)
	w.Sectors[ordinary.Sector].Planet = 0
	delete(w.Planets, ordinary.ID)
	if _, err := w.BootstrapWanderer(clock, func() float64 { return 7.0 / 32 }); err != nil {
		t.Fatal(err)
	}
	planet := w.Planets[1]
	// Isolate transport from economic projections while retaining native identity.
	planet.Owner = p.ID
	planet.Production = [3]float64{}
	planet.Ground = 100
	return w, p, planet
}
func worldJSON(t *testing.T, w *World) []byte {
	t.Helper()
	b, e := json.Marshal(w)
	if e != nil {
		t.Fatal(e)
	}
	return b
}
func TestWandererBootstrapIdentityAndMigration(t *testing.T) {
	w, e := New(clock, 36, 32)
	if e != nil {
		t.Fatal(e)
	}
	out, e := w.BootstrapWanderer(clock, func() float64 { return 0 })
	p := w.Planets[1]
	want := &Planet{Wanderer: true, Generation: 101, ID: 1, Sector: 1, Name: "The Wanderer", Updated: clock.UTC(), Production: [3]float64{5000, 5000, 5000}, Bank: 250000}
	if e != nil || out.Status != "restored" || !reflect.DeepEqual(p, want) || w.NextPlanetGeneration != 102 {
		t.Fatal(out, e, p)
	}
	if e = w.Validate(); e != nil {
		t.Fatal(e)
	}
	before := string(worldJSON(t, w))
	if out, e = w.BootstrapWanderer(clock, func() float64 { t.Fatal("existing identity drew"); return 0 }); e != nil || out.Status != "unchanged" || string(worldJSON(t, w)) != before {
		t.Fatal(out, e)
	}
	// Destruction and restoration reuse the reserved slot, never the incarnation.
	w.destroyPlanet(p)
	if out, e = w.BootstrapWanderer(clock.Add(time.Hour), func() float64 { return 0 }); e != nil || out.Generation != 102 || w.Planets[1].Updated != clock.Add(time.Hour) {
		t.Fatal(out, e)
	}
	// Schema 24 migration does not infer identity or mint assets from a name.
	old, _, planet := mobilityWorld(t)
	planet.Name = "The Wanderer"
	old.Version = 24
	beforePlanet := *planet
	if e = old.Upgrade(); e != nil || old.Version != WorldVersion || len(old.Planets) != 1 || !reflect.DeepEqual(*planet, beforePlanet) || old.wanderer() != nil {
		t.Fatal("migration inferred identity", e)
	}
	old.Version = 24
	planet.Wanderer = true
	if old.Upgrade() == nil {
		t.Fatal("accepted future marker in legacy save")
	}
	for _, mode := range []string{"unmarked-slot", "wrong-slot", "faction-home", "duplicate"} {
		w, _, p := wandererWorld(t)
		switch mode {
		case "unmarked-slot":
			p.Wanderer = false
		case "wrong-slot":
			delete(w.Planets, 1)
			p.ID = 2
			w.Planets[2] = p
			w.Sectors[p.Sector].Planet = 2
		case "faction-home":
			p.FactionHome = MercenaryHome
		case "duplicate":
			q := *p
			q.ID = 3
			q.Generation = 103
			q.Sector = 9
			w.NextPlanetGeneration = 104
			w.Planets[3] = &q
			w.Sectors[9].Planet = 3
		}
		if w.Validate() == nil {
			t.Fatal("invalid identity accepted", mode)
		}
	}
}
func TestWandererFiniteDeferredAndInvalidDraws(t *testing.T) {
	for _, mode := range []string{"full", "slot", "allocator", "nan", "inf", "negative", "one", "nil"} {
		w, _, p := mobilityWorld(t)
		switch mode {
		case "full":
			for _, s := range w.Sectors {
				s.Planet = p.ID
			}
		case "slot":
			w.Planets[1] = p
		case "allocator":
			w.NextPlanetGeneration = math.MaxUint64
		}
		before := string(worldJSON(t, w))
		calls := 0
		rng := func() float64 {
			calls++
			switch mode {
			case "nan":
				return math.NaN()
			case "inf":
				return math.Inf(1)
			case "negative":
				return -.1
			case "one":
				return 1
			}
			t.Fatal("deferred bootstrap drew")
			return 0
		}
		if mode == "nil" {
			rng = nil
		}
		out, e := w.BootstrapWanderer(clock, rng)
		deferred := mode == "full" || mode == "slot" || mode == "allocator"
		if string(worldJSON(t, w)) != before || deferred && (e != nil || out.Status != "deferred" || calls != 0) || !deferred && e == nil {
			t.Fatal(mode, out, e, calls)
		}
	}
	// Virtually vacating the origin makes even a completely occupied universe finite.
	w, _, p := wandererWorld(t)
	for id, s := range w.Sectors {
		if id != p.Sector {
			s.Planet = 2
		}
	}
	calls := 0
	out, e := w.relocateWanderer(clock, func() float64 { calls++; return .999 })
	if e != nil || calls != 1 || out.Status != "held" || out.From != out.To {
		t.Fatal(out, e, calls)
	}
}
func TestWandererRelocationAssetsGrantsAndDailyGuard(t *testing.T) {
	for _, bank := range []int64{0, 17} {
		w, p, planet := wandererWorld(t)
		planet.Bank = bank
		planet.Cargo = [3]float64{2, 3, 4}
		planet.Fighters = 5
		planet.Missiles = 6
		planet.Mines = 7
		planet.Plasma = 8
		other, _ := w.Join("other", "Other")
		other.Sector = 8
		planet.Ground = 0
		if e := w.Land(p.ID, clock); e != nil {
			t.Fatal(e)
		}
		if e := w.Land(other.ID, clock); e != nil {
			t.Fatal(e)
		}
		gen := planet.Generation
		out, e := w.relocateWanderer(clock, func() float64 { return .999 })
		wantBank := bank
		if bank == 0 {
			wantBank = 250000
		}
		if e != nil || out.To != 32 || planet.Sector != 32 || planet.Owner != 0 || planet.Bank != wantBank || planet.Generation != gen || planet.Cargo != [3]float64{2, 3, 4} || planet.Fighters != 5 || planet.Missiles != 6 || planet.Mines != 7 || planet.Plasma != 8 || p.Sector != 8 || other.Sector != 8 || p.PlanetToken != "" || other.PlanetToken != "" || w.Sectors[8].Planet != 0 || w.Sectors[32].Planet != 1 {
			t.Fatal(out, e)
		}
		if e = w.Validate(); e != nil {
			t.Fatal(e)
		}
	}
	w, _, _ := wandererWorld(t)
	first, e := w.RunMaintenance(clock.Add(24*time.Hour), func() float64 { return 0 })
	if e != nil || !first.Ran || first.Wanderer.Generation == 0 {
		t.Fatal(first, e)
	}
	before := string(worldJSON(t, w))
	for _, now := range []time.Time{clock, clock.Add(24 * time.Hour)} {
		out, e := w.RunMaintenance(now, func() float64 { t.Fatal("repeated daily RNG"); return 0 })
		if e != nil || out.Ran || string(worldJSON(t, w)) != before {
			t.Fatal(out, e)
		}
	}
}
func TestWandererSplitTransportBudgetHazardsAndCandidates(t *testing.T) {
	for _, turns := range []int64{9, 10, 19, 20, 21} {
		w, p, planet := wandererWorld(t)
		p.Turns = turns
		if e := w.Land(p.ID, clock); e != nil {
			t.Fatal(e)
		}
		entry, e := w.PreparePlanetAction(p.ID, "thrusters", p.PlanetToken, 10, 0, clock)
		if turns < 20 {
			if e == nil {
				t.Fatal("full quote not enforced", turns)
			}
			continue
		}
		if e != nil {
			t.Fatal(e)
		}
		calls := 0
		out, e := w.CommitPlanetAction(entry, func() float64 {
			calls++
			if calls == 1 {
				return 0
			}
			return .999
		}, clock)
		if e != nil || !out.Vanished || out.Hops != 1 || out.TransportTurns != 10 || p.Turns != turns-10 || p.Sector != 9 || planet.Sector != 32 || out.PlanetSector != 32 || planet.Generation != entry.Planet.Generation || p.PlanetToken != "" || calls != 2 {
			t.Fatal(out, e, calls)
		}
		if e = w.Validate(); e != nil {
			t.Fatal(e)
		}
	}
	for _, hazard := range []string{"random-mines", "random-defense", "planned-mines", "planned-defense", "fatal-mines"} {
		w, p, planet := wandererWorld(t)
		if hazard == "random-mines" {
			w.Sectors[32].Minefield = []MineLayer{{Owner: 0, Count: 3}}
		}
		if hazard == "random-defense" {
			w.Sectors[32].Defense = &SectorDefense{Owner: MercenaryOwner, Fighters: 100}
		}
		if hazard == "planned-mines" || hazard == "fatal-mines" {
			w.Sectors[9].Minefield = []MineLayer{{Owner: 0, Count: 3}}
		}
		if hazard == "fatal-mines" {
			p.Shields = 0
			p.Fighters = 0
			p.Holds = 1
			p.Cargo = [3]int64{}
		}
		if hazard == "planned-defense" {
			enemy, _ := w.Join("enemy", "Enemy")
			w.Sectors[9].Defense = &SectorDefense{Owner: enemy.ID, Fighters: 100}
		}
		entry := mobilityEntry(t, w, p, "thrusters", 10, 0)
		calls := 0
		out, e := w.CommitPlanetAction(entry, func() float64 {
			calls++
			if calls == 2 || hazard == "fatal-mines" && calls > 2 {
				return .999
			}
			return 0
		}, clock)
		if e != nil || planet.Sector != 32 || out.Hops != 1 || !out.Vanished {
			t.Fatal(hazard, out, e)
		}
		if hazard == "planned-mines" && out.Mines.Spent != 3 || hazard == "planned-defense" && !out.HostileDefense || hazard == "fatal-mines" && p.Death == nil {
			t.Fatal(hazard, out)
		}
		if hazard == "random-mines" && len(w.Sectors[32].Minefield) != 1 || hazard == "random-defense" && w.Sectors[32].Defense.Fighters != 100 {
			t.Fatal("random location affected ship", hazard)
		}
		if e = w.Validate(); e != nil {
			t.Fatal(hazard, e)
		}
	}
	// A changed off-route planet occupancy invalidates the sealed candidate set.
	w, p, _ := wandererWorld(t)
	entry := mobilityEntry(t, w, p, "thrusters", 10, 0)
	w.Sectors[32].Planet = 2
	w.Planets[2] = &Planet{ID: 2, Generation: 2, Sector: 32, Name: "New", Updated: clock}
	if _, e := w.CommitPlanetAction(entry, func() float64 { t.Fatal("stale candidates drew"); return 0 }, clock); e == nil {
		t.Fatal("stale candidates accepted")
	}
}
func TestWandererCollisionStressAndNameIdentity(t *testing.T) {
	for _, stress := range []bool{false, true} {
		w, p, planet := wandererWorld(t)
		var target *Planet
		if !stress {
			target = &Planet{ID: 2, Generation: 2, Sector: 9, Name: "Stationary", Updated: clock}
			w.Planets[2] = target
			w.Sectors[9].Planet = 2
		}
		entry := mobilityEntry(t, w, p, "thrusters", 10, 0)
		calls := 0
		out, e := w.CommitPlanetAction(entry, func() float64 {
			calls++
			if stress && calls == 1 {
				return .999
			}
			return 0
		}, clock)
		if e != nil || !out.Destroyed || out.Vanished || out.Hops != 0 || out.TransportTurns != 0 || w.Planets[planet.ID] != nil || p.Sector != 8 || p.Turns != 500 || calls != 3 {
			t.Fatal(out, e, calls)
		}
		if !stress && (w.Planets[2] != target || target.Sector != 9) {
			t.Fatal("collision changed stationary planet")
		}
	}
	w, p, planet := mobilityWorld(t)
	planet.Name = "The Wanderer"
	out, e := w.CommitPlanetAction(mobilityEntry(t, w, p, "thrusters", 10, 0), func() float64 { return 0 }, clock)
	if e != nil || out.Vanished || out.Hops != 2 || planet.Sector != 10 {
		t.Fatal("name inferred special identity", out, e)
	}
	w, p, planet = wandererWorld(t)
	planet.Name = "An old captured name"
	out, e = w.CommitPlanetAction(mobilityEntry(t, w, p, "thrusters", 10, 0), func() float64 { return 0 }, clock)
	if e != nil || !out.Vanished || out.Hops != 1 {
		t.Fatal("identity depended on label", out, e)
	}
}

func TestWandererDailyReceiptReflectsLaterDestructionWithoutResurrection(t *testing.T) {
	w := mobileWorld(t, 12)
	p, _ := w.Join("captain", "Captain")
	p.StoredScore = 4000
	for _, home := range []struct {
		id, sector, owner int
		kind              string
	}{{99, 11, MercenaryOwner, MercenaryHome}, {100, 8, XannorOwner, XannorHome}} {
		w.Planets[home.id] = &Planet{ID: home.id, Generation: uint64(home.id), Sector: home.sector, Owner: home.owner, FactionHome: home.kind, Name: "Home", Updated: clock, Ground: 100, Bank: 1}
		w.Sectors[home.sector].Planet = home.id
	}
	if _, err := w.BootstrapWanderer(clock, func() float64 { return 0 }); err != nil {
		t.Fatal(err)
	}
	mobileGroup(w, 8, 1)
	mobileGroup(w, 9, 100)
	w.Sectors[9].Warps = []int{10}
	w.Sectors[10].Warps = []int{8}
	wanderer := w.Planets[1]
	wanderer.Production = [3]float64{}
	wanderer.Updated = clock.Add(24 * time.Hour)
	wanderer.Bank = 0
	gen := wanderer.Generation
	calls := 0
	out, err := w.RunMaintenance(clock.Add(24*time.Hour), func() float64 {
		calls++
		if calls == 10 {
			return .85
		}
		return .5
	})
	if err != nil || !out.Ran || !out.Wanderer.Destroyed || out.Wanderer.Generation != gen || out.Wanderer.To != 10 || w.Planets[1] != nil {
		t.Fatal(out, err, calls)
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
	if len(w.News) < 1 || w.News[0].Kind != NewsXannorPlanet || w.News[0].Outcome != "destroyed" {
		t.Fatal(w.News)
	}
}
func TestWandererCapturedDestructionRetainsPrivateHistory(t *testing.T) {
	w, p, planet := wandererWorld(t)
	planet.Ground = 0
	planet.Production = [3]float64{}
	force, work, preferred := int64(10), 100, 0
	w.xannorPlanet(8, &force, &work, &preferred, clock, func() float64 { return 0 })
	if w.Planets[1] != nil || len(p.BattleReports) != 1 || p.BattleReports[0].Planet.ID != 1 || !p.BattleReports[0].Destroyed {
		t.Fatal("missing private captured-Wanderer destruction report")
	}
	if err := w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestWandererAndNinetyNineOrdinaryPlanetsShareCapacity(t *testing.T) {
	w, err := New(clock, 36, 128)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = w.BootstrapWanderer(clock, func() float64 { return 0 }); err != nil {
		t.Fatal(err)
	}
	p, _ := w.Join("builder", "Builder")
	for id := 2; id <= 100; id++ {
		p.Sector = id
		p.Credits = 25000
		if err = w.CreatePlanet(p.ID, "Ordinary", clock); err != nil {
			t.Fatal(id, err)
		}
	}
	if len(w.Planets) != 100 {
		t.Fatal(len(w.Planets))
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
	p.Sector = 101
	p.Credits = 25000
	before := string(worldJSON(t, w))
	if err = w.CreatePlanet(p.ID, "Overflow", clock); err == nil || string(worldJSON(t, w)) != before {
		t.Fatal("ordinary creation consumed reserved capacity", err)
	}
	w.destroyPlanet(w.Planets[1])
	out, err := w.BootstrapWanderer(clock, func() float64 { return 0 })
	if err != nil || out.Status != "restored" || len(w.Planets) != 100 || out.Generation <= 200 {
		t.Fatal("Wanderer restoration overwrote ordinary slots", out, err)
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
}

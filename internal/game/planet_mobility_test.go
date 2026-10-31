package game

import (
	"math"
	"math/rand"
	"reflect"
	"testing"
	"time"
)

func mobilityWorld(t *testing.T) (*World, *Player, *Planet) {
	t.Helper()
	w, err := New(clock, 36, 32)
	if err != nil {
		t.Fatal(err)
	}
	p, _ := w.Join("mover", "Mover")
	p.Sector = 8
	p.Credits = 100000
	p.Ground = 1000
	p.Fighters = 10000
	p.Shields = 1000000
	if err = w.CreatePlanet(p.ID, "Mobile", clock); err != nil {
		t.Fatal(err)
	}
	planet := w.Planets[w.Sectors[8].Planet]
	planet.Ground = 100
	planet.Production = [3]float64{}
	planet.Cargo = [3]float64{}
	planet.Bank = 0
	for id, s := range w.Sectors {
		s.Warps = []int{(id % 32) + 1}
	}
	return w, p, planet
}
func mobilityEntry(t *testing.T, w *World, p *Player, kind string, to int, q int64) PlanetIntent {
	t.Helper()
	token := ""
	if kind == "thrusters" {
		if err := w.Land(p.ID, clock); err != nil {
			t.Fatal(err)
		}
		token = p.PlanetToken
	}
	e, err := w.PreparePlanetAction(p.ID, kind, token, to, q, clock)
	if err != nil {
		t.Fatal(err)
	}
	return e
}
func TestThrusterTurnBoundariesAndGrantRevocation(t *testing.T) {
	for _, turns := range []int64{9, 10, 19, 20, 21} {
		w, p, planet := mobilityWorld(t)
		p.Turns = turns
		if err := w.Land(p.ID, clock); err != nil {
			t.Fatal(err)
		}
		e, err := w.PreparePlanetAction(p.ID, "thrusters", p.PlanetToken, 10, 0, clock)
		if turns < 20 {
			if err == nil {
				t.Fatal("unaffordable path")
			}
			continue
		}
		if err != nil {
			t.Fatal(err)
		}
		other, _ := w.Join("observer", "Observer")
		other.Sector = 8
		planet.Ground = 0
		// Permission changed materially, so prepare again before the second landing.
		e = mobilityEntry(t, w, p, "thrusters", 10, 0)
		_ = w.Land(other.ID, clock)
		out, err := w.CommitPlanetAction(e, func() float64 { return 0 }, clock)
		if err != nil || out.Hops != 2 || p.Turns != turns-20 || planet.Sector != 10 || p.Sector != 10 || other.Sector != 8 || other.PlanetToken != "" || p.PlanetToken != "" {
			t.Fatal(out, err, p, other)
		}
		if err = w.Validate(); err != nil {
			t.Fatal(err)
		}
	}
	w, p, _ := mobilityWorld(t)
	p.Turns = 10
	e := mobilityEntry(t, w, p, "thrusters", 9, 0)
	if _, err := w.CommitPlanetAction(e, func() float64 { return 0 }, clock); err != nil || p.Turns != 0 {
		t.Fatal(err, p.Turns)
	}
}
func TestThrusterCollisionStressAndDefenses(t *testing.T) {
	for _, collision := range []int{9, 10, 0} {
		for _, fighters := range []int64{0, 1, 10000} {
			w, p, planet := mobilityWorld(t)
			p.Fighters = fighters
			var target *Planet
			if collision > 0 {
				p.Sector = collision
				_ = w.CreatePlanet(p.ID, "Other", clock)
				target = w.Planets[w.Sectors[collision].Planet]
				p.Sector = 8
			}
			var saved Planet
			if target != nil {
				saved = *target
			}
			e := mobilityEntry(t, w, p, "thrusters", 10, 0)
			rng := func() float64 {
				if collision == 0 {
					return .999
				}
				return 0
			}
			out, err := w.CommitPlanetAction(e, rng, clock)
			hops := 0
			if collision == 10 {
				hops = 1
			}
			if err != nil || !out.Destroyed || out.Hops != hops || p.Sector != 8+hops || p.Turns != 500-int64(hops*10) || w.Planets[planet.ID] != nil || p.Death != nil || p.Shields != 1000000 {
				t.Fatal(out, err, p)
			}
			if fighters == 0 && out.FightersLost != 0 || fighters > 0 && (out.FightersLost < 1 || out.FightersLost > fighters) {
				t.Fatal(out)
			}
			if target != nil && !reflect.DeepEqual(*target, saved) {
				t.Fatal("collision changed stationary planet")
			}
			if err = w.Validate(); err != nil {
				t.Fatal(err)
			}
		}
	}
	for _, hazard := range []string{"mines", "hostile", "own"} {
		w, p, planet := mobilityWorld(t)
		if hazard == "mines" {
			w.Sectors[9].Minefield = []MineLayer{{Owner: 0, Count: 3}}
		} else {
			owner := p.ID
			if hazard == "hostile" {
				enemy, _ := w.Join("enemy", "Enemy")
				owner = enemy.ID
			}
			w.Sectors[9].Defense = &SectorDefense{Owner: owner, Fighters: 100}
		}
		e := mobilityEntry(t, w, p, "thrusters", 10, 0)
		out, err := w.CommitPlanetAction(e, func() float64 { return 0 }, clock)
		want := 9
		if hazard == "own" {
			want = 10
		}
		if err != nil || planet.Sector != want || p.Sector != want {
			t.Fatal(out, err)
		}
		if hazard == "mines" && (out.Mines.Spent != 3 || len(w.Sectors[9].Minefield) != 0) {
			t.Fatal(out)
		}
		if hazard == "hostile" && !out.HostileDefense {
			t.Fatal(out)
		}
		if err = w.Validate(); err != nil {
			t.Fatal(err)
		}
	}
}
func TestGroundAssaultConservationAdoptionAndWorkLimit(t *testing.T) {
	for _, mode := range []string{"capture", "defeat", "unfinished", "adoption"} {
		w, p, planet := mobilityWorld(t)
		enemy, _ := w.Join("enemy", "Enemy")
		planet.Owner = enemy.ID
		planet.Ground = 10
		q := int64(100)
		if mode == "adoption" {
			planet.Owner = 0
			q = 0
		}
		if mode == "defeat" {
			planet.Ground = 10000
		}
		e := mobilityEntry(t, w, p, "assault", 0, q)
		before := *p
		bank := planet.Bank
		calls := 0
		rng := func() float64 {
			calls++
			if mode == "unfinished" {
				if calls%2 == 1 {
					return .5
				}
				return 0
			}
			if mode == "defeat" {
				return .9
			}
			if calls%2 == 1 {
				return 0
			}
			return .9
		}
		out, err := w.CommitPlanetAction(e, rng, clock)
		if err != nil || p.Ground != before.Ground-q || p.Fighters != before.Fighters || p.Shields != before.Shields || p.Turns != before.Turns || planet.Bank != bank {
			t.Fatal(out, err, p)
		}
		if mode == "capture" && (!out.Captured || planet.Owner != p.ID || planet.Ground != q || out.AttackersLost != 0 || out.DefendersLost != 10) {
			t.Fatal(out)
		}
		if mode == "defeat" && (out.Captured || planet.Owner != enemy.ID || out.AttackersLost != q) {
			t.Fatal(out)
		}
		if mode == "unfinished" && (!out.Interrupted || out.Rounds != MaxGroundRounds || calls != 2*MaxGroundRounds || out.Retreated != q || planet.Owner != enemy.ID) {
			t.Fatal(out, calls)
		}
		if mode == "adoption" && (!out.Adopted || out.Committed != 0 || planet.Owner != p.ID) {
			t.Fatal(out)
		}
		if len(w.News) != 1 || w.News[0].Kind != NewsPlayerPlanet || w.News[0].Alias != "Mover" {
			t.Fatal(w.News)
		}
		if err = w.Validate(); err != nil {
			t.Fatal(err)
		}
	}
}
func TestPlanetWarningsRejectChangedStateBeforeRandom(t *testing.T) {
	for _, mode := range []string{"owner", "team", "ship", "route", "mines", "replacement", "deadline", "ground"} {
		w, p, planet := mobilityWorld(t)
		e := mobilityEntry(t, w, p, "thrusters", 10, 0)
		at := clock
		switch mode {
		case "owner":
			enemy, _ := w.Join("enemy", "Enemy")
			planet.Owner = enemy.ID
		case "team":
			p.Team = 1
		case "ship":
			p.Ground++
		case "route":
			w.Sectors[9].Warps = []int{11}
		case "mines":
			w.Sectors[9].Minefield = []MineLayer{{Owner: 0, Count: 1}}
		case "replacement":
			w.destroyPlanet(planet)
			_ = w.CreatePlanet(p.ID, planet.Name, clock)
			p.PlanetToken = e.Ship.PlanetToken
			p.LandedPlanet = planet.ID
		case "deadline":
			at = clock.Add(PlanetActionLifetime)
		case "ground":
			planet.Ground++
		}
		if _, err := w.CommitPlanetAction(e, func() float64 { t.Fatal("stale action drew RNG", mode); return 0 }, at); err == nil {
			t.Fatal("stale intent accepted", mode)
		}
	}
}
func TestPlanetAllocatorMigrationAndFactionRestriction(t *testing.T) {
	w, p, planet := mobilityWorld(t)
	w.Version = 23
	w.NextPlanetGeneration = 0
	planet.Generation = 0
	if err := w.Upgrade(); err != nil || w.Version != WorldVersion || planet.Generation != uint64(planet.ID) || w.NextPlanetGeneration != 101 {
		t.Fatal(err, planet)
	}
	old := planet.Generation
	w.destroyPlanet(planet)
	if err := w.CreatePlanet(p.ID, "Replacement", clock); err != nil {
		t.Fatal(err)
	}
	planet = w.Planets[w.Sectors[p.Sector].Planet]
	if planet.Generation == old {
		t.Fatal("planet identity reused")
	}
	w.NextPlanetGeneration = math.MaxUint64
	w.destroyPlanet(planet)
	if w.CreatePlanet(p.ID, "Exhausted", clock) == nil {
		t.Fatal("exhausted allocator")
	}
	for _, home := range []string{MercenaryHome, XannorHome} {
		w, p, planet = mobilityWorld(t)
		planet.FactionHome = home
		_ = w.Land(p.ID, clock)
		if _, err := w.PreparePlanetAction(p.ID, "thrusters", p.PlanetToken, 9, 0, clock); err == nil {
			t.Fatal("moved captured home")
		}
	}
}

func TestGroundSeededConservationAndLazyProjection(t *testing.T) {
	for seed := int64(0); seed < 32; seed++ {
		w, p, planet := mobilityWorld(t)
		enemy, _ := w.Join("enemy", "Enemy")
		planet.Owner = enemy.ID
		planet.Ground = 100
		e := mobilityEntry(t, w, p, "assault", 0, 500)
		rng := rand.New(rand.NewSource(seed))
		out, err := w.CommitPlanetAction(e, rng.Float64, clock)
		if err != nil || p.Ground != 500 {
			t.Fatal(seed, out, err)
		}
		survivors := out.Retreated
		if out.Captured {
			survivors = out.Garrison
		}
		if out.AttackersLost+survivors != 500 || out.DefendersLost > 100 {
			t.Fatal("forces not conserved", seed, out)
		}
		if err = w.Validate(); err != nil {
			t.Fatal(seed, err)
		}
	}
	w, p, planet := mobilityWorld(t)
	enemy, _ := w.Join("enemy", "Enemy")
	planet.Owner = enemy.ID
	planet.Bank = 1000
	planet.Updated = clock.Add(-time.Hour)
	planet.Production = [3]float64{10, 20, 30}
	e := mobilityEntry(t, w, p, "assault", 0, 1000)
	if !planet.Updated.Equal(clock.Add(-time.Hour)) {
		t.Fatal("quote saved projection")
	}
	calls := 0
	out, err := w.CommitPlanetAction(e, func() float64 {
		calls++
		if calls%2 == 1 {
			return 0
		}
		return .99
	}, clock.Add(time.Second))
	if err != nil || !out.Captured || planet.Bank < 1000 || planet.Production[0] <= 10 {
		t.Fatal(out, err, planet)
	}
}
func TestGroundRejectsReplacementEpochAndNewAdoption(t *testing.T) {
	for _, mode := range []string{"replacement", "season", "owner-death", "growth"} {
		w, p, planet := mobilityWorld(t)
		enemy, _ := w.Join("enemy", "Enemy")
		planet.Owner = enemy.ID
		e := mobilityEntry(t, w, p, "assault", 0, 100)
		at := clock
		switch mode {
		case "replacement":
			replacement := *planet
			w.destroyPlanet(planet)
			replacement.Generation, _ = w.allocatePlanetGeneration()
			w.Planets[replacement.ID] = &replacement
			w.Sectors[replacement.Sector].Planet = replacement.ID
		case "season":
			w.Season++
		case "owner-death":
			enemy.Death = &Death{}
		case "growth":
			planet.Bank = 1000000000 // Prepare again with the actual persisted bank.
			e = mobilityEntry(t, w, p, "assault", 0, 100)
			at = clock.Add(time.Minute)
		}
		if _, err := w.CommitPlanetAction(e, func() float64 { t.Fatal("stale attack RNG", mode); return 0 }, at); err == nil {
			t.Fatal("stale assault", mode)
		}
	}
}

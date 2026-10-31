package game

import (
	"encoding/json"
	"math"
	"os"
	"reflect"
	"testing"
)

func missileWorld(t *testing.T) (*World, *Player, *Player, *Visibility) {
	t.Helper()
	w, a := setup(t)
	a.Missiles = 10
	a.Sector = 1
	d, err := w.Join("defender", "Defender")
	if err != nil {
		t.Fatal(err)
	}
	d.Sector = 2
	d.Cloak = 0
	d.Fighters, d.Shields = 100000, 100000
	d.Missiles = 0
	w.Sectors[1].Warps = []int{2}
	w.Sectors[2].Warps = []int{1, 3}
	v, _ := w.NewVisibility(a.ID)
	return w, a, d, v
}

func TestMissileKillDropsOnlyUnsampledMinesAndClearsWithRemainingShots(t *testing.T) {
	w, a, d, v := missileWorld(t)
	d.Fighters, d.Shields = 1, 1
	d.Mines = 100
	d.Missiles = 100
	w.Ports[2].Owner = d.ID
	w.Ports[2].Treasury = 777
	intent, err := w.PrepareMissile(a.ID, 2, 3, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return .5 }, clock)
	if err != nil {
		t.Fatal(err)
	}
	if !out.Primary.Destroyed || out.Primary.Damage.Spent != 1 || out.Primary.MinesDestroyed != 2 || out.Counter.Launched != 0 {
		t.Fatal(out)
	}
	if d.Death.Cause != "missile" || d.Death.Killer != a.ID || a.Missiles != 57 || d.Missiles != 50 || a.Turns != 499 || d.Mines != 0 || a.Mines != 50 {
		t.Fatal(a, d)
	}
	field := w.Sectors[2].Minefield
	if len(field) != 1 || field[0].Owner != d.ID || field[0].Count != 48 {
		t.Fatal(field)
	}
	if w.Ports[2].Owner != a.ID || w.Ports[2].Treasury != 777 {
		t.Fatal("missile estate lost")
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
	if _, err = w.CommitMissile(intent, v, func() float64 { t.Fatal("replayed launch RNG"); return 0 }, clock); err == nil {
		t.Fatal("replayed launch")
	}
}

func TestRetaliationHitsCloakAndPreservesActualKiller(t *testing.T) {
	w, a, d, v := missileWorld(t)
	a.StoredScore = 500000
	a.Fighters, a.Shields = 0, 0
	a.Mines = 100
	a.Turns = 37
	d.Fighters, d.Shields = MaxQuantity, MaxQuantity
	d.Missiles = 6
	w.Ports[2].Owner = a.ID
	w.Ports[2].Treasury = 777
	intent, err := w.PrepareMissile(a.ID, 2, 1, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return .99 }, clock)
	if err != nil {
		t.Fatal(err)
	}
	if out.Primary.Destroyed || out.Counter.Launched != 6 || !out.Counter.Destroyed || a.Death.Cause != "retaliation" || a.Death.Killer != d.ID {
		t.Fatal(out, a.Death)
	}
	if a.Turns != 36 || d.Turns != 500 || a.Mines != 0 || out.Counter.Disarmed != 2 || len(w.Sectors[1].Minefield) != 0 {
		t.Fatal(out, a, d)
	}
	if w.Ports[2].Owner != d.ID || w.Ports[2].Treasury != 777 {
		t.Fatal("counter estate")
	}
	if err = w.ReplaceShip(a.ID, clock); err != nil {
		t.Fatal("false suicide cooldown", err)
	}
	if a.Turns != 36 || a.StoredScore != 500000 {
		t.Fatal("replacement changed budget/score cache")
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestMissileMineInterceptionPreventsUnhitEnemyCounterfire(t *testing.T) {
	w, a, d, v := missileWorld(t)
	d.Missiles = 100
	w.Sectors[2].Minefield = []MineLayer{{Owner: d.ID, Count: 10}}
	intent, err := w.PrepareMissile(a.ID, 2, 5, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { t.Fatal("intercepted volley consumed RNG"); return 0 }, clock)
	if err != nil || out.Primary.MinesDestroyed != 5 || out.Counter.Launched != 0 || a.Missiles != 5 || d.Missiles != 100 || d.Fighters != 100000 {
		t.Fatal(out, err)
	}
}

func TestMissileConfirmationRevalidatesBeforeRandomness(t *testing.T) {
	for _, change := range []string{"actor moves", "target moves", "target replaced", "actor replaced", "team changes", "cloak changes", "mines change", "ammo spent", "turns spent", "planet arrives", "fighter defense arrives"} {
		t.Run(change, func(t *testing.T) {
			w, a, d, v := missileWorld(t)
			intent, err := w.PrepareMissile(a.ID, 2, 1, v)
			if err != nil {
				t.Fatal(err)
			}
			switch change {
			case "actor moves":
				a.Sector = 3
			case "target moves":
				d.Sector = 3
			case "target replaced":
				d.ShipGeneration++
			case "actor replaced":
				a.ShipGeneration++
			case "team changes":
				a.Team, d.Team = 1, 1
			case "cloak changes":
				d.Cloak = 1
			case "mines change":
				w.Sectors[2].Minefield = []MineLayer{{Owner: 0, Count: 1}}
			case "ammo spent":
				a.Missiles = 0
			case "turns spent":
				a.Turns = 0
			case "planet arrives":
				w.Sectors[2].Planet = 2
			case "fighter defense arrives":
				w.Sectors[2].Defense = &SectorDefense{Owner: d.ID, Fighters: 1}
			}
			before, _ := json.Marshal(w)
			_, err = w.CommitMissile(intent, v, func() float64 { t.Fatal("stale launch RNG"); return 0 }, clock)
			after, _ := json.Marshal(w)
			if err == nil || string(before) != string(after) {
				t.Fatal("stale launch changed state", err)
			}
		})
	}
}

func TestRetaliationVolleyBoundaries(t *testing.T) {
	for _, c := range []struct {
		score, stock int64
		r            float64
		want         int64
	}{{500000, 100, 0, 6}, {1, 100, 0, 1}, {0, 100, .5, 51}, {-1, 100, 0, 1}, {1000000, 3, .5, 2}, {MaxMoney, MaxQuantity, math.Nextafter(1, 0), MaxQuantity}, {1, 0, 0, 0}} {
		n, err := RetaliationVolley(c.score, c.stock, func() float64 { return c.r })
		if err != nil || n != c.want {
			t.Fatal(c, n, err)
		}
	}
	if _, err := RetaliationVolley(0, 1, func() float64 { return math.NaN() }); err == nil {
		t.Fatal("invalid counter RNG")
	}
}

func TestMissileCalculationErrorsAndBounds(t *testing.T) {
	for _, r := range []float64{math.NaN(), math.Inf(1), -1, 1} {
		if _, err := ResolveMissileShip(1, 1, 1, func() float64 { return r }); err == nil {
			t.Fatal("bad RNG", r)
		}
	}
	budget := 2
	if _, err := resolveMissileShip(100, 100, 100, func() float64 { return 0 }, &budget); err == nil {
		t.Fatal("calculation cap")
	}
}

func TestMissileDamageModel(t *testing.T) {
	var cases []struct {
		Name                        string
		Missiles, Fighters, Shields int64
		Draws                       []float64
		Expected                    MissileDamage
	}
	data, err := os.ReadFile("testdata/missile-model.json")
	if err != nil {
		t.Fatal(err)
	}
	if err = json.Unmarshal(data, &cases); err != nil {
		t.Fatal(err)
	}
	for _, c := range cases {
		t.Run(c.Name, func(t *testing.T) {
			i := 0
			out, err := ResolveMissileShip(c.Missiles, c.Fighters, c.Shields, func() float64 { r := c.Draws[i%len(c.Draws)]; i++; return r })
			if err != nil || !reflect.DeepEqual(out, c.Expected) {
				t.Fatal(out, c.Expected, err)
			}
		})
	}
}

func TestUnsupportedMissileEncountersAreRejectedWithoutSpending(t *testing.T) {
	for _, mode := range []string{"same sector", "unreachable route", "no target", "own planet", "no turns", "no stock"} {
		t.Run(mode, func(t *testing.T) {
			w, a, _, v := missileWorld(t)
			to := 2
			switch mode {
			case "same sector":
				to = 1
			case "unreachable route":
				to = 3
				w.Sectors[2].Warps = []int{1}
			case "no target":
				w.Players[2].Sector = 3
			case "own planet":
				w.Sectors[2].Planet = 2
				w.Planets[2] = &Planet{Generation: uint64(2), ID: 2, Sector: 2, Owner: a.ID, Updated: clock, Name: "Home", Ground: 100}
			case "no turns":
				a.Turns = 0
			case "no stock":
				a.Missiles = 0
			}
			before, _ := json.Marshal(w)
			if _, err := w.PrepareMissile(a.ID, to, 1, v); err == nil {
				t.Fatal("unsupported launch")
			}
			after, _ := json.Marshal(w)
			if string(before) != string(after) {
				t.Fatal("preparation mutated state")
			}
		})
	}
}

func routeTwoHop(w *World, target *Player, returnVia int) {
	w.Sectors[1].Warps = []int{2}
	w.Sectors[2].Warps = []int{3}
	w.Sectors[3].Warps = nil
	if returnVia != 0 {
		w.Sectors[3].Warps = []int{returnVia}
		w.Sectors[returnVia].Warps = []int{1}
	}
	target.Sector = 3
}

func TestMissileFollowsLongerDirectedRouteAndIntermediateMines(t *testing.T) {
	w, a, d, v := missileWorld(t)
	routeTwoHop(w, d, 0)
	d.Fighters, d.Shields, d.Missiles = MaxQuantity, MaxQuantity, 10
	w.Sectors[2].Minefield = []MineLayer{{Owner: d.ID, Count: 1}}
	intent, err := w.PrepareMissile(a.ID, 3, 2, v)
	if err != nil || !reflect.DeepEqual(intent.Route, []int{1, 2, 3}) {
		t.Fatal(intent.Route, err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return .5 }, clock)
	if err != nil || out.Primary.MinesDestroyed != 1 || out.Primary.Damage.Spent != 1 || out.Counter.Launched != 0 {
		t.Fatal(out, err)
	}
	if d.Fighters == MaxQuantity || a.Missiles != 8 || a.Turns != 499 {
		t.Fatal("routed attack did not apply atomically", a, d)
	}
}

func TestRoutedMissileCanDestroyTargetWithoutReturnRoute(t *testing.T) {
	w, a, d, v := missileWorld(t)
	routeTwoHop(w, d, 0)
	d.Sector = 3
	d.Fighters, d.Shields, d.Missiles = 1, 1, 10
	intent, err := w.PrepareMissile(a.ID, 3, 1, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return .99 }, clock)
	if err != nil || !out.Primary.Destroyed || d.Death == nil || d.Death.Cause != "missile" || out.Counter.Launched != 0 {
		t.Fatal(out, d, err)
	}
}

func TestRoutedMissileConfirmationRechecksIntermediateHazards(t *testing.T) {
	w, a, d, v := missileWorld(t)
	routeTwoHop(w, d, 0)
	intent, err := w.PrepareMissile(a.ID, 3, 1, v)
	if err != nil {
		t.Fatal(err)
	}
	w.Sectors[2].Minefield = []MineLayer{{Owner: d.ID, Count: 4}}
	before, _ := json.Marshal(w)
	if _, err = w.CommitMissile(intent, v, func() float64 { t.Fatal("stale route sampled RNG"); return 0 }, clock); err == nil {
		t.Fatal("changed intermediate hazard accepted")
	}
	after, _ := json.Marshal(w)
	if string(before) != string(after) {
		t.Fatal("stale route changed world")
	}
}

func TestMissileRouteInterceptsIntermediateFighters(t *testing.T) {
	w, a, d, v := missileWorld(t)
	routeTwoHop(w, d, 0)
	d.Fighters, d.Shields = MaxQuantity, MaxQuantity
	w.Sectors[2].Defense = &SectorDefense{Owner: d.ID, Fighters: 5_000}
	intent, err := w.PrepareMissile(a.ID, 3, 3, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return .5 }, clock)
	if err != nil || out.Primary.SectorMissiles != 2 || out.Primary.SectorFightersDestroyed != 5_000 || out.Primary.Damage.Spent != 1 {
		t.Fatal(out, err)
	}
}

func TestMissileCourseUsesShortestRouteAndStoredWarpOrderForTies(t *testing.T) {
	w, a, d, v := missileWorld(t)
	d.Sector = 4
	w.Sectors[1].Warps = []int{2, 3}
	w.Sectors[2].Warps = []int{4}
	w.Sectors[3].Warps = []int{4}
	w.Sectors[4].Warps = []int{2, 3}
	w.Sectors[2].Minefield = []MineLayer{{Owner: d.ID, Count: 1}}
	intent, err := w.PrepareMissile(a.ID, 4, 2, v)
	if err != nil || !reflect.DeepEqual(intent.Route, []int{1, 2, 4}) {
		t.Fatal(intent.Route, err)
	}
}

func TestMissileIntermediatePlanetPrecedesFartherShip(t *testing.T) {
	w, a, d, v := missileWorld(t)
	routeTwoHop(w, d, 0)
	d.Fighters, d.Shields = MaxQuantity, MaxQuantity
	planet := &Planet{Generation: uint64(2), ID: 2, Sector: 2, Owner: d.ID, Name: "Waystation", Updated: clock, Production: [3]float64{1_000_000, 1_000_000, 1_000_000}}
	w.Planets[planet.ID] = planet
	w.Sectors[2].Planet = planet.ID
	intent, err := w.PrepareMissile(a.ID, 3, 2, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return .99 }, clock)
	if err != nil || len(out.Primary.PlanetImpacts) != 1 || out.Primary.PlanetImpacts[0].Sector != 2 || out.Primary.Damage.Spent != 0 {
		t.Fatal(out, err)
	}
	if d.Fighters != MaxQuantity || d.Shields != MaxQuantity || out.Primary.PlanetMissiles != 2 {
		t.Fatal("farther ship was reached through an intact planet", out, d)
	}
}

func TestMissileContinuesFromDestroyedShipToSecondShipAndPlanet(t *testing.T) {
	t.Run("second ship", func(t *testing.T) {
		w, a, first, v := missileWorld(t)
		first.Fighters, first.Shields = 1, 1
		second, _ := w.Join("second", "Second")
		second.Sector, second.Cloak = 2, 0
		second.Fighters, second.Shields = MaxQuantity, MaxQuantity
		intent, err := w.PrepareMissile(a.ID, 2, 2, v)
		if err != nil {
			t.Fatal(err)
		}
		out, err := w.CommitMissile(intent, v, func() float64 { return .999 }, clock)
		if err != nil || len(out.Primary.ShipImpacts) != 2 || !out.Primary.ShipImpacts[0].Destroyed || out.Primary.ShipImpacts[1].Player != second.ID || out.Primary.ShipImpacts[1].Damage.Spent != 1 {
			t.Fatal(out, err)
		}
		if second.Fighters == MaxQuantity || out.Primary.Target != second.ID {
			t.Fatal("remaining missile did not continue to the next ship", second, out.Primary)
		}
	})
	t.Run("planet", func(t *testing.T) {
		w, a, first, v := missileWorld(t)
		first.Fighters, first.Shields = 1, 1
		planet := &Planet{Generation: uint64(2), ID: 2, Sector: 2, Owner: first.ID, Name: "Target", Updated: clock, Production: [3]float64{1_000_000, 1_000_000, 1_000_000}}
		w.Planets[planet.ID] = planet
		w.Sectors[2].Planet = planet.ID
		intent, err := w.PrepareMissile(a.ID, 2, 2, v)
		if err != nil {
			t.Fatal(err)
		}
		out, err := w.CommitMissile(intent, v, func() float64 { return .999 }, clock)
		if err != nil || len(out.Primary.ShipImpacts) != 1 || !out.Primary.ShipImpacts[0].Destroyed || len(out.Primary.PlanetImpacts) != 1 || out.Primary.PlanetImpacts[0].Missiles != 1 {
			t.Fatal(out, err)
		}
	})
}

func TestMissileUsesPreflightedReturnRouteInterception(t *testing.T) {
	w, a, d, v := missileWorld(t)
	w.Sectors[1].Warps = []int{2}
	w.Sectors[2].Warps = []int{3}
	w.Sectors[3].Warps = []int{4}
	w.Sectors[4].Warps = []int{1}
	d.Sector, d.Fighters, d.Shields, d.Missiles = 3, MaxQuantity, MaxQuantity, 1
	a.Fighters, a.Shields = MaxQuantity, MaxQuantity
	w.Sectors[4].Minefield = []MineLayer{{Owner: d.ID, Count: 1}}
	intent, err := w.PrepareMissile(a.ID, 3, 1, v)
	if err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(intent.Route, []int{1, 2, 3}) || !reflect.DeepEqual(intent.Sectors[1].Ships[0].ReturnRoute, []int{3, 4, 1}) {
		t.Fatal("unexpected preflighted routes", intent)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return .99 }, clock)
	if err != nil || out.Counter.Launched != 1 || out.Counter.MinesDestroyed != 1 || out.Counter.Damage.Spent != 0 || a.Fighters != MaxQuantity {
		t.Fatal(out, err)
	}
}

func TestSurvivingMissileExchangeDoesNotRecurse(t *testing.T) {
	w, a, d, v := missileWorld(t)
	d.Shields = 100
	a.Shields = 100
	d.Missiles = 1
	a.StoredScore = 0
	intent, err := w.PrepareMissile(a.ID, 2, 1, v)
	if err != nil {
		t.Fatal(err)
	}
	draws := 0
	out, err := w.CommitMissile(intent, v, func() float64 { draws++; return 0 }, clock)
	if err != nil || out.Primary.Destroyed || out.Counter.Destroyed || out.Counter.Launched != 1 || a.Death != nil || d.Death != nil || a.Missiles != 9 || d.Missiles != 0 || draws != 7 {
		t.Fatal(out, a, d, draws, err)
	}
}

func TestRetaliationOverrideDoesNotRevealOrHitOtherCloakedShips(t *testing.T) {
	w, a, d, v := missileWorld(t)
	d.Missiles = 1
	a.StoredScore = 1
	hidden, _ := w.Join("hidden", "Hidden")
	hidden.Sector = 1
	hidden.Fighters, hidden.Shields = 100, 100
	hidden.Cloak = 1
	intent, err := w.PrepareMissile(a.ID, 2, 1, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return .5 }, clock)
	if err != nil || !out.Counter.Destroyed || hidden.Fighters != 100 || hidden.Shields != 100 || hidden.Cloak != 1 {
		t.Fatal(out, hidden, err)
	}
}

func TestAutomaticRetaliationDoesNotNeedDefendersTurns(t *testing.T) {
	w, a, d, v := missileWorld(t)
	a.Turns = 1
	a.StoredScore = 1
	d.Turns = 0
	d.Missiles = 1
	intent, err := w.PrepareMissile(a.ID, 2, 1, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return 0 }, clock)
	if err != nil || out.Counter.Launched != 1 || a.Turns != 0 || d.Turns != 0 || a.Cloak != .99 {
		t.Fatal(out, a, d, err)
	}
}

func TestShieldExhaustionDestroysShipEvenWithEscortsRemaining(t *testing.T) {
	w, a, d, v := missileWorld(t)
	d.Shields = 0
	d.Missiles = 1
	intent, err := w.PrepareMissile(a.ID, 2, 1, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return 0 }, clock)
	if err != nil || !out.Primary.Destroyed || out.Primary.LostEscorts != 100000 || out.Primary.Damage.Fighters != 0 || d.Fighters != 0 || out.Counter.Launched != 0 {
		t.Fatal(out, d, err)
	}
	if err = w.Validate(); err != nil {
		t.Fatal(err)
	}
}

func TestRetaliationUsesOriginalAttackersStoredScore(t *testing.T) {
	w, a, d, v := missileWorld(t)
	a.StoredScore = 500000
	a.Fighters, a.Shields = MaxQuantity, MaxQuantity
	d.StoredScore = 0
	d.Missiles = 100
	intent, err := w.PrepareMissile(a.ID, 2, 1, v)
	if err != nil {
		t.Fatal(err)
	}
	out, err := w.CommitMissile(intent, v, func() float64 { return .5 }, clock)
	if err != nil || out.Counter.Launched != 6 || d.Missiles != 94 || a.Missiles != 9 || a.Death != nil {
		t.Fatal(out, a, d, err)
	}
	if len(v.revealed) != 0 {
		t.Fatal("return fire changed observation cache")
	}
}

func TestMissilePreflightSnapshotsPlanetOnReturnPath(t *testing.T) {
	w, a, d, v := missileWorld(t)
	a.StoredScore = 1
	d.Missiles = 1
	w.Sectors[a.Sector].Planet = 2
	w.Planets[2] = &Planet{Generation: uint64(2), ID: 2, Sector: a.Sector, Owner: a.ID, Name: "Home", Updated: clock, Ground: 100}

	intent, err := w.PrepareMissile(a.ID, d.Sector, 1, v)
	if err != nil {
		t.Fatal(err)
	}
	if len(intent.Sectors) != 1 || len(intent.Sectors[0].Ships) != 1 || len(intent.Sectors[0].Ships[0].ReturnSectors) != 1 {
		t.Fatal("return route and its sectors were not captured", intent)
	}
	if got := intent.Sectors[0].Ships[0].ReturnSectors[0].Planet; got == nil || got.ID != 2 {
		t.Fatal("return-path planet snapshot missing", intent.Sectors[0].Ships[0].ReturnSectors)
	}
}
